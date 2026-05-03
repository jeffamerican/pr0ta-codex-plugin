---
name: pr0ta-audio
description: "PR0TA audio workflows for TTS, voice cloning/design, speech-to-speech, transcription, and mandatory time-indexing before timeline editing. Read when generating or analyzing narration, dialogue, voice, or any speech-bearing asset."
---

# Audio Generator Reference

> **See also:** For narration-first pipeline strategy, cue sheets, and the narration timeline API, read `pr0ta-sync`. For post-production assembly, read `pr0ta-timeline`. Narration timing drives the entire edit in voice-driven content.

## Mandatory Time-Indexing Rule (Two Paths)

**Every audio-bearing asset in a PR0TA production must be time-indexed before it enters editing. No exceptions.** "Time-indexed" means the asset has a time-aligned anchor stream the editor can snap to. There are two paths, and they are **not interchangeable** — Scribe V2 is a speech model and does not detect beats or downbeats; the music analysis endpoint is a music model and does not transcribe words.

### Path A — Speech (transcription with Scribe V2)

Use this path for any asset that contains **human speech**:

- **TTS narration and dialogue** generated through the Audio Generator (Gemini Flash TTS by default; ElevenLabs v3 fallback).
- **Music with vocals** — treat as speech; Scribe V2 will transcribe the lyrics and return word-level timing.
- **Video assets with `sound: "on"`** containing native dialogue or ambient speech. `POST /api/v2/projects/{project_id}/transcribe` now accepts video directly (it derives an audio asset under the hood); for narration-timeline auto-population use `POST /api/audio/transcription/start`.
- **Uploaded audio** — any user-provided narration, interview recording, or field audio.
- **Uploaded video with audio** — any user-provided clip with a dialogue or ambient-speech track.

**Endpoint:** `POST /api/audio/transcription/start` with `model_id: "fal-ai/elevenlabs/speech-to-text/scribe-v2"` (preferred for narration-timeline work — it auto-populates the transcript layer), or `POST /api/v2/projects/{project_id}/transcribe` for standalone transcription. See "Audio-to-Text (Transcription) API" below.

**Output:** word-level timing, speaker IDs, per-word `event_type`, and speech-adjacent audio events (breaths, laughter, applause, speaker_change).

### Path B — Instrumental music (music analysis)

Use this path for any asset that is **instrumental music with no speech**:

- Score beds, underscore, stingers, themes.
- Instrumental stems from a larger production.
- Any music asset whose cut beats come from tempo, not words.

**Endpoint:** `POST /api/v2/projects/{project_id}/music/analyze` — see "Music Analysis API" below.

**Output:** `music_analysis.editorial_anchors` (normalized beat-like anchor stream, the `whisper_index` analogue for music), `downbeat_times[]`, `beat_times[]`, `transients[]`, `tempo_bpm`, `beat_confidence`. Persisted on the asset under `music_analysis`, `music_analysis_options`, `music_analysis_summary`.

### The hard gate

**Time-indexing is a hard gate before editing.** An asset that has not been indexed by the correct endpoint is **not available to the editor** — do not add it to the post-production timeline, do not reference it in a cut list, do not select it for an edit pass. Block the workflow until its indexing task succeeds.

**Why this is mandatory:**

- **Word-level cuts require word-level timing.** Beat-keyed editing on speech (see `pr0ta-editorial` → "Beat-Keyed Cutting") cuts on the consonant onset of key words. Without a transcription, the editor has no coordinates for that.
- **Trim bounds need speech/silence detection.** Scribe V2's per-word `event_type` classification identifies breaths, laughter, fillers, and silence — the natural places to trim in and out of a clip.
- **Dialogue matching depends on speaker IDs.** Multi-speaker scenes need Scribe V2's automatic diarization to route lines to the right speaker track on the timeline.
- **Music cuts need beat anchors.** For instrumental music, the music analysis endpoint returns downbeats, beats, and transients that become cut-beat anchors. Scribe V2 does not produce these — it is not a music model.
- **Narration timelines won't populate without transcription.** `POST /api/audio/transcription/start` auto-populates the narration timeline's transcript layer. Skipping this means you have no narration timeline at all.

**How to enforce it:**

1. After every generation, route the asset to the correct indexing endpoint:
   - **Speech (TTS, dialogue clips, music with vocals, video with sound) → Path A** — `POST /api/audio/transcription/start` with `model_id: "fal-ai/elevenlabs/speech-to-text/scribe-v2"`.
   - **Instrumental music → Path B** — `POST /api/v2/projects/{project_id}/music/analyze` with the asset ID.
