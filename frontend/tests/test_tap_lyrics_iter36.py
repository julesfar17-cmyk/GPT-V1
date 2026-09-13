"""Iteration 36 frontend regression for Tap Lyrics + Tap for Cut + persistence."""

import asyncio
import json
import os
from pathlib import Path

from dotenv import load_dotenv
from playwright.async_api import async_playwright

load_dotenv('/app/frontend/.env')
BASE = os.environ['REACT_APP_BACKEND_URL'].rstrip('/')
OUT = Path('/app/test_reports/frontend_taplyrics_iter36.json')

DEMO_EMAIL = 'demo@beatcut.fr'
DEMO_PASSWORD = 'Demo1234!'


def check(condition, message):
    if not condition:
        raise AssertionError(message)


async def ensure_login(page):
    await page.goto(BASE + '/login', wait_until='domcontentloaded')
    await page.wait_for_timeout(800)
    if await page.locator('[data-testid="auth-email-input"]').count():
        await page.get_by_test_id('auth-email-input').fill(DEMO_EMAIL)
        await page.get_by_test_id('auth-password-input').fill(DEMO_PASSWORD)
        await page.get_by_test_id('auth-submit-button').click()
        await page.wait_for_timeout(1600)


async def open_studio_frame(page):
    await page.goto(BASE + '/studio', wait_until='domcontentloaded')
    iframe = await page.wait_for_selector('[data-testid="studio-iframe"]', timeout=30000)
    frame = await iframe.content_frame()
    await frame.wait_for_function(
        """() => typeof TapLyrics!=='undefined' && typeof BeatTapAudio!=='undefined' && typeof DB!=='undefined' && DB.projectQuota!==undefined""",
        polling=100,
        timeout=45000,
    )
    return frame


async def setup_in_memory_fixture(frame):
    await frame.evaluate(
        """() => {
        LANG='fr';
        stopAll();
        restoreIncomplete=true;
        if(!audioCtx) audioCtx = new AudioContext();
        const sr = audioCtx.sampleRate || 48000;
        const dur = 12;
        buffer = audioCtx.createBuffer(1, Math.floor(sr*dur), sr);
        const ch = buffer.getChannelData(0);
        for (let i=0;i<ch.length;i++) ch[i]=0.5*Math.sin(2*Math.PI*220*i/sr);
        ext = {start: 3, dur: 2};
        startOff = ext.start;
        bpm = 120;
        beats = Array.from({length:64}, (_,i)=>i*0.5);
        M = {
          id:'qa-taplyrics-iter36',
          title:'QA TapLyrics Iter36',
          format:'916',
          words:[
            {text:'Avant',start:1,end:2,hardEnd:true,meta:'outside-before'},
            {text:'salut',start:3.10,end:3.55,hardEnd:true,emphasis:{color:'#ff2d55',weight:700}},
            {text:'monde',start:3.55,end:4.20,hardEnd:true},
            {text:'Après',start:7,end:8,hardEnd:true,meta:'outside-after'}
          ],
          cuts:[{time:3,source:'manual'},{time:3.55,source:'manual'}],
          plans:[{start:3,end:3.55,clip:null,seek:0,locked:false},{start:3.55,end:5,clip:null,seek:0,locked:false}],
          fx:{},
          _loaded:true
        };
        DB.morceaux=DB.morceaux.filter(x=>x.id!==M.id);DB.morceaux.push(M);
        loadedFor=M.id;
        go('edit/'+M.id);
        tab('paroles');
        const pv=document.getElementById('preview');
        const ad=document.getElementById('audioDrop');
        if(pv) pv.style.display='block';
        if(ad) ad.style.display='none';
      }"""
    )
    await frame.wait_for_timeout(1000)
    if await frame.get_by_test_id('mob-tuto-skip').is_visible():
        await frame.get_by_test_id('mob-tuto-skip').click()
        await frame.get_by_test_id('mob-tutorial-overlay').wait_for(state='hidden')


async def open_lyrics(frame):
    if await frame.evaluate('window.innerWidth<=900'):
        is_open=await frame.get_by_test_id('tap-lyrics-open').evaluate("e=>e.closest('.col').classList.contains('open')")
        if not is_open:
            await frame.get_by_test_id('mob-tab-paroles').click()
    await frame.get_by_test_id('tap-lyrics-open').click()


