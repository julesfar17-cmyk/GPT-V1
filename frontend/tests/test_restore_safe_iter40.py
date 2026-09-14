"""Iteration 40: safe-restore regression (real API + targeted test-only network fault injection)."""

from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path

from dotenv import load_dotenv
from playwright.async_api import async_playwright


load_dotenv("/app/frontend/.env")
BASE = os.environ["REACT_APP_BACKEND_URL"].rstrip("/")
OUT = Path("/app/test_reports/frontend_restore_safe_iter40.json")

DEMO_EMAIL = "demo@beatcut.fr"
DEMO_PASSWORD = "Demo1234!"

CLIP_A = Path("/app/frontend/public/wc_test_a.mp4")
CLIP_B = Path("/app/frontend/public/wc_test_b.mp4")
AUDIO = Path("/app/test_reports/iter40_tone.wav")


def _check(cond: bool, msg: str):
    if not cond:
        raise AssertionError(msg)


async def _ensure_login(page, report: dict):
    await page.goto(BASE + "/login", wait_until="domcontentloaded")
    await page.wait_for_timeout(1200)
    if await page.locator('[data-testid="auth-email-input"]').count():
        await page.get_by_test_id("auth-email-input").fill(DEMO_EMAIL)
        await page.get_by_test_id("auth-password-input").fill(DEMO_PASSWORD)
        await page.get_by_test_id("auth-submit-button").click()
        await page.wait_for_timeout(1800)
    report.setdefault("checks", []).append("login_ok")


async def _open_studio_frame(page, project_id: str):
    await page.goto(BASE + f"/studio?project={project_id}", wait_until="domcontentloaded")
    iframe_el = await page.wait_for_selector('[data-testid="studio-iframe"]', timeout=45000)
    frame = await iframe_el.content_frame()
    await frame.wait_for_function(
        """() => typeof DB!=='undefined' && DB.projectQuota!==undefined && typeof PROJECT_RESTORE!=='undefined'""",
        polling=100,
        timeout=60000,
    )
    return frame


async def _dismiss_tutorial_if_any(frame):
    try:
        skip = frame.get_by_test_id("mob-tuto-skip")
        if await skip.is_visible(timeout=1200):
            await skip.click()
            await frame.get_by_test_id("mob-tutorial-overlay").wait_for(state="hidden", timeout=8000)
    except Exception:
        pass


async def _upload_media(page, path: Path, mime: str):
    payload = {
        "file": {
            "name": path.name,
            "mimeType": mime,
            "buffer": path.read_bytes(),
        }
    }
    r = await page.request.post(BASE + "/api/media/upload", multipart=payload)
    _check(r.status == 200, f"upload failed {path.name}: {r.status} {await r.text()}")
    data = await r.json()
    media_id = data.get("media_id")
    _check(bool(media_id), f"missing media_id for {path.name}: {data}")
    return media_id


async def _create_project(page, title: str, state: dict):
    r = await page.request.post(
        BASE + "/api/projects",
        data={
            "title": title,
            "state": state,
            "client_id": f"iter40-{title}",
            "seq": 1,
        },
    )
    _check(r.status == 200, f"project create failed {r.status}: {await r.text()}")
    data = await r.json()
    pid = data.get("project_id") or data.get("id")
    _check(bool(pid), f"missing project id in response: {data}")
    return pid


async def _get_project(page, project_id: str):
    r = await page.request.get(BASE + f"/api/projects/{project_id}")
    _check(r.status == 200, f"project get failed {project_id}: {r.status}")
    return await r.json()


async def _delete_project(page, project_id: str):
    r = await page.request.delete(BASE + f"/api/projects/{project_id}")
    return r.status