2. Poll the indexing task to completion alongside the generation's own reliability contract. Do not mark the asset "ready for editing" in `assets.json` until its indexing task has reached `succeeded`.
3. Confirm the time-indexed data exists:
   - **Path A:** `GET /api/v2/projects/{project_id}/assets/{asset_id}/transcription` returns `status: "ready"` with populated `words[]`.
   - **Path B:** `GET /api/v2/projects/{project_id}/music/analyze/{asset_id}` returns `analysis.editorial_anchors` populated.
4. Only then add the asset to the post-production timeline.

**No asset bypasses this rule, even for "quick" edits or "just a B-roll shot."** If it has speech, it gets transcribed. If it is instrumental music, it gets analyzed. If the indexing fails, fix the failure — do not edit around it.

**Note on SFX and short point hits:** Sound effects that are single-point hits (under ~1 second, played once at a marker) do not require indexing — they are placed by marker time. SFX beds, ambient beds, and any longer SFX asset that will be trimmed or cut against should go through Path B if they are music-like, or Path A if they contain speech.

> **When to use PR0TA TTS vs native video audio:**
> - **Non-English dialogue:** Use PR0TA TTS — native video audio is unreliable for non-English speech. Generate video with `sound: "off"` and layer TTS in post.
> - **Narration over footage (any language):** Use PR0TA TTS — gives you precise voice/language/pacing control independent of the video.
> - **English dialogue with visible speaker:** Use native video audio (`sound: "on"` in the video generation) for lip sync — see the `pr0ta-video` skill.

**Agent option available:** Text-to-speech generation can be done through MCP `generation_submit` with `generator=audio`, `mode=txt_to_speech`. REST `POST /api/v2/projects/{project_id}/generate` remains the fallback for scripts and endpoints not exposed through MCP. The default TTS model is **Gemini 3.1 Flash TTS** (`fal-ai/gemini-3.1-flash-tts`). Use **ElevenLabs v3** (`eleven_v3`) as the fallback when Gemini is unavailable, when the user requires a specific ElevenLabs `voice_id`, or when an existing workflow depends on Eleven v3 audio tags. Gemini supports `style_instructions`, multi-speaker via `speakers`, `language_code`, and `temperature`. Use `models_get_defaults` or `GET /api/crew/model_defaults?model_id=fal-ai/gemini-3.1-flash-tts` for the full parameter list. See the `pr0ta-api` skill for the full request schema.

## Modes

### 1. VOICE DESIGN
Create custom voice profiles for text-to-speech.

**Key parameters:** character name, voice characteristics description (max 1000 characters), sample line for preview (max 500 characters), and model selection.

### 2. TXT TO SPEECH -- **GEMINI FLASH TTS**
Convert text to natural speech using Gemini 3.1 Flash TTS.

**Default model: Gemini 3.1 Flash TTS**

**Key parameters:** prompt/text (max 5000 characters), model selection (`fal-ai/gemini-3.1-flash-tts`), optional Gemini voice, `style_instructions`, `language_code`, `temperature`, and `speakers` for multi-speaker dialogue.

### 3. VOICE CHANGE
Transform an existing audio recording to a different voice. The API equivalent is Speech-to-Speech (STS) — see "Voice V2 API" section below for the programmatic route (`POST /voices/sts`).


## Gemini Flash TTS Prompting

Use Gemini Flash TTS first for new narration and dialogue. Gemini responds best when the delivery plan is explicit and separated from the spoken transcript.

**Recommended prompt structure:**

```text
AUDIO PROFILE
Warm documentary narrator, close-mic studio recording, natural conversational delivery, no music, no sound effects.

SCENE
This is a 45-second social-video voiceover explaining a scientific concept to a curious general audience.

DIRECTOR'S NOTES
Pace around 145 words per minute. Keep authority without sounding like an announcer. Pause briefly after the opening sentence. Lightly emphasize the named concepts, but do not overact.

TRANSCRIPT
The actual words to speak go here.
```

**Prompting rules:**

