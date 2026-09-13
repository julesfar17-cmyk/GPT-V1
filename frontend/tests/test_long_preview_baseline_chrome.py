"""Baseline Chrome harness for long imported-video preview freeze reproduction.

Runs against public URL, logs in once, then exercises studio WebCodecs parser/decoder
with a real 185s long-GOP H264 asset. Also verifies upload->proxy integration call path.
"""
from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path

from playwright.async_api import async_playwright


BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
EMAIL = "demo@beatcut.fr"
PASSWORD = "Demo1234!"
ASSET_MANIFEST = Path("/root/beatcut-test-assets/manifest.json")
RESULT_FILE = Path("/app/test_reports/frontend_long_preview_baseline_iter32.json")
SCREENSHOT = Path("/app/test_reports/frontend_long_preview_iter32.jpeg")
STUDIO_PROJECT_ID = "032e4762018d45"
BACKEND_MEDIA_IDS = Path("/app/test_reports/iter32_backend_media_ids.json")


def _require_manifest() -> dict:
    if not ASSET_MANIFEST.exists():
        raise RuntimeError(
            "Missing long-video assets. Run: python /app/frontend/tests/generate_long_gop_assets.py"
        )
    data = json.loads(ASSET_MANIFEST.read_text(encoding="utf-8"))
    for k in ("h264_720", "h264_800"):
        if not Path(data[k]).exists():
            raise RuntimeError(f"Asset missing on disk: {data[k]}")
    return data


async def _login(page) -> None:
    await page.goto(f"{BASE_URL}/login", wait_until="domcontentloaded")
    await page.wait_for_selector('[data-testid="auth-email-input"]', timeout=15000)
    await page.fill('[data-testid="auth-email-input"]', EMAIL)
    await page.fill('[data-testid="auth-password-input"]', PASSWORD)
    await page.click('[data-testid="auth-submit-button"]', force=True)
    await page.wait_for_timeout(1500)


async def _open_studio(page) -> None:
    await page.goto(f"{BASE_URL}/studio.html", wait_until="domcontentloaded")
    await page.wait_for_function("() => typeof window.parseWC === 'function'", timeout=30000)
    await page.wait_for_timeout(1200)


async def _inject_fetch_probe(page) -> None:
    await page.evaluate(
        """() => {
        if (window.__origFetchForBaseline) return;
        window.__fetchLog = [];
        window.__origFetchForBaseline = window.fetch.bind(window);
        window.fetch = async (...args) => {
          const u = typeof args[0] === 'string' ? args[0] : (args[0] && args[0].url) || '';
          window.__fetchLog.push({ url: u, t: Date.now(), method: (args[1] && args[1].method) || 'GET' });
          return window.__origFetchForBaseline(...args);
        };
      }"""
    )


