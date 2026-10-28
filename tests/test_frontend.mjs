import {test} from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';
const registry=new Map();
const defaults={lights:[],output:'browser',speakers:[],volume:.6,brightness:.8,speed:1,offset_ms:0,routing:'all',repeat:false,restore:true,interval_ms:250,audio_mode:'auto',duck_mood:.35};
const context=vm.createContext({HTMLElement:class{attachShadow(){this.shadowRoot={};}},localStorage:{getItem:()=>null},
  URL,customElements:{get:n=>registry.get(n),define:(n,c)=>registry.set(n,c)},Map,Set,structuredClone,Date,Math,performance,Promise});
vm.runInContext(fs.readFileSync(new URL('../custom_components/boocue/frontend/boocue-panel.js',import.meta.url),'utf8').replace(/^import .*?;\n/,'').replaceAll('import.meta.url',JSON.stringify('http://ha.test/boocue-panel.js?build=test')),context);
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
test('scare spots use HA routing without claiming browser audio or altering mood targets',async()=>{
 const {p,calls}=fixture();const mood=structuredClone(p._settings.mood);await p._spotsView.command('play','clown');
 assert.deepEqual(JSON.parse(JSON.stringify(calls[0])),{type:'boocue/spot',action:'play',spot_id:'clown'});
 assert.equal(calls.some(c=>c.type==='boocue/browser_ready'),false);assert.deepEqual(p._settings.mood,mood);assert.equal(p._sources.size,0);
});
test('a late scare-spot start is cancelled by run id after remote Stop all',async()=>{
 const {p,calls}=fixture(),d=deferred(),entered=deferred();
 p._stopSequence=1;p._settings.enabled=true;
 p._hass.callWS=async msg=>{calls.push(msg);if(msg.type==='boocue/spot'&&msg.action==='play'){entered.resolve();return d.promise;}};
 const pending=p._spotsView.command('play','clown');await entered.promise;p._applyControlState({stop_sequence:2,enabled:true});
 d.resolve({playing:true,run_id:'stale',spot_id:'clown'});await pending;
 assert.equal(calls.at(-1).action,'stop');assert.equal(calls.at(-1).spot_id,'clown');assert.equal(calls.at(-1).run_id,'stale');
});
test('pending scare-spot presses are deduplicated per spot while different spots remain independent',async()=>{
 const {p,calls}=fixture(),d=deferred();p._hass.callWS=async msg=>{calls.push(msg);return d.promise;};
 const a=p._spotsView.command('play','clown');const duplicate=p._spotsView.command('play','clown');const b=p._spotsView.command('play','witch');
 await duplicate;assert.equal(calls.length,2);d.resolve({playing:true,run_id:'test'});await Promise.all([a,b]);
});
test('stopping a pending spot loop cancels only the stale returned loop',async()=>{
 const {p,calls}=fixture(),d=deferred(),entered=deferred();
 p._hass.callWS=async msg=>{calls.push(msg);if(msg.action==='show_start'){entered.resolve();return d.promise;}};
 const pending=p._spotsView.command('show_start');await entered.promise;await p._spotsView.command('show_stop');
 d.resolve({playing:true,run_id:'old-loop'});await pending;
 assert.equal(calls.at(-1).action,'show_stop');assert.equal(calls.at(-1).run_id,'old-loop');
});
test('an explicitly empty loop selection cannot silently start all spots',async()=>{
 const {p}=fixture();const messages=[];p._message=m=>messages.push(m);p._spotsView.showDraft={spot_ids:[],mode:'random',repeat:true,gap_min:4,gap_max:15};p._spotsView.useAll=false;
 assert.equal(await p._spotsView.saveShow(),false);assert.equal(messages.length,1);assert.equal(p._settings.spot_show,undefined);
});
test('a hass value assigned before element upgrade reaches the reactive setter',()=>{
 const values=new Map(),hass={locale:{language:'en'}};
 const isolated=vm.createContext({HTMLElement:class{constructor(){Object.defineProperty(this,'hass',{value:hass,writable:true,configurable:true});}attachShadow(){this.shadowRoot={};}},localStorage:{getItem:()=>null},URL,customElements:{get:n=>values.get(n),define:(n,c)=>values.set(n,c)},Map,Set,structuredClone,Date,Math,performance,Promise,Object});
 vm.runInContext(fs.readFileSync(new URL('../custom_components/boocue/frontend/boocue-panel.js',import.meta.url),'utf8').replace(/^import .*?;\n/,'').replaceAll('import.meta.url',JSON.stringify('http://ha.test/boocue-panel.js?build=test')),isolated);
 const panel=new (values.get('boocue-panel'))();assert.equal(panel._hass,hass);assert.equal(Object.hasOwn(panel,'hass'),false);assert.equal(panel._language,'en');
});
for(const stop of ['global','stop_all','show_stop','master_off'])test(`a delayed loop-settings save cannot start after ${stop}`,async()=>{
 const {p,calls}=fixture(),save=deferred(),entered=deferred();p._settings.enabled=true;p._stopSequence=3;
 p._spotsView.saveShow=async()=>{entered.resolve();return save.promise;};
 const pending=p._spotsView.click({dataset:{spAction:'show_start'}});await entered.promise;
 if(stop==='global')p._applyControlState({enabled:true,stop_sequence:4});
 else if(stop==='master_off')p._applyControlState({enabled:false});
 else await p._spotsView.command(stop);
 save.resolve(true);await pending;assert.equal(calls.some(c=>c.action==='show_start'),false);
});
test('changing loop scope preserves the checkbox focus and explicit selection',async()=>{
 const {p}=fixture();p._settings.scare_spots=[{id:'clown',enabled:true}];p._spotsView.initShow();let focus;
 p._spotsView.render=options=>focus=options.focus;
 await p._spotsView.change({dataset:{spAll:''},checked:false,hasAttribute:name=>name==='data-sp-all'});
 assert.equal(focus,'[data-sp-all]');assert.equal(p._spotsView.useAll,false);assert.equal(p._spotsView.showDraft.spot_ids[0],'clown');
});
test('explicit loop selections discard disabled spots without falling back to every spot',async()=>{
 const {p}=fixture();p._settings.scare_spots=[{id:'clown',enabled:false},{id:'witch',enabled:true}];p._spotsView.showDraft={spot_ids:['clown','witch'],mode:'random',repeat:true,gap_min:4,gap_max:15};p._spotsView.useAll=false;
 assert.equal(await p._spotsView.saveShow(),true);assert.equal(p._settings.spot_show.spot_ids.length,1);assert.equal(p._settings.spot_show.spot_ids[0],'witch');
});
test('stopping one pending spot does not cancel a different spot',async()=>{
 const {p,calls}=fixture(),d=deferred();p._hass.callWS=async msg=>{calls.push(msg);if(msg.action==='play')return d.promise;};
 const a=p._spotsView.command('play','clown'),b=p._spotsView.command('play','witch');await p._spotsView.command('stop','clown');
 d.resolve({playing:true,run_id:'run'});await Promise.all([a,b]);
 assert.equal(calls.filter(c=>c.action==='stop'&&c.run_id==='run'&&c.spot_id==='clown').length,1);
 assert.equal(calls.filter(c=>c.action==='stop'&&c.spot_id==='witch').length,0);
});

