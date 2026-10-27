/* BooCue dashboard card. No build step, CDN or external dependency. */
const CARD_TEXT = {
  nl: {on:'Aan',off:'Uit',ready:'Klaar voor kippenvel',playing:'Speelt',mood:'Sfeer',effect:'Effect',queue:'Wachtrij',loop:'Doorlopend',chooseMood:'Kies een sfeer',chooseEffect:'Kies een effect',chooseQueue:'Kies een wachtrij',play:'Afspelen',stop:'Stoppen',next:'Volgende',stopAll:'Stop alles',motion:'Bewegingsregels',noRules:'Geen regels ingesteld',settings:'Instellingen',enableAudio:'Geluid op dit apparaat inschakelen',audioReady:'Geluid op dit apparaat ingeschakeld',browserHelp:'Houd dit dashboard open voor geluid op dit apparaat.',disabled:'BooCue staat uit. Zet het aan om af te spelen.',loading:'BooCue laden…',retry:'Opnieuw proberen',noQueues:'Maak eerst een wachtrij in BooCue.',waitMotion:'Wacht op beweging',waitDelay:'Wacht op volgend effect',now:'Nu',empty:'Er speelt niets',device:'Dit apparaat',speakers:'HA-speakers',silent:'Zonder geluid',favorites:'Favoriete effecten',close:'Melding sluiten',timeline:'Lichtverloop',preparing:'Voorbereiden…',offline:'Verbinding met Home Assistant verbroken.',admin:'Deze BooCue-kaart vereist een Home Assistant-beheerder.',notReady:'BooCue is niet beschikbaar. Controleer de integratie en vernieuw de pagina.',cancelled:'Afspelen geannuleerd.',title:'Titel',theme:'Weergave',auto:'Home Assistant volgen',light:'Licht',dark:'Donker',showMood:'Sfeer tonen',showEffects:'Effecten tonen',showQueue:'Wachtrij tonen',showMotion:'Bewegingsregels tonen',showFavorites:'Favorieten tonen',initialEffect:'Standaardeffect',initialMood:'Standaardsfeer',initialQueue:'Standaardwachtrij',defaults:'Automatisch kiezen',advanced:'Uitgangen per kanaal (optioneel)',inherit:'BooCue-instellingen gebruiken',output:'Geluidsuitgang',lights:'Lampen',players:'Speakers',overrideHelp:'Leeg laten gebruikt de opgeslagen BooCue-keuzes. Bewaar wachtrijen en bewegingsregels in het volledige paneel.',current:'huidig',select:'Selecteren'},
  en: {on:'On',off:'Off',ready:'Ready for goosebumps',playing:'Playing',mood:'Mood',effect:'Effect',queue:'Queue',loop:'Continuous',chooseMood:'Choose a mood',chooseEffect:'Choose an effect',chooseQueue:'Choose a queue',play:'Play',stop:'Stop',next:'Next',stopAll:'Stop all',motion:'Motion rules',noRules:'No rules configured',settings:'Settings',enableAudio:'Enable sound on this device',audioReady:'Sound enabled on this device',browserHelp:'Keep this dashboard open for sound on this device.',disabled:'BooCue is off. Turn it on to start playback.',loading:'Loading BooCue…',retry:'Retry',noQueues:'Create a queue in BooCue first.',waitMotion:'Waiting for motion',waitDelay:'Waiting for next effect',now:'Now',empty:'Nothing playing',device:'This device',speakers:'HA speakers',silent:'No sound',favorites:'Favorite effects',close:'Dismiss message',timeline:'Light timeline',preparing:'Preparing…',offline:'Disconnected from Home Assistant.',admin:'This BooCue card requires a Home Assistant administrator.',notReady:'BooCue is unavailable. Check the integration and refresh the page.',cancelled:'Playback cancelled.',title:'Title',theme:'Appearance',auto:'Follow Home Assistant',light:'Light',dark:'Dark',showMood:'Show mood',showEffects:'Show effects',showQueue:'Show queue',showMotion:'Show motion rules',showFavorites:'Show favorites',initialEffect:'Default effect',initialMood:'Default mood',initialQueue:'Default queue',defaults:'Choose automatically',advanced:'Channel outputs (optional)',inherit:'Use BooCue settings',output:'Sound output',lights:'Lights',players:'Speakers',overrideHelp:'Leave these empty to use saved BooCue choices. Create queues and motion rules in the full panel.',current:'current',select:'Select'},
};
const cardEsc = value => String(value ?? '').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const cardIcon = name => `<ha-icon icon="${cardEsc(name)}" aria-hidden="true"></ha-icon>`;
const cardTime = value => {const n=Math.max(0,Math.floor(value||0));return `${Math.floor(n/60)}:${String(n%60).padStart(2,'0')}`;};
const cardLanguage = hass => hass?.locale?.language?.startsWith('nl') ? 'nl' : 'en';
const cardClients = new WeakMap();
const CARD_RUNTIME = new Set(['lights','output','speakers','volume','brightness','speed','offset_ms','routing','repeat','restore','interval_ms','audio_mode','duck_mood']);
function validateCardConfig(config) {
  if(!config||typeof config!=='object'||Array.isArray(config))throw Error('BooCue: invalid card configuration');
  const result={title:'BooCue',theme:'auto',show_mood:true,show_effects:true,show_queue:true,show_motion:true,show_favorites:true,...structuredClone(config)};
  if(typeof result.title!=='string'||result.title.length>80)throw Error('BooCue: title must be text (up to 80 characters)');
  if(!['auto','light','dark'].includes(result.theme))throw Error('BooCue: theme must be auto, light or dark');
  for(const key of ['show_mood','show_effects','show_queue','show_motion','show_favorites'])if(typeof result[key]!=='boolean')throw Error(`BooCue: ${key} must be true or false`);
  for(const key of ['effect','mood','queue'])if(result[key]!==undefined&&(typeof result[key]!=='string'||!result[key]))throw Error(`BooCue: ${key} must be an id`);
  for(const key of ['effect_settings','mood_settings','queue_settings']){
    const values=result[key]||{};
    if(typeof values!=='object'||Array.isArray(values)||Object.keys(values).some(k=>!CARD_RUNTIME.has(k)))throw Error(`BooCue: invalid ${key}`);
    for(const name of ['lights','speakers'])if(values[name]!==undefined&&(!Array.isArray(values[name])||values[name].some(e=>typeof e!=='string'||!e.startsWith(name==='lights'?'light.':'media_player.'))))throw Error(`BooCue: invalid ${name}`);
    if(values.output!==undefined&&!['browser','speakers','none'].includes(values.output))throw Error('BooCue: invalid output');
    for(const name of ['volume','brightness','duck_mood'])if(values[name]!==undefined&&(!Number.isFinite(values[name])||values[name]<0||values[name]>1))throw Error(`BooCue: invalid ${name}`);
  }
  return result;
}