async def run_frontend_checks(browser, report):

    context = await browser.new_context(viewport={'width': 1920, 'height': 800},has_touch=True)

    async def block_project_writes(route):
        if '/api/projects' in route.request.url and route.request.method != 'GET':
            await route.abort()
        else:
            await route.continue_()

    await context.route('**/*', block_project_writes)
    page = await context.new_page()
    page.on('console', lambda msg: report['checks'].append(f"console:{msg.type}:{msg.text[:180]}"))
    page.on('pageerror', lambda error:report.setdefault('runtime_errors',[]).append(str(error)))

    await ensure_login(page)
    frame = await open_studio_frame(page)
    await setup_in_memory_fixture(frame)

    # Desktop open + prefill
    await open_lyrics(frame)
    await frame.wait_for_selector('[data-testid="taplyrics-overlay"]', timeout=10000)
    prefill = await frame.locator('[data-testid="taplyrics-text"]').input_value()
    check('salut' in prefill and 'monde' in prefill, 'Prefill does not include excerpt words')
    report['checks'].append('desktop_open_prefill_ok')
    await frame.evaluate('TapLyrics.close()')

    # Mobile entrypoint
    await page.set_viewport_size({'width': 390, 'height': 844})
    await frame.get_by_test_id('mob-tab-more').click()
    await frame.wait_for_timeout(300)
    await frame.get_by_test_id('mob-taplyrics-btn').scroll_into_view_if_needed()
    await frame.get_by_test_id('mob-taplyrics-btn').click()
    await frame.wait_for_selector('[data-testid="taplyrics-overlay"]', timeout=10000)
    report['checks'].append('mobile_open_ok')
    await frame.evaluate('TapLyrics.close()')
    await page.set_viewport_size({'width': 1920, 'height': 800})

    # Empty disabled + special chars enabled
    await open_lyrics(frame)
    await frame.locator('[data-testid="taplyrics-text"]').fill('')
    check(await frame.locator('[data-testid="taplyrics-start"]').is_disabled(), 'Start should be disabled for empty lyrics')
    special_text = 'Été — cœur café ÇA va ? ❤️ 你好 monde'
    await frame.locator('[data-testid="taplyrics-text"]').fill(special_text)
    check(not await frame.locator('[data-testid="taplyrics-start"]').is_disabled(), 'Start stayed disabled with non-empty special text')
    await frame.evaluate('TapLyrics.close()')
    report['checks'].append('empty_disable_special_chars_ok')

    # Overflow checks
    overflow = {}
    for width in (320, 768, 1024, 1440):
        await page.set_viewport_size({'width': width, 'height': 800})
        await open_lyrics(frame)
        await frame.wait_for_timeout(220)
        has_overflow = await frame.evaluate(
            """() => {
            const ov = document.getElementById('tapLyricsOverlay');
            if(!ov) return true;
            const rootOverflow = document.documentElement.scrollWidth > document.documentElement.clientWidth + 1;
            const ovOverflow = ov.scrollWidth > ov.clientWidth + 1;
            return rootOverflow || ovOverflow;
            }"""
        )
        overflow[str(width)] = bool(has_overflow)
        await frame.evaluate('TapLyrics.close()')
    check(not any(overflow.values()), f'Horizontal overflow detected: {overflow}')
    report['overflow'] = overflow
    await page.set_viewport_size({'width': 1920, 'height': 800})

    # Capture flow, no double increment per tap
    await frame.get_by_test_id('tap-lyrics-open').click(force=True)
    await frame.locator('[data-testid="taplyrics-text"]').fill('un deux trois')
    await frame.get_by_test_id('taplyrics-rate-75').click(force=True)
    await frame.get_by_test_id('taplyrics-start').click(force=True)
    await frame.wait_for_selector('[data-testid="taplyrics-count"]', timeout=12000)
    count_phase_taps = await frame.evaluate('TapLyrics.state.times.length')
    check(count_phase_taps == 0, 'Times advanced during countdown phase')
    await frame.wait_for_selector('[data-testid="taplyrics-zone"]', timeout=12000)
    before = await frame.evaluate('TapLyrics.state.times.length')
    await frame.get_by_test_id('taplyrics-zone').click(force=True)
    await frame.wait_for_timeout(120)
    after = await frame.evaluate('TapLyrics.state.times.length')
    check(after - before == 1, f'Expected +1 tap increment, got {before}->{after}')
    await page.keyboard.press('Space')
    await frame.wait_for_timeout(120)
    after_space = await frame.evaluate('TapLyrics.state.times.length')
    check(after_space == 2, f'Space did not map to exactly one hit, got {after_space}')
    await frame.get_by_test_id('taplyrics-zone').click(force=True)
    await frame.wait_for_timeout(120)
    await frame.get_by_test_id('taplyrics-stop').click(force=True)
    await frame.wait_for_selector('[data-testid="taplyrics-summary"]', timeout=10000)
    apply_enabled = not await frame.locator('[data-testid="taplyrics-apply"]').is_disabled()
    check(apply_enabled, 'Apply should be enabled for complete take')
    await frame.get_by_test_id('taplyrics-retry').click(force=True)
    await frame.wait_for_selector('[data-testid="taplyrics-start"]', timeout=10000)
    await frame.evaluate('TapLyrics.close()')
    report['checks'].append('capture_space_pointer_review_ok')

    # Partial take -> Apply disabled + close keeps words unchanged
    snap_before = await frame.evaluate('JSON.stringify(M.words)')
    await frame.get_by_test_id('tap-lyrics-open').click(force=True)
    await frame.locator('[data-testid="taplyrics-text"]').fill('alpha beta gamma')
    await frame.get_by_test_id('taplyrics-start').click(force=True)
    await frame.wait_for_selector('[data-testid="taplyrics-zone"]', timeout=12000)
    await frame.get_by_test_id('taplyrics-zone').click(force=True)
    await frame.wait_for_timeout(90)
    await frame.get_by_test_id('taplyrics-stop').click(force=True)
    await frame.wait_for_selector('[data-testid="taplyrics-incomplete"]', timeout=10000)
    check(await frame.locator('[data-testid="taplyrics-apply"]').is_disabled(), 'Apply should be disabled for partial capture')
    await frame.evaluate('TapLyrics.close()')
    snap_after_close = await frame.evaluate('JSON.stringify(M.words)')
    check(snap_after_close == snap_before, 'Closing incomplete session mutated project words')
    report['checks'].append('partial_apply_disabled_and_cancel_safe_ok')

    # Apply flow preserves outside words and emphasis for same text
    await setup_in_memory_fixture(frame)
    await frame.get_by_test_id('tap-lyrics-open').click(force=True)
    await frame.locator('[data-testid="taplyrics-text"]').fill('salut monde')
    await frame.get_by_test_id('taplyrics-rate-100').click(force=True)
    await frame.get_by_test_id('taplyrics-start').click(force=True)
    await frame.wait_for_selector('[data-testid="taplyrics-zone"]', timeout=12000)
    await frame.get_by_test_id('taplyrics-zone').click(force=True)
    await frame.wait_for_timeout(100)
    await frame.get_by_test_id('taplyrics-zone').click(force=True)
    await frame.wait_for_timeout(100)
    await frame.get_by_test_id('taplyrics-stop').click(force=True)
    await frame.get_by_test_id('taplyrics-apply').click(force=True)
    await frame.wait_for_timeout(250)
    applied = await frame.evaluate(
        """() => ({
          words: M.words,
          hasRedo: typeof redo === 'function',
          hasUndo: typeof undo === 'function'
        })"""
    )
    check(applied['words'][0]['text'] == 'Avant' and applied['words'][-1]['text'] == 'Après', 'Outside excerpt words not preserved')
    check(applied['words'][1]['text'] == 'salut', 'Overlapping word text not applied as expected')
    check(applied['words'][1].get('emphasis', {}).get('weight') == 700, 'Existing emphasis metadata for identical text was not preserved')
    check(all(w['end'] > w['start'] for w in applied['words']), 'Applied words contain non-positive durations')
    check(applied['hasUndo'] is True, 'Undo function is missing')
    report['redo_available'] = bool(applied['hasRedo'])
    if applied['hasUndo']:
        await frame.evaluate('undo()')
        await frame.wait_for_timeout(200)
        check(await frame.evaluate('JSON.stringify(M.words)')==snap_before,'Undo did not restore exact original words/timings')
    report['checks'].append('apply_preservation_and_undo_ok')

    # Source-clock timing at each rate, listen/stop, exact case even in English UI.
    report['capture_rates']=[]
    for rate in (100,75,50):
        await open_lyrics(frame)
        await frame.get_by_test_id('taplyrics-text').fill('Annuler Retour')
        await frame.get_by_test_id('taplyrics-rate-'+str(rate)).click()
        await frame.get_by_test_id('taplyrics-start').click()
        await frame.get_by_test_id('taplyrics-zone').wait_for(state='visible')
        await frame.evaluate("LANG='en';applyLang()")
        check(await frame.get_by_test_id('taplyrics-current-word').inner_text()=='Annuler','UI translation changed user lyrics')
        await frame.get_by_test_id('taplyrics-zone').click()
        stamp=await frame.evaluate('performance.now()')
        await frame.wait_for_timeout(700)
        await frame.get_by_test_id('taplyrics-zone').click()
        elapsed=(await frame.evaluate('performance.now()')-stamp)/1000
        times=await frame.evaluate('TapLyrics.state.times.slice()')
        delta=times[1]-times[0]
        check(abs(delta-elapsed*rate/100)<.10,f'Rate{rate}: timestamps do not follow source clock: {delta} / {elapsed}')
        report['capture_rates'].append({'rate':rate,'wall_s':elapsed,'source_delta_s':delta})
        await frame.get_by_test_id('taplyrics-stop').click()
        await frame.get_by_test_id('taplyrics-listen').click()
        await frame.wait_for_timeout(250)
        check(await frame.evaluate('TapLyrics.state.previewing && TapLyrics.state.audio.rate===1'),'Review not playing at100%')
        await frame.get_by_test_id('taplyrics-listen').click()
        check(await frame.evaluate('!TapLyrics.state.previewing && TapLyrics.state.audio.closed'),'Review stop failed')
        await frame.evaluate("TapLyrics.close();LANG='fr';applyLang()")
    report['checks'].append('source_timing_all_rates_review_and_literal_words_ok')

    # Natural ending, actual touchscreen input, stale-draft guard, and cancel/resume race.
    await page.set_viewport_size({'width':390,'height':844})
    await open_lyrics(frame)
    await frame.get_by_test_id('taplyrics-text').fill('Bonjour')
    await frame.get_by_test_id('taplyrics-rate-100').click()
    await frame.get_by_test_id('taplyrics-start').click()
    await frame.get_by_test_id('taplyrics-zone').wait_for(state='visible')
    await frame.get_by_test_id('taplyrics-zone').tap()
    await frame.get_by_test_id('taplyrics-summary').wait_for(state='visible',timeout=6000)
    check(await frame.evaluate('TapLyrics.state.candidate.length===1 && TapLyrics.state.candidate[0].end===TapLyrics.state.range.end'),'Natural finish did not end at excerpt end')
    await frame.evaluate("M.words[0].text='Updated while capturing'")
    await frame.get_by_test_id('taplyrics-apply').click()
    check(await frame.get_by_test_id('taplyrics-apply').is_disabled(),'Stale take overwrote changed project')
    await frame.evaluate('TapLyrics.close()')
    await open_lyrics(frame)
    await frame.get_by_test_id('taplyrics-start').click()
    cancelled=await frame.evaluate('window.qaCancelledAudio=TapLyrics.state.audio;TapLyrics.close();true')
    await frame.wait_for_timeout(3300)
    check(cancelled and await frame.evaluate('qaCancelledAudio.closed && !TapLyrics.state'),'Cancelled countdown restarted')
    await page.set_viewport_size({'width':1920,'height':800})
    report['checks'].append('touch_natural_end_stale_guard_cancel_cleanup_ok')

    # Tap for cut regression smoke: pre-roll + cancel in count + session cleanup
    await frame.get_by_test_id('tap-cut-btn').click(force=True)
    await frame.wait_for_selector('[data-testid="tapcut-overlay"]', timeout=10000)
    await frame.get_by_test_id('tapRate-0.5').click(force=True)
    await frame.get_by_test_id('tapGrid-4').click(force=True)
    await frame.get_by_test_id('tapcut-start').click(force=True)
    await frame.wait_for_selector('[data-testid="tapcut-count"]', timeout=10000)
    await frame.get_by_test_id('tapcut-count-cancel').click(force=True)
    await frame.wait_for_timeout(600)
    tap_state = await frame.evaluate('({overlay: !!TAP.ov, hasSession: !!TAP.session, phase: TAP.phase})')
    check(tap_state['overlay'] is False and tap_state['hasSession'] is False, f'Tap cut did not cleanup on countdown cancel: {tap_state}')
    report['checks'].append('tapcut_count_cancel_cleanup_ok')

    # Existing cut quantization still receives absolute source times after slow pre-roll.
    cut_words=await frame.evaluate('JSON.stringify(M.words)')
    await frame.get_by_test_id('tap-cut-btn').click()
    await frame.get_by_test_id('tapRate-0.5').click()
    await frame.get_by_test_id('tapGrid-4').click()
    await frame.get_by_test_id('tapcut-start').click()
    await frame.get_by_test_id('tapcut-zone').wait_for(state='visible')
    await frame.wait_for_timeout(400)
    await frame.get_by_test_id('tapcut-zone').click()
    before_repeat=await frame.evaluate('TAP.taps.length')
    await frame.evaluate("window.dispatchEvent(new KeyboardEvent('keydown',{code:'Space',key:' ',repeat:true,bubbles:true}))")
    check(await frame.evaluate('TAP.taps.length')==before_repeat,'Key repeat added unwanted cut')
    await frame.wait_for_timeout(350)
    await frame.get_by_test_id('tapcut-zone').click()
    await frame.get_by_test_id('tapcut-stop').click()
    quantized=await frame.evaluate('TAP.q.slice()')
    check(len(quantized)>0 and all(abs(t/.125-round(t/.125))<1e-6 for t in quantized),'Cut quantization changed')
    await frame.get_by_test_id('tapcut-apply').click()
    check(await frame.evaluate('JSON.stringify(M.words)')==cut_words,'Tap for cut changed word timing')
    check(await frame.evaluate('M.cuts[0].time===ext.start && M.cuts.length>1'),'Cut apply did not use excerpt start')
    report['checks'].append('tapcut_slow_quantization_repeat_guard_apply_ok')

    # Real BeatTapAudio checks: pre-roll signal + ramp + offset/rate calculations
    audio_diag = await frame.evaluate(
        """async () => {
        const sleep = ms => new Promise(r => setTimeout(r, ms));
        if(!audioCtx) audioCtx = new AudioContext();
        if(audioCtx.state !== 'running') await audioCtx.resume();
        const sr = audioCtx.sampleRate || 48000;
        const mk = () => {
          const b = audioCtx.createBuffer(1, Math.floor(sr*10), sr);
          const d = b.getChannelData(0);
          for(let i=0;i<d.length;i++) d[i] = 0.8*Math.sin(2*Math.PI*330*i/sr);
          return b;
        };
        const sampleRms = (an) => {
          const arr = new Float32Array(an.fftSize);
          an.getFloatTimeDomainData(arr);
          let s=0; for(const v of arr) s += v*v;
          return Math.sqrt(s/arr.length);
        };

        const out = {rates:[], clamp:{}};
        for(const rate of [1,0.75,0.5]){
          const s = new BeatTapAudio({context:audioCtx, buffer:mk(), start:4, duration:1.5, rate, countdown:3});
          await s.start();
          const an = audioCtx.createAnalyser();
          an.fftSize = 2048;
          s.gain.connect(an);
          await sleep(450);
          let pre=0;
          for(let i=0;i<8;i++){ pre=Math.max(pre, sampleRms(an)); await sleep(35); }
          while(audioCtx.currentTime < s.t0 + 0.15) await sleep(20);
          let run=0;
          for(let i=0;i<8;i++){ run=Math.max(run, sampleRms(an)); await sleep(35); }
          out.rates.push({
            rate,
            playbackRate: s.src.playbackRate.value,
            sourceOffset: s.sourceOffset,
            sourceWhen: s.sourceWhen,
            t0: s.t0,
            pre,
            run,
            ratio: run / Math.max(pre, 1e-6),
            continuityErr: Math.abs((s.t0 - s.sourceWhen) - ((4 - s.sourceOffset) / rate))
          });
          s.stop();
          an.disconnect();
        }

        const s0 = new BeatTapAudio({context:audioCtx, buffer:mk(), start:0, duration:1, rate:1, countdown:3});
        await s0.start();
        out.clamp.start0 = {sourceOffset:s0.sourceOffset, sourceWhen:s0.sourceWhen, t0:s0.t0};
        s0.stop();

        const s05 = new BeatTapAudio({context:audioCtx, buffer:mk(), start:0.5, duration:1, rate:1, countdown:3});
        await s05.start();
        out.clamp.start05 = {sourceOffset:s05.sourceOffset, sourceWhen:s05.sourceWhen, t0:s05.t0};
        s05.stop();

        return out;
      }"""
    )
    report['audio_diag'] = audio_diag
    for entry in audio_diag['rates']:
        check(abs(entry['playbackRate'] - entry['rate']) < 1e-6, f'Wrong playbackRate for {entry}')
        check(entry['ratio'] > 2.5, f'Pre-roll to run amplitude ratio too low: {entry}')
        check(entry['continuityErr'] < 0.03, f'Audio continuity mismatch: {entry}')
    check(audio_diag['clamp']['start0']['sourceOffset'] == 0, f'start=0 should clamp sourceOffset to 0: {audio_diag}')
    check(0 <= audio_diag['clamp']['start05']['sourceOffset'] <= 0.01, f'start=0.5 clamp failed: {audio_diag}')
    report['checks'].append('webaudio_preroll_rate_offset_ok')

    # Error scan required by playbook
    err_text = await page.evaluate(
        """() => {
        const errorElements = Array.from(document.querySelectorAll('.error, [class*="error"], [id*="error"]'));
        return errorElements.map(el => el.textContent).join(', ');
        }"""
    )
    report['page_errors'] = err_text

    check(not report.get('runtime_errors'),f'Runtime errors: {report.get("runtime_errors")}')
    token_state=await context.storage_state()
    await context.close()

    # Real persistence via existing API with authenticated cookies
    pctx = await browser.new_context(storage_state=token_state)
    ppage = await pctx.new_page()
    pctx2 = await browser.new_context(storage_state=token_state, viewport={'width': 1920, 'height': 800})
    p = await pctx2.new_page()

    disposable_state = {
        'ext': {'start': 2.0, 'dur': 2.0},
        'words': [
            {'text': 'persist', 'start': 2.1, 'end': 2.6, 'hardEnd': True},
            {'text': 'check', 'start': 2.6, 'end': 3.8, 'hardEnd': True, 'emphasis': {'weight': 600}},
        ],
        'cuts': [{'time': 2.1, 'source': 'manual'}],
        'plans': [{'start': 2.1, 'end': 4.0, 'clip': None, 'seek': 0, 'locked': False}],
    }
    # Persist the actual applied manual take, not just a fabricated timing payload.
    disposable_state['words']=applied['words']
    create = await p.request.post(
        BASE + '/api/projects',
        data={
            'title': 'QA_DISPOSABLE_ITER36_UI',
            'state': disposable_state,
            'client_id': 'iter36-ui',
            'seq': 1,
        },
    )
    check(create.status == 200, f'Persistence create failed: {create.status} {await create.text()}')
    project_id = (await create.json())['project_id']
    get = await p.request.get(BASE + f'/api/projects/{project_id}')
    check(get.status == 200, f'Persistence get failed: {get.status}')
    persisted = await get.json()
    check(persisted['state']['words'] == applied['words'], 'Actual applied timing/metadata mismatch after server reload')
    delete = await p.request.delete(BASE + f'/api/projects/{project_id}')
    check(delete.status == 200, f'Persistence cleanup failed: {delete.status} {await delete.text()}')
    report['persistence'] = {'project_id': project_id, 'created': True, 'deleted': True}

    await pctx.close()
    await pctx2.close()
    return report


async def main():
    report = {'status': 'running', 'checks': []}
    async with async_playwright() as p:
        browser = await p.chromium.launch(executable_path='/usr/bin/google-chrome', headless=True)
        try:
            result = await run_frontend_checks(browser, report)
            result['status'] = 'passed'
            report = result
            print('PASS: Iteration36 tap lyrics/tap cut frontend regression completed')
        except Exception as exc:
            report['status'] = 'failed'
            report['failure'] = str(exc)
            raise
        finally:
            OUT.write_text(json.dumps(report, indent=2), encoding='utf-8')
            await browser.close()


if __name__ == '__main__':
    asyncio.run(main())
