---
name: pr0ta-sync
description: "PR0TA audio-visual sync and production planning — cue sheets, visual-first vs narration-first strategy, continuous audio generation, the narration timeline API (26 endpoints), and montage best practices. Read BEFORE any multi-asset production (trailers, reels, documentaries, ads, explainers, music videos). Also read when planning timing, building a cue sheet, deciding between visual-first and narration-first pipelines, working with the narration timeline API, or re-transcribing after audio changes. This skill covers the planning and strategy layer — if you are about to generate multiple assets without a timing plan, stop and read this first."
---

# Audio-Visual Synchronization & Production Planning

> **This is the strategy layer.** Cue sheets, pipeline choice (visual-first vs narration-first), the narration timeline API, and montage rules live here. **Execution — clip assembly, Ken Burns, ducking, crossfades, dimension normalization, preview, render — lives on the post-production timeline. Read `pr0ta-timeline` for the execution surface.**
>
> **Before you finalize a cut, read `pr0ta-editorial`.** Sync gets you a technically aligned edit; editorial decides whether the edit should ship. Never deliver without running through the editorial discipline pass.

This reference covers the strategy for producing synchronized multi-asset productions (short films, trailers, reels, ads, documentaries) where visuals, narration, music, and sound effects must align temporally.

## The Division of Labor

PR0TA productions now have three clearly scoped skills:

| Skill | Role | When |
|-------|------|------|
| **`pr0ta-sync`** (this file) | Strategy. *What* to generate, in *what order*, with *what timing plan.* | Before any generation. |
| **`pr0ta-editorial`** | Judgment. *What* to cut, *where* to cut, *when* the cut is done. | Before and after every edit pass. |
| **`pr0ta-timeline`** | Execution. Clip CRUD, Ken Burns, audio mix, preview, snapshots, render. | Every edit, every hand-off, every render. |

If you are writing a cue sheet or choosing between visual-first and narration-first, you are in this skill. If you are adding a clip to a timeline or setting a Ken Burns preset, you are in `pr0ta-timeline`. If you are deciding whether a cut lands, you are in `pr0ta-editorial`. Most productions need all three, in that order.

## The Problem

Each PR0TA generation (image, video, audio, music) is an isolated API call with no inherent temporal relationship to other assets. If you generate 6 video clips, a narration per clip, and 6 music segments, you get 18 assets with no shared timeline. Assembly will sound choppy (hard audio cuts between clips) and narration will drift from the visuals it describes.

The fix is structural, not mechanical: plan the temporal contract before generating anything, then use the narration timeline + post-production timeline to execute.

## Strategy Overview

1. **Cue Sheet** — Build a structured timing plan before any generation.
2. **Generate the timeline anchor first** — Visual-first or narration-first depending on production type (see below).
3. **Continuous Audio Generation** — Generate music and narration as long continuous pieces, not per-scene clips.
4. **Point SFX** — Short sound effects for specific hit points.
5. **Time-index every audio-bearing asset (hard gate — two paths).** Every speech-bearing asset (TTS narration, dialogue clips, music with vocals, video with `sound: "on"`) must be transcribed with Scribe V2 via `POST /api/audio/transcription/start`. Every instrumental music asset (score bed, underscore, stinger) must go through `POST /api/v2/projects/{project_id}/music/analyze` for beat/downbeat/transient anchors. Scribe V2 does not detect musical beats; the music analysis endpoint does not transcribe words. Pick the right path per asset. This is non-negotiable — see `pr0ta-audio` → "Mandatory Time-Indexing Rule (Two Paths)" and "Music Analysis API" for the full policy.
6. **Build on the Timeline** — Add clips (only transcribed assets are eligible for audio-bearing clips), set Ken Burns, configure audio mix, preview, snapshot, hand off.

### Two Pipeline Strategies

**Visual-First (default for action/VFX-driven content):** Generate all images and video clips first, add them to the post-production timeline, then generate audio (narration + music) timed to the actual visuals. Best when precise visual timing matters more than narration pacing.

**Narration-First (recommended for documentaries, video essays, voice-driven content):** Generate all narration first — actual audio durations determine the entire edit timeline. Build cuts in the **narration timeline API** with transcript anchors, verify alignment, then **materialize to the post-production timeline** and continue editing there. Best when the voice track is the primary content and visuals are illustrative.

## The Narration Timeline API — The Preferred Narration-First Path