/* One subscription and audio station per HA connection, shared by all cards. */
class BooCueDashboardClient {
  constructor(hass){
    this.hass=hass;this.connection=hass.connection;this.listeners=new Set();this.data=null;this.status=null;
    this.catalogVersion=0;this.pending=new Set();this.generations={effect:0,mood:0,queue:0};
    this.sources=new Map();this.buffers=new Map();this.receiving=new Map();this.blocked=new Set();
    this.epoch=0;this.clockOffset=0;this.error='';this.online=this.connection.connected!==false;this.teardown=Promise.resolve();
    this._ready=()=>{this.online=true;this.browserId=null;this._cancelAll();void this.refresh();};
    this._offline=()=>{this.online=false;this.browserId=null;this._cancelAll();this.emit();};
  }
  attach(listener){
    this.listeners.add(listener);
    if(this.listeners.size===1)void this._activate();else listener(this);
    return ()=>{this.listeners.delete(listener);if(!this.listeners.size)queueMicrotask(()=>{if(!this.listeners.size)this._deactivate();});};
  }
  async _activate(){
    const epoch=++this.epoch;
    await this.teardown;if(epoch!==this.epoch||!this.listeners.size)return;
    this.connection.addEventListener?.('ready',this._ready);this.connection.addEventListener?.('disconnected',this._offline);
    try{
      const unsubscribe=await this.connection.subscribeEvents(event=>{if(epoch===this.epoch)this._state(event.data);},'boocue_state');
      if(epoch!==this.epoch||!this.listeners.size){await unsubscribe();return;}
      this.unsubscribe=unsubscribe;await this.refresh();
    }catch(error){if(epoch===this.epoch){this.error=this._error(error);this.emit();}}
  }
  _deactivate(){
    ++this.epoch;this._cancelAll();const station=this.browserId;this.browserId=null;
    this.connection.removeEventListener?.('ready',this._ready);this.connection.removeEventListener?.('disconnected',this._offline);
    const unsubscribe=this.unsubscribe;this.unsubscribe=null;const context=this.context;this.context=null;this.buffers.clear();
    const claim=this.claiming;
    this.teardown=(async()=>{
      try{await unsubscribe?.();}catch{}
      try{await claim;}catch{}
      if(station)try{await this.hass.callWS({type:'boocue/browser_release',station_id:station});}catch{}
      if(context&&context.state!=='closed')try{await context.close();}catch{}
    })();
  }
  emit(){for(const listener of this.listeners)listener(this);}
  _error(error){
    const t=CARD_TEXT[cardLanguage(this.hass)];
    if(error?.code==='unauthorized')return t.admin;
    if(['unknown_command','not_ready'].includes(error?.code))return t.notReady;
    return String(error?.message||error||t.notReady);
  }
  async refresh(){
    if(!this.listeners.size)return;
    if(this.loading){this.reload=true;return this.loading;}
    const epoch=this.epoch;
    this.loading=(async()=>{
      try{
        const before=Date.now()/1000,data=await this.hass.callWS({type:'boocue/dashboard'});
        if(epoch!==this.epoch||!this.listeners.size)return;
        this.clockOffset=data.server_time-(before+Date.now()/1000)/2;
        this.data=data;this.catalogVersion++;this.error='';this.online=true;
        this._state({...data.status,server_time:data.server_time},true);
        if(this.status){this.data.settings.enabled=this.status.enabled!==false;this.data.settings.automatic_enabled=this.status.automatic_enabled;}
        this.emit();
      }catch(error){if(epoch===this.epoch){this.error=this._error(error);this.emit();}}
    })();
    await this.loading;this.loading=null;
    if(this.reload){this.reload=false;void this.refresh();}
  }
  _state(state,fromLoad=false){
    if(state.server_time&&this.lastTime&&state.server_time<this.lastTime)return;
    const old=this.status;this.lastTime=state.server_time||this.lastTime;this.status=state;
    const stopped=old&&state.stop_sequence!==undefined&&old.stop_sequence!==state.stop_sequence;
    if(stopped||state.enabled===false)this._cancelAll();
    if(this.data){this.data.settings.enabled=state.enabled!==false;this.data.settings.automatic_enabled=state.automatic_enabled;}
    if(this.browserId&&state.browser_station_id!==undefined&&state.browser_station_id!==this.browserId){this.browserId=null;this._stopAudio();}
    this._syncAudio();
    if(!fromLoad&&(!this.data||state.settings_revision!==this.data.status.settings_revision||state.library_revision!==this.data.status.library_revision))void this.refresh();
    this.emit();
  }
  _cancelAll(){
    for(const key of ['effect','mood','queue']){this.generations[key]++;this.pending.delete(key);}
    this._stopAudio();this.receiving.clear();
  }
  _stopAudio(channel){
    for(const key of channel?[channel]:[...this.sources.keys()]){
      const audio=this.sources.get(key);if(!audio)continue;
      audio.source.onended=null;try{audio.source.stop();}catch{}
      audio.source.disconnect();audio.gain.disconnect();this.sources.delete(key);
    }
    this._duck();
  }
  _block(state){if(state?.run_id){this.blocked.add(state.run_id);if(this.blocked.size>32)this.blocked.delete(this.blocked.values().next().value);}}
  _assertEnabled(){if(!this.online)throw Error(CARD_TEXT[cardLanguage(this.hass)].offline);if(this.status?.enabled===false)throw Error(CARD_TEXT[cardLanguage(this.hass)].disabled);}
  resolved(id,channel,overrides={}){const settings=this.data.settings;return {...(channel==='mood'?settings.mood:settings),...(channel==='effect'?settings.effect_routes[id]:{}),...overrides};}
  async enableAudio(){
    this._assertEnabled();const epoch=this.epoch;
    if(!this.context||this.context.state==='closed')this.context=new AudioContext();
    // Resume inside the user's click before awaiting network or cleanup.
    const resumed=this.context.resume();await this.teardown;await resumed;
    this._assertEnabled();if(epoch!==this.epoch||!this.listeners.size)throw Error(CARD_TEXT[cardLanguage(this.hass)].cancelled);
    if(this.browserId)return this.browserId;
    if(!this.claiming){
      this.claiming=(async()=>{
        const result=await this.hass.callWS({type:'boocue/browser_ready'});
        if(epoch!==this.epoch||!this.listeners.size){await this.hass.callWS({type:'boocue/browser_release',station_id:result.station_id});throw Error(CARD_TEXT[cardLanguage(this.hass)].cancelled);}
        this.browserId=result.station_id;this.emit();return this.browserId;
      })();
    }
    try{return await this.claiming;}finally{this.claiming=null;}
  }
  async _buffer(id){
    if(this.buffers.has(id))return this.buffers.get(id);
    const context=this.context;
    const promise=(async()=>{
      const info=await this.hass.callWS({type:'boocue/audio',effect_id:id});
      const response=await this.hass.fetchWithAuth(info.url);
      if(!response.ok)throw Error(`Audio HTTP ${response.status}`);
      let buffer=await context.decodeAudioData(await response.arrayBuffer());
      const effect=this.data.effects.find(e=>e.id===id),frames=Math.round(effect.duration*buffer.sampleRate);
      if(Math.abs(buffer.duration-effect.duration)<.25&&frames!==buffer.length){
        const aligned=context.createBuffer(buffer.numberOfChannels,frames,buffer.sampleRate);
        for(let i=0;i<buffer.numberOfChannels;i++)aligned.copyToChannel(buffer.getChannelData(i).subarray(0,frames),i);
        buffer=aligned;
      }
      return buffer;
    })();
    if(this.buffers.size>=3)this.buffers.delete(this.buffers.keys().next().value);this.buffers.set(id,promise);
    try{return await promise;}catch(error){if(this.buffers.get(id)===promise)this.buffers.delete(id);throw error;}
  }
  _syncAudio(){
    if(!this.status)return;
    for(const channel of ['effect','mood']){
      const state=this.status.channels?.[channel],source=this.sources.get(channel);
      if(source&&(!state?.playing||state.run_id!==source.run_id||state.browser_id!==this.browserId))this._stopAudio(channel);
      if(state?.playing&&this.status.enabled!==false&&state.output==='browser'&&this.browserId&&state.browser_id===this.browserId&&!this.pending.has(channel)&&!this.sources.has(channel)&&!this.blocked.has(state.run_id))void this._receive(channel,state);
    }
    this._duck();
  }
  async _receive(channel,state){
    if(this.receiving.get(channel)===state.run_id||!this.context)return;
    this.receiving.set(channel,state.run_id);const epoch=this.epoch,generation=this.generations[channel];
    try{
      const buffer=await this._buffer(state.effect_id),current=this.status.channels?.[channel];
      if(epoch!==this.epoch||generation!==this.generations[channel]||this.status.enabled===false||!current?.playing||current.run_id!==state.run_id||current.browser_id!==this.browserId||this.blocked.has(state.run_id)||this.sources.has(channel))return;
      const elapsed=(Date.now()/1000+this.clockOffset-state.start_at)*(state.speed||1);
      if(!state.repeat&&elapsed>=state.duration)return;
      const source=this.context.createBufferSource(),gain=this.context.createGain();
      source.buffer=buffer;source.playbackRate.value=state.speed||1;source.loop=state.repeat;
      source.connect(gain);gain.connect(this.context.destination);gain.gain.value=state.volume;
      this.sources.set(channel,{source,gain,volume:state.volume,run_id:state.run_id});
      source.onended=()=>{if(this.sources.get(channel)?.source===source){source.disconnect();gain.disconnect();this.sources.delete(channel);this._duck();}};
      source.start(this.context.currentTime+Math.max(0,state.start_at-(Date.now()/1000+this.clockOffset)),Math.max(0,elapsed)%buffer.duration);this._duck();
    }catch(error){
      if(epoch===this.epoch&&this.status.channels?.[channel]?.run_id===state.run_id){
        this.error=this._error(error);this._block(state);this.emit();
        try{await this.hass.callWS(state.queue_run_id?{type:'boocue/queue',action:'stop',run_id:state.queue_run_id}:{type:'boocue/stop',channel,run_id:state.run_id});}catch{}
      }
    }finally{if(this.receiving.get(channel)===state.run_id)this.receiving.delete(channel);}
  }
  _duck(){
    if(!this.context)return;
    const effect=this.status?.channels?.effect;
    for(const [channel,audio] of this.sources){
      const factor=channel==='mood'&&effect?.playing&&this.sources.has('effect')?(effect.duck_mood??.35):1;
      const value=audio.volume*factor;
      if(audio.gain.gain.setTargetAtTime)audio.gain.gain.setTargetAtTime(value,this.context.currentTime,.05);else audio.gain.gain.value=value;
    }
  }
  async play(id,channel,overrides={}){
    this._assertEnabled();if(this.pending.has(channel))return;
    const epoch=this.epoch,generation=++this.generations[channel];this.pending.add(channel);this.error='';this.emit();
    try{
      const settings=this.resolved(id,channel,overrides);
      if(settings.output==='browser'){await this.enableAudio();await this._buffer(id);}
      if(epoch!==this.epoch||generation!==this.generations[channel]||this.status.enabled===false)return;
      const result=await this.hass.callWS({type:'boocue/play',effect_id:id,channel,settings:overrides,browser_id:settings.output==='browser'?this.browserId:undefined});
      if(epoch!==this.epoch||generation!==this.generations[channel]||this.status.enabled===false){await this.hass.callWS({type:'boocue/stop',channel,run_id:result.run_id});return;}
      this.status.channels[channel]=result;
    }finally{if(generation===this.generations[channel])this.pending.delete(channel);this._syncAudio();this.emit();}
  }
  queueNeedsBrowser(queue,overrides={}){const s=this.data.settings;return queue.effects.some(id=>({...s,...queue.settings,...s.effect_routes[id],...overrides}).output==='browser');}
  async startQueue(id,overrides={}){
    this._assertEnabled();if(this.pending.has('queue'))return;
    const queue=this.data.settings.queues.find(q=>q.id===id);if(!queue)throw Error(CARD_TEXT[cardLanguage(this.hass)].noQueues);
    const epoch=this.epoch,generation=++this.generations.queue;this.pending.add('queue');this.error='';this.emit();
    try{
      const browser=this.queueNeedsBrowser(queue,overrides);if(browser)await this.enableAudio();
      if(epoch!==this.epoch||generation!==this.generations.queue||this.status.enabled===false)return;
      const result=await this.hass.callWS({type:'boocue/queue',action:'start',queue_id:id,settings:overrides,browser_id:browser?this.browserId:undefined});
      if(epoch!==this.epoch||generation!==this.generations.queue||this.status.enabled===false){await this.hass.callWS({type:'boocue/queue',action:'stop',run_id:result.run_id});return;}
      this.status.queue=result;
    }finally{if(generation===this.generations.queue)this.pending.delete('queue');this.emit();}
  }
  async stop(channel){
    if(channel==='queue'){
      this.generations.queue++;this.pending.delete('queue');const effect=this.status.channels?.effect;
      if(effect?.queue_run_id){this._block(effect);this._stopAudio('effect');}
      this.emit();await this.hass.callWS({type:'boocue/queue',action:'stop'});
    }else{
      if(channel){this.generations[channel]++;this.pending.delete(channel);this._block(this.status.channels?.[channel]);this._stopAudio(channel);if(channel==='effect'){this.generations.queue++;this.pending.delete('queue');}}
      else {for(const state of Object.values(this.status.channels||{}))this._block(state);this._cancelAll();}
      this.emit();await this.hass.callWS({type:'boocue/stop',...(channel?{channel}:{})});
    }
  }
  async next(){this._assertEnabled();if(this.pending.has('queue'))return;const effect=this.status.channels?.effect;if(effect?.queue_run_id){this._block(effect);this._stopAudio('effect');}this.pending.add('queue');this.emit();try{await this.hass.callWS({type:'boocue/queue',action:'next'});}finally{this.pending.delete('queue');this.emit();}}
  async setting(key,value){
    if(this.pending.has(key))return;this.pending.add(key);this.emit();
    try{const values=await this.hass.callWS({type:'boocue/settings',settings:{[key]:value}});if(this.data){this.data.settings[key]=values[key];this.status[key]=values[key];}if(key==='enabled'&&!value)this._cancelAll();}
    finally{this.pending.delete(key);this.emit();}
  }
}
function dashboardClient(hass){let client=cardClients.get(hass.connection);if(!client){client=new BooCueDashboardClient(hass);cardClients.set(hass.connection,client);}client.hass=hass;return client;}

