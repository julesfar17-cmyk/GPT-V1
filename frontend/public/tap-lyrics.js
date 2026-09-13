/* Word-by-word manual timing. Capture is a draft until Apply; no AI call. */
window.TapLyrics = (() => {
  const host = window.BeatCutTapHost;
  const L = (fr,en) => host.language === 'en' ? en : fr;
  let state = null, preferredRate = 1;
  const el = id => state && state.overlay.querySelector('[data-testid="'+id+'"]');
  const tokens = text => text.trim().split(/\s+/u).filter(Boolean);
  const button = (id,text,cls='small',extra='') => '<button type="button" class="'+cls+'" data-testid="'+id+'" '+extra+'>'+text+'</button>';
  function stopAudio() { if(state && state.audio) state.audio.stop(); }
  function close() {
    if(!state) return;
    const previous=state; stopAudio(); state=null;
    previous.overlay.remove(); document.body.style.overflow=previous.overflow;
    window.removeEventListener('keydown',key,true);
    if(previous.opener && previous.opener.isConnected) previous.opener.focus({preventScroll:true});
  }
  function open() {
    if(!host.project || !host.buffer) {host.toast(L('Dépose d’abord ton morceau','Add your track first'));return;}
    if(host.exporting) {host.toast(L('Export en cours — attends la fin','Export in progress'));return;}
    close(); host.closeCuts(); host.stop(); host.exitCropMode();
    const start=host.excerpt.start, end=Math.min(host.buffer.duration,start+host.excerpt.dur);
    const original=(host.project.words||[]).filter(w=>w.start<end && w.end>start).sort((a,b)=>a.start-b.start);
    const overlay=document.createElement('section'); overlay.id='tapLyricsOverlay';
    overlay.setAttribute('data-testid','taplyrics-overlay'); overlay.setAttribute('role','dialog');
    overlay.setAttribute('aria-modal','true'); overlay.setAttribute('aria-label',L('Tap paroles','Tap lyrics'));
    overlay.setAttribute('translate','no');   // paroles utilisateur intactes, même avec l'interface anglaise
    state={overlay,opener:document.activeElement,overflow:document.body.style.overflow,phase:'idle',
      project:host.project,buffer:host.buffer,range:{start,end},snapshot:JSON.stringify(host.project.words||[]),original,
      text:original.length?original.map(w=>w.text).join(' '):(document.getElementById('pasteText').value||''),
      rate:preferredRate,words:[],times:[],audio:null,previewing:false};
    document.body.style.overflow='hidden'; document.body.append(overlay);
    window.addEventListener('keydown',key,true); render();
  }
  function render() {
    if(!state) return;
    const s=state;
    s.overlay.innerHTML='<header class="tl-header"><span class="tl-title" data-testid="taplyrics-title">'+L('Tap paroles','Tap lyrics')+'</span>'
      +button('taplyrics-close','×','small tl-icon','aria-label="'+L('Fermer','Close')+'" title="'+L('Fermer','Close')+'"')+'</header>';
    el('taplyrics-close').onclick=close;
    if(s.phase==='idle') renderSetup();
    else if(s.phase==='count') renderCountdown();
    else if(s.phase==='run') renderCapture();
    else renderReview();
  }
  function append(html) {state.overlay.insertAdjacentHTML('beforeend',html);}
  function renderSetup() {
    const s=state;
    append('<div class="tl-body"><h2 data-testid="taplyrics-heading">'+L('Tes paroles, mot par mot.','Your lyrics, word by word.')+'</h2>'
      +'<label><span class="tl-label">'+L('Paroles de l’extrait','Excerpt lyrics')+'</span><textarea class="tl-text" data-testid="taplyrics-text" maxlength="20000" placeholder="'+L('Colle tes paroles ici…','Paste your lyrics…')+'"></textarea></label>'
      +'<div class="tl-meta" data-testid="taplyrics-word-count"></div>'
      +'<div><span class="tl-label">'+L('Vitesse de l’extrait','Excerpt speed')+'</span><div class="tl-rates" role="group" aria-label="'+L('Vitesse','Speed')+'">'
      +[1,.75,.5].map(rate=>button('taplyrics-rate-'+Math.round(rate*100),Math.round(rate*100)+' %','small','aria-pressed="'+(rate===s.rate)+'"')).join('')+'</div></div>'
      +'<div class="tl-error" data-testid="taplyrics-error" role="alert"></div>'
      +button('taplyrics-start',L('Lancer le décompte','Start countdown'),'onb-cta tl-primary')+'</div>');
    const text=el('taplyrics-text'); text.value=s.text;
    const update=()=>{
      s.text=text.value; const n=tokens(s.text).length;
      el('taplyrics-word-count').textContent=n+' '+L('mots','words')+' · '+s.range.start.toFixed(1)+'–'+s.range.end.toFixed(1)+' s';
      el('taplyrics-start').disabled=!n;
    };
    text.oninput=update;update();
    [1,.75,.5].forEach(rate=>{el('taplyrics-rate-'+Math.round(rate*100)).onclick=()=>{
      s.rate=rate;preferredRate=rate;
      [1,.75,.5].forEach(v=>el('taplyrics-rate-'+Math.round(v*100)).setAttribute('aria-pressed',String(v===rate)));
    };});
    el('taplyrics-start').onclick=start;
    el('taplyrics-close').focus({preventScroll:true});
  }
  function renderCountdown() {
    append('<div class="tl-body" style="text-align:center"><div class="tl-meta" data-testid="taplyrics-preroll">'
      +L('Pré-écoute · volume 25 %','Pre-roll · volume 25 %')+'</div><div class="tl-count" data-testid="taplyrics-count">3</div>'
      +'<div class="tl-next" data-testid="taplyrics-first-word"></div></div>');
    el('taplyrics-first-word').textContent=state.words[0]; el('taplyrics-close').focus({preventScroll:true});
  }
  function renderCapture() {
    append('<div class="tl-progress"><i data-testid="taplyrics-progress"></i></div><div class="tl-capture">'
      +'<button type="button" class="tl-pad" data-testid="taplyrics-zone"><span class="tl-counter" data-testid="taplyrics-counter"></span>'
      +'<span class="tl-word" data-testid="taplyrics-current-word"></span><span class="tl-next" data-testid="taplyrics-next-words"></span></button>'
      +'<footer class="tl-footer">'+button('taplyrics-stop',L('Terminer la prise','Finish take'),'onb-cta tl-primary')+'</footer></div>');
    const pad=el('taplyrics-zone');
    pad.onpointerdown=e=>{if(!e.isPrimary || (e.pointerType==='mouse'&&e.button!==0))return;e.preventDefault();hit();};
    pad.onclick=e=>{if(e.detail===0)hit();};
    el('taplyrics-stop').onclick=()=>finish(false); updateWord(); pad.focus({preventScroll:true});
  }
  function updateWord() {
    const s=state, n=s.times.length, done=n===s.words.length;
    el('taplyrics-counter').textContent=n+' / '+s.words.length+' · '+Math.round(s.rate*100)+' %';
    el('taplyrics-current-word').textContent=done?s.words[n-1]:s.words[n];
    el('taplyrics-next-words').textContent=done?L('Tous les mots sont calés','All words timed'):s.words.slice(n+1,n+5).join(' ');
    el('taplyrics-zone').disabled=done;
    if(done) el('taplyrics-stop').focus({preventScroll:true});
  }
  async function start() {
    const s=state; if(!s || s.phase!=='idle')return;
    s.words=tokens(s.text); if(!s.words.length)return;
    s.times=[];s.phase='count';render();
    s.audio=new window.BeatTapAudio({context:host.context,buffer:s.buffer,start:s.range.start,duration:s.range.end-s.range.start,rate:s.rate,
      onCount:n=>{if(state===s && el('taplyrics-count'))el('taplyrics-count').textContent=n;},
      onRun:()=>{if(state!==s)return;s.phase='run';render();},
      onTick:t=>{if(state===s && el('taplyrics-progress'))el('taplyrics-progress').style.width=(100*t/(s.range.end-s.range.start))+'%';},
      onEnd:()=>{if(state===s)finish(true);}});
    try {await s.audio.start();}
    catch(e){s.audio.stop();if(state!==s)return;s.phase='idle';render();el('taplyrics-error').textContent=e.message;}
  }
  function hit() {
    const s=state;if(!s || s.phase!=='run' || s.times.length>=s.words.length)return;
    const t=s.range.start+s.audio.elapsed(), last=s.times[s.times.length-1];
    if(t>=s.range.end-.02 || (last!==undefined && t-last<.02))return;
    s.times.push(t);updateWord();
    const pad=el('taplyrics-zone');pad.classList.add('hit');setTimeout(()=>pad.classList.remove('hit'),90);
  }
  function finish(atEnd) {
    const s=state;if(!s || s.phase!=='run')return;
    s.finishAt=atEnd?s.range.end:Math.min(s.range.end,s.range.start+s.audio.elapsed());
    stopAudio();
    s.candidate=s.times.map((start,i)=>{
      const old=s.original[i] && s.original[i].text===s.words[i]?s.original[i]:{};
      return {...old,text:s.words[i],start,end:s.times[i+1]??Math.min(s.range.end,Math.max(start+.02,s.finishAt)),hardEnd:true};
    });
    s.phase='done';render();
  }
  function renderReview() {
    const s=state, complete=s.times.length===s.words.length;
    append('<div class="tl-body"><h2 data-testid="taplyrics-summary">'+s.times.length+' / '+s.words.length+' '+L('mots calés','words timed')+'</h2>'
      +'<div class="tl-error" role="status" data-testid="taplyrics-incomplete">'+(complete?'':L('Prise incomplète — le calage actuel est conservé.','Incomplete take — existing timing is unchanged.'))+'</div>'
      +'<div class="tl-review" data-testid="taplyrics-review-words"></div><div class="tl-error" data-testid="taplyrics-error" role="alert"></div>'
      +button('taplyrics-listen',L('Écouter la prise','Listen to take'),'small',s.times.length?'':'disabled')
      +button('taplyrics-apply',L('Appliquer ce calage','Apply timing'),'onb-cta tl-primary',complete?'':'disabled')
      +button('taplyrics-retry',L('Recommencer','Try again'),'small tl-primary')+'</div>');
    s.candidate.forEach((w,i)=>{const span=document.createElement('span');span.textContent=w.text;span.setAttribute('data-testid','taplyrics-review-word-'+i);el('taplyrics-review-words').append(span);});
    el('taplyrics-listen').onclick=listen;
    el('taplyrics-retry').onclick=()=>{stopAudio();s.previewing=false;s.phase='idle';render();};
    el('taplyrics-apply').onclick=apply;el(complete?'taplyrics-apply':'taplyrics-retry').focus({preventScroll:true});
  }
  async function listen() {
    const s=state;if(!s || s.phase!=='done')return;
    if(s.previewing){stopAudio();s.previewing=false;render();return;}
    s.previewing=true;el('taplyrics-listen').textContent=L('Arrêter l’écoute','Stop listening');
    let last=-1;
    s.audio=new window.BeatTapAudio({context:host.context,buffer:s.buffer,start:s.range.start,duration:s.range.end-s.range.start,rate:1,countdown:0,
      onTick:t=>{if(state!==s)return;const at=s.range.start+t,i=s.candidate.findIndex(w=>at>=w.start&&at<w.end);
        if(i===last)return;if(last>=0)el('taplyrics-review-word-'+last)?.classList.remove('active');
        if(i>=0)el('taplyrics-review-word-'+i)?.classList.add('active');last=i;},
      onEnd:()=>{if(state!==s)return;s.previewing=false;render();}});
    try {await s.audio.start();}catch(e){s.audio.stop();if(state!==s)return;s.previewing=false;render();el('taplyrics-error').textContent=e.message;}
  }
  function apply() {
    const s=state;if(!s || s.phase!=='done' || s.times.length!==s.words.length)return;
    if(host.project!==s.project || host.buffer!==s.buffer || host.excerpt.start!==s.range.start || Math.min(host.buffer.duration,host.excerpt.start+host.excerpt.dur)!==s.range.end || JSON.stringify(host.project.words||[])!==s.snapshot){
      stopAudio();s.previewing=false;el('taplyrics-listen').textContent=L('Écouter la prise','Listen to take');
      el('taplyrics-error').textContent=L('L’extrait ou les paroles ont changé. Recommence depuis le studio.','The excerpt or lyrics changed. Start a new take from the studio.');el('taplyrics-apply').disabled=true;return;
    }
    const outside=(host.project.words||[]).filter(w=>w.end<=s.range.start || w.start>=s.range.end);
    host.replaceWords([...outside,...s.candidate].sort((a,b)=>a.start-b.start),s.range.start);
    close();host.refreshWords();
    host.toast(L('Calage mot par mot appliqué','Word timing applied'));
  }
  function key(e) {
    if(!state)return;e.stopImmediatePropagation();
    if(e.key==='Escape'){e.preventDefault();close();return;}
    if(e.key==='Tab'){
      const items=[...state.overlay.querySelectorAll('button:not([disabled]),textarea')];
      const first=items[0],last=items[items.length-1];
      if(e.shiftKey&&document.activeElement===first){e.preventDefault();last.focus();}
      else if(!e.shiftKey&&document.activeElement===last){e.preventDefault();first.focus();}
      return;
    }
    if(e.target.matches('textarea,input'))return;
    if(e.repeat&&(e.code==='Space'||e.key==='Enter')){e.preventDefault();return;}
    if(e.code==='Space'){e.preventDefault();if(e.repeat)return;if(state.phase==='run')hit();else if(state.phase==='idle')start();}
  }
  window.addEventListener('hashchange',()=>{close();host.closeCuts();});
  document.addEventListener('visibilitychange',()=>{if(document.hidden){close();host.closeCuts();}});
  return {open,close,get state(){return state;}};
})();