- Put tone, pace, accent, emotion, mic feel, and audience context in `style_instructions` or the prompt's director notes; keep the transcript readable.
- For narration, include an audio profile and scene context before the transcript. Do not rely on punctuation alone for pacing.
- For dialogue, label lines with speaker names and make the names exactly match the `speakers` configuration.
- Use inline expressive tags sparingly for human reactions or delivery beats, such as `[laughs]`, `[softly]`, or `[pause]`. Do not overload every sentence with tags.
- For long narration, split on paragraph or scene boundaries and reuse the same audio profile/director notes across chunks.
- Verify the rendered take by listening and by transcription. Regenerate if names, acronyms, years, or emphasis land incorrectly.

## Voice Discovery API

Use ElevenLabs voice discovery when the user chooses the ElevenLabs v3 fallback or needs a specific ElevenLabs cloned/generated voice. Before generating ElevenLabs TTS, discover available voices using the ElevenLabs V2 voice listing endpoint directly:

```
GET https://api.elevenlabs.io/v2/voices
```

Requires `xi-api-key` header. Supports pagination (`next_page_token`, `page_size` up to 100), search (`search`), sorting (`sort`: `created_at_unix` or `name`, `sort_direction`: `asc`/`desc`), and filtering (`voice_type`: `personal`/`community`/`default`/`workspace`/`non-default`, `category`: `premade`/`cloned`/`generated`/`professional`).

**V3 compatibility — try-and-fallback, not hard gating:**
- Do **not** derive or expose a `supports_v3` boolean from this endpoint.
- Do **not** treat `high_quality_base_model_ids` or `verified_languages[].model_id` as a hard compatibility gate for `eleven_v3`.
- Instead: attempt TTS with `model_id: "eleven_v3"` and a valid `voice_id`. If it fails, fall back to `eleven_multilingual_v2`.
- This approach is more reliable than metadata-based gating because ElevenLabs may update v3 support for voices without changing their metadata fields.

**Caching:** Cache the voice list for a short TTL (recommended: 10 minutes). Refresh the cache on `404 voice_id` errors — this handles cases where voices are added or removed between cache refreshes.

**Example usage in an ElevenLabs fallback workflow:**
1. Call `GET https://api.elevenlabs.io/v2/voices?page_size=50&category=premade` to browse voices
2. Present voice options to the user (each entry has `voice_id`, `name`, `labels`, `preview_url`)
3. Use the selected `voice_id` in the PR0TA generation request with `model: "eleven_v3"`
4. If the ElevenLabs v3 generation fails with a model-compatibility error, retry with `model: "eleven_multilingual_v2"`

## Voice V2 API — Clone, Design, and Speech-to-Speech

The V2 voice endpoints extend the audio pipeline beyond simple TTS. All routes are project-scoped under `/api/v2/projects/{project_id}/voices/...` and require authenticated access.

### Decision tree — which route to use

Pick the route based on what the user has and what they need:

1. **User has clean sample recordings → voice clone.** `POST /voices/clone` with `sample_asset_ids[]` or `sample_urls[]`. Returns a reusable `voice_id` directly (synchronous, no task polling). The new voice is immediately available for TTS generation.

2. **User has only a written description of the voice they want → prompt voice design (two steps).** First, `POST /voices/design` with `voice_description` and a `model_id` (prefer `eleven_voice_design_prompt`). This returns `previews[]` — each preview has a `generated_voice_id` and `audio_base64` for playback. The user auditions them. Then, `POST /voices/design/commit` with the chosen `generated_voice_id` and a `voice_name`. This creates the permanent, reusable `voice_id`.

3. **User wants to transform an existing spoken recording into a different voice → speech-to-speech (STS).** `POST /voices/sts` with `target_voice_id` and either `source_audio_asset_id` or `source_audio_url`. Model: `eleven_multilingual_sts_v2`. Returns the output audio URL directly. STS preserves the timing, intonation, and emotion of the source performance — only the voice identity changes.

### Model discovery update

`GET /api/v2/models?generator=audio` now returns models for all audio modalities. New mode hints: `voice_design` (for the design route) and `voice_to_voice` (for STS), alongside the existing `txt_to_speech`.

### When to use STS vs re-generating TTS

- **STS wins when** the performance matters more than the text — the actor nailed the timing, breath, and emotion, and you just want a different voice on top.
- **Re-generate TTS when** you're changing the text, speed, or delivery style — STS can't change what's said, only who says it.

### Limitations to know

- Prompt voice design is always two-step (design → commit). No single-call shortcut.
- Voice clone is synchronous — large sample sets may mean longer response times.
- STS is audio-to-audio only on the v2 surface. Video voice-change uses older internal routes.
- Cloned/designed voices are not automatically registered as project Characters for Seedance workflows — update the character registry manually if needed.

