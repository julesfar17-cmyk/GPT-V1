import asyncio, json, sys, time
from playwright.async_api import async_playwright

BASE = "https://pro-mailer-2.preview.emergentagent.com"
PROJECT = sys.argv[1] if len(sys.argv) > 1 else "Recette 150BPM"
BROWSER = sys.argv[2] if len(sys.argv) > 2 else "firefox"
FAULT = sys.argv[3] if len(sys.argv) > 3 else ""

PROBE = """() => {
  const cv=document.getElementById('preview'); const c=cv.getContext('2d');
  const d=c.getImageData(0,0,cv.width,cv.height).data; let h=0;
  for(let i=0;i<d.length;i+=4096) h=(h*31+d[i]+d[i+1]*3+d[i+2]*7)>>>0;
  return {t: (typeof curTime==='function'?curTime():null), hash:h, ptr:wcPtr, playing, extra:(wcA?wcA.latencyExtra:null), learned:SegPlayer.learnedExtra||0, prep:playPreparing, ac:(audioCtx?audioCtx.state:null), pr:!!(window.PreviewReadiness&&window.PreviewReadiness.pending),
    tc: document.querySelector('#tcNow')?.textContent,
    aTs: (wcA&&wcA.cur)?wcA.cur.timestamp:null, aBuf: wcA?wcA.buffered():null, aPend: wcA?wcA.pending:null,
    aErr: wcA?wcA.err:null, aState: (wcA&&wcA.dec)?wcA.dec.state:null, q:(wcA&&wcA.dec)?wcA.dec.decodeQueueSize:null,
    pool: wcPool.length, poolErr: wcPool.filter(e=>e.pl.err).length};
}"""

async def main():
    async with async_playwright() as p:
        bt = getattr(p, BROWSER)
        browser = await bt.launch(headless=True, executable_path=("/usr/bin/google-chrome" if BROWSER=="chromium" else None), firefox_user_prefs={"media.autoplay.default":0,"media.autoplay.blocking_policy":0,"media.autoplay.block-webaudio":False,"dom.media.webcodecs.enabled":True} if BROWSER=="firefox" else None, args=(["--autoplay-policy=no-user-gesture-required"] if BROWSER=="chromium" else []))
        ctx = await browser.new_context(viewport={"width": 1600, "height": 900})
        page = await ctx.new_page()
        logs = []
        page.on("console", lambda m: logs.append(f"[{m.type}] {m.text[:300]}"))
        page.on("pageerror", lambda e: logs.append(f"[pageerror] {str(e)[:300]}"))
        await page.goto(BASE + "/login", wait_until="networkidle")
        await page.fill('input[type="email"]', "demo@beatcut.fr")
        await page.fill('input[type="password"]', "Demo1234!")
        await page.click('button[type="submit"]')
        await page.wait_for_timeout(3000)
        await page.goto(BASE + "/studio.html", wait_until="networkidle")
        await page.wait_for_timeout(3000)
        print("UA:", await page.evaluate("navigator.userAgent"))
        print("WebCodecs:", await page.evaluate("({vd: typeof VideoDecoder, ve: typeof VideoEncoder, ae: typeof AudioEncoder})"))
        await page.click("text=" + PROJECT)
        await page.wait_for_timeout(12000)
        try:
            await page.click("text=Skip", timeout=1500)
        except Exception:
            pass
        info = await page.evaluate("() => ({clips: clips.map(c=>({n:c.name, ready:c._wcReady, fail:c._wcFail, proxy:!!c.wcProxy, opt:!!c._optimizing, missing:!!c._missing, codec:c.wc&&c.wc.config&&c.wc.config.codec})), plans:(M.plans||[]).length, longPending: (typeof clipsLongPreviewPending==='function'?clipsLongPreviewPending():null)})")
        print("CLIPS:", json.dumps(info, ensure_ascii=False))
        await page.evaluate("""() => { if(audioCtx&&audioCtx.state!=='running'){ Object.defineProperty(audioCtx,'state',{get:()=>'running'}); Object.defineProperty(audioCtx,'currentTime',{get:()=>performance.now()/1000}); window.__fakeAudio=true; } }""")
        if FAULT:
            await page.evaluate("""(fault) => {
              const orig=SegPlayer.prototype._onFrame;
              SegPlayer.prototype._onFrame=function(f){
                if(fault==='shift'){ const g=new VideoFrame(f,{timestamp:f.timestamp+700000}); f.close(); return orig.call(this,g); }
                if(fault==='latency'){ this._q=this._q||[]; this._q.push(f); if(this._q.length<20) return; const q=this._q; this._q=q.slice(4); for(const x of q.slice(0,4)) orig.call(this,x); return; }
                if(fault==='order'){ this._q=this._q||[]; this._q.push(f); if(this._q.length<3) return; const [a,b,c]=this._q; this._q=[]; orig.call(this,c); orig.call(this,a); orig.call(this,b); return; }
                return orig.call(this,f);
              };
              window.__fault=fault;
            }""", FAULT)
        await page.click("#playBtn")
        samples = []
        for i in range(60):
            await page.wait_for_timeout(250)
            samples.append(await page.evaluate(PROBE))
        # analyse: consecutive identical hash while playing
        freezes = 0; run = 0; maxrun = 0
        for a, b in zip(samples, samples[1:]):
            if a["hash"] == b["hash"] and b["playing"]:
                run += 1; maxrun = max(maxrun, run)
            else:
                if run >= 2: freezes += 1
                run = 0
        print("SAMPLES(first 12):", json.dumps(samples[:12]))
        print("SAMPLES(last 6):", json.dumps(samples[-6:]))
        print(f"FREEZES(>=750ms same frame): {freezes}, longest same-frame run: {maxrun*250}ms, playing at end: {samples[-1]['playing']}")
        anom = await page.evaluate("() => ({anom: !!window._telTsAnomaly, ooo: wcA&&wcA.ooo, mism: wcA&&wcA.tsMism, stuck: wcA&&wcA.stuckN, stallN:_telStallN, fault: window.__fault})"); print("ANOM", anom)
        tel = await page.evaluate("() => TEL.q.filter(e=>!/thumbs|proxy_ok/.test(e.type)).slice(-20)")
        print("TEL:", json.dumps(tel, ensure_ascii=False)[:2000])
        await page.screenshot(path=f"/tmp/ff_{BROWSER}.png")
        print("LOGS:", "\n".join(logs[-40:]))
        await browser.close()

asyncio.run(main())
