import {test} from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';
const registry=new Map();
class Element {attachShadow(){this.shadowRoot={addEventListener(){}};}dispatchEvent(event){this.lastEvent=event;}}
class Audio {
 constructor(){this.currentTime=0;this.state='running';this.destination={};this.created=[];}
 async resume(){this.state='running';}
 async close(){this.state='closed';}
 createGain(){return {gain:{value:0,setTargetAtTime(value){this.value=value;}},connect(){},disconnect(){}};}
 createBufferSource(){const source={playbackRate:{value:1},connect(){},disconnect(){},start(){this.started=true;},stop(){this.stopped=true;}};this.created.push(source);return source;}
}
const context=vm.createContext({HTMLElement:Element,window:{},customElements:{get:n=>registry.get(n),define:(n,c)=>registry.set(n,c)},structuredClone,Map,Set,WeakMap,Date,Math,Promise,queueMicrotask,AudioContext:Audio,CustomEvent:class {constructor(type,options){this.type=type;Object.assign(this,options);}}});
vm.runInContext(fs.readFileSync(new URL('../custom_components/boocue/frontend/boocue-card.js',import.meta.url),'utf8'),context);
const {BooCueDashboardClient:Client,dashboardClient,validateCardConfig,cardEsc}=vm.runInContext('({BooCueDashboardClient,dashboardClient,validateCardConfig,cardEsc})',context);
const defer=()=>{let resolve,reject;const promise=new Promise((a,b)=>{resolve=a;reject=b;});return {promise,resolve,reject};};
const flush=async()=>{for(let i=0;i<20;i++)await Promise.resolve();};
function fixture(){
 const calls=[],events={},state={playing:false,enabled:true,automatic_enabled:false,settings_revision:0,library_revision:1,stop_sequence:0,channels:{effect:{playing:false},mood:{playing:false}},queue:{playing:false}};
 const runtime={lights:['light.demo'],speakers:[],output:'none',volume:.6,speed:1,repeat:false,duck_mood:.35};
 const data={settings:{...runtime,enabled:true,automatic_enabled:false,mood:{...runtime,repeat:true,volume:.4},effect_routes:{},favorites:[],queues:[{id:'q',name:'Queue',effects:['fx'],settings:{}}]},status:structuredClone(state),effects:[{id:'fx',title:'Effect',category:'effects',duration:1,cue_blocks:[]},{id:'mood',title:'Mood',category:'moods',duration:1,cue_blocks:[]}],motion_rule_count:0};
 let serial=0;
 const connection={connected:true,subscribeCount:0,unsubscribeCount:0,async subscribeEvents(fn){this.subscribeCount++;this.callback=fn;return ()=>{this.unsubscribeCount++;};},addEventListener:(name,fn)=>{events[name]=fn;},removeEventListener:name=>{delete events[name];}};
 const hass={connection,user:{is_admin:true},locale:{language:'nl'},themes:{darkMode:false},callWS:async msg=>{
  calls.push(msg);
  if(msg.type==='boocue/dashboard')return {...structuredClone(data),server_time:Date.now()/1000};
  if(msg.type==='boocue/browser_ready')return {station_id:'station'};
  if(msg.type==='boocue/settings')return {...structuredClone(data.settings),...msg.settings};
  if(msg.type==='boocue/queue')return {playing:msg.action!=='stop',run_id:'queue-run',queue_id:'q'};
  if(msg.type==='boocue/play')return {playing:true,run_id:'run-'+(++serial),effect_id:msg.effect_id,output:c.resolved(msg.effect_id,msg.channel,msg.settings).output,browser_id:msg.browser_id,start_at:Date.now()/1000+.1,duration:1,speed:1,repeat:msg.channel==='mood',volume:msg.channel==='mood'?.4:.8,duck_mood:.25};
 }};
 const c=new Client(hass);c.data=structuredClone(data);c.status=structuredClone(state);c.listeners.add(()=>{});c._buffer=async()=>({duration:1});
 return {c,hass,connection,calls,events,data,state};
}
test('card configuration validates values and escapes untrusted text',()=>{
 assert.equal(validateCardConfig({}).theme,'auto');
 assert.equal(validateCardConfig({mood_settings:{lights:[]}}).mood_settings.lights.length,0);
 for(const config of [{theme:'x'},{show_queue:'no'},{effect:''},{effect_settings:{enabled:true}},{mood_settings:{volume:NaN}},{queue_settings:{lights:['switch.x']}}])assert.throws(()=>validateCardConfig(config));
 assert.equal(cardEsc('<img onerror="x">'),'&lt;img onerror=&quot;x&quot;&gt;');
});
test('card picker, visual editor and sections sizing are registered',()=>{
 const card=new (registry.get('boocue-card'))();card.setConfig({type:'custom:boocue-card',show_queue:false});
 assert.equal(card.getGridOptions().columns,12);assert.equal(card.getGridOptions().rows,'auto');
 assert.ok(registry.has('boocue-card-editor'));assert.equal(context.window.customCards.filter(c=>c.type==='boocue-card').length,1);
});
test('multiple cards share one subscription and release browser audio only after the last detaches',async()=>{
 const {hass,connection,calls}=fixture(),a=dashboardClient(hass),b=dashboardClient({...hass});assert.equal(a,b);
 const removeA=a.attach(()=>{}),removeB=b.attach(()=>{});await flush();
 assert.equal(connection.subscribeCount,1);a.browserId='station';a.context=new Audio();const audio=a.context;
 removeA();await flush();assert.equal(calls.some(x=>x.type==='boocue/browser_release'),false);
 removeB();await flush();await a.teardown;
 assert.equal(connection.unsubscribeCount,1);assert.equal(audio.state,'closed');
 assert.equal(calls.filter(x=>x.type==='boocue/browser_release').length,1);assert.equal(calls.some(x=>x.type==='boocue/stop'),false);
});
test('stop during decoding cancels a manual start before the server is called',async()=>{
 const {c,calls}=fixture(),d=defer();c.data.settings.output='browser';c._buffer=()=>d.promise;
 const pending=c.play('fx','effect');await flush();await c.stop('effect');d.resolve({duration:1});await pending;
 assert.equal(calls.some(x=>x.type==='boocue/play'),false);assert.equal(c.sources.size,0);
});
test('cancelled in-flight card start stops only its returned run id',async()=>{
 const {c,hass,calls}=fixture(),d=defer(),entered=defer(),original=hass.callWS;
 hass.callWS=async msg=>{if(msg.type==='boocue/play'){calls.push(msg);entered.resolve();return d.promise;}return original(msg);};
 const pending=c.play('fx','effect');await entered.promise;await c.stop('effect');
 d.resolve({run_id:'old',playing:true});await pending;
 assert.equal(calls.at(-1).run_id,'old');assert.equal(calls.at(-1).channel,'effect');
});
test('master Off blocks playback and cancels pending browser decoding',async()=>{
 const {c,calls}=fixture(),d=defer();c.data.settings.output='browser';c._buffer=()=>d.promise;
 const pending=c.play('fx','effect');await flush();c._state({...c.status,enabled:false});d.resolve({duration:1});await pending;
 await assert.rejects(c.play('fx','effect'));await assert.rejects(c.startQueue('q'));
 assert.equal(calls.some(x=>x.type==='boocue/play'),false);assert.equal(c.pending.size,0);
});
test('queue routes claim audio before starting; explicit no-sound override wins',async()=>{
 const {c,calls}=fixture();c.data.settings.effect_routes.fx={output:'browser'};
 await c.startQueue('q');assert.equal(calls[0].type,'boocue/browser_ready');assert.equal(calls.at(-1).browser_id,'station');
 c.browserId=null;calls.length=0;await c.startQueue('q',{output:'none'});
 assert.equal(calls.length,1);assert.equal(calls[0].settings.output,'none');
});
test('card browser channels mix once, duck mood and stop independently',async()=>{
 const {c}=fixture();c.context=new Audio();c.browserId='station';c.data.settings.output='browser';c.data.settings.mood.output='browser';
 await c.play('mood','mood');await flush();await c.play('fx','effect');await flush();
 assert.equal(c.sources.size,2);assert.equal(c.sources.get('mood').gain.gain.value,.1);
 const mood=c.sources.get('mood').source;await c.stop('effect');assert.equal(c.sources.has('effect'),false);assert.equal(c.sources.has('mood'),true);assert.equal(mood.stopped,undefined);assert.equal(c.sources.get('mood').gain.gain.value,.4);
});
test('local Stop all blocks old heartbeat audio while server cleanup is pending',async()=>{
 const {c,hass}=fixture();c.context=new Audio();c.browserId='station';c.data.settings.output='browser';await c.play('fx','effect');await flush();
 const old=structuredClone(c.status),source=c.sources.get('effect').source,d=defer(),original=hass.callWS;
 hass.callWS=msg=>msg.type==='boocue/stop'?d.promise:original(msg);
 const stop=c.stop();c._state(old);await flush();assert.equal(source.stopped,true);assert.equal(c.sources.size,0);d.resolve();await stop;
});
test('remote Stop all cancels pending audio without turning master off',async()=>{
 const {c,calls}=fixture(),d=defer();c.data.settings.output='browser';c._buffer=()=>d.promise;
 const pending=c.play('fx','effect');await flush();c._state({...c.status,stop_sequence:1,channels:{effect:{playing:false},mood:{playing:false}}});d.resolve({duration:1});await pending;
 assert.equal(c.status.enabled,true);assert.equal(c.sources.size,0);assert.equal(calls.some(x=>x.type==='boocue/play'),false);
});
test('late browser failure from an old run cannot stop its replacement',async()=>{
 const {c,calls}=fixture(),d=defer();c.context=new Audio();c.browserId='station';c._buffer=()=>d.promise;
 const state={playing:true,run_id:'old',effect_id:'fx',browser_id:'station'};c.status.channels.effect=state;
 const receiving=c._receive('effect',state);c.status.channels.effect={...state,run_id:'new'};d.reject(Error('Late failure'));await receiving;
 assert.equal(calls.some(x=>x.type==='boocue/stop'),false);assert.equal(c.error,'');
});
test('status progress does not reload the catalog; settings changes do',async()=>{
 const {c,calls}=fixture();const old=structuredClone(c.status);c._state({...old,channels:{...old.channels,effect:{playing:true,position:1}}});await flush();assert.equal(calls.length,0);
 c._state({...old,settings_revision:1});await flush();assert.equal(calls.filter(x=>x.type==='boocue/dashboard').length,1);
});
test('disconnect cancels pending starts and reconnect refreshes metadata',async()=>{
 const {hass,events,calls}=fixture(),c=dashboardClient(hass);const remove=c.attach(()=>{});await flush();
 events.disconnected();assert.equal(c.online,false);await assert.rejects(c.play('fx','effect'));
 const count=calls.length;events.ready();await flush();assert.equal(c.online,true);assert.ok(calls.slice(count).some(x=>x.type==='boocue/dashboard'));remove();await flush();
});
test('a browser claim completing after the last card leaves is released',async()=>{
 const {hass,calls}=fixture(),claim=defer(),entered=defer(),original=hass.callWS;
 hass.callWS=async msg=>{if(msg.type==='boocue/browser_ready'){calls.push(msg);entered.resolve();return claim.promise;}return original(msg);};
 const c=dashboardClient(hass),remove=c.attach(()=>{});await flush();const ready=c.enableAudio();await entered.promise;
 remove();await flush();claim.resolve({station_id:'late'});await assert.rejects(ready);await c.teardown;
 assert.equal(calls.filter(x=>x.type==='boocue/browser_release'&&x.station_id==='late').length,1);
});
test('visual editor preserves explicit empty targets and unrelated HA layout options',()=>{
 const editor=new (registry.get('boocue-card-editor'))();editor._config={type:'custom:boocue-card',grid_options:{columns:6},effect_settings:{output:'speakers'}};
 const form={localName:'ha-form',dataset:{channel:'mood'},schema:[]};
 editor._changed({stopPropagation(){},composedPath:()=>[form],detail:{value:{output:'browser',inherit_lights:false,lights:[],inherit_speakers:true,speakers:[]}}});
 assert.equal(editor.lastEvent.detail.config.mood_settings.output,'browser');assert.equal(editor.lastEvent.detail.config.mood_settings.lights.length,0);
 assert.equal(editor.lastEvent.detail.config.mood_settings.speakers,undefined);assert.equal(editor.lastEvent.detail.config.grid_options.columns,6);
 assert.equal(editor.lastEvent.detail.config.effect_settings.output,'speakers');
});
test('direct form changes reach the card preview without rebuilding a focused editor',()=>{
 const editor=new (registry.get('boocue-card-editor'))();let renders=0;editor._render=()=>{renders++;};
 editor.setConfig({type:'custom:boocue-card',title:'Original'});
 const form={localName:'ha-form',dataset:{}};
 editor._changed({stopPropagation(){},composedPath:()=>[],detail:{value:{title:'Changed'}}},form);
 assert.equal(editor.lastEvent.detail.config.title,'Changed');
 editor.setConfig(editor.lastEvent.detail.config);assert.equal(renders,1);
});
