"""Rejoue les vidéos réelles du user (prod) sur la preview : upload réel → proxy → lecture, sonde des gels.
usage: python3 prod_media_probe.py <browser chromium|firefox> <mode cuts|long> [fault]"""
import asyncio, json, sys, time
from pathlib import Path
from playwright.async_api import async_playwright
from test_long_preview_iter38 import _ensure_login, _open_studio_frame, _setup_fixture

BASE = "https://pro-mailer-2.preview.emergentagent.com"
BROWSER = sys.argv[1] if len(sys.argv) > 1 else "chromium"
MODE = sys.argv[2] if len(sys.argv) > 2 else "cuts"
FILES = [Path("/app/memory/prodmedia/6aa84b685ae68058cb23264f.mp4"),   # TADC 1080p60 (proxy 720p60)
         Path("/app/memory/prodmedia/6aa6929518fa5307415cb46b.mp4")]   # Spiderman 720x1280 30fps (pas de proxy)
CACHE = Path("/app/memory/prodmedia/preview_media_ids.json")

PROBE = """() => {
  const cv=document.getElementById('preview'); const c=cv.getContext('2d');
  const d=c.getImageData(0,0,cv.width,cv.height).data; let h=0;
  for(let i=0;i<d.length;i+=4096) h=(h*31+d[i]+d[i+1]*3+d[i+2]*7)>>>0;
  const A=wcA; const bm=(A&&A.cur)?(A.cur instanceof ImageBitmap):null;
  return {bm, t:+(curTime().toFixed(2)), hash:h, ptr:wcPtr, playing, prep:playPreparing,
    aTs:(A&&A.cur)?Math.round(A.cur.timestamp/1000):null, aBuf:A?A.buffered():null, aPend:A?A.pending:null, aSi:A?A.si:null,
    aN:(A&&A.clip)?A.clip.samples.length:null, durS:(A&&A.clip)?+A.clip.durationS.toFixed(2):null, extra:A?A.latencyExtra:null,
    q:(A&&A.dec)?A.dec.decodeQueueSize:null, st:(A&&A.dec)?A.dec.state:null, err:A?String(A.err||''):null, soft:!!(A&&A.soft),
    buf0:(A&&A.frames[0])?Math.round(A.frames[0].timestamp/1000):null, stuck:A?(A.stuckN||0):0, pool:wcPool.length, fps:_fpsLast, stalls:_telStallN};
}"""