const CARD_CSS = `
:host{display:block;min-width:0;container-type:inline-size;font:14px/1.5 var(--ha-font-family-body,system-ui,sans-serif)}
*{box-sizing:border-box}[hidden]{display:none!important}
ha-card{--bc-surface:#fdfcfe;--bc-inset:#ece8f0;--bc-ink:#2d2338;--bc-muted:#685c73;--bc-line:#ded7e5;--bc-accent:#754294;--bc-accent-ink:#fefaff;--bc-focus:#9258b5;--bc-selected:#ede0f4;--bc-selection:#dec7eb;--bc-error:#9e2d43;--bc-error-bg:#fbe9ed;--ha-card-background:var(--bc-surface);--ha-card-border-color:var(--bc-line);color:var(--bc-ink);overflow:hidden;color-scheme:light}
ha-card[data-theme="dark"]{--bc-surface:#282230;--bc-inset:#332b3d;--bc-ink:#f1ebf7;--bc-muted:#b9acc7;--bc-line:#44394f;--bc-accent:#c69ce2;--bc-accent-ink:#2b183a;--bc-focus:#d8aff3;--bc-selected:#44324f;--bc-selection:#604074;--bc-error:#ffb4c2;--bc-error-bg:#492b37;color-scheme:dark}
::selection{background:var(--bc-selection);color:var(--bc-ink)}button,select,input{font:inherit;outline-offset:3px}button:focus-visible,select:focus-visible,input:focus-visible,a:focus-visible{outline:2px solid var(--bc-focus)}input{accent-color:var(--bc-accent);caret-color:var(--bc-accent)}
button{display:inline-flex;align-items:center;justify-content:center;gap:7px;min-height:44px;border:1px solid transparent;border-radius:10px;background:transparent;color:var(--bc-accent);cursor:pointer;padding:8px 12px;font-weight:600;font-size:13px}
button:hover{background:var(--bc-inset)}button:disabled{opacity:.48;cursor:default}ha-icon{display:inline-flex;width:20px;height:20px;--mdc-icon-size:20px;flex-shrink:0}
header{display:flex;align-items:center;gap:12px;padding:20px 20px 14px}header>.ghost{width:29px;height:29px;--mdc-icon-size:29px;color:var(--bc-accent)}.identity{flex:1;min-width:0}h2{font-size:21px;font-weight:700;letter-spacing:-.02em;line-height:1.35;margin:0;overflow-wrap:anywhere}.summary{margin:2px 0 0;font-size:13px;color:var(--bc-muted)}
.power{border-color:var(--bc-line);color:var(--bc-ink);flex-shrink:0}.power[aria-pressed="true"]{background:var(--bc-selected);border-color:var(--bc-accent);color:var(--bc-accent)}
.lane{padding:15px 20px 16px;border-top:1px solid var(--bc-line)}.lane-heading{display:flex;align-items:center;gap:8px;margin-bottom:10px}.lane-heading>ha-icon{color:var(--bc-muted)}.lane.is-playing .lane-heading>ha-icon{color:var(--bc-accent)}h3{margin:0;font-size:14px;font-weight:650}.lane-state{margin-left:auto;color:var(--bc-muted);font-size:13px;min-width:0;text-align:right}.lane.is-playing .lane-state{color:var(--bc-accent)}
.controls{display:flex;gap:8px;align-items:center}.controls select{flex:1;min-width:0;width:0;height:44px;border:1px solid var(--bc-line);border-radius:8px;padding:0 28px 0 10px;background:var(--bc-surface);color:var(--bc-ink);text-overflow:ellipsis}.controls select:disabled{opacity:.6}.actions{display:flex;gap:4px;flex-shrink:0}.actions button{width:40px;min-width:40px;padding:8px}.actions button[data-stop]{color:var(--bc-muted)}
.detail{margin:8px 0 0;min-height:19px;font-size:13px;color:var(--bc-muted);overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.cue-line{display:flex;align-items:flex-end;gap:12px;margin-top:5px;min-height:22px}.cue-strip{display:flex;align-items:flex-end;gap:3px;flex:1;min-width:0;height:22px}.cue-block{position:relative;flex:1;max-width:14px;height:5px;min-width:0}.cue-block>span{display:block;height:5px;border-radius:2px}.cue-pointer{display:none;position:absolute;bottom:7px;left:50%;transform:translateX(-50%);width:16px;height:16px;--mdc-icon-size:16px;color:var(--bc-accent)}.cue-block.is-current>.cue-pointer{display:inline-flex}.time{font-size:13px;color:var(--bc-muted);font-variant-numeric:tabular-nums;white-space:nowrap}
.favorites{display:flex;gap:6px;overflow-x:auto;max-width:100%;margin:11px 0 0;padding:1px 0 3px;scrollbar-width:thin;scrollbar-color:var(--bc-line) transparent}.favorites button{white-space:nowrap;flex-shrink:0;border:1px solid var(--bc-line);min-height:36px;padding:6px 9px;font-weight:500}.favorites ha-icon{width:16px;height:16px;--mdc-icon-size:16px}
footer{border-top:1px solid var(--bc-line);padding:13px 20px 16px}.footer-row{display:flex;gap:12px;align-items:center;justify-content:space-between}.motion{display:flex;align-items:center;gap:8px;font-size:13px;cursor:pointer;min-height:44px}.motion input{width:17px;height:17px;margin:0}.motion-note{display:block;font-size:13px;color:var(--bc-muted);line-height:1.3}.stop-all{background:var(--bc-accent);color:var(--bc-accent-ink);white-space:nowrap}.stop-all:hover{background:var(--bc-accent);filter:brightness(.95)}
.audio-row{padding:0 20px 12px}.audio-row button{padding:0;min-height:36px;text-align:left;justify-content:flex-start;font-weight:500}.audio-row button:hover{background:transparent;text-decoration:underline;text-underline-offset:3px}.hint{font-size:13px;color:var(--bc-muted);margin:0}.bottom-link{display:flex;justify-content:flex-end;margin-top:9px}a{font-size:13px;color:var(--bc-muted);text-decoration:none;text-underline-offset:3px}a:hover{text-decoration:underline}.notice{padding:10px 20px;background:var(--bc-inset);font-size:13px;border-top:1px solid var(--bc-line);margin:0}.error{display:flex;gap:8px;align-items:flex-start;background:var(--bc-error-bg);color:var(--bc-error);padding:10px 12px 10px 20px;font-size:13px;overflow-wrap:anywhere}.error span{flex:1}.error button{color:inherit;min-height:32px;padding:3px}.loading{padding:24px 20px;color:var(--bc-muted)}
@container(max-width:340px){header{padding:16px}.lane{padding:14px 16px}.controls{flex-wrap:wrap}.controls select{width:100%;flex-basis:100%}.actions{margin-left:auto}footer{padding:12px 16px}.audio-row{padding:0 16px 12px}.footer-row{flex-wrap:wrap}.stop-all{margin-left:auto}.favorites{margin-top:8px}}
@media(prefers-reduced-motion:reduce){*{scroll-behavior:auto!important}}
`;

