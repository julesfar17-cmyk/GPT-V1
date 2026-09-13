"""Real long-source regression: lexical studio state, actual transport and MP4 export.

The project fixture exists only in the disposable browser context. Media endpoints,
VideoDecoder/Encoder, proxy generation and playback are real; project writes abort
as a safety net and no quota-consuming download is performed.
"""
import asyncio
import json
import os
from pathlib import Path

from dotenv import load_dotenv
from playwright.async_api import async_playwright

load_dotenv('/app/frontend/.env')
BASE = os.environ['REACT_APP_BACKEND_URL'].rstrip('/')
ASSET = '/root/beatcut-test-assets/h264_longgop_1280x720_185s.mp4'
OUT = Path('/app/test_reports/frontend_long_preview_regression_iter34.json')


async def setup(page):
    # No existing project: never race its restoration or mutate its state.
    await page.goto(BASE + '/studio', wait_until='domcontentloaded')
    el = await page.wait_for_selector('[data-testid="studio-iframe"]')
    frame = await el.content_frame()
    try:
        await frame.wait_for_function("() => typeof API!=='undefined' && API.user && typeof SegPlayer==='function' && typeof DB!=='undefined' && DB.projectQuota!==undefined", polling=100)
    except Exception:
        print('FRAME DIAGNOSTIC', await frame.evaluate("({url:location.href,api:typeof API,user:typeof API!=='undefined'?API.user:null,player:typeof SegPlayer,body:document.body.innerText.slice(0,500)})"),flush=True)
        raise
    await frame.wait_for_timeout(1500)
    await frame.evaluate("""() => {
      stopAll(); restoreIncomplete=true;
      M={id:'qa-long-unsaved',title:'QA long source',format:'169',words:[],cuts:[],plans:[],fx:{},_loaded:true};
      DB.morceaux.push(M); loadedFor=M.id;
      audioCtx=new AudioContext(); buffer=audioCtx.createBuffer(1,48000*30,48000);
      const a=buffer.getChannelData(0);
      for(let i=0;i<a.length;i++) a[i]=0.03*Math.sin(i*2*Math.PI*440/48000);
      ext={start:0,dur:12}; startOff=0; go('edit/'+M.id);
    }""")
    await frame.wait_for_timeout(300)
    await frame.set_input_files('#clipInput', ASSET)
    await frame.wait_for_function("() => clips.some(c=>c.name.includes('h264_longgop')&&c.wc&&c.wcProxy&&c.mediaId)", polling=100, timeout=120000)
    await frame.wait_for_function("() => clips.every(c=>!c._thumbBusy&&!c._optimizing) && !_cutBusy", polling=100, timeout=30000)
    await frame.evaluate("""() => {
      restoreIncomplete=true;
      document.getElementById('preview').style.display='block';
      document.getElementById('audioDrop').style.display='none';
    }""")
    return frame


