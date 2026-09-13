"""Iteration 38 frontend verification for long-video upload recovery and preview readiness.

Scope:
- Real >100MB upload via studio file import using resumable 4MiB chunks
- Intentional chunk fault injection (test-only) and retry resume behavior
- Preview wait overlay flows: cancel, local play, audio-only, timed-out manual launch
- Responsive checks for wait overlay actions (320/768/1024/1440)

Safety:
- Unsaved in-memory fixture; project writes are aborted.
- App APIs are real except explicit chunk fault injection inside this test.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import os
import struct
import subprocess
from pathlib import Path

from dotenv import load_dotenv
from playwright.async_api import async_playwright


load_dotenv("/app/frontend/.env")
BASE = os.environ["REACT_APP_BACKEND_URL"].rstrip("/")
OUT = Path("/app/test_reports/frontend_long_preview_iter38.json")
SRC = Path("/root/beatcut-test-assets/h264_longgop_1280x720_185s.mp4")
PADDED = Path("/root/beatcut-test-assets/h264_longgop_1280x720_185s_110mb.mp4")
TARGET_SIZE = 110_000_000

DEMO_EMAIL = "demo@beatcut.fr"
DEMO_PASSWORD = "Demo1234!"


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            block = f.read(1024 * 1024)
            if not block:
                break
            h.update(block)
    return h.hexdigest()


def _ensure_assets(report: dict) -> None:
    if not SRC.exists():
        subprocess.run(["python", "/app/frontend/tests/generate_long_gop_assets.py"], check=True)
    if not SRC.exists():
        raise RuntimeError("Missing source asset after generation")

    if PADDED.exists() and PADDED.stat().st_size == TARGET_SIZE:
        report["asset"] = {
            "source": str(SRC),
            "source_size": SRC.stat().st_size,
            "source_sha256": _sha256(SRC),
            "padded": str(PADDED),
            "padded_size": PADDED.stat().st_size,
            "padded_sha256": _sha256(PADDED),
            "generated": False,
        }
        return

    src_size = SRC.stat().st_size
    if src_size >= TARGET_SIZE:
        PADDED.write_bytes(SRC.read_bytes())
    else:
        payload = TARGET_SIZE - src_size - 8
        if payload < 0:
            payload = 0
        with SRC.open("rb") as r, PADDED.open("wb") as w:
            while True:
                chunk = r.read(1024 * 1024)
                if not chunk:
                    break
                w.write(chunk)
            # ISO BMFF free box, preserving valid MP4 structure.
            box_size = payload + 8
            w.write(struct.pack(">I4s", box_size, b"free"))
            if payload:
                w.write(b"\x00" * payload)

    report["asset"] = {
        "source": str(SRC),
        "source_size": SRC.stat().st_size,
        "source_sha256": _sha256(SRC),
        "padded": str(PADDED),
        "padded_size": PADDED.stat().st_size,
        "padded_sha256": _sha256(PADDED),
        "generated": True,
    }


def _check(cond: bool, msg: str) -> None:
    if not cond:
        raise AssertionError(msg)


async def _ensure_login(page, report: dict) -> None:
    await page.goto(BASE + "/login", wait_until="domcontentloaded")
    await page.wait_for_timeout(1200)
    if await page.locator('[data-testid="auth-email-input"]').count():
        await page.get_by_test_id("auth-email-input").fill(DEMO_EMAIL)
        await page.get_by_test_id("auth-password-input").fill(DEMO_PASSWORD)
        await page.get_by_test_id("auth-submit-button").click()
        await page.wait_for_timeout(1800)
        report.setdefault("checks", []).append("login_ok")


async def _open_studio_frame(page):
    await page.goto(BASE + "/studio", wait_until="domcontentloaded")
    iframe_el = await page.wait_for_selector('[data-testid="studio-iframe"]', timeout=30000)
    frame = await iframe_el.content_frame()
    await frame.wait_for_function(
        """() => typeof DB!=='undefined' && DB.projectQuota!==undefined && window.PreviewReadiness""",
        polling=100,
        timeout=60000,
    )
    return frame


async def _setup_fixture(frame):
    await frame.evaluate(
        """() => {
      stopAll();
      restoreIncomplete=true;
      if(!audioCtx) audioCtx = new AudioContext();
      const sr = audioCtx.sampleRate || 48000;
      const dur = 30;
      buffer = audioCtx.createBuffer(1, Math.floor(sr*dur), sr);
      const a = buffer.getChannelData(0);
      for(let i=0;i<a.length;i++) a[i]=0.05*Math.sin(2*Math.PI*440*i/sr);
      ext = {start:0,dur:12};
      startOff = 0;
      bpm = 120;
      beats = Array.from({length:96}, (_,i)=>i*0.5);
      M = {
        id:'qa-iter38-long-unsaved',
        title:'QA Iter38 Long Unsaved',
        format:'169',
        words:[],
        cuts:[],
        plans:[],
        fx:{},
        _loaded:true
      };
      DB.morceaux = DB.morceaux.filter(x => x.id !== M.id);
      DB.morceaux.push(M);
      loadedFor = M.id;
      go('edit/'+M.id);
      const pv=document.getElementById('preview');
      const ad=document.getElementById('audioDrop');
      if(pv) pv.style.display='block';
      if(ad) ad.style.display='none';
    }"""
    )
    await frame.wait_for_timeout(900)


async def _dismiss_tutorial_if_any(frame, report: dict):
    try:
        skip = frame.get_by_test_id("mob-tuto-skip")
        if await skip.is_visible(timeout=1200):
            await skip.click()
            await frame.get_by_test_id("mob-tutorial-overlay").wait_for(state="hidden", timeout=8000)
            report.setdefault("checks", []).append("tutorial_dismissed")
    except Exception:
        pass


async def _wait_clip_ready(frame):
    await frame.wait_for_function(
        """() => {
      const c = clips && clips[0];
      return !!(c && c.mediaId && !c._optimizing && c._wcReady);
    }""",
        polling=200,
        timeout=420000,
    )


async def _reset_preview_readiness(frame):
    await frame.evaluate(
        """() => {
      window.PreviewReadiness = window.createPreviewReadiness({
        get project(){return M;},
        get range(){return {start:ext.start,dur:ext.dur};},
        used(from=ext.start){
          const used=new Set(((M&&M.plans)||[]).filter(p=>p.end>from&&p.start<ext.start+ext.dur&&p.clip!=null).map(p=>p.clip));
          return [...used].map(index=>({index,clip:clips[index]}));
        },
        stop:stopAll,
        play:from=>play(from),
        audio:()=>startLoop(true),
        prepare:ensureClipProxy,
        retry(c){if(c.mediaId)ensureClipProxy(c,true);else if(c.pexelsUrl)startPexelsImport(c);else retryClipUpload(clips.indexOf(c));}
      });
    }"""
    )


async def _collect_proxy(page, media_id: str, report: dict) -> None:
    proxy_resp = await page.request.post(BASE + f"/api/media/proxy/{media_id}")
    report.setdefault("proxy", {})["first_status"] = proxy_resp.status
    if proxy_resp.status != 200:
        return
    data = await proxy_resp.json()
    for _ in range(80):
        if data.get("proxy_id"):
            report.setdefault("proxy", {})["proxy_id"] = data.get("proxy_id")
            report.setdefault("proxy", {})["status"] = data.get("status")
            return
        await asyncio.sleep(2)
        r = await page.request.post(BASE + f"/api/media/proxy/{media_id}")
        if r.status != 200:
            continue
        data = await r.json()
    report.setdefault("proxy", {})["status"] = data.get("status")


async def main():
    report = {
        "status": "running",
        "checks": [],
        "fault_injection": {"enabled": True, "scope": "PUT /api/media/uploads/{id}/chunks/1 first 3 attempts"},
        "chunk_stats": {},
        "responsive": {},
        "notes": ["Project writes aborted in test context", "Real app APIs used except explicit chunk fault injection"],
    }

    _ensure_assets(report)

    async with async_playwright() as p:
        browser = await p.chromium.launch(executable_path="/usr/bin/google-chrome", headless=True)
        context = await browser.new_context(viewport={"width": 1920, "height": 1080})

        async def protect_project_writes(route):
            if "/api/projects" in route.request.url and route.request.method != "GET":
                await route.abort()
            else:
                await route.continue_()

        upload_state = {
            "init_upload_ids": [],
            "chunk_attempts": {},
            "chunk0_count": {},
            "max_chunk_size": 0,
            "min_chunk_size": None,
            "media_upload_calls": 0,
            "target_upload": None,
            "fault_count": 0,
            "fault_done": False,
        }

        async def upload_observer(route):
            req = route.request
            url = req.url
            method = req.method

            if method == "POST" and url.endswith("/api/media/upload"):
                upload_state["media_upload_calls"] += 1

            if method == "POST" and "/api/media/uploads" in url and url.rstrip("/").endswith("/api/media/uploads"):
                try:
                    body = req.post_data_json
                    uid = body.get("upload_id")
                    if uid:
                        upload_state["init_upload_ids"].append(uid)
                        if upload_state["target_upload"] is None:
                            upload_state["target_upload"] = uid
                except Exception:
                    pass
                await route.continue_()
                return

            if method == "PUT" and "/api/media/uploads/" in url and "/chunks/" in url:
                parts = url.split("/api/media/uploads/")[-1]
                uid, chunk_part = parts.split("/chunks/")
                try:
                    idx = int(chunk_part.split("?")[0])
                except Exception:
                    idx = -1
                body = req.post_data_buffer
                size = len(body or b"")
                upload_state["max_chunk_size"] = max(upload_state["max_chunk_size"], size)
                if upload_state["min_chunk_size"] is None:
                    upload_state["min_chunk_size"] = size
                else:
                    upload_state["min_chunk_size"] = min(upload_state["min_chunk_size"], size)

                key = f"{uid}:{idx}"
                upload_state["chunk_attempts"][key] = upload_state["chunk_attempts"].get(key, 0) + 1
                if idx == 0:
                    upload_state["chunk0_count"][uid] = upload_state["chunk0_count"].get(uid, 0) + 1

                if uid == upload_state["target_upload"] and idx == 1 and upload_state["fault_count"] < 3:
                    upload_state["fault_count"] += 1
                    if upload_state["fault_count"] >= 3:
                        upload_state["fault_done"] = True
                    await route.abort("failed")
                    return

                await route.continue_()
                return

            await route.continue_()

        await context.route("**/*", protect_project_writes)
        await context.route("**/api/media/uploads**", upload_observer)
        await context.route("**/api/media/upload", upload_observer)

        page = await context.new_page()
        page.on("pageerror", lambda e: report.setdefault("runtime_errors", []).append(str(e)))
        page.on("console", lambda m: report.setdefault("console", []).append(f"{m.type}:{m.text[:220]}"))

        try:
            await _ensure_login(page, report)
            frame = await _open_studio_frame(page)
            await _setup_fixture(frame)
            await _dismiss_tutorial_if_any(frame, report)
            report["checks"].append("studio_fixture_ready")

            await frame.set_input_files("#clipInput", str(PADDED))
            await frame.wait_for_timeout(2000)

            await frame.wait_for_selector('[data-testid="clip-save-failed-badge-0"]', timeout=240000)
            report["checks"].append("failed_badge_visible_after_fault")

            await _dismiss_tutorial_if_any(frame, report)
            await frame.get_by_test_id("clip-save-failed-badge-0").click()
            report["checks"].append("retry_clicked")

            await _wait_clip_ready(frame)
            report["checks"].append("clip_ready_after_retry")

            media_id = await frame.evaluate("() => clips[0] && clips[0].mediaId")
            _check(bool(media_id), "media_id missing after retry")
            report["media_id"] = media_id

            report["chunk_stats"] = {
                "init_upload_ids": upload_state["init_upload_ids"],
                "fault_count": upload_state["fault_count"],
                "fault_done": upload_state["fault_done"],
                "max_chunk_size": upload_state["max_chunk_size"],
                "min_chunk_size": upload_state["min_chunk_size"],
                "chunk0_count": upload_state["chunk0_count"],
                "media_upload_calls": upload_state["media_upload_calls"],
            }

            _check(upload_state["fault_count"] == 3, f"Expected 3 chunk faults, got {upload_state['fault_count']}")
            _check(upload_state["max_chunk_size"] <= 4 * 1024 * 1024, "Chunk exceeded 4MiB")
            _check(upload_state["media_upload_calls"] == 0, "Monolithic /api/media/upload should not be used")
            _check(len(upload_state["init_upload_ids"]) >= 2, "Expected init called again on retry")
            _check(
                upload_state["init_upload_ids"][0] == upload_state["init_upload_ids"][1],
                "Retry did not reuse same upload_id",
            )
            target = upload_state["init_upload_ids"][0]
            _check(upload_state["chunk0_count"].get(target, 0) == 1, "Chunk 0 was resent on retry")
            report["checks"].append("resumable_chunk_resume_verified")

            # Download hash capture (server-side stored media).
            dl = await page.request.get(BASE + f"/api/media/{media_id}")
            report["download"] = {"status": dl.status, "size": len(await dl.body()) if dl.status == 200 else 0}
            if dl.status == 200:
                body = await dl.body()
                report["download"]["sha256"] = hashlib.sha256(body).hexdigest()
                report["download"]["matches_local_padded"] = report["download"]["sha256"] == report["asset"]["padded_sha256"]

            await _collect_proxy(page, media_id, report)

            await frame.evaluate(
                """() => {
              const c = clips[0];
              M.plans=[{start:0,end:8,clip:0,seek:Math.min((c&&c.wc&&c.wc.durationS-9)||0,30)}];
              ext={start:0,dur:12};
              startOff=0;
              stopAll();
              c._proxyState='failed';
              c._proxyError='forced-preview-failure';
              c.wcProxy=null;
              c._wcReady=true;
              renderClips();
            }"""
            )
            await frame.get_by_test_id("studio-play-button").click()
            await frame.wait_for_selector('[data-testid="preview-wait-overlay"]', timeout=15000)
            warn = await frame.get_by_test_id("preview-wait-local-warning").inner_text()
            _check("lecture" in warn.lower(), "Local warning missing")
            await frame.get_by_test_id("preview-wait-local").click()
            await frame.wait_for_timeout(1200)
            mode = await frame.get_by_test_id("preview-mode-status").inner_text()
            _check("locale" in mode.lower(), "Expected local preview mode status")
            await frame.get_by_test_id("studio-play-button").click()
            report["checks"].append("local_playback_from_failed_modal")

            # Audio-only immediate path.
            await _reset_preview_readiness(frame)
            await frame.evaluate(
                """() => {
              const c=clips[0];
              stopAll();
              c._proxyState='loading';
              c.wcProxy=null;
              c._proxyTried=true;
              c._wcReady=true;
              renderClips();
            }"""
            )
            await frame.get_by_test_id("studio-play-button").click()
            await frame.wait_for_selector('[data-testid="preview-wait-overlay"]', timeout=15000)
            await frame.get_by_test_id("preview-wait-audio").click()
            await frame.wait_for_timeout(700)
            audio_diag = await frame.evaluate("() => ({audioOnly: !!audioOnlyPreview, pump: !!wcPump, playing: !!playing})")
            _check(audio_diag["audioOnly"] is True and audio_diag["pump"] is False, f"Audio-only path invalid: {audio_diag}")
            await frame.evaluate("() => { const c=clips[0]; c._proxyState='ready'; c.wcProxy=c.wc; renderClips(); }")
            await frame.wait_for_timeout(700)
            still_audio = await frame.evaluate("() => ({audioOnly: !!audioOnlyPreview, playing: !!playing})")
            _check(still_audio["audioOnly"] is True and still_audio["playing"] is True, "Audio-only loop interrupted unexpectedly")
            await frame.get_by_test_id("studio-play-button").click()
            report["checks"].append("audio_only_immediate_and_no_wcpump")

            # Cancel prevents late autoplay, manual launch resumes.
            await _reset_preview_readiness(frame)
            await frame.evaluate(
                """() => {
              const c=clips[0];
              stopAll();
              c._proxyState='loading';
              c.wcProxy=null;
              c._proxyTried=true;
              renderClips();
            }"""
            )
            await frame.get_by_test_id("studio-play-button").click()
            await frame.wait_for_selector('[data-testid="preview-wait-overlay"]', timeout=15000)
            await frame.get_by_test_id("preview-wait-cancel").click()
            await frame.evaluate("() => { const c=clips[0]; c._proxyState='ready'; c.wcProxy=c.wc; renderClips(); }")
            await frame.wait_for_timeout(1200)
            state = await frame.evaluate("() => ({playing: !!playing})")
            _check(state["playing"] is False, "Late-ready autoplay happened after cancel")
            await frame.get_by_test_id("studio-play-button").click()
            await frame.wait_for_timeout(700)
            state2 = await frame.evaluate("() => ({playing: !!playing})")
            _check(state2["playing"] is True, "Manual play did not start")
            await frame.get_by_test_id("studio-play-button").click()
            report["checks"].append("cancel_blocks_late_autoplay_manual_resume_ok")

            # Deadline forced; overlay requires explicit launch.
            await _reset_preview_readiness(frame)
            await frame.evaluate(
                """() => {
              const c=clips[0];
              stopAll();
              c._proxyState='loading';
              c.wcProxy=null;
              c._proxyTried=true;
              renderClips();
            }"""
            )
            await frame.get_by_test_id("studio-play-button").click()
            await frame.wait_for_selector('[data-testid="preview-wait-overlay"]', timeout=15000)
            await frame.evaluate(
                """() => {
              const c=clips[0];
              if(window.PreviewReadiness && window.PreviewReadiness.pending){
                window.PreviewReadiness.pending.deadline = Date.now()-1000;
              }
              c._proxyState='ready';
              c.wcProxy=c.wc;
              renderClips();
            }"""
            )
            await frame.wait_for_timeout(500)
            primary_text = await frame.get_by_test_id("preview-wait-local").inner_text()
            _check("lancer" in primary_text.lower(), f"Expected manual launch button text, got: {primary_text}")
            await frame.get_by_test_id("preview-wait-local").click()
            await frame.wait_for_timeout(700)
            state3 = await frame.evaluate("() => ({playing: !!playing})")
            _check(state3["playing"] is True, "Manual launch after deadline did not start")
            await frame.get_by_test_id("studio-play-button").click()
            report["checks"].append("deadline_manual_launch_ok")

            # Responsive modal: no horizontal overflow + buttons >=44px.
            for width in (320, 768, 1024, 1440):
                await page.set_viewport_size({"width": width, "height": 900})
                await _reset_preview_readiness(frame)
                await frame.evaluate(
                    """() => {
                  const c=clips[0];
                  stopAll();
                  c._proxyState='loading';
                  c.wcProxy=null;
                  c._proxyTried=true;
                  c._wcReady=true;
                  renderClips();
                }"""
                )
                await frame.get_by_test_id("studio-play-button").click()
                await frame.wait_for_selector('[data-testid="preview-wait-overlay"]', timeout=15000)
                diag = await frame.evaluate(
                    """() => {
                  const ov=document.querySelector('[data-testid="preview-wait-overlay"]');
                  const btns=[...ov.querySelectorAll('button')].map(b=>({h:Math.round(b.getBoundingClientRect().height), t:b.textContent.trim()}));
                  return {
                    rootOverflow: document.documentElement.scrollWidth > document.documentElement.clientWidth + 1,
                    ovOverflow: ov.scrollWidth > ov.clientWidth + 1,
                    minBtnH: Math.min(...btns.map(x=>x.h)),
                    buttons: btns,
                  };
                }"""
                )
                report["responsive"][str(width)] = diag
                _check(diag["rootOverflow"] is False and diag["ovOverflow"] is False, f"Overflow at width {width}: {diag}")
                _check(diag["minBtnH"] >= 44, f"Button smaller than 44px at width {width}: {diag}")
                await frame.get_by_test_id("preview-wait-cancel").click()

            await page.set_viewport_size({"width": 1920, "height": 1080})
            report["checks"].append("responsive_wait_overlay_ok")

            report["status"] = "passed"
            print("PASS: Iteration38 long preview + resumable upload frontend verification")
        except Exception as exc:
            report["status"] = "failed"
            report["failure"] = str(exc)
            raise
        finally:
            OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
            await context.close()
            await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
