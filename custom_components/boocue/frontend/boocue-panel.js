const ASSET_REVISION = new URL(import.meta.url).searchParams.get('build') || '1.0.0';
const TEXT = {
  nl: {
    subtitle: 'Een beetje geluid. Een huis vol kippenvel.', stage: 'Jouw podium', lights: 'Lampen',
    lightSearch: 'Zoek een lamp', noLights: 'Er zijn nog geen lampen. Voeg een lampintegratie toe in Home Assistant.',
    selected: 'geselecteerd', selectAll: 'Selecteer zichtbare lampen', clear: 'Wis selectie',
    output: 'Geluid afspelen op', browser: 'Dit apparaat', silent: 'Geen geluid', test: 'Test dit apparaat',
    adjust: 'Lampen en geluid', chooseEffect: 'Kies een effect', volumeZero: 'Het volume staat op nul. Verhoog het volume om de testtoon te horen.',
    volume: 'Volume', brightness: 'Lichtsterkte', routing: 'Lampverdeling', all: 'Samen',
    alternate: 'Om de beurt', random: 'Willekeurig', repeat: 'Herhaal effect', restore: 'Herstel lampstanden',
    advanced: 'Afstemming', speed: 'Snelheid', offset: 'Lichtvertraging', interval: 'Tijd tussen lichtcommando’s',
    next: 'Instellingen gelden voor het volgende effect.', offsetHelp: 'Positief: licht later. Negatief: licht eerder dan het geluid.',
    library: 'Kies je kippenvel', librarySub: 'Kies je lampen, druk op een effect en laat je huis meespelen.',
    everything: 'Alles', effects: 'Effecten', moods: 'Sfeer', favorites: 'Favorieten',
    search: 'Zoek een effect', import: 'Importeer pakket', importing: 'Pakket importeren…',
    empty: 'Geen effecten gevonden', emptyHelp: 'Pas je zoekopdracht aan of kies een andere categorie.',
    choose: 'Kies eerst een lamp om een effect te starten.', play: 'Speel', listen: 'Beluister',
    favorite: 'Favoriet', ready: 'Klaar voor een beetje onheil?', readySub: 'Je lampen staan nog zoals ze stonden.',
    stop: 'Stop', starting: 'Geluid voorbereiden…', playing: 'Speelt nu', preview: 'Geluidsvoorbeeld',
    close: 'Sluiten', dark: 'Donkere modus', light: 'Lichte modus', saved: 'Opgeslagen',
    testOk: 'Testtoon gestart op dit apparaat. Hoor je niets? Controleer de gekozen geluidsuitgang en het volume van je apparaat.',
    soundError: 'Het geluid kon niet starten. Probeer Test dit apparaat en controleer de geluidsuitgang van je apparaat.',
    disconnected: 'Home Assistant is niet verbonden. Wacht op verbinding en probeer opnieuw.',
    retry: 'Opnieuw proberen', unavailable: 'Niet beschikbaar', imported: 'effecten geïmporteerd',
    noFavorites: 'Nog geen favorieten. Gebruik het hartje bij een effect.',
    version: 'Eigen demo’s en jouw lokale effectpakketten', commands: 'lichtcommando’s overgeslagen',
    menu: 'Open Home Assistant-menu', refresh: 'Lampen verversen',
  },
  en: {
    subtitle: 'A little sound. A house full of goosebumps.', stage: 'Your stage', lights: 'Lights',
    lightSearch: 'Find a light', noLights: 'No lights yet. Add a light integration in Home Assistant.',
    selected: 'selected', selectAll: 'Select visible lights', clear: 'Clear selection',
    output: 'Play sound on', browser: 'This device', silent: 'No sound', test: 'Test this device',
    adjust: 'Lights & sound', chooseEffect: 'Choose effect', volumeZero: 'Volume is zero. Increase the volume to hear the test tone.',
    volume: 'Volume', brightness: 'Brightness', routing: 'Light routing', all: 'Together',
    alternate: 'Take turns', random: 'Random', repeat: 'Repeat effect', restore: 'Restore light states',
    advanced: 'Fine tuning', speed: 'Speed', offset: 'Light delay', interval: 'Time between light commands',
    next: 'Settings apply to the next effect.', offsetHelp: 'Positive: lights later. Negative: lights earlier than sound.',
    library: 'Pick your goosebumps', librarySub: 'Choose your lights, tap an effect and let your house join in.',
    everything: 'All', effects: 'Effects', moods: 'Atmospheres', favorites: 'Favorites',
    search: 'Find an effect', import: 'Import pack', importing: 'Importing pack…',
    empty: 'No effects found', emptyHelp: 'Try another search or category.',
    choose: 'Choose a light before starting an effect.', play: 'Play', listen: 'Listen',
    favorite: 'Favorite', ready: 'Ready for a little mischief?', readySub: 'Your lights are still as you left them.',
    stop: 'Stop', starting: 'Preparing sound…', playing: 'Now playing', preview: 'Sound preview',
    close: 'Dismiss', dark: 'Dark mode', light: 'Light mode', saved: 'Saved',
    testOk: 'Test tone started on this device. No sound? Check your device’s audio output and volume.',
    soundError: 'Sound could not start. Try Test this device and check your device’s audio output.',
    disconnected: 'Home Assistant is disconnected. Wait for a connection and try again.',
    retry: 'Try again', unavailable: 'Unavailable', imported: 'effects imported',
    noFavorites: 'No favorites yet. Tap the heart beside an effect.',
    version: 'Original demos and your local effect packs', commands: 'light commands skipped',
    menu: 'Open Home Assistant menu', refresh: 'Refresh lights',
  },
};