for(const kind of ['spot','queue','rule'])test(`cancelling a ${kind} editor discards only its draft and returns to its trigger`,()=>{
 const {p,calls}=fixture(),rendered=[];
 p._editor={kind,returnFocus:'[data-original-trigger]'};
 p._spotsView.draft={id:'spot-draft'};p._queueDraft={id:'queue-draft'};p._ruleDraft={id:'rule-draft'};
 p._spotsView.render=options=>rendered.push(options);p._renderQueues=options=>rendered.push(options);p._renderAutomatic=options=>rendered.push(options);
 p._cancelEditor();
 assert.equal(kind==='spot'?p._spotsView.draft:kind==='queue'?p._queueDraft:p._ruleDraft,null);
 assert.equal(kind==='spot'?p._queueDraft.id:p._spotsView.draft.id,kind==='spot'?'queue-draft':'spot-draft');
 assert.equal(rendered.length,1);assert.equal(rendered[0].focus,'[data-original-trigger]');
 assert.equal(calls.length,0);
});

test('a failed editor save keeps the draft, blocks dismissal while pending and unlocks for retry',async()=>{
 const {p,calls}=fixture(),busy=[],errors=[];let reject;
 const request=new Promise((resolve,no)=>{reject=no;});
 p._savedSettings=structuredClone(p._settings);p._settings.queues=[{id:'edited',name:'Changed'}];
 p._queueDraft={id:'edited',name:'Changed'};p._editor={kind:'queue'};
 p.shadowRoot={querySelector:()=>({open:true})};p._setEditorBusy=value=>busy.push(value);p._message=m=>errors.push(m);
 p._hass.callWS=async msg=>{calls.push(msg);return request;};
 const save=registry.get('boocue-panel').prototype._save.call(p);
 p._cancelEditor();assert.equal(p._queueDraft.name,'Changed');assert.equal(p._editorSaveCount,1);
 await Promise.resolve();reject(Error('Connection lost'));assert.equal(await save,false);
 assert.equal(p._editorSaveCount,0);assert.equal(p._queueDraft.name,'Changed');
 assert.equal(p._settings.queues.length,0);assert.deepEqual(busy,[true,false]);assert.deepEqual(errors,['Connection lost']);
 assert.deepEqual(Object.keys(calls[0].settings),['queues']);
});

