# Effect packs

Times in BooCue's own format are explicitly **seconds**. `hue` is 0–360, `saturation` and `brightness` are 0–1. `transition` is seconds and is scaled with playback speed. Every cue represents a target light state; BooCue does not interpolate frames itself because the lamp integration handles supported transitions.

```json
{
  "version": 1,
  "id": "my-spooky-pack",
  "title": "My spooky pack",
  "effects": [
    {
      "id": "my-ghost",
      "title": "My ghost",
      "description": "A cold little apparition.",
      "category": "effects",
      "duration": 4.0,
      "audio": "audio/ghost.wav",
      "icon": "mdi:ghost",
      "source": "My own recording",
      "cues": [
        {"at": 0, "hue": 220, "saturation": 0.5, "brightness": 0.1, "transition": 0},
        {"at": 1, "hue": 230, "saturation": 0.2, "brightness": 0.8, "transition": 0.2},
        {"at": 3, "hue": 230, "saturation": 0.5, "brightness": 0, "transition": 0.8}
      ]
    }
  ]
}
```

Include the referenced audio file in the ZIP. WAV, MP3, OGG, FLAC and M4A file names are accepted; the playback device must support the encoded format. Use PCM WAV or standard MP3 for broad compatibility. Keep `duration` equal to the intended audible cycle length. A browser preview will report a decode failure if the audio is invalid.

IDs must match `[a-z0-9][a-z0-9_-]{0,79}` and must not overlap any installed effect. Categories are `effects` or `moods`. Cues must be ordered by `at` and fall between zero and the effect duration; equal-time cues resolve to the latest due row. Each effect needs at least one cue and supports at most 10,000 cues. Effects may be 0.1–1,800 seconds long, transitions 0–30 seconds.

Package only recordings and definitions you want to install locally or are entitled to distribute. Imported content is stored outside the integration directory; deleting the integration's code does not delete your packs.