async def main():
    async with async_playwright() as p:
        bt = getattr(p, BROWSER)
        kw = {}
        if BROWSER == "chromium":
            kw = dict(executable_path="/usr/bin/google-chrome", args=["--autoplay-policy=no-user-gesture-required"])
        else:
            kw = dict(firefox_user_prefs={"media.autoplay.default": 0, "media.autoplay.blocking_policy": 0})
        browser = await bt.launch(headless=True, **kw)
        ctx = await browser.new_context(viewport={"width": 1600, "height": 900})
        page = await ctx.new_page()
        logs = []
        page.on("pageerror", lambda e: logs.append("[pageerror] " + str(e)[:300]))
        report = {}
        await _ensure_login(page, report)
        f = await _open_studio_frame(page)
        f.on("console", lambda m: logs.append(f"[{m.type}] {m.text[:200]}")) if hasattr(f, "on") else None
        await _setup_fixture(f)
        await f.evaluate("() => { ext={start:0,dur:30}; M.format='916'; }")
        cache = json.loads(CACHE.read_text()) if CACHE.exists() else {}
        for i, fp in enumerate(FILES):
            mid = cache.get(fp.name)
            await f.evaluate("""([i,mid]) => {
              const input=document.createElement('input');input.type='file';input.id='qa-file-'+i;
              input.onchange=()=>addClip(input.files[0], mid?{skipUpload:true,mediaId:mid}:{});document.body.append(input);
            }""", [i, mid])
            await f.set_input_files(f"#qa-file-{i}", str(fp))
        await f.wait_for_function("() => clips.length===2 && clips.every(c=>c.mediaId && !c._optimizing && c._wcReady)", polling=300, timeout=600000)
        ids = await f.evaluate("() => clips.map(c=>c.mediaId)")
        CACHE.write_text(json.dumps({FILES[0].name: ids[0], FILES[1].name: ids[1]}))
        # proxy du clip 0 (long ou >720p) : on attend qu'il soit prêt comme en prod
        await f.evaluate("() => clips.forEach(c=>ensureClipProxy&&ensureClipProxy(c))")
        try:
            await f.wait_for_function("() => clips[0].wcProxy || clips[0]._proxyState==='failed' || clips[0]._proxyState==='skipped'", polling=500, timeout=300000)
        except Exception:
            pass
        st = await f.evaluate("() => clips.map(c=>({n:c.name.slice(0,20), proxy:!!c.wcProxy, ps:c._proxyState, dur:c.wc&&c.wc.durationS, pdur:c.wcProxy&&c.wcProxy.durationS, n_s:c.wc&&c.wc.samples.length, pn:c.wcProxy&&c.wcProxy.samples.length, codec:c.wc&&c.wc.config.codec, pcodec:c.wcProxy&&c.wcProxy.config.codec, w:c.wc&&c.wc.config.codedWidth, seeks:(c.seeks||[]).length}))")
        print("CLIPS", json.dumps(st))
        if MODE == "cuts":
            await f.evaluate("() => { M.plans=Array.from({length:52},(_,i)=>({start:i*0.571,end:(i+1)*0.571,clip:i%3===2?1:0,seek:((i*3.7)%20),locked:false})); drawTimeline&&drawTimeline(); }")
        else:
            await f.evaluate("() => { M.plans=[{start:0,end:30,clip:0,seek:2,locked:false}]; drawTimeline&&drawTimeline(); }")
        await f.evaluate("""() => { if(audioCtx&&audioCtx.state!=='running'){ Object.defineProperty(audioCtx,'state',{get:()=>'running'}); Object.defineProperty(audioCtx,'currentTime',{get:()=>performance.now()/1000}); } }""")
        await f.evaluate("() => play(0)")
        samples = []
        for i in range(100):
            await f.wait_for_timeout(250)
            samples.append(await f.evaluate(PROBE))
        run = 0; maxrun = 0; freezes = []
        for a, b in zip(samples, samples[1:]):
            if a["hash"] == b["hash"] and b["playing"] and not b["prep"]:
                run += 1; maxrun = max(maxrun, run)
            else:
                if run >= 2: freezes.append((a["t"], run * 250))
                run = 0
        if run >= 2: freezes.append((samples[-1]["t"], run * 250))
        print("FREEZES:", freezes, "longest:", maxrun * 250, "ms; playing at end:", samples[-1]["playing"])
        print("SAMPLES:", json.dumps(samples[::10]))
        tel = await f.evaluate("() => TEL.q.filter(e=>/stall|miss|error|bump|anomaly|duration|low_fps/.test(e.type)).slice(-12)")
        print("TEL:", json.dumps(tel)[:3000])
        print("LOGS:", "\n".join(l for l in logs if 'error' in l.lower() or 'pageerror' in l)[:1500])
        await f.evaluate("() => stopAll()")
        print("BITMAP_MODE", await f.evaluate("() => ({mode: WC_BITMAP_MODE, curIsBitmap: samplesBm=null})") if False else await f.evaluate("() => WC_BITMAP_MODE"), "cur bitmap seen:", any(x.get("bm") for x in samples))
        if MODE == "long":
            exp = await f.evaluate("""async () => { ext={start:0,dur:1.2}; M.format='169'; M.plans=Array.from({length:6},(_,i)=>({start:i*.2,end:(i+1)*.2,clip:i%2,seek:[3,9.4,5.2][i%3]}));
              const sink=[]; const mode=await offlineSupported(); const ok=await exportOffline('-qa-ff',mode,sink);
              const out={ok,mode,bytes:sink[0]&&sink[0].blob.size};
              if(ok){ try{ const wc=await parseWC(sink[0].blob); out.frames=wc.samples.length; out.duration=wc.durationS; }catch(e){ out.parseErr=String(e); } }
              return out; }""")
            print("EXPORT", exp)
        await browser.close()

asyncio.run(main())
