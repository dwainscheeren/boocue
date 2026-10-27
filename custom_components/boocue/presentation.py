"""Original editorial descriptions and MDI choices, without imported media."""

# id: (expected title, icon, English description, Dutch description)
PRESENTATIONS = {
    'thunder-roll': ('Thunder roll', 'weather-lightning', 'A low rumble with cold flashes.', 'Een lage donderroffel met koude lichtflitsen.'),
    'ghost-wind': ('Ghost wind', 'weather-windy', 'A whispering wind and slow violet light.', 'Fluisterende wind met langzaam paars licht.'),
    'heartbeat': ('Heartbeat', 'heart-pulse', 'A double heartbeat in deep red.', 'Een dubbele hartslag in dieprood licht.'),
    'haunted-bells': ('Haunted bells', 'bell-ring-outline', 'Uneasy chimes with little pools of color.', 'Onheilspellende belletjes met kleine kleuraccenten.'),
    'creaking-door': ('Creaking door', 'door-open', 'A door opens into a green glow.', 'Een krakende deur opent in een groene gloed.'),
    'footsteps': ('Footsteps', 'shoe-print', 'Someone is getting closer.', 'Voetstappen komen steeds dichterbij.'),
    'electric-flicker': ('Electric flicker', 'lightning-bolt-outline', 'An old neon light refuses to settle.', 'Een oude neonlamp knettert en flikkert.'),
    'campfire': ('Campfire', 'campfire', 'Warm crackles and a gentle amber shimmer.', 'Een knapperend vuur met een warme amberkleurige gloed.'),
    'hh-fx1': ('Thunder', 'weather-lightning', 'A sudden clap of thunder.', 'Een plotselinge donderslag.'),
    'hh-fx2': ('Stairs', 'stairs', 'Footsteps on a creaking staircase.', 'Voetstappen op een krakende trap.'),
    'hh-fx3': ('Ghost', 'ghost-outline', 'A ghostly cry breaks the silence.', 'Een spookachtige kreet doorbreekt de stilte.'),
    'hh-fx4': ('Witch', 'magic-staff', 'A witch lets out a wicked cackle.', 'Een heks laat een gemene lach horen.'),
    'hh-fx5': ('Floating spirit', 'weather-windy', 'An eerie spirit drifts past.', 'Een onheilspellende geest zweeft voorbij.'),
    'hh-fx6': ('Thunderstorm', 'weather-lightning-rainy', 'Rolling thunder in a gathering storm.', 'Rommelende donder tijdens een dreigende storm.'),
    'hh-fx7': ('Whispering girl', 'account-voice', 'A girl whispers an unsettling message.', 'Een meisje fluistert een onheilspellende boodschap.'),
    'hh-fx8': ('Thriller', 'music-note', 'A dramatic burst of suspense.', 'Een dramatisch geluid vol spanning.'),
    'hh-fx9': ('Squeaking floor', 'floor-plan', 'Floorboards squeak under unseen feet.', 'Vloerplanken piepen onder onzichtbare voeten.'),
    'hh-fx10': ('Horror organ', 'piano', 'An ominous organ phrase.', 'Een onheilspellende melodie op een orgel.'),
    'hh-fx11': ('Flickering neon', 'lightbulb-fluorescent-tube', 'An electrical buzz with erratic crackles.', 'Elektrisch gezoem met onregelmatig geknetter.'),
    'hh-fx12': ('Countdown', 'timer-sand', 'A countdown builds the anticipation.', 'Een aftelling bouwt de spanning op.'),
    'hh-fx13': ('Creaking floor', 'floor-plan', 'Old wooden floorboards groan.', 'Oude houten vloerplanken kraken.'),
    'hh-fx14': ('Impact neuro', 'waveform', 'A sharp, unsettling impact.', 'Een scherpe, onheilspellende klap.'),
    'hh-fx15': ('Growl short', 'paw', 'A brief, threatening growl.', 'Een korte, dreigende grom.'),
    'hh-fx16': ('Midnight clock', 'clock-outline', 'A clock tolls at midnight.', 'Een klok slaat middernacht.'),
    'hh-fx17': ('Impact cinematic', 'movie-open-outline', 'A dramatic cinematic hit.', 'Een zware, filmische dreun.'),
    'hh-fx18': ('Beasts roar', 'paw', 'A beast unleashes a deep roar.', 'Een beest laat een diepe brul horen.'),
    'hh-fx19': ('Golem stomp', 'foot-print', 'Heavy footsteps from a lumbering creature.', 'Zware voetstappen van een log wezen.'),
    'hh-fx20': ('Scream echo', 'surround-sound', 'A scream trails into an echo.', 'Een schreeuw sterft weg in een echo.'),
    'hh-fx21': ('Heartbeat', 'heart-pulse', 'A tense, pulsing heartbeat.', 'Een gespannen, bonzende hartslag.'),
    'hh-fx22': ('Monster eating', 'silverware-fork-knife', 'A monster noisily devours its meal.', 'Een monster verorbert luidruchtig zijn maaltijd.'),
    'hh-fx23': ('Worst nightmare', 'sleep-off', 'A brief burst of nightmare sounds.', 'Een korte uitbarsting van nachtmerriegeluiden.'),
    'hh-fx24': ('Violins', 'violin', 'Tense strings create a chilling sting.', 'Gespannen strijkers zorgen voor een ijzingwekkend accent.'),
    'hh-fx25': ('Woosh', 'weather-windy', 'A rush of air sweeps past.', 'Een luchtstroom suist voorbij.'),
    'hh-fx26': ('Knocking', 'gesture-tap', 'Someone knocks from the other side.', 'Er klopt iemand aan de andere kant.'),
    'hh-fx27': ('Zombie', 'account-injury', 'An undead creature groans.', 'Een ondood wezen kreunt.'),
    'hh-fx28': ('Signal', 'broadcast', 'A mysterious signal cuts through.', 'Een mysterieus signaal klinkt.'),
    'hh-fx29': ('Witch 2', 'magic-staff', 'Another wicked witch sound.', 'Een tweede onheilspellend heksengeluid.'),
    'hh-fx30': ('Werewoolf', 'weather-night', 'A werewolf howls into the night.', 'Een weerwolf huilt in de nacht.'),
    'hh-fx31': ('Cat', 'cat', 'A cat breaks the silence.', 'Een kat doorbreekt de stilte.'),
    'hh-fx32': ('Door', 'door-open', 'A door moves with an ominous creak.', 'Een deur beweegt met onheilspellend gekraak.'),
    'hh-fx33': ('Kid spirit giggles', 'emoticon-lol-outline', 'A childlike spirit giggles nearby.', 'Een kinderlijke geest giechelt dichtbij.'),
    'hh-fx34': ('Breathing monster', 'lungs', 'A creature breathes heavily nearby.', 'Een wezen ademt zwaar in de buurt.'),
    'hh-fx35': ('Impact nightmare', 'waveform', 'A dark impact jolts the scene.', 'Een duistere klap zorgt voor een schrikmoment.'),
    'hh-fx36': ('Scream', 'bullhorn-outline', 'A sudden piercing scream.', 'Een plotselinge, doordringende schreeuw.'),
    'hh-fx37': ('Panicky breathing', 'lungs', 'Fast, frightened breathing.', 'Snelle, angstige ademhaling.'),
    'hh-fx38': ('Creature scream', 'paw-outline', 'An inhuman creature cries out.', 'Een onmenselijk wezen slaakt een kreet.'),
    'hh-fx39': ('Eerie', 'ear-hearing', 'An eerie sound builds unease.', 'Een griezelig geluid zorgt voor onrust.'),
    'hh-fx40': ('Spirit forest', 'forest', 'Ghostly sounds from a haunted forest.', 'Spookachtige geluiden uit een betoverd bos.'),
    'hh-fx41': ('Impact gong', 'circle-double', 'A resonant gong-like strike.', 'Een diepe slag die als een gong nagalmt.'),
    'hh-fx42': ('Halloween organ', 'piano', 'A spooky Halloween organ phrase.', 'Een griezelige Halloweenmelodie op een orgel.'),
    'hh-fx43': ('Rustling radio', 'radio', 'Radio static rustles and crackles.', 'Radioruis ruist en knettert.'),
    'hh-fx44': ('Spirit voices', 'account-voice', 'Ghostly voices call from the dark.', 'Spookachtige stemmen klinken uit het donker.'),
    'hh-fx45': ('Goblin laugh', 'emoticon-devil-outline', 'A mischievous goblin laugh.', 'Een ondeugende goblin lacht.'),
    'hh-fx46': ('Impact sweep', 'waveform', 'A sweeping sound ends in an impact.', 'Een aanzwellend geluid eindigt in een klap.'),
    'hh-fx47': ('Roar short', 'paw', 'A short, powerful roar.', 'Een korte, krachtige brul.'),
    'hh-fx48': ('I can see you', 'eye-outline', 'An ominous voice calls out.', 'Een onheilspellende stem laat zich horen.'),
    'hh-mood100': ('Drops', 'water', 'Water droplets echo in the background.', 'Waterdruppels echoën op de achtergrond.'),
    'hh-mood200': ('Frog forrest', 'forest', 'Frogs call through a forest soundscape.', 'Kikkers kwaken in een bosachtige omgeving.'),
    'hh-mood300': ('Horror sounds', 'grave-stone', 'A continuous bed of unsettling sounds.', 'Een doorlopende achtergrond van griezelige geluiden.'),
    'hh-mood400': ('Spooky piano', 'piano', 'An eerie piano sets the atmosphere.', 'Een griezelige piano zet de sfeer.'),
    'hh-mood500': ('Whispering', 'account-voice', 'Quiet whispers fill the background.', 'Zachte fluisterstemmen vullen de achtergrond.'),
    'hh-mood600': ('Critters', 'bug-outline', 'Small creatures rustle in the dark.', 'Kleine beestjes ritselen in het donker.'),
    'hh-mood700': ('Forest', 'pine-tree', 'A forest soundscape surrounds the room.', 'Bosgeluiden omringen de kamer.'),
    'hh-mood800': ('Rain', 'weather-rainy', 'Steady rainfall in the background.', 'Aanhoudende regen op de achtergrond.'),
    'hh-mood900': ('ominousMusic', 'music-clef-bass', 'Dark music sustains the suspense.', 'Duistere muziek houdt de spanning vast.'),
    'hh-mood1000': ('Bat cave', 'bat', 'Bats stir inside a shadowy cave.', 'Vleermuizen bewegen in een donkere grot.'),
    'hh-mood1100': ('Distorted piano', 'piano', 'Warped piano tones unsettle the room.', 'Vervormde pianoklanken maken de sfeer onrustig.'),
    'hh-mood1200': ('Halloween bells', 'bell-outline', 'Haunting bells ring in the background.', 'Spookachtige bellen klinken op de achtergrond.'),
}

LEGACY_DESCRIPTION = 'Imported locally · BooCue light routing'


def presentation_for(effect_id, title, description, icon):
    """Enrich known titles while respecting user-authored descriptions/icons."""
    row = PRESENTATIONS.get(effect_id)
    if not row or row[0] != title:
        return {'description': description, 'icon': icon}
    _, chosen_icon, english, dutch = row
    if description not in {'', LEGACY_DESCRIPTION, english}:
        return {'description': description, 'icon': icon}
    return {'description': english, 'descriptions': {'en': english, 'nl': dutch},
            'icon': 'mdi:' + chosen_icon if icon in {'mdi:ghost', 'mdi:weather-night', 'mdi:' + chosen_icon} else icon}