**Full endpoint contracts** (request/response shapes for all four routes, model-ID table, field details): Read `pr0ta-api/reference/voice-v2.md`.

## ElevenLabs v3 Fallback Tags

Use ElevenLabs v3 audio tags only when the user selects the ElevenLabs fallback or when maintaining a legacy ElevenLabs-tagged workflow. Keep Gemini Flash TTS as the first pick for new narration and dialogue.

For the full ElevenLabs tag catalog, examples, punctuation behavior, and constraints, read `reference/elevenlabs-v3-audio-tags.md`.

## MCP TTS Generation (Quick Reference)

The full schema is in `pr0ta-api`, but here's the pattern for generating speech through MCP:

```json
{
  "project_id": "project-uuid-or-slug",
  "request": {
    "generator": "audio",
    "mode": "txt_to_speech",
    "model": "fal-ai/gemini-3.1-flash-tts",
    "text": "AUDIO PROFILE\nWarm documentary narrator, close-mic studio recording, natural conversational delivery.\n\nSCENE\nA 30-second social-video voiceover for a curious general audience.\n\nDIRECTOR NOTES\nPace around 145 words per minute. Pause briefly after the opening sentence. Lightly emphasize the named concepts.\n\nTRANSCRIPT\nThe city had changed since I last saw it, but then again, so had I.",
    "voice": "Kore",
    "style_instructions": "Warm, reflective, measured, never announcer-like.",
    "language_code": "en-US"
  }
}
```

Poll the returned task with `tasks_get`.

## REST TTS Generation (Fallback)

Use REST/curl only when MCP is unavailable, for high-volume scripts, or for endpoints not yet exposed through MCP.

```bash
# 1. Generate speech with Gemini Flash TTS
curl -X POST "https://app.pr0ta.com/api/v2/projects/$PROJECT_ID/generate" \
  -H "Authorization: Bearer $PAT" \
  -H "Content-Type: application/json" \
  -d '{
    "generator": "audio",
    "mode": "txt_to_speech",
    "model": "fal-ai/gemini-3.1-flash-tts",
    "text": "AUDIO PROFILE\nWarm documentary narrator, close-mic studio recording, natural conversational delivery.\n\nSCENE\nA 30-second social-video voiceover for a curious general audience.\n\nDIRECTOR NOTES\nPace around 145 words per minute. Pause briefly after the opening sentence. Lightly emphasize the named concepts.\n\nTRANSCRIPT\nThe city had changed since I last saw it, but then again, so had I.",
    "voice": "Kore",
    "style_instructions": "Warm, reflective, measured, never announcer-like.",
    "language_code": "en-US"
  }'

# 2. Poll for completion — returns task_id
# Task result now includes asset_id directly: result.asset_id
# Use the reliability contract from pr0ta-api to poll and download
```

**TTS Parameters:**

| Parameter | Type | Default | Notes |
|-----------|------|---------|-------|
| `text` | string | required | Max 5000 characters per call |
| `model` | string | `fal-ai/gemini-3.1-flash-tts` | Default TTS model. Use `eleven_v3` as fallback. |
| `voice` | string | optional | Gemini prebuilt voice name. |
| `style_instructions` | string | optional | Tone, pace, accent, emotion, and delivery notes. |
| `language_code` | string | optional | Locale hint such as `en-US` or `fr-FR`. |
| `speakers` | array | optional | Multi-speaker voice config; speaker names must match transcript labels. |
| `voice_id` | string | optional | ElevenLabs fallback only; voice profile ID from discovery API. |

**Fallback:** If Gemini Flash TTS is unavailable or the user requires a specific ElevenLabs voice, retry with `model: "eleven_v3"` and an ElevenLabs `voice_id`. If ElevenLabs v3 itself fails with a model-compatibility error, retry with `"eleven_multilingual_v2"`. See the Voice Discovery API section above.

**For non-English TTS:** Prefer Gemini Flash TTS with the transcript written in the target language and `language_code` set when known. Use ElevenLabs v3 fallback only when the user specifically needs an ElevenLabs voice.

## Audio-to-Text (Transcription) API

PR0TA exposes an **audio-to-text modality** with two providers. Transcription is the source of truth for word-level timing, dialogue matching, subtitle generation, and transcript-driven trimming.

