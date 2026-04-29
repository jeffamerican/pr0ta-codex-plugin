# Voice V2 API — Reference

Voice discovery (direct ElevenLabs V2 endpoint), plus project-scoped PR0TA endpoints for voice cloning, prompt-based voice design, committing voice-design previews, and speech-to-speech (STS) conversion. Clone/design/STS routes sit under `/api/v2/projects/{project_id}/voices/...` and require authenticated project access.

**For workflow guidance** (when to clone vs design vs STS, decision tree), see `pr0ta-audio` → "Voice V2 — Clone, Design, and Speech-to-Speech".

## Voice Discovery (Direct ElevenLabs V2 Endpoint)

Voice listing now uses the ElevenLabs V2 API directly, not a PR0TA wrapper.

```
GET https://api.elevenlabs.io/v2/voices
```

Requires `xi-api-key` header. Supports pagination (`next_page_token`, `page_size` up to 100), search, sorting, and filtering by `voice_type` and `category`.

### Key query parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `search` | string | Search by name, description, labels, category |
| `page_size` | int | Max 100, default 10 |
| `next_page_token` | string | Pagination token from previous response |
| `sort` | string | `created_at_unix` or `name` |
| `sort_direction` | string | `asc` or `desc` |
| `voice_type` | string | `personal`, `community`, `default`, `workspace`, `non-default` |
| `category` | string | `premade`, `cloned`, `generated`, `professional` |
| `voice_ids` | array | Lookup specific voice IDs (max 100) |

### Response shape

```json
{
  "voices": [
    {
      "voice_id": "JBFqnCBsd6RMkjVDRZzb",
      "name": "Bella",
      "category": "premade",
      "labels": { "accent": "american" },
      "preview_url": "https://...",
      "high_quality_base_model_ids": ["..."],
      "verified_languages": [
        { "language": "en", "model_id": "eleven_v3" }
      ],
      "is_legacy": false,
      "created_at_unix": 1700000000
    }
  ],
  "has_more": true,
  "total_count": 150,
  "next_page_token": "abc123"
}
```

### V3 Compatibility — Try-and-Fallback

**Do not** derive or expose a public `supports_v3` boolean from this endpoint's response.

- Do **not** treat `high_quality_base_model_ids` or `verified_languages[].model_id` as a hard compatibility gate for `eleven_v3`.
- Instead: attempt TTS with `model_id: "eleven_v3"` and a valid `voice_id`. If it fails, fall back to `eleven_multilingual_v2`.
- ElevenLabs may update v3 support for voices without updating metadata fields, so metadata-based gating is unreliable.

## Model Discovery Update

`GET /api/v2/models?generator=audio` now returns models for all audio modalities:

| Model ID | Mode Hint | Purpose |
|----------|-----------|---------|
| `eleven_v3` | `txt_to_speech` | Text-to-speech (existing) |
| `eleven_voice_design_prompt` | `voice_design` | Prompt-based voice design |
| `eleven_ttv_v3` | `voice_design` | Voice design (v3 variant) |
| `eleven_multilingual_ttv_v2` | `voice_design` | Voice design (multilingual) |
| `eleven_multilingual_sts_v2` | `voice_to_voice` | Speech-to-speech conversion |

## 1. Voice Clone

Create a reusable ElevenLabs voice from uploaded or project-scoped audio samples.

```
POST /api/v2/projects/{project_id}/voices/clone
```

### Request

Pass project asset IDs, external URLs, or both:

```json
{
  "name": "Maya Clone",
  "sample_asset_ids": [
    "asset-voice-ref-1",
    "asset-voice-ref-2"
  ],
  "description": "Lead actor voice clone for Maya",
  "remove_background_noise": true,
  "labels": "character=maya,source=casting"
}
```

Alternative with external URLs:

```json
{
  "name": "Maya Clone",
  "sample_urls": [
    "https://example.com/maya_take_1.wav",
    "https://example.com/maya_take_2.wav"
  ]
}
```

### Response

```json
{
  "voice_id": "voice-cloned-1"
}
```

### Notes

- `sample_asset_ids[]` are automatically resolved to absolute PR0TA asset download URLs — no need to pre-resolve.
- This route creates the final reusable voice directly (not a preview). The returned `voice_id` is immediately usable in TTS and STS calls.
- This is a **synchronous** call — it returns the created `voice_id` directly, not an async task.