test('picker search matches combined words, entity ids and accents without changing the source',()=>{
 const rows=[{entity_id:'light.garage_spot_2',name:'Café spot',area:'Garage'},{entity_id:'light.hall',name:'Hall',area:'Entry'}];
 const original=JSON.stringify(rows),selected=['light.hall'];
 const result=rows.filter(item=>context.choiceMatches(`${item.name} ${item.entity_id} ${item.area}`,'cafe garage'));
 assert.equal(result.length,1);assert.equal(result[0].entity_id,'light.garage_spot_2');
 assert.equal(context.choiceMatches('Lamp light.garage_spot_2','garage_spot'),true);
 assert.equal(context.choiceMatches('Lamp','   '),true);assert.equal(context.choiceMatches('Lamp','ghost'),false);
 assert.equal(JSON.stringify(rows),original);assert.deepEqual(selected,['light.hall']);
});

test('area grouping uses stable HA ids, naturally sorts names and keeps unassigned devices last',()=>{
 const rows=[{entity_id:'light.z',name:'Spot 10',area:'Garden',area_id:'garden'},{entity_id:'light.a',name:'Spot 2',area:'Garden',area_id:'garden'},{entity_id:'light.b',name:'Entry',area:'Entry',area_id:'entry'},{entity_id:'light.c',name:'Unknown',area:'Overige lampen',area_id:''}];
 const original=JSON.stringify(rows),groups=context.groupChoices(rows,'en');
 assert.equal(groups.length,3);assert.equal(groups[0][0],'entry');assert.equal(groups[1][0],'garden');
 assert.equal(groups[1][1][0].name,'Spot 2');assert.equal(groups[2][0],'__no_area__');
 assert.equal(JSON.stringify(rows),original);
 assert.equal(context.choiceArea({area:'Hall'}),'Hall');
});

test('picker markup escapes device names, area labels and search text while retaining missing selections',()=>{
 const {p}=fixture();p._choiceFilters.set('spot:lights',{query:'"<search>',area:'a'});
 const html=p._choicePicker('spot:lights',[{entity_id:'light.one',name:'<Lamp>',area:'"Garden"',area_id:'a',state:'on'}],['light.missing'],{kind:'lights',binding:id=>`data-rule-light="${id}"`});
 assert.equal(html.includes('<Lamp>'),false);assert.equal(html.includes('&lt;Lamp&gt;'),true);
 assert.equal(html.includes('&quot;&lt;search&gt;'),true);assert.equal(html.includes('&quot;Garden&quot;'),true);
 assert.equal(html.includes('light.missing'),true);assert.equal(html.includes('checked'),true);
});