### Provider Preference: Scribe V2 is the default for all PR0TA work

**Prefer ElevenLabs Scribe V2 over Whisper for every narration workflow.** Scribe V2 returns richer output than Whisper:

- **Speaker IDs** — automatic diarization, no extra pass.
- **Audio events** — laughter, applause, breaths, and other non-speech events detected as timed entries in the stream.
- **Per-word `event_type`** — every word carries an event classification, useful for cutting on breaths, laughs, or emphasis.
- **Higher word-level accuracy** on narration-style English, especially for enunciated proper nouns and numeric content (years, percentages).

Whisper is still available as a secondary provider for niche cases (Whisper-specific language coverage, reproducing a legacy workflow). It is **not** the recommended path for new productions. If you are building a narration timeline, use Scribe V2.

### Recommended: Transcription Start (with Narration Timeline Auto-Population)

```
POST /api/audio/transcription/start
Authorization: Bearer $PAT
```

```json
{
  "asset_id": "<narration_audio_asset_id>",
  "project_id": "<project_id>",
  "model_id": "fal-ai/elevenlabs/speech-to-text/scribe-v2"
}
```

**Both camelCase and snake_case field names are accepted.** The following are equivalent:
```json
{"assetId": "...", "projectId": "..."}
{"asset_id": "...", "project_id": "..."}
```

**What happens automatically:** When transcription completes, the narration timeline's transcript layer is auto-populated with word-level timestamps, sentence boundaries (by punctuation), and paragraph boundaries (by silence gaps > 0.5s). This is the hook that enables the entire narration-timeline workflow in `pr0ta-sync`.

**Provider selection via `model_id`** (both providers are exposed under the audio-to-text modality):
- **Scribe V2 (preferred — use this by default):** `"model_id": "fal-ai/elevenlabs/speech-to-text/scribe-v2"`
- **Whisper (fallback only):** `"model_id": "fal-ai/whisper"`

If `model_id` is omitted, the provider is determined by the user's `audio_to_text_model` setting (Settings > Tools). Agents building narration timelines should pass `model_id` explicitly to pin Scribe V2 regardless of user defaults.

