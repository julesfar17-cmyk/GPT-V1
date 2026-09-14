/* Recovery is project-scoped. Missing files keep their slots; a boolean alone
   cannot prove that the bank, audio and saved plan references are complete. */
window.createProjectRestoreTracker = () => {
  const states=new WeakMap();
  function begin(project){
    const state={loading:true,stateLoaded:false,slots:[],discarded:new Set(),audioExpected:false,audioPendingUpload:false};
    states.set(project,state);return state;
  }
  function prepare(project,state,doc){
    if(states.get(project)!==state)return false;
    state.stateLoaded=true;
    state.audioExpected=!!(doc.audioMediaId||doc.audioName);
    state.slots=(doc.clipRefs||[]).map((ref,key)=>({key,ref:{...ref}}));
    return true;
  }
  function status(project,clips,buffer){
    const state=project&&states.get(project);
    if(!state)return null;
    const audio=state.audioExpected&&(!buffer||!project.audioMediaId||state.audioPendingUpload||project._uploadingAudio);
    const missing=state.slots.flatMap(slot=>{
      if(state.discarded.has(slot.key))return [];
      const index=clips.findIndex(c=>c._restoreKey===slot.key),clip=clips[index];
      // A real proxy is also sufficient to restore the exact, durable reference.
      const available=clip&&(!clip._missing||(clip._wcReady&&clip.wcProxy&&clip.mediaId));
      if(available&&(!clip._restoreUploadRequired||clip.mediaId))return [];
      return [{...slot,index,clip}];
    });
    return {state,loading:state.loading,stateUnavailable:!state.stateLoaded,audio,missing,
      blocked:state.loading||!state.stateLoaded||!!audio||missing.length>0};
  }
  return {begin,prepare,status,get:project=>project&&states.get(project),
    discard(project,key){states.get(project)?.discarded.add(key);}};
};