Object.assign(TEXT.nl, {
  effectMode:'Effecten', moodMode:'Doorlopende sfeer', autoMode:'Bij beweging', speakers:'HA-speakers',
  speakerHint:'Speakers ontvangen hetzelfde geluid. Gebruik een bestaande HA-speakergroep voor betere onderlinge synchronisatie.',
  noSpeakers:'Er zijn geen HA-mediaspelers. Voeg eerst je speakerintegratie toe.',
  speakerCount:'speakers', defaultRoute:'Geluid: standaard', ownRoute:'Eigen speakers', route:'Geluid voor dit effect',
  routeHelp:'Deze keuze geldt alleen voor dit effect en blijft bewaard.', inherit:'Gebruik standaardinstellingen',
  moodHelp:'Sfeer blijft herhalen totdat je hem stopt. Losse effecten spelen daarnaast op hun eigen speakers. Bij gedeelde lampen krijgt het effect voorrang en gaat de sfeer daarna verder.',
  effectsHelp:'Tik op een effect. Bewaar desgewenst per effect een eigen speakerkeuze.',
  stopEffect:'Stop effect', stopMood:'Stop sfeer', stopAll:'Stop alles', idleEffect:'Nog geen effect', idleMood:'Geen sfeer actief',
  continuous:'Blijft herhalen', active:'Actief', outputNone:'Alleen lampen', configure:'Instellen',
  autoHelp:'Kies een bewegingssensor en één of meer effecten. BooCue speelt bij nieuwe beweging één effect en slaat triggers over zolang een effect speelt. Voor tijdschema’s en extra voorwaarden gebruik je een HA-automatisering.',
  armed:'Bewegingsregels activeren', armedHelp:'Stop alles schakelt deze regels ook uit. Sfeer kan ondertussen blijven spelen.',
  noRules:'Maak je eerste bewegingsregel', noRulesHelp:'Bijvoorbeeld: beweging bij de voordeur → een willekeurig spookgeluid op de speakers buiten.',
  newRule:'Nieuwe regel', edit:'Bewerken', remove:'Verwijderen', cancel:'Annuleren', saveRule:'Regel bewaren',
  ruleName:'Naam', sensor:'Bewegingssensor', pickSensor:'Kies een sensor', pool:'Welke effecten mogen afgaan?',
  cooldown:'Minimale tijd tussen starts (seconden)', selection:'Volgorde', sequence:'Om de beurt', enabled:'Regel ingeschakeld',
  ruleLights:'Lampen voor deze regel', ruleOutput:'Geluid voor deze regel', ruleVolume:'Speakervolume',
  cooldownHelp:'Alleen een overgang van geen beweging naar beweging telt. De wachttijd voorkomt te vaak afspelen.',
  ruleRequired:'Geef de regel een naam, kies een sensor en minstens één effect.',
  savedRule:'Bewegingsregel opgeslagen. Activeer de regels wanneer je klaar bent.',
  sharedHint:'Sfeer en effecten hebben aparte speakers nodig; een speaker kan maar één audiostream tegelijk afspelen.',
  autoDocs:'Voorbeeld voor HA-automatiseringen', undo:'Ongedaan maken', removed:'Regel verwijderd.',
  played:'Afgespeeld', busy:'Overgeslagen: effect speelt', cooldownState:'Wachttijd actief', waiting:'Wacht op beweging',
  ruleOff:'Uitgeschakeld', autoOff:'Automatisch staat uit', previewStop:'Stop voorbeeld',
  moodLibrary:'Kies je sfeer', moodSub:'Een achtergrond voor de hele avond, met eigen lampen en geluid.',
  emptySelection:'Nog geen speakers gekozen', cannotPlay:'Kan geen audio afspelen',
});
Object.assign(TEXT.en, {
  effectMode:'Effects', moodMode:'Continuous mood', autoMode:'On motion', speakers:'HA speakers',
  speakerHint:'Speakers receive the same sound. Use an existing HA speaker group for better synchronization between speakers.',
  noSpeakers:'No HA media players yet. Add your speaker integration first.',
  speakerCount:'speakers', defaultRoute:'Sound: default', ownRoute:'Custom speakers', route:'Sound for this effect',
  routeHelp:'This choice applies only to this effect and is saved.', inherit:'Use defaults',
  moodHelp:'Mood repeats until you stop it. Effects play alongside it on their own speakers. On shared lights the effect takes priority, then mood lighting resumes.',
  effectsHelp:'Tap an effect. Optionally save a separate speaker choice for each effect.',
  stopEffect:'Stop effect', stopMood:'Stop mood', stopAll:'Stop all', idleEffect:'No effect playing', idleMood:'No mood playing',
  continuous:'Keeps repeating', active:'Active', outputNone:'Lights only', configure:'Configure',
  autoHelp:'Choose a motion sensor and one or more effects. BooCue plays one effect on new motion and skips triggers while an effect is playing. Use a HA automation for schedules and extra conditions.',
  armed:'Enable motion rules', armedHelp:'Stop all also disables these rules. Mood can keep playing alongside triggered effects.',
  noRules:'Create your first motion rule', noRulesHelp:'For example: motion at the front door → a random spooky sound on the outdoor speakers.',
  newRule:'New rule', edit:'Edit', remove:'Remove', cancel:'Cancel', saveRule:'Save rule',
  ruleName:'Name', sensor:'Motion sensor', pickSensor:'Choose a sensor', pool:'Which effects can play?',
  cooldown:'Minimum time between starts (seconds)', selection:'Order', sequence:'Take turns', enabled:'Rule enabled',
  ruleLights:'Lights for this rule', ruleOutput:'Sound for this rule', ruleVolume:'Speaker volume',
  cooldownHelp:'Only a change from no motion to motion counts. The cooldown prevents overly frequent playback.',
  ruleRequired:'Name the rule, choose a sensor and at least one effect.',
  savedRule:'Motion rule saved. Enable the rules when you are ready.',
  sharedHint:'Mood and effects need separate speakers; one speaker can play only one audio stream at a time.',
  autoDocs:'HA automation example', undo:'Undo', removed:'Rule removed.',
  played:'Played', busy:'Skipped: effect playing', cooldownState:'Cooldown active', waiting:'Waiting for motion',
  ruleOff:'Disabled', autoOff:'Automatic mode is off', previewStop:'Stop preview',
  moodLibrary:'Choose your mood', moodSub:'A background for the whole evening, with its own lights and sound.',
  emptySelection:'No speakers selected', cannotPlay:'Cannot play audio',
});
Object.assign(TEXT.nl,{
 queueMode:'Wachtrijen',moodTab:'Sfeer',queueTitle:'Jouw wachtrijen',queueHelp:'Zet effecten in je eigen volgorde. Laat ze vanzelf afspelen of ga verder bij beweging; sfeer blijft op de achtergrond spelen.',
 newQueue:'Nieuwe wachtrij',queueName:'Naam van de wachtrij',saveQueue:'Wachtrij bewaren',noQueues:'Maak je eerste wachtrij',noQueuesHelp:'Bijvoorbeeld: deurgekraak → voetstappen → een spook. Kies een vaste volgorde of schud de lijst.',
 queueOrder:'Volgorde',queueAdvance:'Volgend effect',timed:'Automatisch na een pauze',onMotion:'Wachten op beweging of Volgende',gapMin:'Kortste pauze (seconden)',gapMax:'Langste pauze (seconden)',queueRepeat:'Hele wachtrij herhalen',
 addEffect:'Effect toevoegen',pickEffect:'Kies een effect',add:'Toevoegen',moveUp:'Omhoog',moveDown:'Omlaag',removeItem:'Uit wachtrij halen',queueItems:'Effecten in deze wachtrij',queueRequired:'Geef de wachtrij een naam en voeg minstens één effect toe.',
 queueSettings:'Uitgangen en lampen',useDefaults:'Gebruik de standaardinstellingen voor effecten',queueSettingsHelp:'Deze instellingen zijn de basis. Een eigen geluidskeuze per effect heeft voorrang. Wijzigingen gelden bij de volgende start.',
 startQueue:'Start wachtrij',nextQueue:'Volgende',stopQueue:'Stop wachtrij',waitingMotion:'Wacht op beweging of Volgende',waitingDelay:'Wacht op volgend effect',queueSaved:'Wachtrij opgeslagen.',queueNoActive:'Er speelt geen wachtrij.',
 sensors:'Bewegingssensoren',sensorLogic:'Wanneer afgaan?',anySensor:'Bij beweging op één van de sensoren (OF)',allSensors:'Als alle gekozen sensoren beweging zien (EN)',sensorLogicHelp:'Alleen nieuwe beweging telt. Een sensor die aan blijft, triggert niet telkens opnieuw.',
 motionAction:'Wat moet er gebeuren?',playOne:'Eén effect afspelen',startSelectedQueue:'Wachtrij starten',nextSelectedQueue:'Volgende effect, of wachtrij starten',chooseQueue:'Kies een wachtrij',queueRuleHelp:'Gebruikt de opgeslagen wachtrij en geluidskeuzes per effect. Stel de uitgangen daar in.',
 enableBrowser:'Automatisch geluid op dit apparaat inschakelen',browserReady:'Dit apparaat is gereed voor automatisch geluid',browserHelp:'Houd dit paneel open. Sfeer en effecten worden hier gemengd. Voor gebruik zonder browser kies je HA-speakers.',
 audioMode:'Sfeer en effecten mengen',mixAuto:'Dit apparaat en geschikte Sonos-speakers',mixSeparate:'Aparte HA-speakers gebruiken',duck:'Sfeervolume tijdens een effect',mixHelp:'Dit apparaat mengt twee geluiden. Sonos gebruikt ondersteunde aankondigingen; andere HA-speakers hebben aparte uitgangen nodig.',
 queued:'wachtrij',selectedSensors:'sensoren geselecteerd',queueDraftEmpty:'Voeg effecten toe met de keuzelijst hieronder.',
 autoHelp:'Kies één of meer sensoren. Speel één effect, start een wachtrij of wissel naar het volgende effect. Gebruik HA-automatiseringen voor uitgebreidere voorwaarden.',
 sharedHint:'Sfeer blijft doorlopen. Dit apparaat kan geluiden mengen; geschikte Sonos-speakers gebruiken aankondigingen. Kies aparte uitgangen voor andere HA-speakers.',
 ruleRequired:'Geef de regel een naam, kies sensoren en kies effecten of een wachtrij.',
});
Object.assign(TEXT.en,{
 queueMode:'Queues',moodTab:'Mood',queueTitle:'Your queues',queueHelp:'Put effects in your own order. Play automatically or advance on motion while mood keeps playing in the background.',
 newQueue:'New queue',queueName:'Queue name',saveQueue:'Save queue',noQueues:'Create your first queue',noQueuesHelp:'For example: a creaking door → footsteps → a ghost. Use a fixed order or shuffle the list.',
 queueOrder:'Order',queueAdvance:'Next effect',timed:'Automatically after a gap',onMotion:'Wait for motion or Next',gapMin:'Shortest gap (seconds)',gapMax:'Longest gap (seconds)',queueRepeat:'Repeat the whole queue',
 addEffect:'Add effect',pickEffect:'Choose an effect',add:'Add',moveUp:'Move up',moveDown:'Move down',removeItem:'Remove from queue',queueItems:'Effects in this queue',queueRequired:'Name the queue and add at least one effect.',
 queueSettings:'Outputs and lights',useDefaults:'Use the default effect settings',queueSettingsHelp:'These settings are the defaults. Per-effect audio choices take priority. Changes apply at the next start.',
 startQueue:'Start queue',nextQueue:'Next',stopQueue:'Stop queue',waitingMotion:'Waiting for motion or Next',waitingDelay:'Waiting for next effect',queueSaved:'Queue saved.',queueNoActive:'No queue is playing.',
 sensors:'Motion sensors',sensorLogic:'When to trigger?',anySensor:'When any selected sensor detects motion (OR)',allSensors:'When all selected sensors detect motion (AND)',sensorLogicHelp:'Only new motion counts. A sensor staying on does not keep retriggering.',
 motionAction:'What should happen?',playOne:'Play one effect',startSelectedQueue:'Start queue if idle',nextSelectedQueue:'Next effect, or start the queue',chooseQueue:'Choose a queue',queueRuleHelp:'Uses the saved queue and per-effect audio choices. Configure outputs there.',
 enableBrowser:'Enable automatic sound on this device',browserReady:'This device is ready for automatic sound',browserHelp:'Keep this panel open. Mood and effects mix here. Choose HA speakers for playback without a browser.',
 audioMode:'Mix mood and effects',mixAuto:'This device and compatible Sonos speakers',mixSeparate:'Use separate HA speakers',duck:'Mood volume during an effect',mixHelp:'This device mixes two sounds. Sonos uses supported announcements; other HA speakers need separate outputs.',
 queued:'queue',selectedSensors:'sensors selected',queueDraftEmpty:'Add effects using the list below.',
 autoHelp:'Choose one or more sensors. Play an effect, start a queue or advance to its next effect. Use HA automations for more advanced conditions.',
 sharedHint:'Mood keeps playing. This device can mix sounds; compatible Sonos speakers use announcements. Choose separate outputs for other HA speakers.',
 ruleRequired:'Name the rule, choose sensors and select effects or a queue.',
});
Object.assign(TEXT.nl, {cueTimeline:'Lichtverloop',queueId:'Wachtrij-id voor HA-acties',powerOn:'BooCue aan',powerOff:'BooCue uit',powerHelp:'Globale schakelaar voor alle BooCue-weergave.',disabledHelp:'BooCue staat uit. Afspelen en bewegingsregels zijn geblokkeerd; je kunt instellingen blijven aanpassen. Aan zetten hervat geen oude show.',enableFirst:'Zet eerst BooCue aan met de globale schakelaar.'});
Object.assign(TEXT.en, {cueTimeline:'Light timeline',queueId:'Queue id for HA actions',powerOn:'BooCue on',powerOff:'BooCue off',powerHelp:'Master switch for all BooCue playback.',disabledHelp:'BooCue is off. Playback and motion triggers are blocked; you can still edit settings. Turning on does not resume an old show.',enableFirst:'Turn on the BooCue master switch first.'});

// Each overview block represents a consecutive group of cues across the full clip.
function cueBlocks(effect) {
  const cues=effect?.cues||[],count=Math.min(18,cues.length);
  return Array.from({length:count},(_,i)=>cues[Math.floor(i*cues.length/count)]);
}
function cueBlockIndex(effect,seconds) {
  const blocks=cueBlocks(effect);
  let lo=0,hi=blocks.length;
  while(lo<hi){const mid=(lo+hi)>>>1;if(blocks[mid].at<=seconds)lo=mid+1;else hi=mid;}
  return lo-1;
}
function lightPosition(state,now,clockOffset=0) {
  const elapsed=(now+clockOffset-state.start_at-(state.offset_ms||0)/1000)*(state.speed||1);
  return elapsed<0?elapsed:state.repeat?elapsed%state.duration:Math.min(elapsed,state.duration);
}

const RUNTIME_KEYS = ['lights','output','speakers','volume','brightness','speed','offset_ms','routing','repeat','restore','interval_ms','audio_mode','duck_mood'];

const esc = (value) => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const icon = (name) => `<ha-icon icon="${esc(name)}" aria-hidden="true"></ha-icon>`;
const duration = seconds => `${Math.floor(Math.max(0, seconds) / 60)}:${String(Math.floor(Math.max(0, seconds) % 60)).padStart(2, '0')}`;