If auto-population fails (e.g. project doesn't exist yet), transcription still succeeds. Use `POST /api/v2/projects/{id}/narration-timeline/transcript/populate` as a manual fallback. If narration is regenerated, call the populate endpoint again to re-build the transcript layer.

### Retrieving Word-Level Transcription Data

After transcription completes, retrieve word-level timing from the **dedicated transcription endpoint**:

```
GET /api/v2/projects/{project_id}/assets/{asset_id}/transcription
```

Returns `status: "ready"` with `words[]` (flat word-level timing) and `segments[].words[]` (segment-grouped). When using Scribe V2, entries additionally include speaker IDs and per-word `event_type` classifications. This is the **only supported retrieval path.** See `pr0ta-api` for the full response shape.

### Standalone Transcription Route

```
POST /api/v2/projects/{project_id}/transcribe
Authorization: Bearer $PAT
```

Provide **exactly one** input source:

```json
{ "asset_id": "existing-pr0ta-audio-asset-id" }
```
```json
{ "source_url": "https://example.com/audio.wav" }
```
Or multipart form-data: `file=@audio.wav`

### Optional Parameters

```json
{
  "language": "en",
  "diarization": true,
  "timestamp_granularity": "word"
}
```

- `timestamp_granularity`: `"word"` or `"segment"` (not both in one call)
- `diarization`: speaker labels when `true`
- `language`: ISO code; omit for auto-detect

### Response (Async Task)

```json
{
  "task_id": "uuid",
  "status": "queued",
  "asset_id": "target-audio-asset-id",
  "input_kind": "asset|source_url|upload",
  "created_asset": false,
  "download_url": "/api/v2/projects/{project_id}/assets/{asset_id}/download"
}
```

Poll the task until complete (same reliability contract as other generators — see `pr0ta-api`). **Retrieve results from the dedicated transcription endpoint** (`GET /api/v2/projects/{project_id}/assets/{asset_id}/transcription`).

### Batch Mode

```
POST /api/v2/projects/{project_id}/transcribe/batch
```
```json
{
  "asset_ids": ["asset-1", "asset-2"],
  "language": "en",
  "diarization": false,
  "timestamp_granularity": "segment"
}
```

### Behavior Notes

- `asset_id` inputs are project-scoped and validated against the current project.
- `source_url` and uploads are first materialized as PR0TA audio assets, then transcribed through the same pipeline.
- For remote `source_url` assets, transcription uses the original external URL (not a placeholder storage path).
- Do **not** request `timestamp_granularity="both"` — the backend supports one mode per call.

### Recommended Workflow

**For narration-driven productions (preferred):**
1. Generate the narration audio asset.
2. `POST /api/audio/transcription/start` with `asset_id`, `project_id`, and `model_id: "fal-ai/elevenlabs/speech-to-text/scribe-v2"` — this auto-populates the narration timeline's transcript layer with Scribe V2's enriched output.
3. Build the cut list against transcript anchors, verify alignment, and materialize to the post-production timeline via the narration timeline API. See `pr0ta-sync` → "Narration Timeline API" for the full workflow.

**For standalone transcription (subtitles, dialogue matching, trimming):**
1. Generate or identify the audio asset.
2. `POST /transcribe` with `timestamp_granularity: "word"` for sync work, `"segment"` for subtitles/summaries. Pass `model_id: "fal-ai/elevenlabs/speech-to-text/scribe-v2"` to pin Scribe V2.
3. Poll the task until complete.
4. Retrieve word-level data from the dedicated endpoint: `GET /api/v2/projects/{project_id}/assets/{asset_id}/transcription`.
5. Use the `words[]` array for: subtitle SRT generation, sentence-accurate trims, dialogue-to-visual sync, drift detection. With Scribe V2, also leverage speaker IDs for multi-voice dialogue and `event_type` for cutting on breaths or laughs.

Always use the transcription API for word-level timing — it is the only reliable source for the narration timeline and every sync workflow downstream.

## Music Analysis API — Path B

**The music analysis endpoint is the Path B indexing endpoint for instrumental music.** Scribe V2 does not detect musical beats or downbeats; this endpoint does. It is PR0TA's first-party beat detector, persisted as asset metadata the same way transcription is (`music_analysis` on asset metadata; analogous to `whisper_index` for dialogue).

**When to use:** any instrumental music asset (score bed, underscore, stinger) that will drive cut timing. If the asset is speech, use Scribe V2 (Path A) above. If the asset is music, use this endpoint.

**Editorial anchor strategy — pick the right stream:**

1. **Downbeats** (`downbeat_times`, or `editorial_anchors` entries with `kind: "downbeat"`) — large structural cuts, section resets, montage phrase starts, scene transitions.
2. **Beats** (`beat_times`, `kind: "beat"`) — rhythmic cut candidates and cadence snapping within a phrase.
3. **Transients** (`transients[]` with `{time, strength}`) — sharp accents where the beat tracker is too coarse, or where you want an impact hit.
4. **`editorial_anchors`** overall — the normalized, word-like anchor stream for music. Treat as the single unified anchor stream and snap cut points to the nearest anchor the way narration-first workflows snap to words. Direct analogue to `whisper_index` for dialogue.

**Caveats:**
- First-party heuristic detector built on decoded audio plus signal analysis. Best results on instrumental tracks with a stable pulse.
- `downbeat_times` are inferred from beat phase and transient strength — useful for editing, not guaranteed to match musical barlines in complex meter.
- For rubato, ambient, orchestral, or meter-shifting music, fall back from `downbeat_times` to `transients` plus local context.

**Dialogue vs music timing paths:**
- Dialogue: asset → transcription task → `whisper_index` / `words[]`.
- Music: asset → music analysis task → `music_analysis.editorial_anchors`.

The editorial intent is identical — time-aligned anchor streams that downstream skills snap cuts against. Pick the path that matches the asset content.

**Full endpoint contract** (start analysis, get cached analysis, request/response shapes, storage fields): see `pr0ta-api/reference/music-analysis.md`.

## Tips

- **Use the ElevenLabs V2 voice listing** (`GET https://api.elevenlabs.io/v2/voices`) to discover available voices before TTS generation. This is more reliable than hardcoding voice IDs.
- Create voice characters first in the **Voice Design** tab before generating TTS -- this gives you consistent, reusable voices
- The Character dropdown loads available voices -- make sure they're loaded before selecting
- For dialogue, generate each character's lines separately with their specific voice, then combine on the Timeline
- ElevenLabs v3 is an "Alpha" model -- it excels at natural dialogue but may occasionally need regeneration for tricky pronunciations
- Use the Snap toggle for precise trimming aligned to time markers