class BooCueCard extends HTMLElement {
  constructor(){super();this.attachShadow({mode:'open'});this.selected={};this._config=validateCardConfig({});this.shadowRoot.addEventListener('click',event=>void this._click(event));this.shadowRoot.addEventListener('change',event=>void this._change(event));}
  setConfig(config){this._config=validateCardConfig(config);this.selected={effect:config.effect,mood:config.mood,queue:config.queue};this._renderKey=null;this._update();}
  set hass(value){const changed=this._hass?.connection!==value.connection;this._hass=value;if(changed&&this._detach){this._detach();this._detach=null;this.client=null;}if(this.isConnected&&!this._detach)this._connect();if(this.client)this.client.hass=value;this._update();}
  connectedCallback(){this._connect();this._update();}
  disconnectedCallback(){this._detach?.();this._detach=null;}
  _connect(){if(!this._hass||this._detach)return;this.client=dashboardClient(this._hass);this._detach=this.client.attach(()=>this._update());}
  getCardSize(){return 2+3*['show_mood','show_effects','show_queue'].filter(key=>this._config[key]).length+(this._config.show_motion?1:0);}
  getGridOptions(){return {columns:12,rows:'auto',min_columns:6};}
  static getStubConfig(){return {title:'BooCue'};}
  static getConfigElement(){return document.createElement('boocue-card-editor');}
  get t(){return CARD_TEXT[cardLanguage(this._hass)];}
  get theme(){return this._config.theme==='auto'?(this._hass?.themes?.darkMode?'dark':'light'):this._config.theme;}
  _update(){
    if(!this._hass)return;
    const key=`${JSON.stringify(this._config)}|${cardLanguage(this._hass)}|${this.client?.catalogVersion||0}`;
    if(key!==this._renderKey){this._renderKey=key;this._render();}
    this.shadowRoot.querySelector('ha-card')?.setAttribute('data-theme',this.theme);this._paint();
  }
  _render(){
    const t=this.t,data=this.client?.data,focus=this.shadowRoot.activeElement?.id;
    this.shadowRoot.innerHTML=`<style>${CARD_CSS}</style><ha-card data-theme="${this.theme}"><header>${cardIcon('mdi:ghost').replace('<ha-icon ','<ha-icon class="ghost" ')}<div class="identity"><h2>${cardEsc(this._config.title)}</h2><p class="summary" id="summary"></p></div><button class="power" id="power" data-action="power" aria-pressed="false">${cardIcon('mdi:power')}<span></span></button></header><div class="error" role="alert" id="error" hidden><span></span><button data-action="dismiss" aria-label="${t.close}">${cardIcon('mdi:close')}</button></div><p class="notice" id="disabled" role="status" hidden>${t.disabled}</p>${data?this._lanes(data):`<div class="loading">${t.loading}<button data-action="retry">${t.retry}</button></div>`}${data?`<div class="audio-row" id="audio-row" hidden><button data-action="audio" id="audio-ready">${cardIcon('mdi:volume-high')}<span></span></button><p class="hint">${t.browserHelp}</p></div><footer><div class="footer-row"><label class="motion" ${this._config.show_motion?'':'hidden'}><input type="checkbox" id="motion"><span>${t.motion}<small class="motion-note" id="motion-note"></small></span></label><button class="stop-all" data-action="stop-all" id="stop-all">${cardIcon('mdi:stop')}${t.stopAll}</button></div><div class="bottom-link"><a href="/boocue">${t.settings}</a></div></footer>`:''}</ha-card>`;
    if(focus)this.shadowRoot.getElementById(focus)?.focus({preventScroll:true});
  }
  _lanes(data){
    const t=this.t;
    return ['mood','effect','queue'].filter(channel=>this._config[channel==='effect'?'show_effects':`show_${channel}`]).map(channel=>{
      const items=channel==='queue'?data.settings.queues:data.effects.filter(e=>(e.category==='moods')===(channel==='mood'));
      if(!items.some(e=>e.id===this.selected[channel]))this.selected[channel]=items.find(e=>e.id===(channel==='queue'?this.client.status?.queue?.queue_id:this.client.status?.channels?.[channel]?.effect_id))?.id||items.find(e=>data.settings.favorites.includes(e.id))?.id||items[0]?.id;
      const selected=items.find(e=>e.id===this.selected[channel]);
      const icon=channel==='queue'?'mdi:playlist-play':channel==='mood'?'mdi:weather-night':selected?.icon||'mdi:lightning-bolt-outline';
      const choose=t[channel==='mood'?'chooseMood':channel==='queue'?'chooseQueue':'chooseEffect'];
      const favorite=channel==='effect'&&this._config.show_favorites?items.filter(e=>data.settings.favorites.includes(e.id)).slice(0,8):[];
      return `<section class="lane" data-lane="${channel}" aria-labelledby="heading-${channel}"><div class="lane-heading">${cardIcon(icon)}<h3 id="heading-${channel}">${t[channel]}</h3><span class="lane-state" id="state-${channel}"></span></div><div class="controls"><select id="select-${channel}" data-channel="${channel}" aria-label="${choose}" ${items.length?'':'disabled'}>${items.length?items.map(e=>`<option value="${cardEsc(e.id)}" ${e.id===this.selected[channel]?'selected':''}>${cardEsc(e.title||e.name)}</option>`).join(''):`<option value="">${choose}</option>`}</select><div class="actions"><button id="play-${channel}" data-play="${channel}" aria-label="${t.play}: ${t[channel]}" title="${t.play}">${cardIcon('mdi:play')}</button>${channel==='queue'?`<button id="next-queue" data-action="next" aria-label="${t.next}: ${t.queue}" title="${t.next}">${cardIcon('mdi:skip-next')}</button>`:''}<button id="stop-${channel}" data-stop="${channel}" aria-label="${t.stop}: ${t[channel]}" title="${t.stop}">${cardIcon('mdi:stop')}</button></div></div><p class="detail" id="detail-${channel}">${channel==='queue'&&!items.length?t.noQueues:''}</p>${channel!=='queue'?`<div class="cue-line"><div class="cue-strip" id="cues-${channel}" role="img" aria-label="${t.timeline}"></div><span class="time" id="time-${channel}"></span></div>`:''}${favorite.length?`<div class="favorites" aria-label="${t.favorites}">${favorite.map(e=>`<button data-favorite="${cardEsc(e.id)}">${cardIcon(e.icon)}${cardEsc(e.title)}</button>`).join('')}</div>`:''}</section>`;
    }).join('');
  }
  _text(id,value){const node=this.shadowRoot.getElementById(id);if(node&&node.textContent!==value)node.textContent=value;}
  _paint(){
    const c=this.client,t=this.t,status=c?.status,data=c?.data,root=this.shadowRoot;
    const unavailable=!status||!c.online||this._hass.user?.is_admin===false,disabled=unavailable||status.enabled===false||c.pending.has('enabled');
    const power=root.getElementById('power');if(power){power.hidden=!status;power.disabled=unavailable||c.pending.has('enabled');power.setAttribute('aria-pressed',String(status?.enabled!==false));power.querySelector('span').textContent=status?.enabled===false?t.off:t.on;power.setAttribute('aria-label',`BooCue ${status?.enabled===false?t.on:t.off}`);}
    this._text('summary',!status?t.loading:!c?.online?t.offline:status?.enabled===false?t.off:status?.playing?t.playing:t.ready);
    const error=root.getElementById('error'),message=this._hass.user?.is_admin===false?t.admin:c?.error;
    if(error){error.hidden=!message;error.querySelector('span').textContent=message||'';}
    const notice=root.getElementById('disabled');if(notice)notice.hidden=status?.enabled!==false;
    if(!data||!status)return;
    for(const channel of ['mood','effect','queue']){
      const lane=root.querySelector(`[data-lane="${channel}"]`);if(!lane)continue;
      const state=channel==='queue'?status.queue:status.channels?.[channel],running=Boolean(state?.playing),pending=c.pending.has(channel);
      lane.classList.toggle('is-playing',running);lane.setAttribute('aria-busy',String(pending));
      const play=root.getElementById(`play-${channel}`);play.disabled=disabled||pending||!this.selected[channel];
      const stop=root.getElementById(`stop-${channel}`);stop.disabled=unavailable||!running&&!pending&&(channel!=='effect'||!status.queue?.playing);
      this._text(`state-${channel}`,pending?t.preparing:running?(channel==='mood'?t.loop:t.playing):'');
      if(channel==='queue'){
        root.getElementById('next-queue').disabled=disabled||pending||!running;
        const q=data.settings.queues.find(q=>q.id===this.selected.queue);
        this._text('detail-queue',state?.error|| (running?`${state.name} · ${((state.step-1)%state.total)+1}/${state.total}${state.waiting?` · ${state.waiting==='motion'?t.waitMotion:t.waitDelay}`:''}`:q?`${q.effects.length} ${q.effects.length===1?'effect':cardLanguage(this._hass)==='nl'?'effecten':'effects'}`:t.noQueues));
      }else{
        const effect=data.effects.find(e=>e.id===(running?state.effect_id:this.selected[channel]));
        lane.querySelector('.lane-heading>ha-icon')?.setAttribute('icon',channel==='mood'?'mdi:weather-night':effect?.icon||'mdi:lightning-bolt-outline');
        const description=effect?.descriptions?.[cardLanguage(this._hass)]||effect?.description||'';
        this._text(`detail-${channel}`,state?.error||(running?`${t.now}: ${state.title||effect?.title||''}`:description));
        const detail=root.getElementById(`detail-${channel}`);detail.title=detail.textContent;
        this._paintCues(channel,effect,running?state:null);
      }
    }
    for(const button of root.querySelectorAll('[data-favorite]'))button.disabled=disabled||c.pending.has('effect');
    const motion=root.getElementById('motion');if(motion){motion.checked=Boolean(data.settings.automatic_enabled);motion.disabled=unavailable||!data.motion_rule_count||c.pending.has('automatic_enabled');}
    this._text('motion-note',data.motion_rule_count?(status.enabled===false?t.off:''):t.noRules);
    const stopAll=root.getElementById('stop-all');if(stopAll)stopAll.disabled=unavailable||!status.playing&&!c.pending.has('effect')&&!c.pending.has('mood')&&!c.pending.has('queue')&&!data.settings.automatic_enabled;
    const needsBrowser=['effect','mood'].some(channel=>this._config[channel==='effect'?'show_effects':'show_mood']&&this.selected[channel]&&c.resolved(this.selected[channel],channel,this._config[`${channel}_settings`]).output==='browser')||this._config.show_queue&&data.settings.queues.some(q=>q.id===this.selected.queue&&c.queueNeedsBrowser(q,this._config.queue_settings));
    const audio=root.getElementById('audio-row');if(audio)audio.hidden=!needsBrowser&&!c.browserId;
    const ready=root.getElementById('audio-ready');if(ready){ready.disabled=disabled||Boolean(c.browserId);ready.querySelector('span').textContent=c.browserId?t.audioReady:t.enableAudio;}
  }
  _paintCues(channel,effect,state){
    const strip=this.shadowRoot.getElementById(`cues-${channel}`);if(!strip)return;
    const blocks=effect?.cue_blocks||[];
    if(strip.dataset.effect!==effect?.id){strip.dataset.effect=effect?.id||'';strip.innerHTML=blocks.map((cue,i)=>`<i class="cue-block" data-block="${i}"><span style="background:hsl(${Number(cue.hue)} ${Number(cue.saturation)*70}% 55%);opacity:${.2+Number(cue.brightness)*.8}"></span>${cardIcon('mdi:arrow-down-bold').replace('<ha-icon ','<ha-icon class="cue-pointer" ')}</i>`).join('');}
    let current=-1,elapsed=0;
    if(state){const raw=(Date.now()/1000+this.client.clockOffset-state.start_at-(state.offset_ms||0)/1000)*(state.speed||1);elapsed=Math.max(0,(Date.now()/1000+this.client.clockOffset-state.start_at)*(state.speed||1));const at=raw<0?raw:state.repeat?raw%state.duration:Math.min(raw,state.duration);for(let i=0;i<blocks.length;i++)if(blocks[i].at<=at)current=i;}
    if(strip.dataset.current!==String(current)){strip.dataset.current=String(current);for(const block of strip.children)block.classList.toggle('is-current',Number(block.dataset.block)===current);strip.setAttribute('aria-label',current<0?this.t.timeline:`${this.t.timeline} · ${current+1}/${blocks.length}`);}
    this._text(`time-${channel}`,state?`${cardTime(state.repeat?elapsed%state.duration:Math.min(elapsed,state.duration))} / ${cardTime(state.duration)}`:cardTime(effect?.duration));
  }
  async _run(action){try{await action();}catch(error){if(this.client){this.client.error=this.client._error(error);this.client.emit();}}}
  async _click(event){
    const button=event.target.closest('button');if(!button||button.disabled||!this.client)return;const c=this.client;
    if(button.dataset.play){const channel=button.dataset.play;await this._run(()=>channel==='queue'?c.startQueue(this.selected.queue,this._config.queue_settings):c.play(this.selected[channel],channel,this._config[`${channel}_settings`]));}
    else if(button.dataset.stop)await this._run(()=>c.stop(button.dataset.stop));
    else if(button.dataset.favorite)await this._run(()=>c.play(button.dataset.favorite,'effect',this._config.effect_settings));
    else switch(button.dataset.action){case 'power':await this._run(()=>c.setting('enabled',c.status?.enabled===false));break;case 'stop-all':await this._run(()=>c.stop());break;case 'next':await this._run(()=>c.next());break;case 'audio':await this._run(()=>c.enableAudio());break;case 'retry':await c.refresh();break;case 'dismiss':c.error='';c.emit();break;}
  }
  async _change(event){const target=event.target;if(target.dataset.channel){this.selected[target.dataset.channel]=target.value;this._paint();}else if(target.id==='motion')await this._run(()=>this.client.setting('automatic_enabled',target.checked));}
}

