"""Historical iteration33 harness, superseded by test_long_preview_regression_iter34.py.

Do not use for acceptance: its scrub fixture used source time outside its timeline.
"""
from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path

from dotenv import load_dotenv
from playwright.async_api import async_playwright


load_dotenv(Path("/app/frontend/.env"))

BASE_URL = os.environ["REACT_APP_BACKEND_URL"].rstrip("/")
EMAIL = "demo@beatcut.fr"
PASSWORD = "Demo1234!"
ASSET_720 = Path("/root/beatcut-test-assets/h264_longgop_1280x720_185s.mp4")
OUT = Path("/app/test_reports/frontend_long_preview_regression_iter33.json")


async def _login(page):
    await page.goto(f"{BASE_URL}/login", wait_until="domcontentloaded")
    await page.wait_for_selector('[data-testid="auth-email-input"]', timeout=15000)
    await page.fill('[data-testid="auth-email-input"]', EMAIL)
    await page.fill('[data-testid="auth-password-input"]', PASSWORD)
    await page.click('[data-testid="auth-submit-button"]', force=True)
    await page.wait_for_timeout(1500)


async def _open_studio(page):
    await page.goto(f"{BASE_URL}/studio.html", wait_until="domcontentloaded")
    await page.wait_for_function("() => typeof addClip === 'function' && typeof SegPlayer === 'function'", timeout=40000)
    await page.wait_for_timeout(1200)