async def main():
    report = {
        "status": "running",
        "checks": [],
        "created_projects": [],
        "fault_injection": {
            "enabled": True,
            "type": "first GET /api/media/{videoA}",
        },
    }

    _check(CLIP_A.exists() and CLIP_B.exists() and AUDIO.exists(), "Missing iter40 fixtures")

    async with async_playwright() as p:
        browser = await p.chromium.launch(executable_path="/usr/bin/google-chrome", headless=True)
        context = await browser.new_context(viewport={"width": 1920, "height": 1080})
        page = await context.new_page()
        page.on("pageerror", lambda e: report.setdefault("runtime_errors", []).append(str(e)))

        post_events = []
        response_events = []
        route_state = {
            "video_a": None,
            "fail_enabled": True,
            "failed_count": 0,
            "track_project_posts": True,
            "media_get_urls": [],
        }

        async def route_guard(route):
            req = route.request
            url = req.url
            if route_state["track_project_posts"] and req.method == "POST" and "/api/projects" in url:
                post_events.append({"url": url})
            if req.method == "GET" and "/api/media" in url:
                route_state["media_get_urls"].append(url)
            if (
                route_state["fail_enabled"]
                and route_state["video_a"]
                and req.method == "GET"
                and "/api/media/" in url
                and route_state["video_a"] in url
            ):
                route_state["failed_count"] += 1
                await route.abort("failed")
                return
            await route.continue_()

        await context.route("**/*", route_guard)
        page.on(
            "response",
            lambda resp: response_events.append(
                {"url": resp.url, "status": resp.status, "method": resp.request.method}
            )
            if "/api/projects" in resp.url and resp.request.method == "POST"
            else None,
        )

        project_1 = None
        project_2 = None

        try:
            await _ensure_login(page, report)

            audio_id = await _upload_media(page, AUDIO, "audio/wav")
            clip_a_id = await _upload_media(page, CLIP_A, "video/mp4")
            clip_b_id = await _upload_media(page, CLIP_B, "video/mp4")
            route_state["video_a"] = clip_a_id
            report["media_ids"] = {"audio": audio_id, "clip_a": clip_a_id, "clip_b": clip_b_id}

            state1 = {
                "v2": True,
                "bpm": 123,
                "format": "916",
                "ext": {"start": 0.8, "dur": 3.6},
                "words": [
                    {"text": "alpha", "start": 0.9, "end": 1.2, "hardEnd": True},
                    {"text": "beta", "start": 1.2, "end": 1.6, "hardEnd": True, "emphasis": {"weight": 700}},
                    {"text": "gamma", "start": 1.6, "end": 2.2, "hardEnd": True},
                ],
                "cuts": [{"time": 0.9, "source": "manual"}, {"time": 1.6, "source": "manual"}],
                "plans": [
                    {"start": 0.8, "end": 2.0, "clip": 0, "seek": 0.5, "locked": True},
                    {"start": 2.0, "end": 4.4, "clip": 1, "seek": 0.8, "locked": True},
                ],
                "audioMediaId": audio_id,
                "audioName": AUDIO.name,
                "clipRefs": [
                    {"mediaId": clip_a_id, "name": CLIP_A.name, "crop": {"x": 0.12, "y": -0.08}},
                    {"mediaId": clip_b_id, "name": CLIP_B.name, "crop": {"x": -0.15, "y": 0.05}},
                ],
            }
            project_1 = await _create_project(page, "QA_DISPOSABLE_ITER40_RESTORE_1", state1)
            report["created_projects"].append(project_1)

            baseline = await _get_project(page, project_1)
            report["baseline_updated_at"] = baseline.get("updated_at")

            frame = await _open_studio_frame(page, project_1)
            await _dismiss_tutorial_if_any(frame)

            await frame.wait_for_selector('[data-testid="missing-clip-0"]', timeout=90000)
            await frame.wait_for_function(
                """() => {
                  const b=document.getElementById('restoreRetry');
                  return !!(b && getComputedStyle(b).display!=='none');
                }""",
                timeout=90000,
            )
            await frame.wait_for_timeout(900)

            blocked_diag = await frame.evaluate(
                """() => ({
                  restoreIncomplete: !!restoreIncomplete,
                  canPersist: !!canPersist(),
                  saveState: (document.getElementById('saveState')||{}).textContent || '',
                  plans: (M.plans||[]).map(p=>p.clip),
                  words: (M.words||[]).map(w=>w.text),
                  clip0Missing: !!document.querySelector('[data-testid="missing-clip-0"]'),
                  clip1Missing: !!document.querySelector('[data-testid="missing-clip-1"]'),
                  clip1Crop: clips[1]?.crop || null,
                  clipMediaIds: clips.map(c=>c.mediaId||null)
                })"""
            )
            report["fault_injection"]["failed_count"] = route_state["failed_count"]
            report["fault_injection"]["media_get_urls"] = route_state["media_get_urls"][:20]
            _check(route_state["failed_count"] >= 1, f"Fault injection did not trigger. Media GETs: {route_state['media_get_urls'][:20]}")
            _check(blocked_diag["restoreIncomplete"] is True, f"restoreIncomplete should be true: {blocked_diag}")
            _check(blocked_diag["canPersist"] is False, f"canPersist should be false while missing: {blocked_diag}")
            _check(blocked_diag["clip0Missing"] is True, "slot0 should be missing after injected fault")
            _check(blocked_diag["clip1Missing"] is False, "slot1 should stay loaded")
            _check(blocked_diag["plans"] == [0, 1], f"plan clip indices changed unexpectedly: {blocked_diag['plans']}")
            report["blocked_diag"] = blocked_diag
            report["checks"].append("missing_slot_persists_and_plan_indices_preserved")

            await asyncio.sleep(1.8)
            _check(len(post_events) == 0, f"Unexpected /api/projects POST during incomplete restore: {post_events}")
            report["checks"].append("no_project_write_during_incomplete_restore")

            await frame.evaluate("""() => { M.words[0].text='alpha_edited_while_missing'; dirty(); }""")
            await frame.wait_for_timeout(1200)
            after_edit = await frame.evaluate(
                """() => ({canPersist: !!canPersist(), saveState: document.getElementById('saveState')?.textContent || ''})"""
            )
            _check(after_edit["canPersist"] is False, f"editing while missing should remain blocked: {after_edit}")
            _check(len(post_events) == 0, "Word edit while missing triggered unexpected save POST")
            report["checks"].append("edit_while_missing_kept_blocked")

            route_state["fail_enabled"] = False
            if await frame.locator('[data-testid="missing-clip-retry-0"]').count():
                await frame.get_by_test_id("missing-clip-retry-0").click(force=True)
            else:
                await frame.get_by_test_id("restore-retry-button").click(force=True)

            await frame.wait_for_timeout(5000)
            if await frame.locator('[data-testid="missing-clip-0"]').count():
                await frame.evaluate("""() => retryMissingClip(0)""")

            await frame.wait_for_function(
                """() => !document.querySelector('[data-testid="missing-clip-0"]') && !restoreIncomplete && canPersist()""",
                timeout=90000,
            )
            await frame.wait_for_timeout(1800)

            project_posts = [e for e in response_events if e["status"] == 200]
            _check(len(project_posts) >= 1, "Expected autosave POST after successful recovery")
            save_text = await frame.locator('[data-testid="save-state"]').inner_text()
            _check(("Enregistr" in save_text) or ("SAVED" in save_text.upper()), f"Expected saved state after successful save, got: {save_text}")
            report["checks"].append("retry_recovers_exact_slot_and_autosave_runs")

            latest = await _get_project(page, project_1)
            latest_state = latest.get("state") or {}
            _check((latest_state.get("words") or [])[0]["text"] == "alpha_edited_while_missing", "Edited word not persisted")
            _check((latest_state.get("plans") or [{}])[0].get("clip") == 0, "Plan[0].clip changed unexpectedly")
            _check((latest_state.get("plans") or [{}, {}])[1].get("clip") == 1, "Plan[1].clip changed unexpectedly")

            storage = await context.storage_state()
            await context.close()

            fresh = await browser.new_context(storage_state=storage, viewport={"width": 1920, "height": 1080})
            fresh_page = await fresh.new_page()
            fresh_frame = await _open_studio_frame(fresh_page, project_1)
            await _dismiss_tutorial_if_any(fresh_frame)
            await fresh_frame.wait_for_timeout(1500)
            reopened = await fresh_frame.evaluate(
                """() => ({
                  words:(M.words||[]).map(w=>w.text),
                  plans:(M.plans||[]).map(p=>p.clip),
                  ext:{...ext},
                  bpm,
                  mediaIds:clips.map(c=>c.mediaId||null),
                  crops:clips.map(c=>c.crop||null)
                })"""
            )
            _check(reopened["words"][0] == "alpha_edited_while_missing", f"reopen word mismatch: {reopened}")
            _check(reopened["plans"] == [0, 1], f"reopen plan indices mismatch: {reopened['plans']}")
            _check(reopened["mediaIds"][:2] == [clip_a_id, clip_b_id], f"reopen media ids mismatch: {reopened['mediaIds']}")
            report["checks"].append("fresh_context_reopen_exact_state_ok")
            await fresh.close()

            context = await browser.new_context(viewport={"width": 1920, "height": 1080})
            page = await context.new_page()
            await _ensure_login(page, report)

            state2 = {
                "v2": True,
                "bpm": 120,
                "format": "916",
                "ext": {"start": 0.5, "dur": 3.0},
                "words": [{"text": "delta", "start": 0.6, "end": 1.2, "hardEnd": True}],
                "cuts": [{"time": 0.6, "source": "manual"}],
                "plans": [
                    {"start": 0.5, "end": 1.7, "clip": 0, "seek": 0.4, "locked": True},
                    {"start": 1.7, "end": 3.5, "clip": 1, "seek": 0.7, "locked": True},
                ],
                "audioMediaId": audio_id,
                "audioName": AUDIO.name,
                "clipRefs": [
                    {"mediaId": clip_b_id, "name": CLIP_B.name, "crop": {"x": 0.0, "y": 0.0}},
                    {"name": "missing_no_ref.mp4", "crop": {"x": 0.22, "y": -0.1}},
                ],
            }
            project_2 = await _create_project(page, "QA_DISPOSABLE_ITER40_RESTORE_2", state2)
            report["created_projects"].append(project_2)

            frame2 = await _open_studio_frame(page, project_2)
            await _dismiss_tutorial_if_any(frame2)
            await frame2.wait_for_selector('[data-testid="missing-clip-1"]', timeout=90000)

            await frame2.get_by_test_id("missing-clip-retry-1").click(force=True)
            await frame2.wait_for_timeout(1300)
            still_blocked = await frame2.evaluate("""() => ({blocked: !!restoreIncomplete, hasMissing: !!document.querySelector('[data-testid="missing-clip-1"]')})""")
            _check(still_blocked["blocked"] and still_blocked["hasMissing"], f"retry without mediaId/url unlocked unexpectedly: {still_blocked}")

            await frame2.set_input_files("#clipInput", str(CLIP_A))
            await frame2.wait_for_timeout(2500)
            unrelated_diag = await frame2.evaluate(
                """() => ({
                  blocked: !!restoreIncomplete,
                  hasMissing: !!document.querySelector('[data-testid="missing-clip-1"]'),
                  totalClips: clips.length
                })"""
            )
            _check(unrelated_diag["blocked"] and unrelated_diag["hasMissing"], f"Unrelated import should not satisfy missing slot: {unrelated_diag}")
            report["checks"].append("partial_retry_and_unrelated_import_do_not_unlock")

            cancel_seen = {"done": False}

            def cancel_dialog(d):
                cancel_seen["done"] = True
                asyncio.create_task(d.dismiss())

            page.once("dialog", cancel_dialog)
            missing_remove = frame2.locator('[data-testid^="missing-clip-remove-"]').first
            _check(await missing_remove.count() >= 1, "Missing remove button not found")
            await missing_remove.click(force=True)
            await frame2.wait_for_timeout(700)
            _check(cancel_seen["done"], "Expected confirm dialog on missing reference remove (cancel phase)")
            after_cancel = await frame2.evaluate("""() => !!document.querySelector('[data-testid^="missing-clip-"]')""")
            _check(after_cancel is True, "Cancel remove should keep missing reference untouched")

            accept_seen = {"done": False}

            def accept_dialog(d):
                accept_seen["done"] = True
                asyncio.create_task(d.accept())

            page.once("dialog", accept_dialog)
            missing_remove2 = frame2.locator('[data-testid^="missing-clip-remove-"]').first
            await missing_remove2.click(force=True)
            await frame2.wait_for_timeout(1200)
            _check(accept_seen["done"], "Expected confirm dialog on missing reference remove (accept phase)")

            after_accept = await frame2.evaluate(
                """() => ({
                  hasMissing: !!document.querySelector('[data-testid^="missing-clip-"]'),
                  blocked: !!restoreIncomplete,
                  plans: (M.plans||[]).map(p=>p.clip)
                })"""
            )
            _check(after_accept["hasMissing"] is False, f"Accepted remove should clear missing slot: {after_accept}")
            _check(after_accept["blocked"] is False, f"Accepted remove should unblock save when nothing else missing: {after_accept}")
            _check(all((c is None) or (c in (0,)) for c in after_accept["plans"]), f"Plan indices not updated after remove: {after_accept['plans']}")
            report["checks"].append("missing_reference_remove_confirm_flow_ok")

            report["post_events"] = post_events
            report["project_post_responses"] = response_events
            report["status"] = "passed"
            print("PASS: Iteration40 safe-restore critical scenarios")

        except Exception as exc:
            report["status"] = "failed"
            report["failure"] = str(exc)
            raise
        finally:
            try:
                if project_2:
                    report.setdefault("cleanup", {})[project_2] = await _delete_project(page, project_2)
            except Exception as e:
                report.setdefault("cleanup_errors", []).append(f"{project_2}: {e}")
            try:
                if project_1:
                    report.setdefault("cleanup", {})[project_1] = await _delete_project(page, project_1)
            except Exception as e:
                report.setdefault("cleanup_errors", []).append(f"{project_1}: {e}")
            OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
            await context.close()
            await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