For narration-first productions, the **narration timeline API** replaces manual timing maps with a persistent, structured, server-side timeline. It stores transcript word-level timing, visual assets with content affinity tags, a cut list with transcript anchors and editorial rationale, and alignment verification.

See `pr0ta-api` → "Narration Timeline API" for the full endpoint reference (26 endpoints).

**Workflow:**

1. **Generate narration** — ElevenLabs TTS via `POST /api/v2/projects/{id}/generate` (see `pr0ta-audio`).
2. **Transcribe** — `POST /api/audio/transcription/start` with `asset_id` and `project_id`. **Scribe V2 is the preferred transcription provider** — it returns speaker IDs, audio events (laughter, applause), and per-word `event_type`. Whisper is still available as a fallback but is not recommended for narration-timeline work. Both are exposed via the audio-to-text modality (see `pr0ta-audio`). The transcript layer auto-populates in the narration timeline with word-level timestamps, sentence boundaries, and paragraph boundaries.
3. **Review transcript** — `GET /narration-timeline/transcript` to verify word timing. Query specific ranges: `GET /transcript/words?from=44.0&to=52.0`.
4. **Tag transcript segments** — `PUT /narration-timeline/transcript/tags` with content labels (e.g. `market_size`, `franchise_model`). These labels bridge narration to visuals.
5. **Generate visuals** — Images and video clips via the generation API. Duration ≥ each narration segment.
6. **Register assets** — `POST /narration-timeline/assets` with `affinity_tags` matching your content labels. Query unused matches: `GET /assets?affinity=market_size&status=unused`. Or use the suggestion engine: `GET /assets/suggest?transcript_range=44.0-52.0`.
7. **Build cut list** — `POST /narration-timeline/cuts` for each narration segment. Each cut records: position, timing, asset reference, transcript anchor (word indices), rationale, Ken Burns motion, and transition. The system auto-tracks asset usage (prevents repetition) and auto-denormalizes anchor text for audit trails.
8. **Verify alignment** — `GET /narration-timeline/verify`. This is the **quality gate**: returns per-cut drift, gaps, overlaps, misalignment flags. Fix flagged cuts with `PATCH /cuts/{cut_id}`, reflow with `POST /cuts/reflow`, re-verify.
9. **Configure audio layers** — `PUT /narration-timeline/config` with narration_offset, pre_roll_duration, frame_rate, resolution.
10. **Snapshot** — `POST /narration-timeline/snapshot` before making changes. `GET /snapshot/{name}/diff` to compare versions. `POST /snapshot/{name}/restore` to roll back.
11. **Materialize to the post-production timeline** — `POST /narration-timeline/materialize-to-post-production`. This converts verified cuts into post-production clips with stable IDs, preserves transcript anchor provenance under `metadataOverrides.origin`, converts narration motion into `kenBurns` metadata, creates narration and music audio clips, and writes narration offset and ducking intent into `timeline.audioMix`. **After materialization, all further editing happens on the post-production timeline — see `pr0ta-timeline`.**

**Key advantages of this path:**

- No custom build scripts — the timeline is the build plan.
- Transcript anchors make misalignment visible and auditable.
- Incremental edits — `PATCH` one cut, `reflow`, re-verify, re-materialize. No rebuild.
- Asset usage tracking prevents accidental image repetition.
- Alignment verification catches drift before the user sees the video.
- Snapshots replace version directories.
- Materialization is a one-way handoff to the NLE — the narration timeline's job is done once the post-production timeline exists.

**If the narration timeline is throwing errors** — misalignment on cuts you know are correct, materialization failures, verification flags that don't make sense — file a bug with platform engineering. The narration + post-production timelines are the supported production path. If they have gaps, we fix the platform rather than route around them.

## Step 1: Build the Cue Sheet

Before any generation API call, create a cue sheet — a structured document that defines the temporal contract for the entire production. This is the single source of truth.

### Cue Sheet Format

