import {test} from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';
const registry=new Map();
const defaults={lights:[],output:'browser',speakers:[],volume:.6,brightness:.8,speed:1,offset_ms:0,routing:'all',repeat:false,restore:true,interval_ms:250,audio_mode:'auto',duck_mood:.35};
const context=vm.createContext({HTMLElement:class{attachShadow(){this.shadowRoot={};}},localStorage:{getItem:()=>null},
  URL,customElements:{get:n=>registry.get(n),define:(n,c)=>registry.set(n,c)},Map,Set,structuredClone,Date,Math,performance,Promise});
vm.runInContext(fs.readFileSync(new URL('../custom_components/boocue/frontend/boocue-panel.js',import.meta.url),'utf8').replaceAll('import.meta.url',JSON.stringify('http://ha.test/boocue-panel.js?build=test')),context);
function fixture(){
 const p=new (registry.get('boocue-panel'))();
 p._settings={...structuredClone(defaults),favorites:[],effect_routes:{},motion_rules:[],queues:[],automatic_enabled:false,mood:{...structuredClone(defaults),repeat:true,volume:.3}};
 p._effects=[{id:'fx',category:'effects',duration:1},{id:'mood',category:'moods',duration:1}];
 p._status={channels:{effect:{playing:false},mood:{playing:false}}};
 p._renderStatus=()=>{};p._renderEffects=()=>{};p._save=async()=>true;p._message=message=>{throw Error(message)};
 const calls=[];
 p._hass={callWS:async msg=>{calls.push(msg);if(msg.type==='boocue/browser_ready')return {station_id:'test-station'};return {playing:true,run_id:msg.channel+'-run',start_at:Date.now()/1000,server_time:Date.now()/1000};}};
 p._context={currentTime:0,state:'running',createBufferSource:()=>({playbackRate:{value:1},connect(){},disconnect(){},start(){},stop(){this.stopped=true;}}),createGain:()=>({gain:{value:0},connect(){},disconnect(){}})};
 p._audioContext=async()=>p._context;p._buffer=async()=>({duration:1});
 return {p,calls};
}
const deferred=()=>{let resolve;const promise=new Promise(r=>resolve=r);return {promise,resolve};};
test('mood, effect and preview use separate audio sources; preview does not stop shows',async()=>{
 const {p,calls}=fixture();await p._start('mood');await p._start('fx');await p._start('fx',true);
 assert.equal(p._sources.size,3);
 assert.equal(calls.filter(c=>c.type==='boocue/play').length,2);
 assert.equal(calls.filter(c=>c.type==='boocue/stop').length,0);
 await p._stopChannel('effect');assert.equal(p._sources.has('mood'),true);assert.equal(p._sources.has('effect'),false);
});
test('stop while audio decodes prevents any server start',async()=>{
 const {p,calls}=fixture(),d=deferred();p._buffer=()=>d.promise;
 const pending=p._start('fx');await Promise.resolve();await p._stopChannel('effect');d.resolve({});await pending;
 assert.equal(calls.filter(c=>c.type==='boocue/play').length,0);assert.equal(p._sources.size,0);
});
test('cancelled in-flight server start is stopped using only its returned run id',async()=>{
 const {p,calls}=fixture(),d=deferred(),entered=deferred();p._settings.output='none';p._settings.lights=['light.demo'];
 p._hass.callWS=async msg=>{calls.push(msg);if(msg.type==='boocue/play'){entered.resolve();return d.promise;}};
 const pending=p._start('fx');await entered.promise;await p._stopChannel('effect');
 d.resolve({run_id:'old-run',playing:true,server_time:Date.now()/1000,start_at:Date.now()/1000});await pending;
 assert.equal(calls.at(-1).run_id,'old-run');assert.equal(calls.at(-1).channel,'effect');assert.equal(p._sources.size,0);
});
test('per-effect routes override audio only and preserve mood and light choices',()=>{
 const {p}=fixture();p._settings.lights=['light.demo'];p._settings.effect_routes.fx={output:'speakers',speakers:['media_player.one','media_player.two'],volume:.8};
 const effect=p._resolved('fx','effect'),mood=p._resolved('mood','mood');
 assert.equal(effect.speakers.length,2);assert.equal(effect.volume,.8);assert.equal(effect.lights[0],'light.demo');
 assert.equal(mood.volume,.3);assert.equal(mood.repeat,true);assert.equal(mood.output,'browser');
});
test('automatic browser runs mix and duck mood, then restore its chosen volume',async()=>{
 const {p}=fixture();p._browserId='test-station';
 p._status.channels.mood={playing:true,run_id:'mood',effect_id:'mood',output:'browser',repeat:true,volume:.4,speed:1,start_at:Date.now()/1000,duration:1};
 await p._receiveBrowserRun('mood',p._status.channels.mood);
 p._status.channels.effect={playing:true,run_id:'fx',effect_id:'fx',output:'browser',repeat:false,volume:.8,duck_mood:.25,speed:1,start_at:Date.now()/1000,duration:1};
 await p._receiveBrowserRun('effect',p._status.channels.effect);p._updateDuck();
 assert.equal(p._sources.size,2);assert.equal(p._sources.get('mood').gain.gain.value,.1);
 p._stopAudio('effect');assert.equal(p._sources.get('mood').gain.gain.value,.4);
});
test('a delayed browser decode cannot play after Stop or a newer run',async()=>{
 const {p}=fixture(),d=deferred();p._buffer=()=>d.promise;
 const state={playing:true,run_id:'old',effect_id:'fx',speed:1,start_at:Date.now()/1000,duration:1};
 p._status.channels.effect=state;
 const pending=p._receiveBrowserRun('effect',state);await Promise.resolve();await p._stopChannel('effect');
 d.resolve({duration:1});await pending;assert.equal(p._sources.size,0);
});
test('cancelled queue start stops only the returned queue generation',async()=>{
 const {p,calls}=fixture(),d=deferred(),entered=deferred();
 p._settings.output='none';p._settings.queues=[{id:'test',effects:['fx'],settings:{}}];
 p._hass.callWS=async msg=>{calls.push(msg);if(msg.type==='boocue/queue'&&msg.action==='start'){entered.resolve();return d.promise;}};
 const pending=p._startQueue('test');await entered.promise;p._queueGeneration++;
 d.resolve({playing:true,run_id:'old-queue'});await pending;
 assert.equal(calls.at(-1).action,'stop');assert.equal(calls.at(-1).run_id,'old-queue');
 assert.equal(calls.some(c=>c.type==='boocue/browser_ready'),false);
});
test('browser queue claims audio station before requesting server start',async()=>{
 const {p,calls}=fixture();p._settings.queues=[{id:'test',effects:['fx'],settings:{}}];
 await p._startQueue('test');
 assert.equal(calls[0].type,'boocue/browser_ready');assert.equal(calls[1].browser_id,'test-station');
});
test('saving a queue sends only edited settings and preserves newer server preferences',async()=>{
 const {p,calls}=fixture();p._savedSettings=structuredClone(p._settings);
 p._settings.queues=[{id:'test',name:'Test',effects:['fx']}];
 p._hass.callWS=async msg=>{calls.push(msg);return {...p._settings,volume:.17};};
 await registry.get('boocue-panel').prototype._save.call(p);
 assert.deepEqual(Object.keys(calls[0].settings),['queues']);assert.equal(p._settings.volume,.17);
});
test('cue blocks cover the full clip, including a final group beyond the old 18-cue truncation',()=>{
 const effect={cues:Array.from({length:35},(_,at)=>({at,hue:at*10}))};
 const blocks=context.cueBlocks(effect);assert.equal(blocks.length,18);
 assert.equal(blocks[0].at,0);assert.equal(blocks.at(-1).at,33);
 assert.equal(context.cueBlockIndex(effect,17),9);assert.equal(context.cueBlockIndex(effect,34),17);
});
test('the arrow waits for the first cue and holds its block across uneven cue gaps',()=>{
 const effect={cues:[{at:.5},{at:1},{at:12},{at:14}]};
 assert.equal(context.cueBlockIndex(effect,0),-1);assert.equal(context.cueBlockIndex(effect,.5),0);
 assert.equal(context.cueBlockIndex(effect,11.9),1);assert.equal(context.cueBlockIndex(effect,12),2);
 assert.equal(context.cueBlockIndex(effect,14),3);
});
test('playhead timing follows light delay, speed and repeat wrapping',()=>{
 const state={start_at:10,offset_ms:500,speed:2,duration:8,repeat:true};
 assert.equal(context.lightPosition(state,10),-1);
 assert.equal(context.lightPosition(state,12.5),4);
 assert.equal(context.lightPosition(state,15.5),2);
 assert.equal(context.lightPosition({...state,offset_ms:-500},10),1);
 assert.equal(context.lightPosition({...state,repeat:false},20),8);
});
test('descriptions follow HA language and retain custom text as a fallback',()=>{
 const {p}=fixture(),effect={description:'Custom',descriptions:{en:'Thunder',nl:'Donder'}};
 p._language='nl';assert.equal(p._description(effect),'Donder');p._language='en';assert.equal(p._description(effect),'Thunder');
 assert.equal(p._description({description:'Own sound'}),'Own sound');
});
test('idle playhead cleans once and stop/start transitions bypass the paint cadence',()=>{
 const {p}=fixture();p._loaded=true;let traversals=0;
 p.shadowRoot={querySelector:()=>null,querySelectorAll:()=>{traversals++;return [];}};
 p._renderLightFeedback();p._renderLightFeedback();p._renderLightFeedback();assert.equal(traversals,1);
 p._status.channels.effect={playing:true,effect_id:'fx',light_preview:[]};
 p._renderLightFeedback();assert.equal(traversals,2);
 p._renderLightFeedback();assert.equal(traversals,2);
 p._status.channels.effect.playing=false;p._renderLightFeedback();assert.equal(traversals,3);
 p._renderLightFeedback();assert.equal(traversals,3);
 p._status.channels.effect.playing=true;p._renderLightFeedback();assert.equal(traversals,4);
 p._status.channels.effect.playing=false;p._renderLightFeedback();assert.equal(traversals,5);
 p._renderLightFeedback();assert.equal(traversals,5);
});
test('master Off blocks effects, Listen, queues and test tone before any output request',async()=>{
 const {p,calls}=fixture(),messages=[];p._settings.enabled=false;p._message=m=>messages.push(m);
 await p._start('fx');await p._start('fx',true);await p._startQueue('test');await p._testSound();
 assert.equal(calls.length,0);assert.equal(p._sources.size,0);assert.equal(messages.length,4);
});
test('master Off cancels audio that is still decoding and ignores a late buffer',async()=>{
 const {p,calls}=fixture(),d=deferred();p._buffer=()=>d.promise;
 const pending=p._start('fx');await Promise.resolve();p._applyControlState({enabled:false,automatic_enabled:true});
 d.resolve({duration:1});await pending;
 assert.equal(calls.some(c=>c.type==='boocue/play'),false);assert.equal(p._sources.size,0);
 assert.equal(p._pending.size,0);assert.equal(p._settings.automatic_enabled,true);
});
test('remote Stop all cancels playing previews and pending Listen without disabling master',async()=>{
 const {p,calls}=fixture();p._settings.enabled=true;p._stopSequence=0;
 await p._start('fx',true);const source=p._sources.get('preview').source;
 p._applyControlState({stop_sequence:1,enabled:true,automatic_enabled:false});
 assert.equal(source.stopped,true);assert.equal(p._sources.size,0);assert.equal(p._settings.enabled,true);
 const d=deferred();p._buffer=()=>d.promise;
 const pending=p._start('fx',true);await Promise.resolve();
 p._applyControlState({stop_sequence:2,enabled:true,automatic_enabled:false});
 d.resolve({duration:1});await pending;
 assert.equal(p._sources.size,0);assert.equal(p._pending.size,0);
 assert.equal(calls.some(c=>c.type==='boocue/play'),false);
});
test('remote master and motion changes update the save baseline rather than being resent by unrelated edits',async()=>{
 const {p,calls}=fixture();p._settings.enabled=true;p._savedSettings=structuredClone(p._settings);
 p._applyControlState({enabled:false,automatic_enabled:true});p._settings.brightness=.7;
 p._hass.callWS=async msg=>{calls.push(msg);return structuredClone(p._settings);};
 await registry.get('boocue-panel').prototype._save.call(p);
 assert.deepEqual(Object.keys(calls[0].settings),['brightness']);
});
test('master toggle sends only its flag and ignores duplicate presses while pending',async()=>{
 const {p,calls}=fixture(),d=deferred();p._settings.enabled=true;
 p._hass.callWS=async msg=>{calls.push(msg);return d.promise;};
 const first=p._togglePower();await p._togglePower();assert.equal(calls.length,1);
 assert.deepEqual(Object.keys(calls[0].settings),['enabled']);assert.equal(calls[0].settings.enabled,false);
 d.resolve({enabled:false,automatic_enabled:false});await first;assert.equal(p._settings.enabled,false);
});