METRICS = """async ({mobile}) => {
  const sleep=ms=>new Promise(r=>setTimeout(r,ms));
  const idx=clips.findIndex(c=>c.name.includes('h264_longgop'));
  const cl=clips[idx], original=cl.wc, proxy=cl.wcProxy;
  const gap=w=>Math.max(...w.keyframes.slice(1).map((k,i)=>(k.ts-w.keyframes[i].ts)/1e6));
  const result={build:BC_BUILD,poolLimit:WC_POOL,source:{duration:original.durationS,samples:original.samples.length,
    width:original.config.codedWidth,height:original.config.codedHeight,gop:gap(original)},
    proxy:{duration:proxy.durationS,gop:gap(proxy),width:proxy.config.codedWidth,height:proxy.config.codedHeight},
    usesProxy:wcPrev(cl)===proxy,mediaId:cl.mediaId};
  stopAll(); M.fx={}; M.plans=[{start:0,end:12,seek:85,clip:idx}]; ext={start:0,dur:12};
  const scratch=document.createElement('canvas'); scratch.width=32;scratch.height=32;
  const hash=()=>{const c=scratch.getContext('2d');c.drawImage(document.getElementById('preview'),0,0,32,32);
    return Array.from(c.getImageData(0,0,32,32).data).reduce((v,x,i)=>(v+x*(i+1))%1000000007,0);};
  result.scrub=[];
  for(const sourceT of [90,89.4,89.5,90.45,90.53]){
    if(sourceT===90.53) await sleep(3200);
    startOff=sourceT-85; const before=hash(); drawPreview(curTime());
    await sleep(350);
    const f=wcScrub&&wcScrub.cur;
    result.scrub.push({target:sourceT,got:f?f.timestamp/1e6:null,changed:hash()!==before});
  }
  await sleep(100); result.scrubTimerIdle=_wcRedrawTimer===null;
  // A real long-GOP source is unsafe for rapid cuts until its proxy is ready.
  const savedProxyState=cl._proxyState;
  cl.wcProxy=null; cl._proxyState='loading'; renderClips(); await play(0);
  result.pendingGate={blocked:!playing,visible:!!document.querySelector('[data-testid="clip-preview-status-'+idx+'"]')};
  cl._proxyState='failed';cl._proxyTried=false;renderClips();
  const retryButton=document.querySelector('[data-testid="clip-preview-retry-'+idx+'"]');
  result.retryVisible=!!retryButton;
  if(retryButton)retryButton.click();
  const retryDeadline=performance.now()+15000;
  while(!cl.wcProxy&&performance.now()<retryDeadline)await sleep(100);
  result.retryReady=!!cl.wcProxy&&cl._proxyState==='ready';
  cl.wcProxy=proxy;cl._proxyState=savedProxyState;
  const plans=[{start:0,end:3.5,clip:idx,seek:179}];
  for(let t=3.5,i=0;t<12;i++){
    const end=Math.min(12,t+[0.1,0.2,0.25][i%3]);
    plans.push({start:t,end,clip:idx,seek:[89.4,5.17,179.18][i%3]}); t=end;
  }
  M.plans=plans; M.cuts=plans.map(p=>({time:p.start,source:'manual'}));
  const cancelled=warmUpPlans(0); stopAll(); result.cancelledWarmup=(await cancelled)===false;
  result.playback=[];
  const savedDraw=drawPreview;
  for(const useProxy of (mobile?[true]:[false,true])){
    cl.wcProxy=useProxy?proxy:null; startOff=0;
    const stats={mode:useProxy?'proxy':'original',ticks:0,missing:0,wrong:0,maxLag:0,plans:{},maxBuffered:0};
    drawPreview=function(t,cv){
      savedDraw(t,cv);
      if(!playing||cv||t>=11.5) return;
      const pi=M.plans.findIndex(p=>t>=p.start&&t<p.end),p=M.plans[pi]; if(!p)return;
      const f=wcA&&wcA.cur;
      stats.ticks++; if(!f)stats.missing++;
      else{
        const lag=Math.abs(f.timestamp/1e6-(p.seek+t-p.start));
        stats.maxLag=Math.max(stats.maxLag,lag); if(lag>0.12)stats.wrong++;
        const v=stats.plans[pi]||(stats.plans[pi]={frames:[],samples:0}); v.samples++;
        if(v.frames[v.frames.length-1]!==f.timestamp) v.frames.push(f.timestamp);
      }
      stats.maxBuffered=Math.max(stats.maxBuffered,...[wcA,...wcPool.map(e=>e.pl)].filter(Boolean).map(pl=>pl.buffered()+pl.pending));
    };
    await play(0);
    const deadline=performance.now()+15000;
    while(playing&&curTime()<11.5&&performance.now()<deadline) await sleep(50);
    stats.elapsedTimeline=curTime(); stats.audioRunning=audioCtx.state==='running';
    stopAll(); drawPreview=savedDraw; result.playback.push(stats);
    await sleep(100);
  }
  cl.wcProxy=proxy;
  result.originalRetained=cl.wc===original;
  // Real loop transport and its independent decode pump.
  ext={start:0,dur:2}; M.plans=[{start:0,end:2,seek:89.4,clip:idx}];
  await startLoop(); await sleep(500);
  result.loop={playing,looping,pump:!!wcPump,frame:wcA&&wcA.cur?wcA.cur.timestamp/1e6:null}; stopAll();
  // EOF, software recovery, and bounded idle reservation on the real decoder.
  const pl=new SegPlayer(); pl.setClip(original); pl.idle=true; pl.seek(89.4);
  for(let i=0;i<80;i++){pl.fill();await sleep(5);}
  result.idleBudget={total:pl.buffered()+pl.pending,limit:5+Math.max(2,original.reorderDepth)};
  pl.idle=false; pl.seek(184.99); await wcWaitFrame(pl,184.99,2500);
  result.eof={timestamp:pl.cur&&pl.cur.timestamp/1e6,drained:pl.drained,pending:pl.pending};
  pl.recover(); pl.seek(90.4); await wcWaitFrame(pl,90.4,2500);
  result.recovery={timestamp:pl.cur&&pl.cur.timestamp/1e6,error:pl.err,software:pl.soft}; pl.destroy();
  if(!mobile){
    ext={start:0,dur:1.2};
    M.plans=Array.from({length:6},(_,i)=>({start:i*0.2,end:(i+1)*0.2,clip:idx,seek:[179,89.4,5.17][i%3]}));
    const exp=new SegPlayer(); result.exportFrames=[];
    for(let n=0;n<36;n++){
      const t=n/30; await wcExportSeek(exp,t); const p=M.plans.find(p=>t>=p.start&&t<p.end);
      result.exportFrames.push({expected:p.seek+t-p.start,got:wcExpFrame&&wcExpFrame.timestamp/1e6,original:exp.clip===original});
    }
    exp.destroy(); wcExpFrame=null;
    const mode=await offlineSupported(); const sink=[];
    const ok=mode?await exportOffline('-qa',mode,sink):false;
    result.mp4Export={mode,ok,bytes:sink[0]&&sink[0].blob.size};
    if(ok&&sink.length){
      const video=await parseWC(sink[0].blob);
      result.mp4Export.samples=video.samples.length; result.mp4Export.duration=video.durationS;
      result.mp4Export.width=video.config.codedWidth; result.mp4Export.height=video.config.codedHeight;
    }
  }
  stopAll(); return result;
}"""