class BooCueCardEditor extends HTMLElement {
  constructor(){super();this.attachShadow({mode:'open'});this._boundForms=new WeakSet();}
  setConfig(config){const key=JSON.stringify(config);if(key===this._configKey)return;this._configKey=key;this._config=structuredClone(config);this._render();}
  set hass(value){const changed=this._hass?.connection!==value.connection;this._hass=value;if(changed||!this._catalogRequested){this._catalogRequested=true;void value.callWS({type:'boocue/dashboard'}).then(data=>{this._data=data;this._render();}).catch(()=>{});}if(this._language!==cardLanguage(value)){this._language=cardLanguage(value);this._render();}else for(const form of this.shadowRoot.querySelectorAll('ha-form'))form.hass=value;}
  _render(){
    if(!this._config||!this._hass)return;const t=CARD_TEXT[cardLanguage(this._hass)];
    if(this._domLanguage!==cardLanguage(this._hass)){this._domLanguage=cardLanguage(this._hass);this.shadowRoot.innerHTML=`<style>:host{display:block}ha-form{display:block}details{margin-top:16px}summary{cursor:pointer;font-weight:600;padding:10px 0}p{color:var(--secondary-text-color);font-size:13px;line-height:1.5}.channel{margin:12px 0 22px}h3{font-size:14px}</style><ha-form id="general"></ha-form><details><summary>${t.advanced}</summary><p>${t.overrideHelp}</p>${['mood','effect','queue'].map(channel=>`<section class="channel"><h3>${t[channel]}</h3><ha-form data-channel="${channel}"></ha-form></section>`).join('')}</details>`;}
    const labels={inherit_lights:cardLanguage(this._hass)==='nl'?'Opgeslagen lampen gebruiken':'Use saved lights',inherit_speakers:cardLanguage(this._hass)==='nl'?'Opgeslagen speakers gebruiken':'Use saved speakers',title:t.title,theme:t.theme,show_mood:t.showMood,show_effects:t.showEffects,show_queue:t.showQueue,show_motion:t.showMotion,show_favorites:t.showFavorites,effect:t.initialEffect,mood:t.initialMood,queue:t.initialQueue,output:t.output,lights:t.lights,speakers:t.players};
    const select=(name,options)=>({name,selector:{select:{mode:'dropdown',options}}});
    const general=this.shadowRoot.getElementById('general');general.hass=this._hass;general.data={...validateCardConfig(this._config),effect:this._config.effect||'',mood:this._config.mood||'',queue:this._config.queue||''};general.computeLabel=s=>labels[s.name]||s.name;this._bindForm(general);
    general.schema=[{name:'title',selector:{text:{}}},select('theme',[['auto',t.auto],['light',t.light],['dark',t.dark]].map(([value,label])=>({value,label}))),...['mood','effect','queue'].map(channel=>select(channel,[{value:'',label:t.defaults},...(channel==='queue'?this._data?.settings.queues||[]:(this._data?.effects||[]).filter(e=>(e.category==='moods')===(channel==='mood'))).map(e=>({value:e.id,label:e.title||e.name}))])),...['show_mood','show_effects','show_queue','show_motion','show_favorites'].map(name=>({name,selector:{boolean:{}}}))];
    for(const form of this.shadowRoot.querySelectorAll('ha-form[data-channel]')){form.hass=this._hass;const values=this._config[`${form.dataset.channel}_settings`]||{};form.data={output:'inherit',inherit_lights:!Object.hasOwn(values,'lights'),inherit_speakers:!Object.hasOwn(values,'speakers'),...values};form.computeLabel=s=>labels[s.name]||s.name;this._bindForm(form);form.schema=[select('output',[['inherit',t.inherit],['browser',t.device],['speakers',t.speakers],['none',t.silent]].map(([value,label])=>({value,label}))),{name:'inherit_lights',selector:{boolean:{}}},{name:'lights',disabled:form.data.inherit_lights,selector:{entity:{multiple:true,filter:{domain:'light'}}}},{name:'inherit_speakers',selector:{boolean:{}}},{name:'speakers',disabled:form.data.inherit_speakers,selector:{entity:{multiple:true,filter:{domain:'media_player'}}}}];}
  }
  _bindForm(form){if(this._boundForms.has(form))return;this._boundForms.add(form);form.addEventListener('value-changed',event=>this._changed(event,form));}
  _changed(event,source){
    event.stopPropagation();const form=source||event.composedPath().find(el=>el.localName==='ha-form');if(!form||!event.detail?.value||typeof event.detail.value!=='object')return;
    const config=structuredClone(this._config),values=structuredClone(event.detail.value);
    if(form.dataset.channel){form.data=structuredClone(values);for(const field of form.schema)if(['lights','speakers'].includes(field.name))field.disabled=values[`inherit_${field.name}`];form.schema=[...form.schema];if(values.output==='inherit')delete values.output;for(const name of ['lights','speakers']){if(values[`inherit_${name}`])delete values[name];else values[name]=values[name]||[];delete values[`inherit_${name}`];}const key=`${form.dataset.channel}_settings`;if(Object.keys(values).length)config[key]=values;else delete config[key];}
    else{Object.assign(config,values);for(const key of ['mood','effect','queue'])if(!config[key])delete config[key];}
    this._config=config;this._configKey=JSON.stringify(config);this.dispatchEvent(new CustomEvent('config-changed',{bubbles:true,composed:true,detail:{config}}));
  }
}
if(!customElements.get('boocue-card'))customElements.define('boocue-card',BooCueCard);
if(!customElements.get('boocue-card-editor'))customElements.define('boocue-card-editor',BooCueCardEditor);
window.customCards=window.customCards||[];
if(!window.customCards.some(card=>card.type==='boocue-card'))window.customCards.push({type:'boocue-card',name:'BooCue',description:'Mood, effects and queues. A little sound, right on your dashboard.',preview:true,documentationURL:'https://github.com/dwainscheeren/boocue/blob/main/docs/DASHBOARD.md'});