async def _collect_decoder_metrics(page, media_id: str) -> dict:
    return await page.evaluate(
        """async (mediaId) => {
        const sleep = (ms) => new Promise(r => setTimeout(r, ms));
        const resp = await fetch('/api/media/' + mediaId, { credentials: 'include' });
        if (!resp.ok) return { error: 'media_fetch_failed', status: resp.status };
        const blob = await resp.blob();
        const wc = await parseWC(blob);
        if (!wc || !wc.samples || !wc.samples.length) return { error: 'wc_not_ready', mediaId };

        const clip = { wc, wcProxy: null, name: 'baseline_from_api.mp4', mediaId };
        (window.clips = window.clips || []).push(clip);

        const durationS = wc.durationS || 0;
        const sampleCount = wc.samples.length;
        const firstTs = wc.samples[0].ts;
        const lastTs = wc.samples[wc.samples.length - 1].ts;

        const pl = new SegPlayer();
        pl.setClip(wc);

        const seekTargets = [10, 90, 170, Math.min(179, Math.max(0.1, durationS - 0.15))];
        const seekResults = [];
        for (const target of seekTargets) {
          const t0 = performance.now();
          pl.seek(target);
          let f = null;
          for (let i = 0; i < 450; i++) {
            pl.fill();
            f = pl.frameAt(target);
            if (f) break;
            await sleep(5);
          }
          seekResults.push({
            target,
            elapsedMs: Math.round(performance.now() - t0),
            gotFrame: !!f,
            frameTsSec: f ? +(f.timestamp / 1e6).toFixed(3) : null,
            decodeQueueSize: pl.dec ? pl.dec.decodeQueueSize : null,
            buffered: pl.buffered(),
            sampleIndex: pl.si,
          });
        }

        // Scrub behavior: backseek + small forward <=0.8s should avoid full reseek in wcScrubFrame path.
        const scrubTargets = [90, 89.4, 89.9, 90.45, 90.95, 90.2];
        const scrub = [];
        for (const t of scrubTargets) {
          const t0 = performance.now();
          const f = wcScrubFrame(clip, t);
          scrub.push({
            target: t,
            elapsedMs: Math.round(performance.now() - t0),
            gotFrame: !!f,
            frameTsSec: f ? +(f.timestamp / 1e6).toFixed(3) : null,
          buffered: null,
          });
          await sleep(40);
        }

        // Idle fill / queue growth probe at still target for 2s.
        pl.seek(Math.min(90, Math.max(0.2, durationS * 0.5)));
        let maxBuffered = 0;
        let maxDecodeQueue = 0;
        let decodeSubmittedSamples = 0;
        const tIdle0 = performance.now();
        while (performance.now() - tIdle0 < 2000) {
          pl.fill();
          maxBuffered = Math.max(maxBuffered, pl.buffered());
          if (pl.dec) maxDecodeQueue = Math.max(maxDecodeQueue, pl.dec.decodeQueueSize || 0);
          decodeSubmittedSamples = Math.max(decodeSubmittedSamples, pl.si);
          await sleep(15);
        }

        // Near EOF repeated seek/flush behavior.
        const eofTarget = Math.max(0.1, durationS - 0.12);
        const eofRepeats = [];
        for (let i = 0; i < 6; i++) {
          const t0 = performance.now();
          pl.seek(eofTarget);
          let f = null;
          for (let j = 0; j < 380; j++) {
            pl.fill();
            f = pl.frameAt(eofTarget);
            if (f) break;
            await sleep(6);
          }
          eofRepeats.push({
            i,
            elapsedMs: Math.round(performance.now() - t0),
            gotFrame: !!f,
            frameTsSec: f ? +(f.timestamp / 1e6).toFixed(3) : null,
            decodeQueueSize: pl.dec ? pl.dec.decodeQueueSize : null,
            buffered: pl.buffered(),
            sampleIndex: pl.si,
          });
        }

        // Rapid cuts probe: 0.1-0.25s step around beginning, middle, end.
        const mkSeries = (start, step, n) => Array.from({ length: n }, (_, i) => +(start + i * step).toFixed(3));
        const rapidTargets = [
          ...mkSeries(0.1, 0.12, 6),
          ...mkSeries(Math.max(0.2, durationS * 0.5), 0.15, 6),
          ...mkSeries(Math.max(0.2, durationS - 1.6), 0.2, 6),
        ].map(t => Math.min(Math.max(0.05, t), Math.max(0.06, durationS - 0.05)));

        const rapid = [];
        for (const t of rapidTargets) {
          const t0 = performance.now();
          pl.seek(t);
          let f = null;
          for (let j = 0; j < 320; j++) {
            pl.fill();
            f = pl.frameAt(t);
            if (f) break;
            await sleep(5);
          }
          rapid.push({
            target: t,
            elapsedMs: Math.round(performance.now() - t0),
            gotFrame: !!f,
            frameTsSec: f ? +(f.timestamp / 1e6).toFixed(3) : null,
          });
        }

        pl.destroy();
        return {
          clipName: clip.name || null,
          mediaId: clip.mediaId || null,
          durationS: +durationS.toFixed(3),
          sampleCount,
          firstTsSec: +(firstTs / 1e6).toFixed(3),
          lastTsSec: +(lastTs / 1e6).toFixed(3),
          tailGapSec: +(Math.max(0, durationS - (lastTs / 1e6))).toFixed(3),
          seekResults,
          scrub,
          idleProbe: { maxBuffered, maxDecodeQueue, decodeSubmittedSamples },
          eofRepeats,
          rapid,
        };
      }""",
        media_id,
    )