## 2. Prompt Voice Design

Generate voice previews from a written voice description. This is a two-step flow: generate previews first, then commit the chosen preview into a reusable voice.

```
POST /api/v2/projects/{project_id}/voices/design
```

### Request

With auto-generated preview text:

```json
{
  "voice_description": "Warm, intimate narrator with subtle rasp and natural timing.",
  "model_id": "eleven_voice_design_prompt",
  "auto_generate_text": true
}
```

With explicit preview text:

```json
{
  "voice_description": "Young confident action heroine, slightly breathy, modern American accent.",
  "model_id": "eleven_ttv_v3",
  "text": "I know this looks impossible, but give me thirty seconds and I will get us out."
}
```

### Response

```json
{
  "previews": [
    {
      "generated_voice_id": "generated-1",
      "audio_base64": "ZmFrZQ==",
      "media_type": "audio/mpeg",
      "duration_secs": 4.2,
      "language": "en"
    }
  ],
  "text": "Preview line",
  "task_id": "task-voice-design"
}
```

### Notes

- Returns **preview candidates**, not a final reusable voice. The `generated_voice_id` is ephemeral — you must call the commit route (below) to turn a chosen preview into a persistent voice.
- Supported `model_id` values: `eleven_voice_design_prompt`, `eleven_ttv_v3`, `eleven_multilingual_ttv_v2`.
- The `audio_base64` field contains the preview audio as a base64-encoded audio file. Decode to play back to the user for selection.

## 3. Commit Voice Design Preview

Convert a chosen preview from the design step into a reusable, persistent voice.

```
POST /api/v2/projects/{project_id}/voices/design/commit
```

### Request

```json
{
  "generated_voice_id": "generated-1",
  "voice_name": "Maya Final",
  "voice_description": "Warm, intimate narrator with subtle rasp and natural timing."
}
```

Optional fields:
- `labels` — freeform labels for organization.
- `played_not_selected_voice_ids[]` — IDs of previews the user auditioned but did not select. Used for analytics/recommendation tuning.

### Response

```json
{
  "voice_id": "voice-final-1",
  "name": "Maya Final",
  "result": {
    "voice_id": "voice-final-1"
  }
}
```

The returned `voice_id` is now a permanent, reusable voice — usable in TTS (`voice_id` in `/generate` with `generator=audio`) and as a target in STS calls.

## 4. Speech-to-Speech (STS)

Convert a source audio performance into a target voice. Preserves the timing, intonation, and emotion of the source performance while replacing the voice identity.

```
POST /api/v2/projects/{project_id}/voices/sts
```

### Request

Using a project asset:

```json
{
  "target_voice_id": "voice-target-1",
  "source_audio_asset_id": "asset-audio-1",
  "model_id": "eleven_multilingual_sts_v2",
  "options": {
    "stability": 0.5
  }
}
```

Using a direct URL:

```json
{
  "target_voice_id": "voice-target-1",
  "source_audio_url": "https://example.com/source-performance.wav",
  "model_id": "eleven_multilingual_sts_v2"
}
```

### Response

```json
{
  "url": "https://cdn.example.com/sts-output.mp3"
}
```

### Notes

- `source_audio_asset_id` is automatically resolved to an absolute PR0TA asset download URL.
- Returns the generated audio URL directly (not an async task).
- Current STS model: `eleven_multilingual_sts_v2`.
- STS currently supports audio-to-audio conversion. Video voice-change remains on the older internal route family — not exposed through this v2 surface.

## Current Limitations

- All V2 voice routes target the existing ElevenLabs-backed implementation.
- Prompt voice design is a two-step flow: previews first, commit second. There is no single-call "design and save" shortcut.
- Voice clone is synchronous — it returns the created voice directly, not a task ID. For large sample sets, expect longer response times.
- STS supports audio-to-audio only on the public v2 surface. Video voice-change (replacing a speaker's voice in a video clip) uses the older internal routes.
- `character_ids` integration with cloned/designed voices is not yet automatic — after creating a voice via these routes, manually update the project's character registry if the voice needs to be referenced in Seedance character workflows.