class BooCuePanel extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: 'open' });
    this._effects = [];
    this._entities = { lights: [], players: [], sensors: [] };
    this._mode = 'effect'; this._modeViews = {}; this._sources = new Map(); this._pending = new Set(); this._generations = {}; this._ruleDraft = null; this._queueDraft = null; this._browserId = null; this._receiving = new Map();
    this._settings = {};
    this._status = { playing: false };
    this._category = 'everything';
    this._query = '';
    this._lightQuery = '';
    this._buffers = new Map();
    this._clockOffset = 0;
    this._language = 'nl';
    this._themePreference = localStorage.getItem('boocue-theme');
    this._motionPreference=typeof matchMedia==='function'?matchMedia('(prefers-reduced-motion: reduce)'):null;
    this._boundClick = e => this._onClick(e);
    this._boundInput = e => this._onInput(e);
    this._boundChange = e => this._onChange(e);
  }

  set hass(value) {
    this._hass = value;
    if(value?.connected===false){this._browserId=null;this._stopAudio();this._reloadAfterConnect=true;}
    if(value?.connected===true&&this._reloadAfterConnect){this._reloadAfterConnect=false;if(this.isConnected&&!this._loading)this._load();}
    this._language = (value?.locale?.language || value?.language || 'nl').startsWith('nl') ? 'nl' : 'en';
    if (this.isConnected && !this._loaded && !this._loading) this._load();
    if (this._loaded && !this._themePreference) this._applyTheme();
  }
  get hass() { return this._hass; }
  get t() { return TEXT[this._language]; }

  connectedCallback() {
    this.shadowRoot.addEventListener('click', this._boundClick);
    this.shadowRoot.addEventListener('input', this._boundInput);
    this.shadowRoot.addEventListener('change', this._boundChange);
    this._animation = requestAnimationFrame(() => this._animate());
    if (this._hass && !this._loading) this._load();
  }
  disconnectedCallback() {
    this._queueGeneration=(this._queueGeneration||0)+1;
    for (const c of ['effect','mood','preview']) this._generations[c] = (this._generations[c] || 0) + 1;
    this.shadowRoot.removeEventListener('click', this._boundClick);
    this.shadowRoot.removeEventListener('input', this._boundInput);
    this.shadowRoot.removeEventListener('change', this._boundChange);
    cancelAnimationFrame(this._animation);
    this._unsubscribe?.();
    this._unsubscribe = null;
    // Leaving the initiating browser panel stops its show; remote-player shows continue.
    for (const [channel, audio] of this._sources) if (channel !== 'preview') this._hass.callWS({type:'boocue/stop', channel, run_id:audio.run_id}).catch(() => {});
    if(this._browserId)this._hass.callWS({type:'boocue/browser_release',station_id:this._browserId}).catch(()=>{});
    this._browserId=null;
    this._stopAudio();
    this._context?.close();
    this._context = null;
    this._loaded = false;
  }

  async _load() {
    this._loading = true;
    if (!this._loaded) this._renderLoading();
    try {
      const before = Date.now() / 1000;
      const data = await this._hass.callWS({ type: 'boocue/get' });
      this._clockOffset = data.server_time - (before + Date.now() / 1000) / 2;
      this._effects = data.effects;
      this._entities = data.entities;
      this._settings = data.settings; this._savedSettings = structuredClone(data.settings);
      this._status = data.status;
      this._stopSequence = data.status.stop_sequence;
      this._loaded = true;
      if (!this._unsubscribe) {
        this._unsubscribe = await this._hass.connection.subscribeEvents(event => {
          const state = event.data;
          this._status = state;
          this._applyControlState(state);
          if(this._browserId&&state.browser_station_id!==undefined&&state.browser_station_id!==this._browserId)this._browserId=null;
          for (const channel of ['effect','mood']) {
            const audio=this._sources.get(channel),current=state.channels?.[channel];
            if(audio&&!this._pending.has(channel)&&(!current?.playing||current.run_id!==audio.run_id))this._stopAudio(channel);
            if(current?.playing&&current.output==='browser'&&current.browser_id===this._browserId&&!this._pending.has(channel)&&!this._sources.has(channel))this._receiveBrowserRun(channel,current);
          }
          this._renderStatus();
          for (const channel of ['effect','mood']) {
            const current = state.channels?.[channel];
            if (current?.error && this._lastError !== current.error) { this._lastError = current.error; this._message(current.error, true); }
          }
        }, 'boocue_state');
      }
      this._render();
      if (data.library_errors?.length) this._message(data.library_errors.join(' · '), true);
    } catch (err) {
      this._renderLoading(String(err.message || err));
    } finally { this._loading = false; }
  }

  _renderLoading(error) {
    this.shadowRoot.innerHTML = `<link rel="stylesheet" href="/boocue_frontend/panel.css?v=1.0.0&build=${encodeURIComponent(ASSET_REVISION)}">
      <section class="app loading"><h1>BooCue</h1>${error ? `<p role="alert">${esc(error)}</p><button data-action="retry">${this.t.retry}</button>` : '<div class="skeleton"></div><div class="skeleton short"></div>'}</section>`;
  }

  _render({preserve=true,focus=null}={}) {
    const view=preserve?this._captureView():null;
    const t = this.t, s = this._runtime();
    const ready=s.lights.length || s.output==='browser' || (s.output==='speakers' && s.speakers.length);
    const theme = this._themePreference || (this._hass?.themes?.darkMode ? 'dark' : 'light');
    this.shadowRoot.innerHTML = `<link rel="stylesheet" href="/boocue_frontend/panel.css?v=1.0.0&build=${encodeURIComponent(ASSET_REVISION)}">
    <div class="app" data-theme="${theme}">
      <header class="app-header">
        <button class="icon-button menu" data-action="menu" aria-label="${t.menu}">${icon('mdi:menu')}</button>
        <div class="brand">${icon('mdi:ghost')}<div><h1>BooCue</h1><p>${t.subtitle}</p></div></div>
        <button class="icon-button theme" data-action="theme" aria-label="${theme === 'dark' ? t.light : t.dark}" title="${theme === 'dark' ? t.light : t.dark}">${icon(theme === 'dark' ? 'mdi:white-balance-sunny' : 'mdi:weather-night')}</button>
      </header>
      <nav class="mode-tabs" aria-label="BooCue">${[['effect',t.effectMode,'mdi:lightning-bolt-outline'],['queue',t.queueMode,'mdi:playlist-play'],['mood',t.moodTab,'mdi:weather-night'],['automatic',t.autoMode,'mdi:motion-sensor']].map(([key,label,i]) => `<button data-mode="${key}" aria-pressed="${this._mode===key}">${icon(i)}${label}<span data-mode-state="${key}"></span></button>`).join('')}</nav>
      <div id="message" class="message" role="status" hidden></div>
      <div class="browser-station"><button class="secondary-button master-power" data-action="power" aria-pressed="${this._settings.enabled!==false}" title="${t.powerHelp}">${icon('mdi:power')}<span>${this._settings.enabled===false?t.powerOff:t.powerOn}</span></button><button class="text-button" data-action="browser-ready">${icon('mdi:volume-high')}<span id="browser-ready-label">${this._browserId?t.browserReady:t.enableBrowser}</span></button><span class="field-help">${t.browserHelp}</span></div>
      <p class="master-disabled" id="master-disabled" role="status" ${this._settings.enabled===false?'':'hidden'}>${t.disabledHelp}</p>
      <div class="workspace ${['automatic','queue'].includes(this._mode)?'automatic-workspace':''}">
        <aside class="setup ${ready ? '' : 'expanded'}" aria-labelledby="stage-title">
          <div class="section-heading"><h2 id="stage-title">${t.stage}</h2><span id="selection-count"></span><button class="setup-toggle text-button" data-action="setup" aria-expanded="${!ready}"></button></div>
          <div class="lamp-heading"><label for="light-search">${t.lights}</label><button class="icon-button small" data-action="refresh" aria-label="${t.refresh}">${icon('mdi:refresh')}</button></div>
          <div class="search-box">${icon('mdi:magnify')}<input id="light-search" type="search" placeholder="${t.lightSearch}" aria-label="${t.lightSearch}" value="${esc(this._lightQuery)}" autocomplete="off"></div>
          <div id="light-list" class="light-list"></div>
          <div class="selection-actions"><button class="text-button" data-action="select-all">${t.selectAll}</button><button class="text-button" data-action="clear">${t.clear}</button></div>
          <div class="output-block"><label for="output">${t.output}</label><select id="output" data-setting="output">
            <option value="browser">${t.browser}</option><option value="speakers">${t.speakers}</option><option value="none">${t.silent}</option>
          </select><div id="stage-speakers" ${s.output!=='speakers'?'hidden':''}>${this._speakerPicker('stage',s.speakers)}</div><button class="text-button test-button" data-action="test">${icon('mdi:volume-high')}${t.test}</button></div>
          <div class="slider-label"><label for="volume">${t.volume}</label><output id="volume-value">${Math.round(s.volume * 100)}%</output></div>
          <input id="volume" data-setting="volume" type="range" min="0" max="1" step="0.01" value="${s.volume}">
          <div class="slider-label"><label for="brightness">${t.brightness}</label><output id="brightness-value">${Math.round(s.brightness * 100)}%</output></div>
          <input id="brightness" data-setting="brightness" type="range" min="0.01" max="1" step="0.01" value="${s.brightness}">
          <label for="routing">${t.routing}</label><select id="routing" data-setting="routing">
            <option value="all">${t.all}</option><option value="alternate">${t.alternate}</option><option value="random">${t.random}</option>
          </select>
          ${this._mode === 'mood' ? `<p class="next-note">${t.continuous}</p>` : `<label class="check-row"><input type="checkbox" data-setting="repeat" ${s.repeat ? 'checked' : ''}><span>${t.repeat}</span></label>`}
          <label class="check-row"><input type="checkbox" data-setting="restore" ${s.restore ? 'checked' : ''}><span>${t.restore}</span></label>
          <details class="advanced" ${this._mode==='mood'?'hidden':''}><summary>${t.advanced}</summary>
            <label for="audio_mode">${t.audioMode}</label><select id="audio_mode" data-setting="audio_mode"><option value="auto">${t.mixAuto}</option><option value="separate">${t.mixSeparate}</option></select><p>${t.mixHelp}</p>
            <label for="duck_mood">${t.duck} (%)</label><input id="duck_mood" data-duck="true" type="number" min="0" max="100" step="1" value="${Math.round(s.duck_mood*100)}">
            <label for="speed">${t.speed}</label><select id="speed" data-setting="speed"><option value="0.5">0.5×</option><option value="0.75">0.75×</option><option value="1">1×</option><option value="1.25">1.25×</option><option value="1.5">1.5×</option><option value="2">2×</option></select>
            <label for="offset_ms">${t.offset} (ms)</label><input id="offset_ms" data-setting="offset_ms" type="number" min="-2000" max="2000" step="50" value="${s.offset_ms}"><p>${t.offsetHelp}</p>
            <label for="interval_ms">${t.interval} (ms)</label><input id="interval_ms" data-setting="interval_ms" type="number" min="100" max="2000" step="50" value="${s.interval_ms}">
          </details><p class="next-note">${t.next}</p>
        </aside>
        <main class="library" aria-labelledby="library-title">
          <div class="library-heading"><div><h2 id="library-title">${this._mode==='mood'?t.moodLibrary:t.library}</h2><p>${this._mode==='mood'?t.moodSub:t.effectsHelp}</p></div>
          <button class="secondary-button import-button" data-action="import">${icon('mdi:tray-arrow-down')}<span>${t.import}</span></button>
          <input id="pack-file" type="file" accept=".zip,application/zip" hidden></div>
          <div class="library-tools"><nav class="categories" aria-label="${t.library}">${['everything','favorites'].map(key => `<button data-category="${key}" aria-pressed="${key === this._category}">${key === 'favorites' ? icon('mdi:heart-outline') : ''}${t[key]}</button>`).join('')}</nav>
          <div class="search-box effect-search">${icon('mdi:magnify')}<input id="effect-search" type="search" placeholder="${t.search}" aria-label="${t.search}" value="${esc(this._query)}" autocomplete="off"></div></div>
          <p class="mode-help">${this._mode==='mood'?t.moodHelp:t.sharedHint}</p><p class="choose-note" id="choose-note">${t.choose}</p>
          <div id="effects" class="effects"></div>
          <div class="library-foot"><span>${t.version}</span><span id="library-count"></span></div>
        </main>
      </div>
      <section class="transport dual-transport" aria-label="${t.playing}">
        <div class="channel-tracks"><div class="queue-transport" id="queue-transport" hidden><span data-queue-status></span><button class="text-button" data-action="queue-next">${t.nextQueue}</button><button class="text-button" data-action="queue-stop">${t.stopQueue}</button></div>${['effect','mood'].map(channel=>`<div class="channel-track" data-channel="${channel}"><span class="channel-label">${channel==='mood'?t.moodMode:t.effectMode}</span><div class="track"><div class="track-heading"><strong id="${channel}-title"></strong><span class="time" id="${channel}-time"></span></div><p id="${channel}-detail"></p><progress id="${channel}-progress" max="100" value="0" aria-label="${channel==='mood'?t.moodMode:t.effectMode}"></progress></div><button class="secondary-button lane-stop" data-stop="${channel}" disabled>${icon('mdi:stop')}${channel==='mood'?t.stopMood:t.stopEffect}</button></div>`).join('')}<div id="preview-status" hidden><span>${t.preview}</span><button class="text-button" data-action="stop-preview">${t.previewStop}</button></div></div>
        <button class="stop-button" id="stop" data-action="stop" disabled>${icon('mdi:stop')}${t.stopAll}</button>
      </section>
    </div>`;
    for (const key of ['output','routing','speed','audio_mode']) this.shadowRoot.getElementById(key).value = String(s[key]);
    this._renderLights(); this._renderEffects(); if (this._mode === 'automatic') this._renderAutomatic(); if(this._mode==='queue')this._renderQueues(); this._renderStatus();
    this._restoreView(view,{focus});
  }

  _applyTheme() {
    const app = this.shadowRoot.querySelector('.app');
    if (app) app.dataset.theme = this._themePreference || (this._hass?.themes?.darkMode ? 'dark' : 'light');
  }

  _renderLights() {
    const list = this.shadowRoot.getElementById('light-list');
    if (!list) return;
    const lights = this._visibleLights();
    let group = null;
    list.innerHTML = lights.length ? lights.map(light => {
      const area = light.area !== group ? `<h3>${esc(light.area)}</h3>` : '';
      group = light.area;
      const unavailable = ['unavailable','unknown'].includes(light.state);
      const hasColor = light.color_modes.some(c => ['hs','rgb','rgbw','rgbww','xy'].includes(c));
      return `${area}<label class="lamp-row ${unavailable ? 'unavailable' : ''}"><input type="checkbox" data-light="${esc(light.entity_id)}" ${this._runtime().lights.includes(light.entity_id) ? 'checked' : ''} ${unavailable ? 'disabled' : ''}>${icon(hasColor ? 'mdi:lightbulb-multiple-outline' : 'mdi:lightbulb-outline')}<span>${esc(light.name)}${unavailable ? `<small>${this.t.unavailable}</small>` : ''}</span><span class="light-dot ${light.state === 'on' ? 'on' : ''}" aria-hidden="true"></span></label>`;
    }).join('') : `<p class="empty-lights">${esc(this._entities.lights.length ? this.t.emptyHelp : this.t.noLights)}</p>`;
    this.shadowRoot.getElementById('selection-count').textContent = `${this._runtime().lights.length} ${this.t.selected}`;
    const note=this.shadowRoot.getElementById('choose-note'); if(note) note.hidden = this._runtime().lights.length > 0 || this._runtime().output !== 'none';
    this._updateSetupToggle();
  }

  _updateSetupToggle() {
    const aside = this.shadowRoot.querySelector('.setup');
    const button = this.shadowRoot.querySelector('[data-action="setup"]');
    if (!aside || !button) return;
    const expanded = aside.classList.contains('expanded');
    button.setAttribute('aria-expanded', String(expanded));
    button.innerHTML = `${expanded ? this.t.chooseEffect : this.t.adjust}${icon(expanded ? 'mdi:chevron-up' : 'mdi:chevron-down')}`;
  }

  _visibleLights() {
    const query = this._lightQuery.toLocaleLowerCase();
    return this._entities.lights.filter(l => `${l.name} ${l.area}`.toLocaleLowerCase().includes(query));
  }

  _description(effect) {return effect.descriptions?.[this._language]||effect.description;}

  _filteredEffects() {
    return this._effects.filter(e => (this._mode === 'mood' ? e.category === 'moods' : e.category !== 'moods') && (this._category === 'everything' ||
      (this._category === 'favorites' ? this._settings.favorites.includes(e.id) : e.category === this._category)) &&
      `${e.title} ${this._description(e)} ${e.source}`.toLocaleLowerCase().includes(this._query.toLocaleLowerCase()));
  }

  _renderEffects() {
    const root = this.shadowRoot.getElementById('effects');
    if (!root) return;
    const view=this._captureView();
    const effects = this._filteredEffects();
    root.innerHTML = effects.length ? effects.map(e => {
      const favorite = this._settings.favorites.includes(e.id);
      return `<article class="effect ${Object.values(this._status.channels||{}).some(c=>c.playing&&c.effect_id===e.id) ? 'is-playing' : ''}" data-effect="${esc(e.id)}">
        <button class="effect-play" data-play="${esc(e.id)}" ${this._settings.enabled===false||this._pending.has(this._mode) ? 'disabled' : ''} aria-label="${this.t.play} ${esc(e.title)}">
          <span class="effect-top">${icon(e.icon)}<span class="effect-duration">${duration(e.duration)}</span></span>
          <strong>${esc(e.title)}</strong><span class="effect-description">${esc(this._description(e))}</span>
          <span class="effect-cue"><span class="mini-strip" role="img" aria-label="${this.t.cueTimeline}">${cueBlocks(e).map((c,i) => `<i data-cue-block="${i}"><span style="background:hsl(${c.hue} ${c.saturation * 70}% 55%);opacity:${.2 + c.brightness * .8}"></span><ha-icon class="cue-pointer" icon="mdi:arrow-down-bold" aria-hidden="true"></ha-icon></i>`).join('')}</span><span class="play-mark">${icon('mdi:play')}</span></span>
        </button>
        <div class="effect-actions"><button class="text-button" data-preview="${esc(e.id)}" ${this._settings.enabled===false||this._pending.has(this._mode) ? 'disabled' : ''}>${icon('mdi:headphones')}${this.t.listen}</button><button class="icon-button small favorite ${favorite ? 'active' : ''}" data-favorite="${esc(e.id)}" aria-label="${this.t.favorite}: ${esc(e.title)}" aria-pressed="${favorite}">${icon(favorite ? 'mdi:heart' : 'mdi:heart-outline')}</button></div>
        ${e.category !== 'moods' ? this._routeEditor(e) : `<p class="mood-repeat">${this.t.continuous}</p>`}
      </article>`;
    }).join('') : `<div class="empty"><h3>${this.t.empty}</h3><p>${this._category === 'favorites' ? this.t.noFavorites : this.t.emptyHelp}</p></div>`;
    this.shadowRoot.getElementById('library-count').textContent = `${effects.length} / ${this._effects.length}`;
    this._restoreView(view);this._lastLightPaint=0;this._renderLightFeedback();
    for (const b of this.shadowRoot.querySelectorAll('[data-category]')) b.setAttribute('aria-pressed', String(b.dataset.category === this._category));
  }

  _controlKey(el) {
    if(!el)return null;
    if(el.id)return `#${CSS.escape(el.id)}`;
    if(el.hasAttribute('data-speaker-scope'))return `[data-speaker-scope="${CSS.escape(el.dataset.speakerScope)}"][value="${CSS.escape(el.value)}"]`;
    for(const attr of ['data-mode','data-action','data-route-mode','data-route-volume','data-rule-field','data-rule-percent','data-rule-effect','data-rule-light','data-rule-enabled','data-edit-rule','data-remove-rule','data-play','data-preview','data-favorite','data-stop','data-start-queue','data-edit-queue','data-remove-queue','data-queue-field','data-queue-runtime','data-queue-percent','data-rule-sensor','data-queue-add','data-queue-up','data-queue-down','data-queue-remove','data-queue-inherit','data-queue-light','data-queue-item']) {
      if(el.hasAttribute(attr))return `[${attr}="${CSS.escape(el.getAttribute(attr))}"]`;
    }
    if(el.tagName==='SUMMARY') {const key=this._disclosureKey(el.parentElement);return key?`${key}>summary`:null;}
    return null;
  }

  _disclosureKey(el) {
    if(el.id)return `#${CSS.escape(el.id)}`;
    if(el.dataset.pickerScope)return `[data-picker-scope="${CSS.escape(el.dataset.pickerScope)}"]`;
    if(el.classList.contains('route-editor'))return `[data-effect="${CSS.escape(el.closest('[data-effect]').dataset.effect)}"] .route-editor`;
    if(el.dataset.sensorPicker)return '[data-sensor-picker]';
    if(el.classList.contains('queue-options'))return '.queue-options';
    if(el.classList.contains('queue-lights'))return '.queue-lights';
    if(el.classList.contains('rule-lights'))return '.rule-lights';
    if(el.classList.contains('advanced'))return '.advanced';
    return null;
  }

  _captureView() {
    const root=this.shadowRoot,active=root.activeElement,workspace=root.querySelector('.workspace');
    const details=[...root.querySelectorAll('details')].map(el=>({key:this._disclosureKey(el),open:el.open,scroll:el.querySelector('.speaker-list')?.scrollTop}));
    return {focus:this._controlKey(active),selection:typeof active?.selectionStart==='number'?[active.selectionStart,active.selectionEnd]:null,
      scroll:workspace?.scrollTop||0,expanded:root.querySelector('.setup')?.classList.contains('expanded'),details,
      scrollers:['.light-list','.rule-pool .rule-choices','.rule-lights .rule-choices','.sensor-picker .rule-choices','.rule-effect-choices','.queue-lights .rule-choices'].map(key=>({key,scroll:root.querySelector(key)?.scrollTop||0}))};
  }

  _restoreView(view,{focus=null,scroll=null}={}) {
    const root=this.shadowRoot;
    if(view) {
      if(view.expanded!==undefined)root.querySelector('.setup')?.classList.toggle('expanded',view.expanded);
      for(const item of view.details) {const el=item.key?root.querySelector(item.key):null;if(el){el.open=item.open;if(item.scroll!==undefined&&el.querySelector('.speaker-list'))el.querySelector('.speaker-list').scrollTop=item.scroll;}}
      for(const item of view.scrollers){const el=root.querySelector(item.key);if(el)el.scrollTop=item.scroll;}
      const workspace=root.querySelector('.workspace');if(workspace)workspace.scrollTop=view.scroll;
      this._updateSetupToggle();
    }
    const key=focus||view?.focus,el=key?root.querySelector(key):null;
    if(el&&!el.disabled) {
      el.focus({preventScroll:true});
      if(!focus&&view?.selection)try{el.setSelectionRange(...view.selection);}catch{}
      if(scroll)(scroll==='start'?el.closest('.rule-editor,.queue-editor')||el:el).scrollIntoView({block:scroll,behavior:'auto'});
    }
  }

  _runtime(channel = this._mode === 'mood' ? 'mood' : 'effect') { return channel === 'mood' ? this._settings.mood : this._settings; }

  _resolved(id,channel) {
    const values=Object.fromEntries(RUNTIME_KEYS.map(k=>[k,structuredClone(this._runtime(channel)[k])]));
    if(channel==='effect') Object.assign(values,this._settings.effect_routes[id]||{});
    else {values.repeat=true;values.speed=1;}
    return values;
  }

  _speakerPicker(scope,selected=[]) {
    const t=this.t, players=[...this._entities.players,...selected.filter(id=>!this._entities.players.some(p=>p.entity_id===id)).map(id=>({entity_id:id,name:id,state:'unavailable',area:'',supported_features:0}))];
    return `<details class="speaker-picker" data-picker-scope="${esc(scope)}"><summary>${selected.length ? `${selected.length} ${t.speakerCount}` : t.emptySelection}</summary><div class="speaker-list">${players.length?players.map(p=>{
      const unavailable=['unavailable','unknown'].includes(p.state), incapable=!(p.supported_features&512);
      return `<label class="check-row"><input type="checkbox" data-speaker-scope="${esc(scope)}" value="${esc(p.entity_id)}" ${selected.includes(p.entity_id)?'checked':''} ${(!selected.includes(p.entity_id)&&(unavailable||incapable))?'disabled':''}><span>${esc(p.name)}<small>${esc(p.area)}${unavailable?` · ${t.unavailable}`:incapable?` · ${t.cannotPlay}`:''}</small></span></label>`;
    }).join(''):`<p>${t.noSpeakers}</p>`}</div><p class="field-help">${t.speakerHint}</p></details>`;
  }

  _routeEditor(effect) {
    const r=this._settings.effect_routes[effect.id], mode=r?.output||'default', t=this.t;
    return `<details class="route-editor"><summary>${icon('mdi:speaker-multiple')}${r ? (mode==='speakers'?`${r.speakers.length} ${t.speakerCount}`:mode==='browser'?t.browser:t.silent) : t.defaultRoute}</summary><label>${t.route}<select data-route-mode="${esc(effect.id)}">${[['default',t.inherit],['speakers',t.ownRoute],['browser',t.browser],['none',t.silent]].map(([v,l])=>`<option value="${v}" ${mode===v?'selected':''}>${l}</option>`).join('')}</select></label>${mode==='speakers'?this._speakerPicker('route:'+effect.id,r.speakers):''}${r?`<label class="route-volume">${t.volume}<input data-route-volume="${esc(effect.id)}" type="range" min="0" max="1" step="0.01" value="${r.volume}"><output>${Math.round(r.volume*100)}%</output></label>`:''}<p class="field-help">${t.routeHelp}</p></details>`;
  }

  _renderStatus() {
    const root=this.shadowRoot;
    if(!root.getElementById('effect-title'))return;
    const disabled=this._settings.enabled===false;
    const power=root.querySelector('[data-action="power"]');
    if(power){power.disabled=Boolean(this._powerPending);power.setAttribute('aria-pressed',String(!disabled));power.querySelector('span').textContent=disabled?this.t.powerOff:this.t.powerOn;}
    const notice=root.getElementById('master-disabled');if(notice)notice.hidden=!disabled;
    for(const button of root.querySelectorAll('[data-play],[data-preview]'))button.disabled=disabled||this._pending.has(this._mode);
    for(const button of root.querySelectorAll('[data-start-queue]'))button.disabled=disabled||this._pending.has('queue');
    for(const button of root.querySelectorAll('[data-action="test"],[data-action="browser-ready"]'))button.disabled=disabled;
    let active=false;
    for(const channel of ['effect','mood']) {
      const state=this._status.channels?.[channel]||{playing:false}, pending=this._pending.has(channel);
      const queueWaiting=channel==='effect'&&this._status.queue?.playing&&!state.playing;
      active ||= state.playing || pending;
      root.getElementById(`${channel}-title`).textContent=pending?this.t.starting:state.playing?state.title:queueWaiting?this._status.queue.name:channel==='mood'?this.t.idleMood:this.t.idleEffect;
      const count=state.speakers?.length||0;
      root.getElementById(`${channel}-detail`).textContent=state.error || (state.playing ? `${state.output==='browser'?this.t.browser:state.output==='speakers'?`${count} ${this.t.speakerCount}`:this.t.silent} · ${state.lights?.length||0} ${this.t.lights.toLowerCase()}${state.warnings?` · ${state.notes?.[0]||state.warnings}`:''}`:(state.notes?.[0]||''));
      root.querySelector(`[data-stop="${channel}"]`).disabled=!state.playing&&!pending&&!(channel==='effect'&&this._status.queue?.playing);
      root.querySelector(`[data-channel="${channel}"]`).classList.toggle('active',Boolean(state.playing));
      const mode=root.querySelector(`[data-mode-state="${channel}"]`); if(mode)mode.textContent=state.playing?this.t.active:'';
      if(!state.playing) {root.getElementById(`${channel}-time`).textContent='';root.getElementById(`${channel}-progress`).value=0;}
    }
    root.getElementById('preview-status').hidden=!this._sources.has('preview')&&!this._pending.has('preview');
    root.getElementById('stop').disabled=!this._status.queue?.playing&&!active&&!this._pending.size&&!this._sources.has('preview')&&!this._settings.automatic_enabled;
    for(const tile of root.querySelectorAll('[data-effect]'))tile.classList.toggle('is-playing',Object.values(this._status.channels||{}).some(c=>c.playing&&c.effect_id===tile.dataset.effect));
    const q=this._status.queue||{};
    const queueTransport=root.getElementById('queue-transport');if(queueTransport)queueTransport.hidden=!q.playing;
    for(const el of root.querySelectorAll('[data-queue-status]'))el.textContent=q.error||(!q.playing?this.t.queueNoActive:`${q.name} · ${q.step?((q.step-1)%q.total)+1:0}/${q.total}${q.waiting?` · ${q.waiting==='motion'?this.t.waitingMotion:this.t.waitingDelay}`:''}`);
    for(const el of root.querySelectorAll('[data-queue-row]'))el.classList.toggle('is-playing',q.playing&&el.dataset.queueRow===q.queue_id);
    for(const button of root.querySelectorAll('[data-action="queue-next"]'))button.disabled=disabled||!q.playing;
    for(const button of root.querySelectorAll('[data-action="queue-stop"]'))button.disabled=!q.playing&&!this._pending.has('queue');
    const queueMode=root.querySelector('[data-mode-state="queue"]');if(queueMode)queueMode.textContent=q.playing?this.t.active:'';
    const ready=root.getElementById('browser-ready-label');if(ready)ready.textContent=this._browserId?this.t.browserReady:this.t.enableBrowser;
    this._updateDuck();this._renderLightFeedback();
    const armed=root.querySelector('[data-action="arm"]');if(armed)armed.checked=this._settings.automatic_enabled;
    const auto=root.querySelector('[data-mode-state="automatic"]');if(auto)auto.textContent=!disabled&&this._settings.automatic_enabled?this.t.active:'';
    for(const el of root.querySelectorAll('[data-rule-status]')) {
      const rule=this._settings.motion_rules.find(r=>r.id===el.dataset.ruleStatus), event=this._status.motion?.[rule?.id];
      el.textContent=disabled?this.t.powerOff:!rule?.enabled?this.t.ruleOff:!this._settings.automatic_enabled?this.t.autoOff:event?({played:this.t.played,busy:this.t.busy,cooldown:this.t.cooldownState,error:event.error}[event.state]||this.t.waiting):this.t.waiting;
    }
  }

  _animate() {
    if(this._loaded)for(const channel of ['effect','mood']) {
      const state=this._status.channels?.[channel];if(!state?.playing)continue;
      const seconds=Math.max(0,(Date.now()/1000+this._clockOffset-state.start_at)*state.speed);
      const position=state.repeat?seconds%state.duration:Math.min(seconds,state.duration);
      const bar=this.shadowRoot.getElementById(`${channel}-progress`);
      if(bar){bar.value=position/state.duration*100;this.shadowRoot.getElementById(`${channel}-time`).textContent=`${duration(position)} / ${duration(state.duration)}`;}
    }
    this._renderLightFeedback();
    this._animation=requestAnimationFrame(()=>this._animate());
  }

  _renderLightFeedback() {
    if(!this._loaded||!this.shadowRoot.querySelectorAll)return;
    const states=Object.values(this._status.channels||{}),preview=this._sources.get('preview');
    const live=Boolean(states.some(s=>s.playing)||preview);
    const now=Date.now(),cadence=this._motionPreference?.matches?1000:250;
    if(!live&&this._feedbackActive===false)return;
    if(live&&this._feedbackActive===true&&now-(this._lastLightPaint||0)<cadence)return;
    this._feedbackActive=live;this._lastLightPaint=now;
    const positions=new Map();
    for(const state of states)if(state.playing)positions.set(state.effect_id,lightPosition(state,now/1000,this._clockOffset));
    if(preview&&!positions.has(preview.id)){
      const effect=this._effects.find(e=>e.id===preview.id),seconds=now/1000-preview.started_at;
      if(seconds<effect?.duration)positions.set(preview.id,seconds);
    }
    for(const tile of this.shadowRoot.querySelectorAll('[data-effect]')) {
      const effect=this._effects.find(e=>e.id===tile.dataset.effect),seconds=positions.get(tile.dataset.effect);
      const current=seconds===undefined?-1:cueBlockIndex(effect,seconds),strip=tile.querySelector('.mini-strip');
      if(!strip||strip.dataset.currentBlock===String(current))continue;
      strip.dataset.currentBlock=String(current);
      for(const block of strip.querySelectorAll('[data-cue-block]'))block.classList.toggle('is-current',Number(block.dataset.cueBlock)===current);
      strip.setAttribute('aria-label',current<0?this.t.cueTimeline:`${this.t.cueTimeline} · ${current+1}/${cueBlocks(effect).length}`);
    }
  }

  async _audioContext() {
    if(!this._context||this._context.state==='closed')this._context=new AudioContext();
    await this._context.resume();return this._context;
  }

  async _buffer(id) {
    if (this._buffers.has(id)) return this._buffers.get(id);
    const info = await this._hass.callWS({ type: 'boocue/audio', effect_id: id });
    const response = await this._hass.fetchWithAuth(info.url);
    if (!response.ok) throw new Error(`Audio HTTP ${response.status}`);
    let buffer = await this._context.decodeAudioData(await response.arrayBuffer());
    const effect = this._effects.find(e => e.id === id);
    // Codec padding must not accumulate drift when an imported MP3 loops.
    const frames = Math.round(effect.duration * buffer.sampleRate);
    if (Math.abs(buffer.duration - effect.duration) < .25 && frames !== buffer.length) {
      const aligned = this._context.createBuffer(buffer.numberOfChannels, frames, buffer.sampleRate);
      for (let channel=0; channel<buffer.numberOfChannels; channel++) aligned.copyToChannel(buffer.getChannelData(channel).subarray(0, frames), channel);
      buffer = aligned;
    }
    if (this._buffers.size >= 3) this._buffers.delete(this._buffers.keys().next().value);
    this._buffers.set(id, buffer);
    return buffer;
  }

  _stopAudio(channel) {
    if(!channel){try{this._testTone?.stop();}catch{}this._testTone=null;}
    for(const key of channel?[channel]:[...this._sources.keys()]) {
      const audio=this._sources.get(key);if(!audio)continue;
      audio.source.onended=null;try{audio.source.stop();}catch{}
      audio.source.disconnect();audio.gain.disconnect();this._sources.delete(key);
    }
    this._updateDuck();
  }

  _applyControlState(state) {
    const wasEnabled=this._settings.enabled!==false;
    const globalStop=Number.isInteger(state.stop_sequence)&&this._stopSequence!==undefined&&state.stop_sequence!==this._stopSequence;
    if(Number.isInteger(state.stop_sequence))this._stopSequence=state.stop_sequence;
    for(const key of ['enabled','automatic_enabled'])if(typeof state[key]==='boolean'){
      this._settings[key]=state[key];if(this._savedSettings)this._savedSettings[key]=state[key];
    }
    if(globalStop||state.enabled===false&&(wasEnabled||this._pending.size||this._sources.size||this._testTone)){
      this._queueGeneration=(this._queueGeneration||0)+1;
      for(const key of ['effect','mood','preview','test'])this._generations[key]=(this._generations[key]||0)+1;
      this._pending.clear();this._stopAudio();
    }
  }

  async _togglePower() {
    if(this._powerPending)return;
    this._powerPending=true;this._renderStatus();
    try{this._applyControlState(await this._hass.callWS({type:'boocue/settings',settings:{enabled:this._settings.enabled===false}}));}
    catch(err){this._message(String(err.message||err),true);}
    finally{this._powerPending=false;this._renderStatus();}
  }

  async _start(id,preview=false) {
    if(this._settings.enabled===false){this._message(this.t.enableFirst,true);return;}
    const effect=this._effects.find(e=>e.id===id), channel=preview?'preview':effect.category==='moods'?'mood':'effect';
    if(this._pending.has(channel))return;
    const settings=this._resolved(id,channel==='preview'?(this._mode==='mood'?'mood':'effect'):channel);
    if(!preview&&!settings.lights.length&&settings.output==='none'){this._message(this.t.choose,true);return;}
    this._pending.add(channel);
    const generation=this._generations[channel]=(this._generations[channel]||0)+1;
    const browserAudio=preview||settings.output==='browser';
    const contextReady=browserAudio?(preview?this._audioContext():this._ensureBrowserStation()):Promise.resolve();
    this._renderStatus();this._renderEffects();let started;
    try {
      await contextReady;
      const buffer=browserAudio?await this._buffer(id):null;
      if(generation!==this._generations[channel])return;
      let state;
      if(!preview) {
        const before=Date.now()/1000;
        state=await this._hass.callWS({type:'boocue/play',effect_id:id,channel,settings,browser_id:this._browserId||undefined});started=state;
        if(generation!==this._generations[channel]){await this._hass.callWS({type:'boocue/stop',channel,run_id:state.run_id});return;}
        this._clockOffset=state.server_time-(before+Date.now()/1000)/2;
        this._status.channels={...this._status.channels,[channel]:state};
        if(channel==='mood'){this._settings.mood.effect_id=id;this._save();}
      }
      this._stopAudio(channel);
      if(buffer) {
        const source=this._context.createBufferSource(),gain=this._context.createGain();
        gain.gain.value=settings.volume;gain.connect(this._context.destination);source.buffer=buffer;source.connect(gain);
        source.playbackRate.value=preview?1:settings.speed;source.loop=!preview&&settings.repeat;
        source.onended=()=>{if(this._sources.get(channel)?.source!==source)return;source.disconnect();gain.disconnect();this._sources.delete(channel);this._renderStatus();};
        this._sources.set(channel,{source,gain,run_id:state?.run_id,id,volume:settings.volume,started_at:Date.now()/1000});
        this._updateDuck();
        const wait=preview?0:Math.max(0,state.start_at-(Date.now()/1000+this._clockOffset));
        source.start(this._context.currentTime+wait);
      }
    } catch(err) {
      if(started)try{await this._hass.callWS({type:'boocue/stop',channel,run_id:started.run_id});}catch{}
      this._message(String(err.message||this.t.soundError),true);
    } finally {if(generation===this._generations[channel])this._pending.delete(channel);this._renderStatus();this._renderEffects();}
  }

  async _testSound() {
    if(this._settings.enabled===false){this._message(this.t.enableFirst,true);return;}
    const generation=this._generations.test=(this._generations.test||0)+1;
    if (this._runtime().volume <= 0) { this._message(this.t.volumeZero); return; }
    try {
      const ctx = await this._audioContext();
      if(this._settings.enabled===false||generation!==this._generations.test)return;
      try{this._testTone?.stop();}catch{}
      const gain = ctx.createGain(); const tone = ctx.createOscillator();
      tone.frequency.value = 440; tone.connect(gain); gain.connect(ctx.destination);
      gain.gain.setValueAtTime(0, ctx.currentTime);
      gain.gain.linearRampToValueAtTime(.18 * this._runtime().volume, ctx.currentTime + .03);
      gain.gain.exponentialRampToValueAtTime(.001, ctx.currentTime + .45);
      this._testTone=tone;tone.start(); tone.stop(ctx.currentTime + .5);
      tone.onended = () => { if(this._testTone===tone)this._testTone=null;tone.disconnect(); gain.disconnect(); };
      this._message(this.t.testOk);
    } catch { this._message(this.t.soundError, true); }
  }

  _message(text, error = false) {
    const el = this.shadowRoot.getElementById('message');
    if (!el) return;
    el.hidden = false; el.classList.toggle('error', error);
    el.replaceChildren(document.createTextNode(text));
    const close = document.createElement('button'); close.className = 'icon-button';
    close.dataset.action = 'dismiss'; close.setAttribute('aria-label', this.t.close);
    close.innerHTML = icon('mdi:close'); el.append(close);
  }

  async _save() {
    const snapshot=structuredClone(this._settings),sequence=this._saveSequence=(this._saveSequence||0)+1;
    const changes=Object.fromEntries(Object.entries(snapshot).filter(([key,value])=>JSON.stringify(value)!==JSON.stringify(this._savedSettings?.[key])));
    this._saveQueue=(this._saveQueue||Promise.resolve()).then(async()=>{
      try {const result=await this._hass.callWS({type:'boocue/settings',settings:changes});this._savedSettings=structuredClone(result);if(sequence===this._saveSequence)this._settings=result;return true;}
      catch(err){if(sequence===this._saveSequence)this._settings=structuredClone(this._savedSettings);this._message(String(err.message||err),true);return false;}
    });return this._saveQueue;
  }

  async _onClick(event) {
    const button = event.target.closest('button');
    if (!button || button.disabled) return;
    if(button.dataset.startQueue)return this._startQueue(button.dataset.startQueue);
    if(button.dataset.editQueue){this._queueDraft=structuredClone(this._settings.queues.find(q=>q.id===button.dataset.editQueue));this._renderQueues({focus:'[data-queue-field="name"]',scroll:'start'});return;}
    if(button.dataset.removeQueue){const id=button.dataset.removeQueue,previous=structuredClone(this._settings.queues);this._deletedQueue=this._settings.queues.find(q=>q.id===id);this._settings.queues=this._settings.queues.filter(q=>q.id!==id);if(await this._save()){this._queueDraft=null;this._renderQueues();this._message(this.t.removed);const undo=document.createElement('button');undo.className='text-button';undo.dataset.action='undo-queue';undo.textContent=this.t.undo;this.shadowRoot.getElementById('message').append(undo);this._restoreView(null,{focus:'[data-action="undo-queue"]'});}else{this._settings.queues=previous;this._deletedQueue=null;}return;}
    for(const [key,delta] of [['queueUp',-1],['queueDown',1],['queueRemove',0]])if(button.dataset[key]!==undefined){const i=Number(button.dataset[key]),a=this._queueDraft.effects;if(delta)[a[i],a[i+delta]]=[a[i+delta],a[i]];else a.splice(i,1);this._renderQueues({focus:a.length?`[data-queue-item="${Math.min(delta?i+delta:i,a.length-1)}"]`:'[data-queue-add]'});return;}
    if (button.dataset.mode) {this._modeViews[this._mode]=this._captureView();this._mode=button.dataset.mode;this._category='everything';this._query='';const focus=`[data-mode="${this._mode}"]`;this._render({preserve:false,focus});this._restoreView(this._modeViews[this._mode],{focus});return;}
    if (button.dataset.stop) return this._stopChannel(button.dataset.stop);
    if (button.dataset.editRule) {this._ruleDraft=structuredClone(this._settings.motion_rules.find(r=>r.id===button.dataset.editRule));this._renderAutomatic({focus:'[data-rule-field="name"]',scroll:'start'});return;}
    if (button.dataset.removeRule) {this._deletedRule=this._settings.motion_rules.find(r=>r.id===button.dataset.removeRule);this._settings.motion_rules=this._settings.motion_rules.filter(r=>r.id!==button.dataset.removeRule);if(await this._save()){this._renderAutomatic();this._message(this.t.removed);const undo=document.createElement('button');undo.className='text-button';undo.dataset.action='undo-rule';undo.textContent=this.t.undo;this.shadowRoot.getElementById('message').append(undo);this._restoreView(null,{focus:'[data-action="undo-rule"]'});}return;}
    if (button.dataset.play) return this._start(button.dataset.play);
    if (button.dataset.preview) return this._start(button.dataset.preview, true);
    if (button.dataset.favorite) {
      const id = button.dataset.favorite;
      this._settings.favorites = this._settings.favorites.includes(id) ? this._settings.favorites.filter(x => x !== id) : [...this._settings.favorites, id];
      this._renderEffects(); return this._save();
    }
    if (button.dataset.category) { this._category = button.dataset.category; this._renderEffects(); return; }
    switch (button.dataset.action) {
      case 'browser-ready':try{await this._ensureBrowserStation();}catch(err){this._message(String(err.message||err),true);}break;
      case 'queue-next':case 'queue-stop':if(button.dataset.action==='queue-stop'){this._queueGeneration=(this._queueGeneration||0)+1;this._pending.delete('queue');}try{this._status.queue=await this._hass.callWS({type:'boocue/queue',action:button.dataset.action==='queue-next'?'next':'stop'});this._renderStatus();}catch(err){this._message(String(err.message||err),true);}break;
      case 'new-queue':this._queueDraft={id:crypto.randomUUID(),name:'',effects:[],mode:'sequence',advance:'auto',repeat:true,gap_min:4,gap_max:15,settings:{}};this._renderQueues({focus:'[data-queue-field="name"]',scroll:'start'});break;
      case 'cancel-queue':{const id=this._queueDraft?.id;this._queueDraft=null;this._renderQueues({focus:this._settings.queues.some(q=>q.id===id)?`[data-edit-queue="${CSS.escape(id)}"]`:'[data-action="new-queue"]',scroll:'nearest'});break;}
      case 'add-queue-effect':{const id=this.shadowRoot.querySelector('[data-queue-add]').value;if(id&&this._queueDraft.effects.length<100){this._queueDraft.effects.push(id);this._renderQueues({focus:'[data-queue-add]'});}break;}
      case 'save-queue':{const q=this._queueDraft;if(!q.name.trim()||!q.effects.length){this._message(this.t.queueRequired,true);break;}const i=this._settings.queues.findIndex(item=>item.id===q.id);if(i<0)this._settings.queues.push(structuredClone(q));else this._settings.queues[i]=structuredClone(q);if(await this._save()){this._queueDraft=null;this._renderQueues({focus:`[data-edit-queue="${CSS.escape(q.id)}"]`,scroll:'nearest'});this._message(this.t.queueSaved);}break;}
      case 'menu': this.dispatchEvent(new Event('hass-toggle-menu', {bubbles:true, composed:true})); break;
      case 'retry': case 'refresh': this._load(); break;
      case 'theme': {
        const current = this.shadowRoot.querySelector('.app').dataset.theme;
        this._themePreference = current === 'dark' ? 'light' : 'dark';
        localStorage.setItem('boocue-theme', this._themePreference); this._render(); break;
      }
      case 'setup': {
        const aside = this.shadowRoot.querySelector('.setup');
        aside.classList.toggle('expanded'); this._updateSetupToggle();
        if (!aside.classList.contains('expanded')) this.shadowRoot.querySelector('.library').scrollIntoView({block:'start',behavior:'auto'});
        break;
      }
      case 'dismiss': this.shadowRoot.getElementById('message').hidden = true; break;
      case 'power':await this._togglePower();break;
      case 'test': this._testSound(); break;
      case 'select-all': {
        const selected = this._visibleLights().filter(l => !['unknown','unavailable'].includes(l.state)).map(l => l.entity_id);
        this._runtime().lights = [...new Set([...this._runtime().lights, ...selected])].slice(0,32);
        this._renderLights(); this._save(); break;
      }
      case 'clear': this._runtime().lights = []; this._renderLights(); this._save(); break;
      case 'stop':
        this._queueGeneration=(this._queueGeneration||0)+1;
        for(const c of ['effect','mood','preview']){this._generations[c]=(this._generations[c]||0)+1;this._pending.delete(c);}
        this._stopAudio();
        try{await this._hass.callWS({type:'boocue/stop'});this._settings.automatic_enabled=false;for(const s of Object.values(this._status.channels||{}))s.playing=false;}
        catch(err){this._message(String(err.message||err),true);}this._renderStatus();this._renderEffects();break;
      case 'stop-preview': this._generations.preview=(this._generations.preview||0)+1;this._pending.delete('preview');this._stopAudio('preview');this._renderStatus();break;
      case 'undo-queue':if(this._deletedQueue){const id=this._deletedQueue.id;this._settings.queues.push(this._deletedQueue);if(await this._save()){this._deletedQueue=null;this.shadowRoot.getElementById('message').hidden=true;this._renderQueues({focus:`[data-edit-queue="${CSS.escape(id)}"]`,scroll:'nearest'});}}break;
      case 'new-rule': {
        const settings=this._resolved('', 'effect');
        this._ruleDraft={...settings,id:crypto.randomUUID(),name:'',sensor:'',sensors:[],match:'any',action:'effect',queue_id:null,effects:[],cooldown:30,mode:'random',enabled:true};this._renderAutomatic({focus:'[data-rule-field="name"]',scroll:'start'});break;
      }
      case 'cancel-rule':{const id=this._ruleDraft?.id;this._ruleDraft=null;this._renderAutomatic({focus:this._settings.motion_rules.some(r=>r.id===id)?`[data-edit-rule="${CSS.escape(id)}"]`:'[data-action="new-rule"]',scroll:'nearest'});break;}
      case 'save-rule': {
        const rule=this._ruleDraft;if(!rule.name.trim()||!rule.sensors?.length||(rule.action==='effect'?!rule.effects.length:!rule.queue_id)){this._message(this.t.ruleRequired,true);break;}
        const index=this._settings.motion_rules.findIndex(r=>r.id===rule.id);
        if(index<0)this._settings.motion_rules.push(structuredClone(rule));else this._settings.motion_rules[index]=structuredClone(rule);
        if(await this._save()){this._ruleDraft=null;this._renderAutomatic({focus:`[data-edit-rule="${CSS.escape(rule.id)}"]`,scroll:'nearest'});this._message(this.t.savedRule);}break;
      }
      case 'undo-rule':if(this._deletedRule){const id=this._deletedRule.id;this._settings.motion_rules.push(this._deletedRule);if(await this._save()){this._deletedRule=null;this.shadowRoot.getElementById('message').hidden=true;this._renderAutomatic({focus:`[data-edit-rule="${CSS.escape(id)}"]`,scroll:'nearest'});}}break;
      case 'import': this.shadowRoot.getElementById('pack-file').click(); break;
    }
  }

  async _stopChannel(channel) {
    this._generations[channel]=(this._generations[channel]||0)+1;this._pending.delete(channel);this._stopAudio(channel);
    try{await this._hass.callWS({type:'boocue/stop',channel});if(this._status.channels?.[channel])this._status.channels[channel].playing=false;}
    catch(err){this._message(String(err.message||err),true);}this._renderStatus();this._renderEffects();
  }

  _sensorPicker(rule) {
    const selected=rule.sensors||[rule.sensor].filter(Boolean);
    return `<details class="sensor-picker" data-sensor-picker="true"><summary>${selected.length} ${this.t.selectedSensors}</summary><div class="rule-choices">${this._entities.sensors.map(sensor=>`<label class="check-row"><input type="checkbox" data-rule-sensor="${esc(sensor.entity_id)}" ${selected.includes(sensor.entity_id)?'checked':''}><span>${esc(sensor.name)}<small>${esc(sensor.area)}</small></span></label>`).join('')}</div></details>`;
  }

  _renderAutomatic({focus=null,scroll=null}={}) {
    const root=this.shadowRoot.querySelector('.library'),t=this.t,r=this._ruleDraft;if(!root||this._mode!=='automatic')return;
    const view=this._captureView();
    const queueOptions=this._settings.queues.map(q=>`<option value="${esc(q.id)}" ${r?.queue_id===q.id?'selected':''}>${esc(q.name)}</option>`).join('');
    root.innerHTML=`<div class="library-heading"><div><h2>${t.autoMode}</h2><p>${t.autoHelp}</p></div><button class="secondary-button" data-action="new-rule">${icon('mdi:plus')}${t.newRule}</button></div>
      <div class="auto-arm"><label class="check-row"><input type="checkbox" data-action="arm" ${this._settings.automatic_enabled?'checked':''}><strong>${t.armed}</strong></label><p>${t.armedHelp}</p></div>
      ${r?`<section class="rule-editor" aria-label="${t.configure}"><label>${t.ruleName}<input data-rule-field="name" maxlength="80" value="${esc(r.name)}"></label>
      <fieldset class="rule-pool"><legend>${t.sensors}</legend>${this._sensorPicker(r)}${r.sensors.length?`<p class="field-help">${r.sensors.map(id=>esc(this._entities.sensors.find(s=>s.entity_id===id)?.name||id)).join(' · ')}</p>`:''}</fieldset>
      <div class="rule-fields"><label>${t.sensorLogic}<select data-rule-field="match"><option value="any" ${r.match==='any'?'selected':''}>${t.anySensor}</option><option value="all" ${r.match==='all'?'selected':''}>${t.allSensors}</option></select></label><label>${t.motionAction}<select data-rule-field="action">${[['effect',t.playOne],['start_queue',t.startSelectedQueue],['next_queue',t.nextSelectedQueue]].map(([v,l])=>`<option value="${v}" ${r.action===v?'selected':''}>${l}</option>`).join('')}</select></label></div><p class="field-help">${t.sensorLogicHelp}</p>
      ${r.action!=='effect'?`<label>${t.chooseQueue}<select data-rule-field="queue_id"><option value="">${t.chooseQueue}</option>${queueOptions}</select></label><p class="field-help">${t.queueRuleHelp}</p>`:`
      <fieldset class="rule-pool"><legend>${t.pool}</legend><div class="rule-choices rule-effect-choices">${this._effects.filter(e=>e.category!=='moods').map(e=>`<label class="check-row"><input type="checkbox" data-rule-effect="${esc(e.id)}" ${r.effects.includes(e.id)?'checked':''}>${esc(e.title)}</label>`).join('')}</div></fieldset>
      <label>${t.selection}<select data-rule-field="mode"><option value="random" ${r.mode==='random'?'selected':''}>${t.random}</option><option value="sequence" ${r.mode==='sequence'?'selected':''}>${t.sequence}</option></select></label>
      <label>${t.ruleOutput}<select data-rule-field="output">${[['browser',t.browser],['speakers',t.speakers],['none',t.silent]].map(([v,l])=>`<option value="${v}" ${r.output===v?'selected':''}>${l}</option>`).join('')}</select></label>${r.output==='speakers'?this._speakerPicker('rule',r.speakers):r.output==='browser'?`<p class="field-help">${t.browserHelp}</p>`:''}
      <div class="rule-fields"><label>${t.ruleVolume} (%)<input data-rule-percent="volume" type="number" min="0" max="100" value="${Math.round(r.volume*100)}"></label><label>${t.brightness} (%)<input data-rule-percent="brightness" type="number" min="1" max="100" value="${Math.round(r.brightness*100)}"></label></div>
      <details class="rule-lights"><summary>${t.ruleLights} · ${r.lights.length} ${t.selected}</summary><div class="rule-choices">${this._entities.lights.map(l=>`<label class="check-row"><input type="checkbox" data-rule-light="${esc(l.entity_id)}" ${r.lights.includes(l.entity_id)?'checked':''}>${esc(l.name)}</label>`).join('')}</div></details>`}
      <label>${t.cooldown}<input data-rule-field="cooldown" type="number" min="0" max="3600" value="${r.cooldown}"></label><p class="field-help">${t.cooldownHelp}</p>
      <label class="check-row"><input type="checkbox" data-rule-field="enabled" ${r.enabled?'checked':''}>${t.enabled}</label><div class="rule-actions"><button class="stop-button" data-action="save-rule">${t.saveRule}</button><button class="secondary-button" data-action="cancel-rule">${t.cancel}</button></div></section>`:''}
      <div class="motion-rules">${this._settings.motion_rules.length?this._settings.motion_rules.map(rule=>`<article class="motion-rule"><div><h3>${esc(rule.name)}</h3><p>${(rule.sensors||[rule.sensor]).length} ${t.sensors.toLowerCase()} · ${rule.match==='all'?'AND':'OR'} · ${rule.action==='effect'?`${rule.effects.length} ${t.effectMode.toLowerCase()}`:esc(this._settings.queues.find(q=>q.id===rule.queue_id)?.name||rule.queue_id)} · ${rule.cooldown}s</p><p data-rule-status="${esc(rule.id)}"></p></div><label class="check-row"><input type="checkbox" data-rule-enabled="${esc(rule.id)}" ${rule.enabled?'checked':''}>${t.enabled}</label><div class="rule-actions"><button class="text-button" data-edit-rule="${esc(rule.id)}">${t.edit}</button><button class="text-button" data-remove-rule="${esc(rule.id)}">${t.remove}</button></div></article>`).join(''):`<div class="empty" ${r?'hidden':''}><h3>${t.noRules}</h3><p>${t.noRulesHelp}</p></div>`}</div>
      <p class="automation-link"><a href="https://github.com/dwainscheeren/boocue/blob/main/docs/AUTOMATIONS.md" target="_blank" rel="noopener">${t.autoDocs}</a></p>`;
    this._renderStatus();this._restoreView(view,{focus,scroll});
  }

  _renderQueues({focus=null,scroll=null}={}) {
    if(this._mode!=='queue')return;
    const root=this.shadowRoot.querySelector('.library'),t=this.t,q=this._queueDraft,view=this._captureView();
    root.innerHTML=`<div class="library-heading"><div><h2>${t.queueTitle}</h2><p>${t.queueHelp}</p></div><button class="secondary-button" data-action="new-queue">${icon('mdi:plus')}${t.newQueue}</button></div>
      <div class="queue-now"><span data-queue-status></span><button class="text-button" data-action="queue-next">${t.nextQueue}</button><button class="text-button" data-action="queue-stop">${t.stopQueue}</button></div>
      ${q?`<section class="queue-editor rule-editor" aria-label="${t.configure}"><label>${t.queueName}<input data-queue-field="name" maxlength="80" value="${esc(q.name)}"></label>
      <div class="rule-fields"><label>${t.queueOrder}<select data-queue-field="mode"><option value="sequence" ${q.mode==='sequence'?'selected':''}>${t.sequence}</option><option value="random" ${q.mode==='random'?'selected':''}>${t.random}</option></select></label><label>${t.queueAdvance}<select data-queue-field="advance"><option value="auto" ${q.advance==='auto'?'selected':''}>${t.timed}</option><option value="motion" ${q.advance==='motion'?'selected':''}>${t.onMotion}</option></select></label></div>
      <div class="rule-fields" ${q.advance==='motion'?'hidden':''}><label>${t.gapMin}<input data-queue-field="gap_min" type="number" min="0" max="3600" value="${q.gap_min}"></label><label>${t.gapMax}<input data-queue-field="gap_max" type="number" min="0" max="3600" value="${q.gap_max}"></label></div>
      <label class="check-row"><input data-queue-field="repeat" type="checkbox" ${q.repeat?'checked':''}>${t.queueRepeat}</label>
      <h3>${t.queueItems}</h3><ol class="queue-items">${q.effects.length?q.effects.map((id,i)=>{const e=this._effects.find(e=>e.id===id);return `<li tabindex="-1" data-queue-item="${i}"><span class="queue-index">${i+1}</span><strong>${esc(e?.title||id)}</strong><span class="queue-item-actions"><button class="icon-button small" data-queue-up="${i}" aria-label="${t.moveUp}: ${esc(e?.title||id)}" ${i===0?'disabled':''}>${icon('mdi:arrow-up')}</button><button class="icon-button small" data-queue-down="${i}" aria-label="${t.moveDown}: ${esc(e?.title||id)}" ${i===q.effects.length-1?'disabled':''}>${icon('mdi:arrow-down')}</button><button class="icon-button small" data-queue-remove="${i}" aria-label="${t.removeItem}: ${esc(e?.title||id)}">${icon('mdi:close')}</button></span></li>`;}).join(''):`<li class="empty-queue">${t.queueDraftEmpty}</li>`}</ol>
      <div class="queue-add"><label>${t.addEffect}<select data-queue-add="true"><option value="">${t.pickEffect}</option>${this._effects.filter(e=>e.category!=='moods').map(e=>`<option value="${esc(e.id)}">${esc(e.title)}</option>`).join('')}</select></label><button class="secondary-button" data-action="add-queue-effect">${icon('mdi:plus')}${t.add}</button></div>
      <details class="queue-options"><summary>${t.queueSettings}</summary><label>${t.queueId}<input id="queue-id" readonly value="${esc(q.id)}"></label><label class="check-row"><input data-queue-inherit="true" type="checkbox" ${!Object.keys(q.settings).length?'checked':''}>${t.useDefaults}</label><p class="field-help">${t.queueSettingsHelp}</p>${Object.keys(q.settings).length?`
      <label>${t.output}<select data-queue-runtime="output">${[['browser',t.browser],['speakers',t.speakers],['none',t.silent]].map(([v,l])=>`<option value="${v}" ${q.settings.output===v?'selected':''}>${l}</option>`).join('')}</select></label>${q.settings.output==='speakers'?this._speakerPicker('queue',q.settings.speakers):''}
      <div class="rule-fields"><label>${t.volume} (%)<input data-queue-percent="volume" type="number" min="0" max="100" value="${Math.round(q.settings.volume*100)}"></label><label>${t.brightness} (%)<input data-queue-percent="brightness" type="number" min="1" max="100" value="${Math.round(q.settings.brightness*100)}"></label></div>
      <details class="queue-lights"><summary>${t.lights} · ${q.settings.lights.length} ${t.selected}</summary><div class="rule-choices">${this._entities.lights.map(l=>`<label class="check-row"><input type="checkbox" data-queue-light="${esc(l.entity_id)}" ${q.settings.lights.includes(l.entity_id)?'checked':''}>${esc(l.name)}</label>`).join('')}</div></details>`:''}</details>
      <div class="rule-actions"><button class="stop-button" data-action="save-queue">${t.saveQueue}</button><button class="secondary-button" data-action="cancel-queue">${t.cancel}</button></div></section>`:''}
      <div class="queue-list">${this._settings.queues.length?this._settings.queues.map(item=>`<article class="motion-rule" data-queue-row="${esc(item.id)}"><div><h3>${esc(item.name)}</h3><p>${item.effects.length} ${t.effectMode.toLowerCase()} · ${item.mode==='random'?t.random:t.sequence} · ${item.advance==='motion'?t.onMotion:`${item.gap_min}–${item.gap_max}s`}</p></div><div class="rule-actions"><button class="secondary-button" data-start-queue="${esc(item.id)}">${icon('mdi:play')}${t.startQueue}</button><button class="text-button" data-edit-queue="${esc(item.id)}">${t.edit}</button><button class="text-button" data-remove-queue="${esc(item.id)}">${t.remove}</button></div></article>`).join(''):`<div class="empty" ${q?'hidden':''}><h3>${t.noQueues}</h3><p>${t.noQueuesHelp}</p></div>`}</div>`;
    this._renderStatus();this._restoreView(view,{focus,scroll});
  }

  async _ensureBrowserStation() {
    await this._audioContext();
    if(!this._browserId){const result=await this._hass.callWS({type:'boocue/browser_ready'});this._browserId=result.station_id;}
    this._renderStatus();return this._browserId;
  }

  _updateDuck() {
    if(!this._sources)return;
    const effect=this._status.channels?.effect,mood=this._sources.get('mood');
    for(const [channel,audio] of this._sources){
      const factor=channel==='mood'&&effect?.playing&&effect.output==='browser'&&this._sources.has('effect')?(effect.duck_mood??this._settings.duck_mood??.35):1;
      const value=(audio.volume??this._runtime(channel==='mood'?'mood':'effect').volume)*factor;
      if(audio.gain.gain.setTargetAtTime)audio.gain.gain.setTargetAtTime(value,this._context.currentTime,.05);else audio.gain.gain.value=value;
    }
  }

  async _receiveBrowserRun(channel,state) {
    if(this._settings.enabled===false)return;
    if(this._receiving.get(channel)===state.run_id)return;
    this._receiving.set(channel,state.run_id);
    const generation=this._generations[channel]||0;
    try{
      await this._audioContext();const buffer=await this._buffer(state.effect_id);
      if(this._receiving.get(channel)!==state.run_id||generation!==(this._generations[channel]||0)||this._status.channels?.[channel]?.run_id!==state.run_id||!this._status.channels[channel].playing||this._sources.has(channel))return;
      const elapsed=(Date.now()/1000+this._clockOffset-state.start_at)*state.speed;
      if(!state.repeat&&elapsed>=state.duration)return;
      const source=this._context.createBufferSource(),gain=this._context.createGain();
      const volume=state.volume??this._runtime(channel).volume;
      gain.gain.value=volume;gain.connect(this._context.destination);source.buffer=buffer;source.connect(gain);source.playbackRate.value=state.speed;source.loop=state.repeat;
      this._sources.set(channel,{source,gain,run_id:state.run_id,id:state.effect_id,volume});
      source.onended=()=>{if(this._sources.get(channel)?.source===source){source.disconnect();gain.disconnect();this._sources.delete(channel);this._renderStatus();}};
      const wait=Math.max(0,state.start_at-(Date.now()/1000+this._clockOffset)),offset=Math.max(0,elapsed)%buffer.duration;
      source.start(this._context.currentTime+wait,offset);this._renderStatus();
    }catch(err){this._message(String(err.message||this.t.soundError),true);try{if(state.queue_run_id)await this._hass.callWS({type:'boocue/queue',action:'stop',run_id:state.queue_run_id});else await this._hass.callWS({type:'boocue/stop',channel,run_id:state.run_id});}catch{}}
    finally{if(this._receiving.get(channel)===state.run_id)this._receiving.delete(channel);}
  }

  async _startQueue(id) {
    if(this._settings.enabled===false){this._message(this.t.enableFirst,true);return;}
    const queue=this._settings.queues.find(q=>q.id===id);if(!queue||this._pending.has('queue'))return;
    this._pending.add('queue');
    const generation=this._queueGeneration=(this._queueGeneration||0)+1;
    try{
      const needsBrowser=queue.effects.some(eid=>({...this._settings,...queue.settings,...this._settings.effect_routes[eid]}).output==='browser');
      if(needsBrowser)await this._ensureBrowserStation();
      if(generation!==this._queueGeneration)return;
      const state=await this._hass.callWS({type:'boocue/queue',action:'start',queue_id:id,browser_id:needsBrowser?this._browserId:undefined});
      if(generation!==this._queueGeneration){await this._hass.callWS({type:'boocue/queue',action:'stop',run_id:state.run_id});return;}
      this._status.queue=state;
    }catch(err){this._message(String(err.message||err),true);}
    finally{if(generation===this._queueGeneration)this._pending.delete('queue');this._renderStatus();}
  }

  _onInput(event) {
    const target = event.target;
    if(target.dataset.queueField&&target.type!=='checkbox'&&target.tagName!=='SELECT'){const k=target.dataset.queueField;this._queueDraft[k]=['gap_min','gap_max'].includes(k)?Number(target.value):target.value;}
    if(target.dataset.queuePercent)this._queueDraft.settings[target.dataset.queuePercent]=Number(target.value)/100;
    if(target.dataset.rulePercent)this._ruleDraft[target.dataset.rulePercent]=Number(target.value)/100;
    if(target.dataset.ruleField&&target.type!=='checkbox'&&target.tagName!=='SELECT'){const key=target.dataset.ruleField;this._ruleDraft[key]=['cooldown','volume','brightness'].includes(key)?Number(target.value):target.value;}
    if(target.dataset.routeVolume)target.nextElementSibling.textContent=`${Math.round(Number(target.value)*100)}%`;
    if (target.id === 'effect-search') { this._query = target.value; this._renderEffects(); }
    else if (target.id === 'light-search') { this._lightQuery = target.value; this._renderLights(); }
    else if (target.type === 'range' && target.dataset.setting) {
      this._runtime()[target.dataset.setting] = Number(target.value);
      this.shadowRoot.getElementById(`${target.id}-value`).textContent = `${Math.round(Number(target.value) * 100)}%`;
      if(target.id==='volume'){const audio=this._sources.get(this._mode);if(audio){audio.volume=Number(target.value);this._updateDuck();}}
    }
  }

  async _onChange(event) {
    const target = event.target;
    if(target.dataset.duck){this._runtime().duck_mood=Number(target.value)/100;this._save();this._updateDuck();
    }else if(target.dataset.queueField){const k=target.dataset.queueField;this._queueDraft[k]=target.type==='checkbox'?target.checked:['gap_min','gap_max'].includes(k)?Number(target.value):target.value;if(k==='advance')this._renderQueues();
    }else if(target.dataset.queueInherit){this._queueDraft.settings=target.checked?{}:Object.fromEntries(RUNTIME_KEYS.map(k=>[k,structuredClone(this._settings[k])]));this._renderQueues();
    }else if(target.dataset.queueRuntime){this._queueDraft.settings[target.dataset.queueRuntime]=target.value;this._renderQueues();
    }else if(target.dataset.queuePercent){this._queueDraft.settings[target.dataset.queuePercent]=Number(target.value)/100;
    }else if(target.dataset.queueLight){const a=this._queueDraft.settings.lights;this._queueDraft.settings.lights=target.checked?[...new Set([...a,target.dataset.queueLight])].slice(0,32):a.filter(id=>id!==target.dataset.queueLight);
    }else if(target.dataset.ruleSensor){const a=this._ruleDraft.sensors;this._ruleDraft.sensors=target.checked?[...new Set([...a,target.dataset.ruleSensor])].slice(0,16):a.filter(id=>id!==target.dataset.ruleSensor);this._ruleDraft.sensor=this._ruleDraft.sensors[0]||'';this._renderAutomatic();
    }else if(target.dataset.speakerScope) {
      const scope=target.dataset.speakerScope;
      const object=scope==='stage'?this._runtime():scope==='rule'?this._ruleDraft:scope==='queue'?this._queueDraft.settings:this._settings.effect_routes[scope.slice(6)];
      object.speakers=target.checked?[...new Set([...object.speakers,target.value])].slice(0,16):object.speakers.filter(p=>p!==target.value);
      const picker=target.closest('.speaker-picker');picker.querySelector('summary').textContent=object.speakers.length?`${object.speakers.length} ${this.t.speakerCount}`:this.t.emptySelection;
      if(scope.startsWith('route:')){const summary=target.closest('.route-editor').querySelector('summary');summary.innerHTML=`${icon('mdi:speaker-multiple')}${object.speakers.length} ${this.t.speakerCount}`;}
      if(!['rule','queue'].includes(scope))this._save();
    } else if(target.dataset.routeMode) {
      const id=target.dataset.routeMode;
      if(target.value==='default')delete this._settings.effect_routes[id];
      else this._settings.effect_routes[id]={...(this._settings.effect_routes[id]||{speakers:[...this._settings.speakers],volume:this._settings.volume}),output:target.value};
      await this._save();this._renderEffects();
      this.shadowRoot.querySelector(`[data-effect="${CSS.escape(id)}"] .route-editor`).open=true;
    } else if(target.dataset.routeVolume) {this._settings.effect_routes[target.dataset.routeVolume].volume=Number(target.value);target.nextElementSibling.textContent=`${Math.round(Number(target.value)*100)}%`;this._save();
    } else if(target.dataset.action==='arm'){this._settings.automatic_enabled=target.checked;await this._save();this._renderStatus();
    } else if(target.dataset.ruleEnabled){this._settings.motion_rules.find(r=>r.id===target.dataset.ruleEnabled).enabled=target.checked;await this._save();this._renderStatus();
    } else if(target.dataset.rulePercent){this._ruleDraft[target.dataset.rulePercent]=Number(target.value)/100;
    } else if(target.dataset.ruleField){const key=target.dataset.ruleField;this._ruleDraft[key]=target.type==='checkbox'?target.checked:['cooldown','volume','brightness'].includes(key)?Number(target.value):target.value;if(['output','action'].includes(key))this._renderAutomatic();
    } else if(target.dataset.ruleEffect){this._ruleDraft.effects=target.checked?[...new Set([...this._ruleDraft.effects,target.dataset.ruleEffect])]:this._ruleDraft.effects.filter(id=>id!==target.dataset.ruleEffect);
    } else if(target.dataset.ruleLight){this._ruleDraft.lights=target.checked?[...new Set([...this._ruleDraft.lights,target.dataset.ruleLight])].slice(0,32):this._ruleDraft.lights.filter(id=>id!==target.dataset.ruleLight);
    } else if (target.dataset.light) {
      this._runtime().lights = target.checked ? [...new Set([...this._runtime().lights, target.dataset.light])].slice(0,32) : this._runtime().lights.filter(x => x !== target.dataset.light);
      this._renderLights(); this._save();
    } else if (target.dataset.setting) {
      const key = target.dataset.setting;
      this._runtime()[key] = target.type === 'checkbox' ? target.checked : ['speed','offset_ms','interval_ms','volume','brightness'].includes(key) ? Number(target.value) : target.value;
      this._save();
      if(key==='output'){this.shadowRoot.getElementById('stage-speakers').hidden=target.value!=='speakers';this._renderLights();}
    } else if (target.id === 'pack-file' && target.files?.[0]) {
      const button = this.shadowRoot.querySelector('[data-action="import"]');
      button.disabled = true; button.textContent = this.t.importing;
      try {
        const data = new FormData(); data.append('file', target.files[0]);
        const response = await this._hass.fetchWithAuth('/api/boocue/import', {method:'POST', body:data});
        const result = await response.json();
        if (!response.ok) throw new Error(result.message || `HTTP ${response.status}`);
        await this._load(); this._message(`${result.imported} ${this.t.imported}`);
      } catch (err) { this._message(String(err.message || err), true); }
      finally { if (button.isConnected) { button.disabled = false; button.textContent = this.t.import; } }
    }
  }
}

if (!customElements.get('boocue-panel')) customElements.define('boocue-panel', BooCuePanel);
