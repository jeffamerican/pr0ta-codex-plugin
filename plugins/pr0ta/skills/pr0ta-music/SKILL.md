---
name: pr0ta-music
description: "PR0TA music and sound effect generation via ElevenLabs Music — background scores, soundtracks, ambient beds, point SFX, and foley. Covers TOS-compliant prompt writing (no artist names), the composition workspace for structured multi-section scores, output format selection, and music analysis for beat-keyed editing. Read when generating background music, scoring a video, creating sound effects or foley, composing audio for any production, or writing music prompts. Also read when you need to understand music-specific API parameters or TOS restrictions that cause prompt rejections."
---

# Music Generator Reference

> **See also:** For placing music in a production timeline with proper ducking, crossfades, and cue-sheet-driven timing, read `pr0ta-sync`. For editorial judgment on whether the score serves the story, read `pr0ta-editorial`. **After generating instrumental music, time-index it** via `POST /api/v2/projects/{project_id}/music/analyze` (Path B of the mandatory time-indexing rule) before adding it to the timeline — see `pr0ta-audio` → "Mandatory Time-Indexing Rule".

## Overview

The Music Generator uses **ElevenLabs Music** to compose original music tracks, sound effects, and soundscapes from text prompts. It handles two distinct production needs:

- **Scores and beds** — continuous background music that runs under narration or video. Typically 30-120 seconds. Generated once, placed on a dedicated `music` track, ducked under dialogue.
- **Point SFX and foley** — short isolated sounds (whooshes, impacts, ambient textures, UI sounds) placed at specific cue-sheet timestamps. Typically 1-10 seconds.

The distinction matters because scores need emotional arc descriptions and duration planning, while SFX need precise sound-design language and short durations.

## API Quick Reference

Music and sound effect generation uses the unified generation endpoint:

```bash
curl -X POST "https://app.pr0ta.com/api/v2/projects/{project_id}/generate" \
  -H "Authorization: Bearer $PR0TA_PAT" \
  -H "Content-Type: application/json" \
  -d '{
    "generator": "music",
    "mode": "txt_to_music",
    "model_id": "elevenlabs/music",
    "prompt": "Tense orchestral underscore with low cello drones and sparse pizzicato strings, building slowly over 45 seconds to a crescendo with timpani rolls",
    "duration": 45,
    "output_format": "mp3_44100_192"
  }'
```

**Key parameters:**

| Parameter | Description | Default |
|-----------|-------------|---------|
| `prompt` | Text description of the music | Required |
| `duration` | Target length in seconds | 30 |
| `model_id` | `"elevenlabs/music"` | Default |
| `output_format` | `mp3_44100_192`, `pcm_44100`, or legacy `"mp3"` | `mp3_44100_192` |

See `pr0ta-api` for the full request/response schema, task polling, and error handling.

## Writing Effective Music Prompts

The prompt is the only creative input — there are no reference images or style transfers for music. A good prompt specifies five things:

1. **Genre and style** — "cinematic orchestral", "lo-fi hip-hop", "ambient electronic", "jazz trio"
2. **Instruments** — name them: "cello, piano, brushed snare, synth pad" not "various instruments"
3. **Energy and mood** — "tense and building", "warm and reflective", "high-energy and driving"
4. **Progression** — describe the arc: "starts sparse with solo piano, strings enter at the midpoint, builds to a full orchestral crescendo in the final quarter"
5. **Production quality** — "warm analog tone", "clean digital production", "lo-fi with vinyl crackle"

**Prompt examples by use case:**

**Score — documentary underscore:**
> "Contemplative ambient score with warm analog synth pads, slow evolving textures, gentle piano arpeggios entering at the midpoint, and a gradual swell of low strings toward the end. Minimal percussion. Introspective and hopeful. 60 seconds."

**Score — trailer:**
> "Epic cinematic trailer music building from a single sustained cello note through layered strings, brass stabs, and taiko drum hits to a massive orchestral crescendo with choir. Dark to triumphant arc. 45 seconds."

**Point SFX — transition whoosh:**
> "Short cinematic whoosh transition sound, 1 second, metallic with reverb tail, left-to-right pan feeling"

**Point SFX — ambient texture:**
> "Gentle rain on a window with distant thunder rumbles, cozy indoor ambience, 10 seconds, loopable"

## Music Prompt Restrictions (TOS)

ElevenLabs Music rejects prompts containing artist or band name references — this is a TOS violation, not a soft preference. The rejection is immediate and non-negotiable.

```
❌ REJECTED: "Ólafur Arnalds meets Hans Zimmer — ambient piano with cinematic strings"
❌ REJECTED: "in the style of Radiohead — atmospheric electronic"
❌ REJECTED: "Billie Eilish-inspired dark pop with breathy vocals"

✅ WORKS: "Ambient electronic with ethereal piano, deep cinematic bass, orchestral strings building to a climax"
✅ WORKS: "Dark atmospheric pop with breathy female vocals, sparse reverb-heavy production"
✅ WORKS: "Minimalist neo-classical piano with granular synthesis textures and slow string swells"
```

The fix is always the same: describe the *sound* you want (instruments, production techniques, mood, energy) rather than the *artist* you want it to sound like. Genre descriptors, instrument names, and production vocabulary are all safe.

## Music Composition Workspace

For longer or structurally complex pieces, the composition workspace lets you plan before generating:

- **Section durations** — break a 90-second score into intro (8s), verse (24s), build (16s), chorus (24s), bridge (12s), outro (6s)
- **Beat markers** — set tempo and key signature per section
- **Lyrical cues** — anchor vocal melodies or rhythmic patterns to specific bars
- **Iteration** — adjust structure and re-generate without starting from scratch

This is particularly useful for scores that need to hit specific cue-sheet timestamps — plan the sections to align with your scene changes, then generate.

## Time-Indexing Generated Music

Every instrumental music asset must be time-indexed before it can enter the timeline. The correct endpoint for music is `POST /api/v2/projects/{project_id}/music/analyze` (Path B of the mandatory time-indexing rule). This produces:

- `editorial_anchors` — key structural moments useful for cut points
- `downbeat_times` — beat-aligned timestamps for beat-keyed editing
- `beat_times`, `transients[]` — raw timing data
- `tempo_bpm`, `beat_confidence` — metadata

Scribe V2 transcription (Path A) is for speech — it does not produce beat or downbeat data and should not be used for instrumental music.

## Integration with the Production Pipeline

1. **Plan the music arc in your cue sheet** — decide duration, emotional progression, and where the score should peak relative to the video. See `pr0ta-sync`.
2. **Generate one continuous piece** covering the full production when possible. One 90-second generation with a described arc produces better results than three 30-second pieces stitched together.
3. **Time-index immediately** after generation via music/analyze.
4. **Place on a dedicated `music` track** — never on the same track as narration or dialogue. Concurrent audio on the same track is invalid and the renderer rejects it. Create the track first with `POST /timeline/tracks`. See `pr0ta-timeline`.
5. **Configure ducking** — set the timeline's `duckedGain` property so the music dips under dialogue automatically. See `pr0ta-timeline` → "Audio Mix".
6. **Check balance** — use `GET /audio/analyze` to verify music-vs-narration levels before rendering a full preview.
7. **Point SFX** go on a separate `sfx` track, each aligned to its cue-sheet timestamp.