```json
{
  "title": "Product Launch Trailer",
  "total_target_duration": 30.0,
  "scenes": [
    {
      "id": "scene_01",
      "description": "Opening wide shot -- dawn over city skyline",
      "target_duration": 5.0,
      "actual_duration": null,
      "markers": [
        { "id": "M1", "time": 0.0, "label": "picture_start" },
        { "id": "M2", "time": 2.5, "label": "title_reveal", "sfx": "whoosh_rise" }
      ],
      "narration": {
        "text": "In a world moving faster than ever...",
        "target_start": 0.5,
        "target_end": 4.5
      }
    },
    {
      "id": "scene_02",
      "description": "Medium shot -- protagonist at desk, looks up",
      "target_duration": 5.0,
      "actual_duration": null,
      "markers": [
        { "id": "M3", "time": 5.0, "label": "cut_to_medium" },
        { "id": "M4", "time": 8.0, "label": "hero_turns", "sfx": "paper_rustle" }
      ],
      "narration": {
        "text": "One team decided to build something different.",
        "target_start": 5.5,
        "target_end": 9.5
      }
    }
  ],
  "music": {
    "style": "Cinematic orchestral, modern hybrid",
    "arc": "Quiet tension 0-10s, building momentum 10-20s, triumphant peak at 20s, resolving warmth 25-30s",
    "total_duration": 30.0
  },
  "sfx": [
    { "marker": "M2", "description": "Rising whoosh transition", "duration": 1.5 },
    { "marker": "M4", "description": "Subtle paper rustle", "duration": 0.8 }
  ]
}
```

### Key Rules