def validate(r, mobile=False):
    assert r['source']['duration'] == 185 and r['source']['samples'] == 4440
    assert r['source']['gop'] >= 8 and r['proxy']['gop'] <= .55
    assert r['usesProxy'] and r['originalRetained']
    assert all(s['got'] is not None and abs(s['got']-s['target']) < .075 for s in r['scrub']), r['scrub']
    assert any(s['changed'] for s in r['scrub']) and r['scrubTimerIdle']
    assert r['pendingGate']['blocked'] and r['pendingGate']['visible'] and r['retryVisible'] and r['retryReady']
    assert r['cancelledWarmup']
    for mode in r['playback']:
        assert mode['elapsedTimeline'] >= 11.5 and mode['ticks'] > 100 and mode['audioRunning'], mode
        assert len(mode['plans']) >= 25, len(mode['plans'])
        if mode['mode'] == 'proxy':
            assert mode['missing'] == 0 and mode['wrong'] == 0, mode
            assert all(len(p['frames']) >= 2 for p in mode['plans'].values() if p['samples'] > 3), mode
    assert r['loop']['playing'] and r['loop']['looping'] and r['loop']['pump'] and r['loop']['frame'] is not None
    assert r['idleBudget']['total'] <= r['idleBudget']['limit']
    assert r['eof']['drained'] and r['eof']['pending'] == 0 and r['eof']['timestamp'] > 184.95
    assert r['recovery']['software'] and not r['recovery']['error'] and abs(r['recovery']['timestamp']-90.4) < .075
    assert r['poolLimit'] == (4 if mobile else 8)
    if not mobile:
        assert all(f['original'] and f['got'] is not None and abs(f['got']-f['expected']) < .075 for f in r['exportFrames']), r['exportFrames']
        assert r['mp4Export']['ok'] and r['mp4Export']['samples'] == 36 and r['mp4Export']['bytes'] > 20000, r['mp4Export']


async def main():
    report={'status':'running','safety':'Unsaved browser fixture; project writes aborted, no media/decoder mocks','errors':[]}
    async with async_playwright() as p:
        browser=await p.chromium.launch(executable_path='/usr/bin/google-chrome',headless=True)
        context=await browser.new_context(viewport={'width':1920,'height':800})
        async def protect(route):
            if '/api/projects' in route.request.url and route.request.method != 'GET':
                await route.abort()
            else: await route.continue_()
        await context.route('**/*',protect)
        page=await context.new_page()
        page.on('pageerror',lambda e:report['errors'].append(str(e)))
        try:
            await page.goto(BASE+'/login')
            await page.get_by_test_id('auth-email-input').fill('demo@beatcut.fr')
            await page.get_by_test_id('auth-password-input').fill('Demo1234!')
            await page.get_by_test_id('auth-submit-button').click()
            await page.wait_for_timeout(1500)
            frame=await setup(page)
            report['desktop']=await frame.evaluate(METRICS,{'mobile':False})
            OUT.write_text(json.dumps(report,indent=2))
            validate(report['desktop'])
            print('PASS desktop import, source/proxy playback, scrub, recovery and MP4 export',flush=True)
            mobile=await browser.new_context(storage_state=await context.storage_state(),viewport={'width':390,'height':844},
                user_agent='Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 CriOS/151.0.0.0 Mobile/15E148 Safari/604.1')
            await mobile.route('**/*',protect)
            mp=await mobile.new_page(); mf=await setup(mp)
            report['mobile_chrome_emulation']=await mf.evaluate(METRICS,{'mobile':True})
            validate(report['mobile_chrome_emulation'],True)
            print('PASS mobile-UA Chrome playback and pool4 (not physical iPhone)',flush=True)
            await mobile.close()
            assert not report['errors'],report['errors']
            report['status']='passed'
        except Exception as e:
            report['status']='failed';report['failure']=str(e);raise
        finally:
            OUT.write_text(json.dumps(report,indent=2))
            await browser.close()


if __name__=='__main__':
    asyncio.run(main())