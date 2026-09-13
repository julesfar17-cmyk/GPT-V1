/* Resumable transport only. Authentication, quotas and finalization remain server-owned. */
window.BeatCutUpload = (() => {
  const pause=ms=>new Promise(resolve=>setTimeout(resolve,ms));
  async function request(path, options={}, timeout=90000) {
    let last;
    for(let attempt=0;attempt<3;attempt++){
      const controller=new AbortController(), timer=setTimeout(()=>controller.abort(),timeout);
      try{
        const r=await fetch(path,{...options,credentials:'include',signal:controller.signal});
        const data=await r.json().catch(()=>({}));
        if(!r.ok){const error=new Error(typeof data.detail==='string'?data.detail:'Envoi interrompu (HTTP '+r.status+')');error.status=r.status;throw error;}
        return data;
      }catch(e){last=e;if(e.status && ![408,429,500,502,503,504].includes(e.status))throw e;}
      finally{clearTimeout(timer);}
      if(attempt<2)await pause(500*2**attempt);
    }
    if(last.name==='AbortError')throw new Error('Envoi interrompu : délai réseau dépassé. Les blocs reçus sont conservés.');
    throw last;
  }
  async function send(file,onProgress,owner){
    if(!file.size || file.size>300000000)throw new Error('Fichier vide ou trop lourd (max 300 Mo)');
    const ends=new Blob([file.slice(0,65536),file.slice(Math.max(0,file.size-65536))]);
    const digest=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',await ends.arrayBuffer()))).map(v=>v.toString(16).padStart(2,'0')).join('');
    const key='bc_upload:'+owner+':'+file.size+':'+file.name+':'+digest;
    let id;try{id=localStorage.getItem(key);}catch(_){}
    let session;
    for(let turn=0;turn<2;turn++){
      if(!id)id=crypto.randomUUID();
      try{
        session=await request('/api/media/uploads',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({upload_id:id,filename:file.name||'media',size:file.size,content_type:file.type||'application/octet-stream'})});
        break;
      }catch(e){if(turn===0&&[404,410].includes(e.status)){id=null;continue;}throw e;}
    }
    try{localStorage.setItem(key,id);}catch(_){}
    if(session.media_id){try{localStorage.removeItem(key);}catch(_){}return session;}
    const received=new Set(session.received);
    const progress=()=>{if(onProgress)onProgress(Math.round([...received].reduce((sum,i)=>sum+Math.min(session.chunk_size,file.size-i*session.chunk_size),0)/file.size*100));};
    progress();
    if(session.status==='uploading'){
      for(let i=0;i<session.total_chunks;i++){
        if(received.has(i))continue;
        await request('/api/media/uploads/'+id+'/chunks/'+i,{method:'PUT',headers:{'Content-Type':'application/octet-stream'},body:file.slice(i*session.chunk_size,Math.min(file.size,(i+1)*session.chunk_size))});
        received.add(i);progress();
      }
    }
    const until=Date.now()+300000;
    while(Date.now()<until){
      const result=await request('/api/media/uploads/'+id+'/complete',{method:'POST'},30000);
      if(result.media_id){try{localStorage.removeItem(key);}catch(_){}return result;}
      await pause(1000);
    }
    throw new Error('Finalisation trop longue — reprends l’envoi pour retrouver les blocs sauvegardés.');
  }
  return {send};
})();