- Every scene gets a `target_duration` and an `actual_duration` (filled in after video generation via the platform's asset metadata).
- Markers define key moments with absolute timestamps from the start of the production.
- Narration text is mapped to time windows with `target_start` and `target_end`.
- Music gets an arc description with timestamps that reference markers or absolute times.
- SFX are point events tied to specific markers.

### Building the Cue Sheet

When the user describes a creative vision:

1. Break the vision into discrete scenes (typically 3–10 for a 30–60s piece).
2. Assign target durations based on content density — fast-paced action gets shorter scenes, emotional beats get longer ones.
3. Identify key moments that need sync — reveals, impacts, transitions, dialogue beats.
4. Write all narration text and map it to time windows.
5. Describe the music arc across the full duration.
6. List any SFX with their trigger points.

Present the cue sheet to the user for approval before generating anything. Timing changes are cheap at this stage and expensive after generation.

**The cut plan precedes asset generation — this ordering is non-negotiable for narration-driven productions.** Always: write the cut plan first (anchor word, target start, target duration, intended visual content per beat) → then generate the assets to match → then place. Never the reverse. If you generate first and place after, editorial decisions become "where can I fit this animation?" — the wrong question. The right question is "what visual does the narration call for here?" The answer might be an asset you haven't generated yet, a fan-out variant, or a script change. See `pr0ta-editorial` for why generating-to-fill is an anti-pattern.

**If the narration audio is regenerated for any reason — re-record, new voice, script edit — re-transcribe before doing anything else.** Run `POST /api/audio/transcription/start` with Scribe V2 and rebuild word-level timing values and marks from the fresh transcript. Even small drifts (200-400ms across re-records of the same script) propagate through the entire timeline and look like random cut placement on playback. Do not reuse old timestamps on new audio.

## Step 2: Visual-First Generation (when visuals lead)

### Why Visuals First

Video durations from Kling and Seedance are approximate — a 10s request might yield 9.8s or 10.2s. Music and narration durations from ElevenLabs are more predictable but still not frame-exact. By generating visuals first and adding them to the post-production timeline, the platform measures and normalizes them for you; audio can then conform to the locked visual track.

This mirrors professional post-production: lock picture, then score to picture.

### Process

All generation steps should use the **reliability contract** from the `pr0ta-api` skill, which handles task polling, asset correlation, and download fallbacks automatically.

1. Generate all key frame images (Nano Banana 2) via batch if possible. Use asset-listing fallback for completion detection (image events are unreliable).
2. Generate all video clips with target durations from the cue sheet. **Seedance 2.0 Omni** and **Kling V3/O3 with multi-shot** are co-equal alternatives — choose based on the shot's needs (see `pr0ta-video` for the model selection guide). Video generation can take up to 20 minutes on busy days — the reliability contract polls for up to 1200s.
3. Add clips to the post-production timeline via `POST /timeline/clips` with Ken Burns presets and placement. The platform handles dimension normalization and FPS consistency.
4. Use `GET /timeline/clips` to read the actual durations the platform measured for each clip.
5. Update the cue sheet: replace `target_duration` with `actual_duration` per scene.
6. Recalculate marker timestamps if needed for audio cue planning.
7. Generate narration and music against the now-locked visual track.

## Step 3: Continuous Audio Generation

**The single biggest quality improvement is generating fewer, longer audio pieces instead of many short ones.**

### Music: One Piece for the Full Sequence

Instead of generating separate music clips per scene, generate one continuous piece that covers the entire production duration.

**Why:**
- No seams between scenes — the music flows naturally.
- The AI can create a coherent arc (build, peak, resolve) across the full duration.
- Mood transitions happen musically rather than as hard cuts.
- The result sounds like a composed score, not a playlist of loops.

**How:**

After the visual track is laid down, calculate the total production length from the timeline. Then generate one music piece:

```json
{
  "generator": "music",
  "mode": "txt_to_music",
  "model": "music-v1",
  "prompt": "Cinematic orchestral score. Gentle piano and strings 0-10s. Building momentum with percussion entering at 10s. Triumphant brass peak at 22s. Warm resolution with piano returning 26-32s. Modern hybrid film score feel.",
  "duration": 32
}
```

Include temporal cues in the prompt referencing actual timestamps from the updated cue sheet. The music model responds well to time-based arc descriptions.

If the total duration exceeds the music generator's max duration, generate 2–3 overlapping sections with 3–5 seconds of overlap. Add them as separate clips on the timeline and let the platform render crossfades at the overlap points — `pr0ta-timeline` → "Transitions".

### Narration: Fewest Possible Takes

Group all narration into the fewest possible TTS calls. Ideally one call per voice/character.

**Why:**
- Consistent pacing, tone, and prosody across the whole narration.
- Natural breath and rhythm between sentences.
- No tonal discontinuities between clips.
- The voice "performs" the full text as a coherent read.

**How:**

**Voice selection:** Before generating narration, use `GET https://api.elevenlabs.io/v2/voices` (direct ElevenLabs endpoint, requires `xi-api-key` header) to discover available voices. Cache the voice list for ~10 minutes and refresh on `404 voice_id` errors. See the `pr0ta-audio` skill for the voice discovery workflow.

Concatenate all narration text in scene order with appropriate pause indicators:

```json
{
  "generator": "audio",
  "mode": "txt_to_speech",
  "model": "eleven_v3",
  "text": "In a world moving faster than ever... [pause] One team decided to build something different. [pause] They asked a simple question. [pause] What if creation had no limits?",
  "voice_id": "JBFqnCBsd6RMkjVDRZzb",
  "speed": 0.95
}
```

Use `[pause]`, `...`, or paragraph breaks to create natural gaps between scene narrations. A slightly slower speed (0.9–0.95) often gives a more cinematic feel. For rich emotional delivery, use audio tags throughout — `[reflective]`, `[building intensity]`, `[awe]`, `[whispers]`, etc. **See `pr0ta-audio` → "Audio Tags & Emotion Control" for the full tag reference and dialogue/narration writing techniques.**

After generation, **transcribe with Scribe V2** via the audio-to-text modality to get word-level timestamps. These become the anchors in the narration timeline API (Step 2 of the narration-first workflow above).

**ElevenLabs text limit:** 5000 characters per call. If narration exceeds this, split at natural paragraph boundaries and add both clips to the timeline — the platform will crossfade them.

### Sound Effects: Individual Point Events

SFX are the exception to the "generate long" rule. They're short, punchy, and placed at specific markers.

Generate each SFX as a separate music/audio call with a short duration:

```json
{
  "generator": "music",
  "mode": "txt_to_music",
  "model": "music-v1",
  "prompt": "Rising cinematic whoosh transition sound effect, building energy, 1.5 seconds",
  "duration": 2
}
```

Or for more realistic/foley-style effects, describe them precisely. Keep durations short (1–5 seconds). Add them to an SFX audio track on the post-production timeline aligned to their marker timestamps.

## Step 4: Build on the Post-Production Timeline

This is where planning ends and execution begins. All assembly — clip placement, Ken Burns motion, audio mix (ducking, narration offset, volume), crossfades, dissolves, preview, snapshot, render — happens on the post-production timeline.

**Read `pr0ta-timeline` for the complete API reference and workflow.** The summary:

1. **Create separate audio tracks first** via `POST /timeline/tracks` — at minimum `dialogue`, `music`, and `sfx`. Concurrent audio on the same track is invalid; the renderer will reject overlapping clips on a single track.
2. **Add visual clips** via `POST /timeline/clips` with Ken Burns presets on the `video` track.
3. **Add audio clips** — narration clips on `dialogue`, music clips on `music`, SFX on `sfx` — with the right start times. Never stack concurrent audio on one track.
4. **Configure audio mix** via `POST /timeline` — ducking, narration offset, per-clip volume.
5. **Check the mix** — escalate from cheapest to most expensive: `GET /audio/analyze` (instant approximate diagnostic) → `GET /audio/meter` (actual LUFS/LRA/true-peak if loudness spec matters) → `GET /preview/audio` (listen to audio-only `.wav`) → `GET /preview` (full picture+sound) only when needed.
6. **Snapshot** before major passes: `POST /timeline/snapshot`.
7. **Hand off to the user** for browser-based review at `app.pr0ta.com/timeline`.
8. **Read back** the updated state with `GET /timeline/state`, address remaining notes.
9. **Final export** via `POST /export` when the cut is locked. Use `POST /render` for preview-task rendering during iteration.

The platform handles: Ken Burns rendering (super-resolution, FPS consistency, duration-aware formulas), audio ducking (gain automation), crossfades and dissolves (overlay playlists), dimension normalization, persistent edit state. You send presets and configs — the platform does the rest.

## Narration Offset — Set Once on the Timeline

Every narration-driven production needs a few seconds of visual lead-in before narration starts — title card, ambient establish, mood-setting shot. On the post-production timeline, this is a single field:

```json
{ "audioMix": { "narration_offset_ms": 2500 } }
```

Set it with `POST /timeline`. The platform applies the offset when laying down the narration track against the visuals. No coordinate-space bookkeeping, no hand-conversion functions, no debug sessions chasing an off-by-2.5s cut.

If you built the cut list in the narration timeline API, `POST /narration-timeline/materialize-to-post-production` writes `narration_offset_ms` into `timeline.audioMix` for you, carrying forward whatever offset you configured in `PUT /narration-timeline/config`.

## Music Ducking — A Timeline Property

Ducking music under narration is a single configuration on the timeline:

```json
{
  "audioMix": {
    "ducking": [
      {
        "sourceTrack": "music",
        "keyTrack": "dialogue",
        "duckedGain": 0.15,
        "attackMs": 200,
        "releaseMs": 500
      }
    ]
  }
}
```

`duckedGain` is the fraction of nominal source-track volume while the key track is active: `1.0` = no ducking, `0.5` ≈ −6 dB, `0.0` = full mute. (`threshold` is a deprecated alias still accepted by the backend.)

**Ducking levels by content type:**

- **Voice-driven content (documentaries, video essays, explainers):** `duckedGain: 0.08–0.10`. Even 0.20 is too hot — the voice must dominate.
- **Cinematic/action content:** `duckedGain: 0.25–0.40`. The score carries more emotional weight in these formats.
- **Music-only sections (no narration):** Full music volume (no key track active).

The platform applies ducking as animated gain envelopes on the music clips. See `pr0ta-timeline` → "Audio Mix" for the full schema.

## Montage Best Practices

For productions that intercut still images and video clips (common in documentaries, social media, and explainers):

- **Still images should not linger more than 3–4 seconds.** Generate many images and cut between them to maintain visual energy.
- **Intercut video clips into still-image montages** to add motion and hold attention. Even a single 5–10s video clip between stills dramatically improves engagement.
- **Alternate Ken Burns directions** across adjacent shots: `push_in` → `pull_back`, `drift_left` → `drift_right`, `push_in` → `hold`. Repeating the same direction reads as monotonous. See `pr0ta-timeline` → "Ken Burns as a Clip Property" for the preset list.
- **Flash cards use `hold` or `zoom_in_extreme`** — never a slow preset. A flash card needs to land.
- **Never use boomerang (forward-then-reverse) to extend video clips.** It reads as repetitive and cheap. Gentle slow-motion (down to ~70% speed) is acceptable and often looks cinematic.
- **Prefer fewer, longer video generations** over many short clips. A single 15s multi-prompt generation is more visually consistent than three 5s clips. See `pr0ta-video` for multi-prompt and duration guidance — this is especially true for Kling V3/O3 multi-shot, which can pack up to six camera cuts into one generation with shared character and scene continuity.
- **For narration-driven montages:** Build cuts in the narration timeline API against transcript anchors (name drops, year drops, emotional pivots). Materialize, then tune pacing on the post-production timeline.

## Title Cards — Generate with the Model, Not with Text Filters

**AI-generated title cards look dramatically better than overlaid text filters**, even for simple typography. The mild inefficiency of a generation call is more than repaid in visual quality. This is confirmed user feedback across multiple productions.

**Use this pattern:**

1. Generate the title card as a **scene image** via Nano Banana 2 with proper typographic language. See the "Title Card" and "Flash Card Recipe" sections in the `pr0ta-image` skill.
2. Add it to the timeline as a clip with the `hold` Ken Burns preset (or `push_in_fast` for a subtle reveal).
3. Never reach for a text-overlay filter as the primary title mechanism.

**When a text overlay is acceptable:** Debugging/scratch previews before the real title card is generated. Non-delivered working files. Lower-thirds that must update programmatically per-scene (rare).

**When it is NOT acceptable:** Any delivered title card, chapter break, or flash card. Any full-frame typographic moment. Anything the viewer will hold on for more than half a second.

## Editorial Discipline — See `pr0ta-editorial`

Editorial judgment is a first-class discipline with its own skill. This file covers the strategy side — cue sheets, pipeline choice, narration timeline workflow, continuous audio, montage best practices. `pr0ta-timeline` covers the execution side. **For the judgment side — story spine, the rewrite loop, beat-keyed cutting as a discipline, no-reuse / no-time-stretch / no-filler, kill-your-darlings, the self-critique protocol, ship criteria, and the uncompromising-quality stance — read `pr0ta-editorial` before shipping any cut.**

## Assembly QC Checklist

Before delivering any assembled video from the post-production timeline, run through this checklist.

### Pre-Render Checks

- [ ] Every visual clip in the timeline has an intended Ken Burns preset (`hold` is a valid choice but should be deliberate).
- [ ] Narration offset is set correctly in `timeline.audioMix` (typically 2.0–2.5s).
- [ ] Ducking config matches content type (voice-driven: 0.08–0.10; cinematic: 0.25–0.40).
- [ ] No accidentally-repeated visual clips — verify with `GET /timeline/clips` and scan for duplicate asset IDs.
- [ ] All visual clips have matching aspect ratios (the platform normalizes, but mismatched source aspect ratios can produce unintended letterboxing).
- [ ] Snapshot created before the final export pass: `POST /timeline/snapshot`.

### Preview Verification

- [ ] Preview the first 10 seconds: intro pacing, title card timing, narration lead-in, music fade-in.
- [ ] Preview every transition point: `GET /preview?from={t-2}&to={t+2}&quality=low` around each cut. Watch for abrupt motion direction changes or audio pops.
- [ ] Preview the last 10 seconds: ending beat, credits, music resolution. The tail must not be a silent black frame from an uncovered narration.
- [ ] Preview any frame-critical cut — name drop, year drop, emotional pivot — and verify the right visual is on screen during the right word. This catches off-by-one cut errors that audio sync alone will miss.

### Post-Render Verification

- [ ] Watch the full render end-to-end. Don't just spot-check.
- [ ] Listen for narration drift from visuals in the second half of longer pieces.
- [ ] Verify file size and codec meet the target platform's spec (e.g. TikTok max 287.6 MB, H.264, AAC).
- [ ] Re-read any AI-generated title/credit cards for typos. Vision models are bad at catching their own typography errors.

## Quick Reference: The Six Principles

1. **Plan before you generate.** Build the cue sheet first. Timing changes are cheap at planning stage and expensive after generation.
2. **Pick your anchor up front.** Visual-first for action/VFX content. Narration-first for voice-driven content.
3. **Use the narration timeline API for narration-first work.** Transcript anchors, alignment verification, asset usage tracking, snapshots. Materialize to the post-production timeline when verified.
4. **Generate fewer, longer audio pieces.** One continuous music score. One narration take per voice. Kling multi-shot over three separate generations.
5. **Execute on the post-production timeline.** Clip CRUD, Ken Burns as presets, audio mix as metadata, preview as the verification gate, snapshots before major passes. See `pr0ta-timeline`.
6. **Read `pr0ta-editorial` before you ship.** Sync gets you a technically aligned edit. Editorial decides whether it should ship.

## Cross-References

- `pr0ta-timeline` — Post-production timeline execution (clip CRUD, Ken Burns, audio mix, preview, snapshots, render).
- `pr0ta-editorial` — Editorial judgment (story spine, cutting discipline, ship criteria).
- `pr0ta-api` → "Narration Timeline API" — Full endpoint reference for the narration timeline (26 endpoints).
- `pr0ta-audio` — ElevenLabs TTS, voice discovery, Scribe V2 transcription, music generation.
- `pr0ta-video` — Seedance 2.0 Omni and Kling V3/O3 multi-shot for video generation.
- `pr0ta-image` — Nano Banana 2 for stills, title cards, and flash cards.
- `pr0ta-consistency` — Multi-shot character and style continuity across generations.
