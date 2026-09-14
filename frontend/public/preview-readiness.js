/* A bounded, cancellable playback intent; never confuse upload failure with proxy work. */
window.createPreviewReadiness = host => {
  const local=new WeakSet(); let pending=null, timer=null, overlay=null, overflow='';
  function allows(clip){return local.has(clip);}
  function localInUse(from){return host.used(from).some(({clip})=>clip&&allows(clip)&&!clip.wcProxy&&clip._proxyState!=='ready');}
  function blockers(from){
    return host.used(from).flatMap(({clip,index})=>{
      if(!clip)return [{clip,index,kind:'missing',message:'Vidéo manquante — réimporte ce fichier.'}];
      if(clip._wcReady&&clip.wc&&(clip.wc.durationS<90||clip.wcProxy||clip._proxyState==='ready'||allows(clip)))return [];
      let kind,message;
      if(clip._missing){kind='missing';message='Fichier à récupérer — son emplacement est conservé dans le montage.';}
      else if(clip._saveFailed&&!clip.mediaId){kind='upload-failed';message='Envoi échoué : '+clip._saveFailed;}
      else if(!clip.mediaId){kind=clip._optimizing?'uploading':'not-uploaded';message=clip._optimizing?'Envoi en cours'+(Number.isFinite(clip._upPct)?' — '+clip._upPct+' %':''):'Vidéo locale non envoyée — aucun aperçu serveur n’est en préparation.';}
      else if(clip._proxyState==='failed'){kind='proxy-failed';message=clip._proxyError||'La préparation de l’aperçu a échoué.';}
      else if(clip._proxyState==='transcoding'){kind='processing';message='Optimisation du fichier sur le serveur…';}
      else{kind='proxy';message='Création de l’aperçu optimisé…';}
      return [{clip,index,kind,message}];
    });
  }
  function cancel(){
    clearInterval(timer);timer=null;pending=null;
    if(overlay){overlay.remove();overlay=null;document.body.style.overflow=overflow;}
  }
  function resume(useLocal=false){
    if(!pending)return;
    const p=pending;
    if(useLocal)blockers(p.from).forEach(x=>{if(x.clip?._wcReady&&x.clip.wc)local.add(x.clip);});
    cancel();host.play(p.from);
  }
  function render(){
    if(!pending||!overlay)return;
    const entries=blockers(pending.from), list=overlay.querySelector('[data-testid="preview-wait-list"]');
    const timedOut=Date.now()>pending.deadline;
    overlay.querySelector('[data-testid="preview-wait-title"]').textContent=!entries.length?'L’aperçu est prêt':timedOut?'La préparation prend trop de temps':entries.some(x=>x.kind.includes('failed')||x.kind==='not-uploaded')?'La vidéo n’est pas prête':'Préparation de la lecture';
    const signature=JSON.stringify(entries.map(x=>[x.index,x.kind,x.message]))+timedOut;
    if(pending.signature!==signature){
      pending.signature=signature;list.replaceChildren();
      entries.forEach(x=>{
        const row=document.createElement('div');row.style.cssText='padding:12px 0;border-bottom:1px solid var(--line);overflow-wrap:anywhere';
        const name=document.createElement('strong');name.textContent=x.clip?.name||'Vidéo';name.setAttribute('data-testid','preview-wait-name-'+x.index);
        const text=document.createElement('p');text.textContent=x.message;text.setAttribute('data-testid','preview-wait-status-'+x.index);text.style.cssText='font-size:13px;line-height:1.5;margin:6px 0';row.append(name,text);
        if(x.clip&&(x.kind.includes('failed')||x.kind==='not-uploaded'||timedOut)){
          const b=document.createElement('button');b.className='small';b.textContent=x.clip.mediaId?'Relancer l’aperçu':'Reprendre l’envoi';b.setAttribute('data-testid','preview-wait-retry-'+x.index);
          b.disabled=!!(x.clip._optimizing&&!x.clip.mediaId);
          b.onclick=()=>{pending.deadline=Date.now()+300000;host.retry(x.clip);};row.append(b);
        }
        list.append(row);
      });
    }
    const primary=overlay.querySelector('[data-testid="preview-wait-local"]');
    primary.textContent=entries.length?'Lire la vidéo locale':'Lancer la lecture';
    primary.disabled=entries.length>0&&!entries.every(x=>x.clip?._wcReady&&x.clip.wc);
    overlay.querySelector('[data-testid="preview-wait-local-warning"]').textContent=entries.length
      ?'La vidéo locale reste disponible. Sa lecture peut saccader sur les coupes rapides et ne confirme pas la sauvegarde.'
      :'La préparation est terminée. Relance la lecture quand tu es prêt.';
  }
  function request(from){
    if(!blockers(from).length)return false;
    host.stop();cancel();
    pending={from,project:host.project,range:JSON.stringify(host.range),deadline:Date.now()+300000,signature:null};
    overflow=document.body.style.overflow;document.body.style.overflow='hidden';
    overlay=document.createElement('div');overlay.setAttribute('data-testid','preview-wait-overlay');overlay.setAttribute('role','dialog');overlay.setAttribute('aria-modal','true');overlay.setAttribute('aria-labelledby','previewWaitTitle');
    overlay.style.cssText='position:fixed;inset:0;z-index:9990;background:#000b;display:grid;place-items:center;padding:16px;overflow:auto';
    overlay.innerHTML='<section style="width:min(100%,520px);max-height:90dvh;overflow:auto;background:var(--void,#111);color:var(--text,#fff);padding:24px;border:1px solid var(--line,#444);border-radius:8px">'
      +'<h2 id="previewWaitTitle" data-testid="preview-wait-title" style="font-size:18px;margin-bottom:16px"></h2><div data-testid="preview-wait-list" aria-live="polite"></div>'
      +'<p data-testid="preview-wait-local-warning" style="font-size:13px;line-height:1.5;margin:18px 0;color:var(--muted)">La vidéo locale reste disponible. Sa lecture peut saccader sur les coupes rapides et ne confirme pas la sauvegarde.</p>'
      +'<div style="display:grid;gap:10px">'
      +'<button class="primary" data-testid="preview-wait-local">Lire la vidéo locale</button>'
      +'<button class="small" data-testid="preview-wait-audio">Écouter l’audio seul</button>'
      +'<button class="small" data-testid="preview-wait-cancel">Annuler la lecture</button></div></section>';
    document.body.append(overlay);
    overlay.querySelectorAll('button').forEach(b=>{b.style.whiteSpace='normal';b.style.minHeight='44px';});
    overlay.querySelector('[data-testid="preview-wait-local"]').onclick=()=>resume(true);
    overlay.querySelector('[data-testid="preview-wait-audio"]').onclick=()=>{cancel();host.audio();};
    overlay.querySelector('[data-testid="preview-wait-cancel"]').onclick=cancel;
    const tick=()=>{
      if(!pending)return;
      if(host.project!==pending.project||JSON.stringify(host.range)!==pending.range){cancel();return;}
      if(!blockers(pending.from).length&&Date.now()<=pending.deadline){resume();return;}
      render();
    };
    render();overlay.querySelector('[data-testid="preview-wait-cancel"]').focus();timer=setInterval(tick,250);
    blockers(from).forEach(x=>{if(x.clip?.mediaId&&!x.clip._proxyTried&&x.clip._proxyState!=='failed')host.prepare(x.clip);});
    return true;
  }
  window.addEventListener('keydown',e=>{
    if(!pending)return;e.stopImmediatePropagation();
    if(e.key==='Escape'){e.preventDefault();cancel();}
    else if(e.key==='Tab'){
      const buttons=[...overlay.querySelectorAll('button:not([disabled])')], first=buttons[0],last=buttons[buttons.length-1];
      if(e.shiftKey&&document.activeElement===first){e.preventDefault();last.focus();}
      else if(!e.shiftKey&&document.activeElement===last){e.preventDefault();first.focus();}
    }
  },true);
  window.addEventListener('hashchange',cancel);
  document.addEventListener('visibilitychange',()=>{if(document.hidden)cancel();});
  return {allows,localInUse,blockers,request,cancel,get pending(){return pending;}};
};