async def run() -> None:
    if not BASE_URL:
        raise RuntimeError("REACT_APP_BACKEND_URL is required")

    assets = _require_manifest()
    source_720 = assets["h264_720"]
    if not BACKEND_MEDIA_IDS.exists():
        raise RuntimeError("Missing /app/test_reports/iter32_backend_media_ids.json. Run backend baseline pytest first.")
    media_ids = json.loads(BACKEND_MEDIA_IDS.read_text(encoding="utf-8"))
    media_720_id = media_ids["h264_720"]
    results = {
        "base_url": BASE_URL,
        "chrome_binary": "/usr/bin/google-chrome",
        "steps": [],
    }

    async with async_playwright() as p:
        browser = await p.chromium.launch(executable_path="/usr/bin/google-chrome", headless=True)
        context = await browser.new_context(ignore_https_errors=True)
        page = await context.new_page()
        await page.set_viewport_size({"width": 1920, "height": 1080})
        page.on("console", lambda msg: print(f"CONSOLE[{msg.type}]: {msg.text}"))

        try:
            print("STEP: login")
            await _login(page)
            results["steps"].append({"name": "login", "ok": True})

            print("STEP: open studio")
            await _open_studio(page)
            await _inject_fetch_probe(page)
            await page.screenshot(path=str(SCREENSHOT), quality=40, full_page=False)
            results["steps"].append({"name": "open_studio", "ok": True})

            print("STEP: probe decoder support")
            support = await page.evaluate(
                """async () => {
                const out = { userAgent: navigator.userAgent };
                try {
                  const a = await VideoDecoder.isConfigSupported({codec:'avc1.4D401F', codedWidth:1280, codedHeight:720});
                  const b = await VideoDecoder.isConfigSupported({codec:'avc1.64001F', codedWidth:1280, codedHeight:720});
                  out.avc1_main = !!a.supported;
                  out.avc1_high = !!b.supported;
                } catch (e) {
                  out.error = String(e && e.message || e);
                }
                return out;
              }"""
            )
            results["decoder_support"] = support

            print("STEP: parse/decode baseline without server upload")
            parse_metrics = await _collect_decoder_metrics(page, media_720_id)
            results["parse_pass_wc_ready"] = parse_metrics.get("error") is None
            results["parse_decode_metrics"] = parse_metrics

            print("STEP: startClipUpload integration probe")
            integration = await page.evaluate(
                """async () => {
                const src = String(startClipUpload);
                const staticHasEnsure = src.includes('ensureClipProxy(');

                let ensureCalls = 0;
                let mediaStatusCalls = 0;
                const oldEnsure = window.ensureClipProxy;
                const oldApi = window.API;
                const oldSwap = window.swapClipMedia;
                const oldRender = window.renderClips;
                const oldDirty = window.dirty;
                const oldToast = window.toast;

                try {
                  window.ensureClipProxy = function(){ ensureCalls++; };
                  window.swapClipMedia = function(){};
                  window.renderClips = function(){};
                  window.dirty = function(){};
                  window.toast = function(){};
                  window.API = Object.assign({}, oldApi, {
                    uploadMedia: async () => 'TEST_MEDIA_ID_UPLOAD',
                    mediaStatus: async () => { mediaStatusCalls++; return { transcoded: true, skipped: true, failed: false }; },
                    fetchMedia: async () => null,
                  });

                  const clip = { name: 'integration_probe.mp4', thumbs: [], seeks: [], _wcParse: Promise.resolve() };
                  const fakeFile = new File([new Uint8Array([0,1,2,3])], 'integration_probe.mp4', { type: 'video/mp4' });
                  startClipUpload(clip, fakeFile);
                  await new Promise(r => setTimeout(r, 120));
                  return {
                    staticHasEnsure,
                    ensureCalls,
                    mediaStatusCalls,
                    clipMediaId: clip.mediaId || null,
                    clipOptimizing: !!clip._optimizing,
                    probeUsesMockedAPI: true,
                  };
                } finally {
                  window.ensureClipProxy = oldEnsure;
                  window.API = oldApi;
                  window.swapClipMedia = oldSwap;
                  window.renderClips = oldRender;
                  window.dirty = oldDirty;
                  window.toast = oldToast;
                }
              }"""
            )
            results["start_clip_upload_proxy_integration"] = integration

            error_text = await page.evaluate(
                """() => {
                const errorElements = Array.from(document.querySelectorAll('.error, [class*="error"], [id*="error"]'));
                return errorElements.map(el => el.textContent).join(', ');
                }"""
            )
            results["page_error_text"] = error_text
            if error_text:
                print(f"Found error message: {error_text}")
            else:
                print("No error messages found on the page")

        finally:
            await context.close()
            await browser.close()

    RESULT_FILE.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"Wrote baseline results to {RESULT_FILE}")


if __name__ == "__main__":
    asyncio.run(run())
