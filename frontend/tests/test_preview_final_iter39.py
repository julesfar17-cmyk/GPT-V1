"""Real-proxy lifecycle confidence pass, extending iteration38 (no upload fault injection here)."""
import asyncio
import json
from pathlib import Path

from playwright.async_api import async_playwright
from test_long_preview_iter38 import _ensure_login, _open_studio_frame, _setup_fixture, SRC

OUT=Path('/app/test_reports/frontend_preview_final_iter39.json')


async def main():
    report={'status':'running','checks':[],'runtime_errors':[]}
    media_id=json.loads(Path('/app/test_reports/frontend_long_preview_iter38.json').read_text())['media_id']
    async with async_playwright() as p:
        browser=await p.chromium.launch(executable_path='/usr/bin/google-chrome',headless=True)
        context=await browser.new_context(viewport={'width':1920,'height':800})
        async def protect(route):
            if '/api/projects' in route.request.url and route.request.method!='GET':await route.abort()
            else:await route.continue_()
        await context.route('**/*',protect)
        page=await context.new_page()
        page.on('pageerror',lambda e:report['runtime_errors'].append(str(e)))
        try:
            await _ensure_login(page,report)
            f=await _open_studio_frame(page);await _setup_fixture(f)
            await f.evaluate("""id=>{
              const input=document.createElement('input');input.type='file';input.id='qa-local-file';
              input.onchange=()=>addClip(input.files[0],{skipUpload:true,mediaId:id});document.body.append(input);
            }""",media_id)
            await f.set_input_files('#qa-local-file',str(SRC))
            await f.wait_for_function("() => clips[0]?._wcReady && clips[0]?.wcProxy",polling=100,timeout=60000)
            await f.wait_for_timeout(1200)
            result=await f.evaluate("""async()=>{
              const sleep=ms=>new Promise(r=>setTimeout(r,ms)),c=clips[0],raw=c.wc;
              const wait=async(predicate,ms=20000)=>{const until=performance.now()+ms;while(!predicate()&&performance.now()<until)await sleep(50);if(!predicate())throw Error('Readiness timeout');};
              const out={};
              const reset=()=>{stopAll();M.plans=[{start:0,end:12,clip:0,seek:89.4}];ext={start:0,dur:12};startOff=0;};
              reset();c.wcProxy=null;c._proxyState='loading';c._proxyTried=false;
              await play(0);out.pendingInitially=!!PreviewReadiness.pending;
              await wait(()=>playing&&wcA&&wcA.clip===c.wcProxy);
              out.autoResumeUsesRealProxy=c.wcProxy!==raw&&c.wcProxy.config.codedHeight<=720;
              const first=wcA.cur?.timestamp;await sleep(900);out.proxyProgressUs=wcA.cur.timestamp-first;
              out.pendingCleared=!PreviewReadiness.pending;stopAll();

              // Real proxy download/demux while the immediate audio-only loop runs.
              reset();c.wcProxy=null;c._proxyState='failed';c._proxyTried=false;
              await startLoop();out.audioImmediate=playing&&audioOnlyPreview&&!wcPump;
              await ensureClipProxy(c,true);
              out.proxyLoadedDuringAudio=!!c.wcProxy&&c.wcProxy!==raw&&playing&&audioOnlyPreview;
              await play(0);await wait(()=>playing&&!audioOnlyPreview&&wcA?.clip===c.wcProxy);stopAll();

              // Unused and past failed sources do not affect the requested plan.
              const unused={...c,mediaId:null,wcProxy:null,_proxyState:'upload-failed',_saveFailed:'test state',_optimizing:false};
              clips.push(unused);reset();await play(0);out.unusedIgnored=playing&&!PreviewReadiness.pending;stopAll();
              M.plans=[{start:0,end:4,clip:1,seek:0},{start:4,end:12,clip:0,seek:89.4}];
              await play(5);out.pastPlanIgnored=playing&&!PreviewReadiness.pending;stopAll();clips.pop();

              // A cancelled intent stays cancelled even when a REAL proxy arrives.
              reset();c.wcProxy=null;c._proxyState='loading';c._proxyTried=true;
              await play(0);PreviewReadiness.cancel();c._proxyTried=false;await ensureClipProxy(c);
              await sleep(350);out.noLateAutoplay=!playing&&!PreviewReadiness.pending;
              reset();c.wcProxy=null;c._proxyState='loading';c._proxyTried=true;
              await play(0);ext={start:1,dur:11};await sleep(350);
              c._proxyTried=false;await ensureClipProxy(c);out.rangeChangeCancelled=!playing&&!PreviewReadiness.pending;

              // Actual fast-cut render loop on the optimized preview, not FPS-only.
              reset();ext={start:0,dur:8};M.plans=[{start:0,end:2.5,clip:0,seek:179}];
              for(let t=2.5,i=0;t<8;i++){const end=Math.min(8,t+[.1,.2,.25][i%3]);M.plans.push({start:t,end,clip:0,seek:[5.2,89.4,179][i%3]});t=end;}
              const draw=drawPreview, stats={ticks:0,missing:0,wrong:0,maxLag:0};
              drawPreview=function(t,cv){draw(t,cv);if(!playing||audioOnlyPreview||cv||t>=7.5)return;
                const p=M.plans.find(p=>t>=p.start&&t<p.end);if(!p)return;stats.ticks++;
                if(!wcA?.cur){stats.missing++;return;}
                const lag=Math.abs(wcA.cur.timestamp/1e6-(p.seek+t-p.start));stats.maxLag=Math.max(lag,stats.maxLag);if(lag>.12)stats.wrong++;
              };
              try{await play(0);await wait(()=>playing);await sleep(7600);}finally{stopAll();drawPreview=draw;}
              out.fastCuts=stats;

              // Source-quality export remains independent of the preview transport.
              ext={start:0,dur:1.2};M.format='169';M.plans=Array.from({length:6},(_,i)=>({start:i*.2,end:(i+1)*.2,clip:0,seek:[179,89.4,5.2][i%3]}));
              const sink=[],mode=await offlineSupported();const ok=await exportOffline('-qa-recovery',mode,sink);
              out.export={ok,bytes:sink[0]?.blob.size,originalRetained:c.wc===raw};
              if(ok){const wc=await parseWC(sink[0].blob);out.export.frames=wc.samples.length;out.export.duration=wc.durationS;}

              // Explicit local playback uses live decoded frames (single long plan).
              reset();c.wcProxy=null;c._proxyState='failed';c._proxyTried=true;
              await play(0);document.querySelector('[data-testid="preview-wait-local"]').click();
              await wait(()=>playing&&wcA?.cur);
              const localFirst=wcA.cur.timestamp;await sleep(900);
              out.localProgressUs=wcA.cur.timestamp-localFirst;
              renderClips();out.proxyRetryVisibleDuringLocal=!!document.querySelector('[data-testid="clip-preview-retry-0"]');
              out.localLabel=document.getElementById('previewModeStatus').textContent;stopAll();
              return out;
            }""")
            report['results']=result
            for name in ['pendingInitially','autoResumeUsesRealProxy','pendingCleared','audioImmediate','proxyLoadedDuringAudio','unusedIgnored','pastPlanIgnored','noLateAutoplay','rangeChangeCancelled']:
                assert result[name],(name,result)
            assert result['proxyProgressUs']>400000 and result['localProgressUs']>400000,result
            assert 'locale' in result['localLabel'],result
            assert result['proxyRetryVisibleDuringLocal'],result
            assert result['fastCuts']['ticks']>100 and result['fastCuts']['missing']==0 and result['fastCuts']['wrong']==0,result['fastCuts']
            assert result['export']['ok'] and result['export']['originalRetained'] and result['export']['frames']==36,result['export']
            assert not report['runtime_errors'],report['runtime_errors']
            report['status']='passed';print('PASS: real proxy auto-resume, audio-only completion, used-only gate, fast cuts and MP4 export',flush=True)
        except Exception as e:
            report['status']='failed';report['failure']=str(e);raise
        finally:
            OUT.write_text(json.dumps(report,indent=2));await browser.close()


if __name__=='__main__':asyncio.run(main())