async def main():
    if not ASSET_720.exists():
        raise RuntimeError(f"Missing asset: {ASSET_720}")

    report = {
        "base_url": BASE_URL,
        "asset": str(ASSET_720),
        "autosave_blocked_for_safety": True,
        "steps": [],
        "network": {"proxy_calls": [], "media_fetch_calls": []},
    }

    async with async_playwright() as p:
        browser = await p.chromium.launch(executable_path="/usr/bin/google-chrome", headless=True)
        context = await browser.new_context(ignore_https_errors=True)
        page = await context.new_page()
        await page.set_viewport_size({"width": 1920, "height": 1080})

        # Safety only: block autosave writes to avoid overwriting user projects during regression.
        blocked = {"count": 0}

        async def route_handler(route):
            req = route.request
            url = req.url
            if "/api/projects" in url and req.method in {"POST", "PUT", "PATCH", "DELETE"}:
                blocked["count"] += 1
                await route.fulfill(status=204, content_type="application/json", body="{}")
                return
            await route.continue_()

        await page.route("**/*", route_handler)

        requests_seen = []
        page.on("request", lambda req: requests_seen.append(req.url))

        try:
            await _login(page)
            report["steps"].append({"name": "login", "ok": True})

            await _open_studio(page)
            report["steps"].append({"name": "open_studio", "ok": True})

            initial_count = await page.evaluate("() => (Array.isArray(clips) ? clips.length : 0)")

            await page.set_input_files("#clipInput", str(ASSET_720))
            await page.wait_for_function(
                "(n) => Array.isArray(clips) && clips.length > n",
                arg=initial_count,
                timeout=45000,
            )
            clip_index = await page.evaluate("() => Math.max(0, (clips.length || 1) - 1)")
            await page.wait_for_function(
                "(idx) => !!(clips[idx] && clips[idx].mediaId)",
                arg=clip_index,
                timeout=240000,
            )
            await page.wait_for_function(
                "(idx) => !!(clips[idx] && (clips[idx].wc || clips[idx]._wcFail))",
                arg=clip_index,
                timeout=120000,
            )

            pre_proxy = await page.evaluate(
                """(idx) => {
                const cl = clips[idx];
                window.__iter33_original_wc = cl.wc;
                return {
                  clipIndex: idx,
                  mediaId: cl.mediaId || null,
                  hasWc: !!cl.wc,
                  hasWcProxy: !!cl.wcProxy,
                  sampleCount: cl.wc && cl.wc.samples ? cl.wc.samples.length : 0,
                  durationS: cl.wc && cl.wc.durationS ? cl.wc.durationS : 0,
                };
              }""",
                clip_index,
            )
            assert pre_proxy["hasWc"], "Original wc should be ready after addClip"
            assert pre_proxy["sampleCount"] >= 4400, f"Unexpected sample count: {pre_proxy['sampleCount']}"
            report["import_pre_proxy"] = pre_proxy

            await page.wait_for_function(
                "(idx) => !!(clips[idx] && clips[idx].wcProxy && clips[idx].wcProxy.config)",
                arg=clip_index,
                timeout=360000,
            )

            proxy_state = await page.evaluate(
                """(idx) => {
                const cl = clips[idx];
                const wcPrevUsesProxy = (typeof wcPrev === 'function') ? (wcPrev(cl) === cl.wcProxy) : false;
                return {
                  clipIndex: idx,
                  mediaId: cl.mediaId || null,
                  hasWcProxy: !!cl.wcProxy,
                  wcStillOriginal: cl.wc === window.__iter33_original_wc,
                  wcPrevUsesProxy,
                  proxyDurationS: cl.wcProxy && cl.wcProxy.durationS ? cl.wcProxy.durationS : 0,
                  proxySamples: cl.wcProxy && cl.wcProxy.samples ? cl.wcProxy.samples.length : 0,
                };
              }""",
                clip_index,
            )
            assert proxy_state["hasWcProxy"], "wcProxy should be present"
            assert proxy_state["wcStillOriginal"], "clip.wc must remain original source"
            assert proxy_state["wcPrevUsesProxy"], "wcPrev should prefer proxy"
            report["proxy_state"] = proxy_state

            metrics = await page.evaluate(
                """async (idx) => {
                const sleep = (ms) => new Promise(r => setTimeout(r, ms));
                const cl = clips[idx];
                const src = cl.wc;
                const px = cl.wcProxy;

                async function runSet(wc, tag){
                  const pl = new SegPlayer();
                  pl.setClip(wc);
                  const seeks = [89.4, 90.45, 179, 184.99].map(t => Math.min(Math.max(0.05, t), Math.max(0.06, (wc.durationS || 0) - 0.01)));
                  const seekOut = [];
                  for (const t of seeks){
                    const t0 = performance.now();
                    pl.seek(t);
                    let f = null;
                    for (let i=0;i<520;i++){
                      pl.fill();
                      f = pl.frameAt(t);
                      if (f && pl.frames.length && pl.frames[0].timestamp > t*1e6) break;
                      await sleep(4);
                    }
                    seekOut.push({
                      target: t,
                      elapsedMs: Math.round(performance.now()-t0),
                      got: !!f,
                      ts: f ? +(f.timestamp/1e6).toFixed(3) : null,
                      err: pl.err || null,
                    });
                  }

                  // Budget check: frames+pending must remain bounded.
                  pl.seek(Math.min(90, Math.max(0.2, (wc.durationS || 10)/2)));
                  let maxTotal = 0, maxBudget = 0, breaches = 0;
                  const cap = pl.idle ? 5 : 14;
                  const budget = cap + Math.max(2, wc.reorderDepth || 0);
                  for (let i=0;i<220;i++){
                    pl.fill();
                    const total = pl.buffered() + (pl.pending || 0);
                    maxTotal = Math.max(maxTotal, total);
                    maxBudget = Math.max(maxBudget, budget);
                    if (total > budget) breaches++;
                    await sleep(8);
                  }

                  // EOF flush/drain and seek after EOF.
                  const eof = Math.max(0.05, (wc.durationS || 1) - 0.01);
                  const eofRuns = [];
                  for (let i=0;i<3;i++){
                    pl.seek(eof);
                    let f=null;
                    for (let j=0;j<420;j++){
                      pl.fill();
                      f = pl.frameAt(eof);
                      if (f && pl.drained && !pl.frames.length) break;
                      await sleep(5);
                    }
                    eofRuns.push({ got: !!f, drained: !!pl.drained, pending: pl.pending || 0, err: pl.err || null });
                  }

                  pl.seek((wc.durationS || 1) + 2.0);
                  let afterEof = null;
                  for (let i=0;i<360;i++){
                    pl.fill();
                    const f = pl.frameAt((wc.durationS || 1) + 2.0);
                    if (f){
                      afterEof = +(f.timestamp/1e6).toFixed(3);
                      break;
                    }
                    await sleep(5);
                  }

                  // Rapid cut sweeps (widely separated clusters).
                  const rapidTargets = [0.1,0.2,0.25,5.0,5.2,89.4,89.65,90.0,179.0,179.25,179.5]
                    .map(t => Math.min(Math.max(0.05, t), Math.max(0.06, (wc.durationS || 0)-0.01)));
                  const rapid = [];
                  for (const t of rapidTargets){
                    pl.seek(t);
                    let f = null;
                    for (let i=0;i<300;i++){
                      pl.fill();
                      f = pl.frameAt(t);
                      if (f) break;
                      await sleep(4);
                    }
                    rapid.push({target:t, got:!!f, ts:f?+(f.timestamp/1e6).toFixed(3):null, err:pl.err||null});
                  }

                  // 10s progression probe (decoder timestamps should progress, not stall).
                  const prog=[];
                  for (let t=0;t<=10;t+=1){
                    pl.seek(t);
                    let f=null;
                    for (let i=0;i<240;i++){
                      pl.fill();
                      f=pl.frameAt(t);
                      if (f) break;
                      await sleep(4);
                    }
                    prog.push(f?+(f.timestamp/1e6).toFixed(3):null);
                  }

                  pl.destroy();
                  return { tag, seekOut, maxTotal, maxBudget, budgetBreaches: breaches, eofRuns, afterEof, rapid, prog };
                }

                const srcM = await runSet(src, 'source');
                const pxM = await runSet(px, 'proxy');

                // Real scrub catch-up with drawPreview / curTime path.
                const cv = document.getElementById('preview');
                const sample = () => {
                  try {
                    if(!cv) return 'na';
                    const c = cv.getContext('2d', {willReadFrequently:true});
                    if(!c) return 'na';
                    const d = c.getImageData(Math.floor(cv.width*0.5), Math.floor(cv.height*0.5), 1, 1).data;
                    return `${d[0]}-${d[1]}-${d[2]}-${d[3]}`;
                  } catch (e) { return 'na'; }
                };
                const oldM = M;
                const oldStartOff = startOff;
                const oldPlaying = playing;
                const oldLooping = looping;
                M = Object.assign({}, M || {}, {
                  plans: [{ start: 0, end: Math.min(12, Math.max(1, px.durationS || 12)), clip: idx, seek: 85.0 }],
                });
                playing = false;
                looping = false;
                wcReset();
                const scrubTargets = [90, 89.4, 89.5, 90.45].map(t => Math.min(Math.max(0.05, t), Math.max(0.06, (px.durationS || 0)-0.01)));
                const scrub = [];
                for (const t of scrubTargets){
                  const before = sample();
                  startOff = t;
                  drawPreview(t);
                  await sleep(220);
                  const after = sample();
                  const fts = (wcScrub && wcScrub.cur) ? +(wcScrub.cur.timestamp/1e6).toFixed(3) : null;
                  scrub.push({ target:t, before, after, changed: before!==after, frameTs: fts });
                }
                await sleep(3200);
                const t2 = Math.min(Math.max(0.05, scrubTargets[scrubTargets.length-1] + 0.08), Math.max(0.06, (px.durationS || 0)-0.01));
                const b2 = sample();
                startOff = t2;
                drawPreview(t2);
                await sleep(240);
                const a2 = sample();
                scrub.push({ target:t2, before:b2, after:a2, changed:b2!==a2, frameTs:(wcScrub && wcScrub.cur)?+(wcScrub.cur.timestamp/1e6).toFixed(3):null, postPause:true });
                M = oldM;
                startOff = oldStartOff;
                playing = oldPlaying;
                looping = oldLooping;

                await sleep(250);
                return {
                  srcM,
                  pxM,
                  scrub,
                  redrawTimerLeaked: _wcRedrawTimer !== null,
                  wcPool,
                  mobilePoolExpected: /iPhone|iPad|iPod|Android/i.test(navigator.userAgent) ? 4 : 8,
                };
              }""",
                clip_index,
            )
            report["decoder_metrics"] = metrics

            # Assertions
            for mode in ("srcM", "pxM"):
                m = metrics[mode]
                assert all(x["got"] for x in m["seekOut"]), f"{mode} missing seek frames: {m['seekOut']}"
                assert m["budgetBreaches"] == 0, f"{mode} exceeded frame budget: {m['budgetBreaches']}"
                assert all(x["got"] and x["drained"] and x["pending"] == 0 for x in m["eofRuns"]), f"{mode} eof drain issue"
                assert m["afterEof"] is not None, f"{mode} seek after EOF produced no frame"
                assert all(x["got"] for x in m["rapid"]), f"{mode} rapid seek gaps"

            prog = [x for x in metrics["pxM"]["prog"] if x is not None]
            assert len(prog) >= 8, f"Proxy progression sparse: {metrics['pxM']['prog']}"
            assert prog[-1] > prog[0], f"Proxy progression did not advance: {prog}"

            assert all(x["frameTs"] is not None for x in metrics["scrub"]), f"Scrub frame timestamps missing: {metrics['scrub']}"
            assert not metrics["redrawTimerLeaked"], "wcScrub redraw timer leak detected"

            proxy_calls = [u for u in requests_seen if "/api/media/proxy/" in u]
            media_calls = [u for u in requests_seen if "/api/media/" in u and "/status" not in u and "/proxy/" not in u]
            report["network"]["proxy_calls"] = proxy_calls
            report["network"]["media_fetch_calls"] = media_calls
            assert any(f"/api/media/proxy/{pre_proxy['mediaId']}" in u for u in proxy_calls), "Missing /api/media/proxy call"
            assert any("/api/media/" in u for u in media_calls), "Missing /api/media/{proxy_id} fetch"

            # Mobile UA check (Chrome emulation, not real iPhone).
            mobile_ctx = await browser.new_context(
                ignore_https_errors=True,
                user_agent=(
                    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
                    "AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/151.0.0.0 Mobile/15E148 Safari/604.1"
                ),
                viewport={"width": 390, "height": 844},
            )
            mobile_page = await mobile_ctx.new_page()
            await _open_studio(mobile_page)
            mobile_pool = await mobile_page.evaluate("() => ({ua:navigator.userAgent, wcPool:WC_POOL})")
            await mobile_ctx.close()
            report["mobile_chrome_emulation"] = {
                "note": "Chrome mobile UA emulation only, not real iPhone runtime",
                "ua": mobile_pool["ua"],
                "wc_pool": mobile_pool["wcPool"],
            }
            assert mobile_pool["wcPool"] == 4, f"Expected mobile WC_POOL=4, got {mobile_pool['wcPool']}"

            report["autosave_blocked_count"] = blocked["count"]
            report["status"] = "passed"

        finally:
            await context.close()
            await browser.close()

    OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    asyncio.run(main())
