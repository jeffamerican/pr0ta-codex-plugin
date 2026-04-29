# Unified Generation API — Reference

The primary way to trigger all generation programmatically. A single submission route dispatches to the appropriate generation backend. This file documents the full request/response contract for every generator/mode combination.

## Overview

### Submit Generation (Auth Required)

```
POST /api/v2/projects/{project_id}/generate
```

Behavior:
- Resolves `project_id` and verifies edit access
- Resolves input asset IDs to stable internal URLs
- Resolves stored project `element_ids` and `character_ids` into provider-ready references
- Dispatches to the image, video, audio, or music generation stack
- Returns a task ID for event/task polling

**Important:** `generator` is required on every request. Sending only `model` and `mode` will fail validation.

### Supported Generators and Modes

| Generator | Mode | Description |
|-----------|------|-------------|
| `image` | `txt_to_img` | Text-to-image (Nano Banana 2 default, GPT Image 2 for prompt adherence / character consistency) |
| `image` | `img_to_img` | Prompt-based image editing |
| `image` | `ref_to_img` | Reference-driven image generation |
| `image` | `edit_img` | Direct image editing |
| `video` | `ref_to_vid` | Reference-to-video (Kling, Runway, etc.) |
| `video` | `txt_to_vid` | Text-to-video (Seedance, LTX, etc.) |
| `audio` | `txt_to_speech` | Text-to-speech (ElevenLabs v3) |
| `music` | `txt_to_music` | Text-to-music (ElevenLabs Music) |

Unsupported combinations return `400`.

**Mode/model compatibility:** The API validates that the chosen mode is compatible with the resolved model. Kling models are reference-only -- use `mode=ref_to_vid`. Seedance and LTX models support `mode=txt_to_vid`. Sending `txt_to_vid` with a reference-only model (or vice versa) returns `400`. Seedance image-based modes strictly require at least one image reference.

### Image Generation Request

```json
{
  "generator": "image",
  "mode": "txt_to_img",
  "model": "nano_banana_2",
  "prompt": "Extreme close-up inside a swirling psychedelic vortex...",
  "width": 2048,
  "height": 2048,
  "format": "png",
  "negative_prompt": "blurry, distorted"
}
```

Required fields: `generator`, `mode`, `prompt`
Optional fields: `model`, `width`, `height`, `image_size`, `num_images`, `format`, `negative_prompt`, `seed`, `thinking_level`

**Full image parameter reference:**

| Parameter | Type | Notes |
|-----------|------|-------|
| `width` | int | Output width in pixels |
| `height` | int | Output height in pixels |
| `image_size` | string | Alternative to width/height (e.g., `landscape_4_3`). GPT Image 1.5 ignores this. |
| `num_images` | int | Number of images to generate (default: 1) |
| `format` | string | `png`, `jpeg`, `webp`. NB2 may return PNG regardless. |
| `seed` | int | For reproducibility (leave blank for random) |
| `thinking_level` | string | Reasoning level for complex prompts. **Nano Banana 2 only** — passed through to provider. |
| `negative_prompt` | string | What to exclude from generation |

**Image format:** Accepted values: `png`, `jpeg`, `jpg`, `webp`. The value `jpg` is normalized to `jpeg`. Unsupported formats return `400`. Note: Nano Banana 2 may output PNG regardless of the requested format -- accept whatever format the asset comes back as.

**Image resolution constraints by model:**
- **Nano Banana 2** -- Supports all aspect ratios and resolutions up to 4K. Most flexible. Note: `portrait_4_3` currently returns landscape (1408x768) — use `3:4` or `9:16` for portrait.
- **GPT Image 1.5** -- Ignores `image_size` parameter via API. Always outputs 1024x1024 regardless of requested dimensions. Use Nano Banana 2 for controlled dimensions.
- Other models -- Check `GET /api/v2/models` for supported dimensions.

### Model Capabilities Quick Reference

| Model | Generator | Duration | Aspect Ratios | Key Features | Quirks |
|-------|-----------|----------|---------------|-------------|--------|
| Nano Banana 2 | image | n/a | All ratios, up to 4K | Fast, precise, thinking level | `portrait_4_3` returns landscape |
| GPT Image 1.5 | image | n/a | 1024x1024 only | Cheap, uncensored | Ignores `image_size` parameter |
| Kling O3 Pro | video | 3–15s | `16:9`, `9:16`, `1:1` (ref-to-video variant) | Multi-prompt (6 cuts), elements, voice, sound | Often outputs 1440×1440 square |
| Kling V3 Pro | video | 3–15s | `16:9`, `9:16`, `1:1` | Multi-shot (5 shots), camera control, sound | Camera control API parameter |
| Seedance 2.0 Omni | video | Integer; provider-defined | `21:9`, `16:9`, `4:3`, `1:1`, `3:4`, `9:16` | Character ID (frontal+sheet), quad-modal (9img/3vid/3aud), sound | Landscape refs OK for portrait. @image/@video/@audio tokens. |
| Seedance 2.0 T2V / I2V | video | `5`, `10`, `15` | `16:9`, `9:16`, `4:3`, `3:4` | Text-only (T2V) or image-to-video (I2V), sound | Narrower aspect list than Omni |
| ElevenLabs v3 | audio | Auto (by text length) | n/a | Best TTS quality, voice discovery | Max 5000 chars per call |
| Music v1 | music | 1–300s | n/a | Duration param, emotional arc prompts | Prompt for temporal cues |

Always verify current capabilities against `GET /api/v2/models`. For the authoritative per-model duration / aspect matrix see `pr0ta-video` → "Per-Model Duration Constraints" (synced with the PR0TA API team response).

### Image Edit Request

For `img_to_img`, `ref_to_img`, and `edit_img` modes. Requires at least one input image or element reference.

```json
{
  "generator": "image",
  "mode": "img_to_img",
  "model": "fal-ai/nano-banana-2/edit",
  "prompt": "Keep the subject identity and pose, but relight as a moody neon noir portrait with blue rim light and light rain.",
  "image_asset_id": "c4f3bdf3-472a-4d6a-ad08-ea3872b8ed0c",
  "reference_image_asset_ids": ["729f2c9e-94f6-4d16-a4d6-469d4c5457ac"],
  "format": "png"
}
```

Reference-driven Kling image edit:
```json
{
  "generator": "image",
  "mode": "ref_to_img",
  "model": "kling/o1/image-edit",
  "prompt": "Match the wardrobe and facial structure from the references, convert into polished sci-fi key art.",
  "reference_image_urls": ["https://example.com/hero-base.png", "https://example.com/style-ref.png"],
  "element_ids": ["project-element-uuid-1"]
}
```

GPT Image edit:
```json
{
  "generator": "image",
  "mode": "edit_img",
  "model": "fal-ai/gpt-image-1/edit-image",
  "prompt": "Replace the plain background with a softly lit editorial studio set.",
  "image_asset_id": "482ee64f-f2e2-4f7f-b5f5-2be9822f7758"
}
```

Valid image-edit inputs: `image_asset_id`, `image_url`, `start_image_asset_id`, `start_image_url`, `reference_image_asset_ids[]`, `reference_image_urls[]`, `element_ids[]`, `elements[]`.

### Video Generation Request (Basic Ref-to-Vid)

```json
{
  "generator": "video",
  "mode": "ref_to_vid",
  "model": "kling_o3_pro",
  "prompt": "@Image1 -- camera pulls back from psychedelic vortex to reveal logo...",
  "duration": 10,
  "aspect_ratio": "1:1",
  "refs_strength": 140,
  "start_image_asset_id": "abc-123",
  "end_image_asset_id": "def-456",
  "elements": [
    {
      "frontal_asset_id": "ghi-789",
      "additional_asset_ids": ["jkl-012"]
    }
  ],
  "negative_prompt": "blurry, distorted, low quality",
  "cfg": 0.5,
  "sound": "off"
}
```

Required fields: `generator`, `mode`, `prompt` (or `multi_prompt`), and one of `start_image_asset_id`, `start_image_url`, or `image_asset_id` for Kling-style workflows.
Optional fields: `model`, `duration`, `aspect_ratio`, `refs_strength`, `end_image_asset_id`, `end_image_url`, `elements[]`, `element_ids[]`, `character_ids[]`, `negative_prompt`, `cfg`, `sound`, `seed`

**Sound control:** Always pass `sound: "on"` or `sound: "off"` explicitly for video requests. Omitting this field may result in unexpected audio in the output.

**CRITICAL prompt rules** (same as browser UI):
- Use `@Image1` to reference the Start Image in the prompt
- Do NOT use `@Image2` -- the End Image is an implicit structural target, not a promptable token
- Use `@Element1`, `@Element2` etc. for added Elements
- If `end_image_asset_id` is provided, `start_image_asset_id` is also required

### Video Generation with Stored Consistency Resources

Use `element_ids` to reference project-scoped Kling elements and `character_ids` for Seedance characters instead of passing inline references every time.

Advanced Kling request with stored elements + multi-prompt + camera control:
```json
{
  "generator": "video",
  "mode": "ref_to_vid",
  "model": "kling/o3/image-to-video",
  "prompt": "Hero exits frame into fog",
  "element_ids": ["project-element-uuid-1", "project-element-uuid-2"],
  "multi_prompt": [
    { "prompt": "Hero steps into frame" },
    { "prompt": "Hero turns and exits into fog" }
  ],
  "prompt_mode": "multi_prompt",
  "camera_control": {
    "type": "simple",
    "config": { "horizontal": 5 }
  },
  "voice_ids": ["1234567890"]
}
```

Advanced Seedance Omni request with stored character + multi-modal references:
```json
{
  "generator": "video",
  "mode": "txt_to_vid",
  "model": "muapi/seedance-2.0-omni-reference",
  "prompt": "Match the character from @Image1, the motion style from @Video1, and the rhythm from @Audio1.",
  "character_ids": ["project-character-uuid-1"],
  "reference_image_urls": ["https://example.com/hero.png"],
  "reference_video_urls": ["https://example.com/motion.mov"],
  "reference_audio_urls": ["https://example.com/music.wav"],
  "references": [
    { "type": "image", "image_url": "https://example.com/hero.png" },
    { "type": "video", "video_url": "https://example.com/motion.mov" },
    { "type": "audio", "audio_url": "https://example.com/music.wav" }
  ]
}
```

**Notes on consistency fields:**
- `element_ids[]` -- references stored project Elements (resolved server-side to Kling provider format)
- `character_ids[]` -- references stored project Characters (currently resolves one character per request)
- `character_id` -- direct MuAPI Seedance character reference (alternative to stored resolution). To **create** a new Omni character token, use `muapi/seedance-2-omni-reference-train` (single portrait) or `muapi/seedance-2-character` (character sheet / 1-3 stills); both return the token in `result_refs.character_id`. See `pr0ta-consistency` → "Creating a Seedance Character Token — Two Paths".
- **Consistency bundle** -- before multi-shot character generation, read `GET /characters/{id}/consistency` or `GET /characters/consistency?name=...` to get all approved references, Elements, tokens, and `provider_payloads` in one call. See `reference/projects-models-resources.md` → "Character Consistency Bundles".
- `multi_prompt[]` -- array of prompt segments for multi-shot generation; set `prompt_mode: "multi_prompt"` to activate
- `camera_control` -- structured camera control for Kling V3/O3
- `references[]` -- typed multi-modal references for Seedance Omni (`image`, `video`, `audio`)
- `reference_video_urls[]` -- video reference URLs for Seedance Omni
- `reference_audio_urls[]` -- audio reference URLs for Seedance Omni
- `voice_ids[]` -- voice control for Kling O3
- `sound` -- `"on"` or `"off"` -- explicit audio control for video generation. Always set this explicitly.
- `seed` -- reproducibility seed

### Audio Generation Request (Text-to-Speech)

```json
{
  "generator": "audio",
  "mode": "txt_to_speech",
  "model": "eleven_v3",
  "text": "Once upon a time, a little turtle found a very large cake.",
  "voice_id": "JBFqnCBsd6RMkjVDRZzb",
  "language": "en",
  "speed": 1.0
}
```

Required fields: `generator`, `mode`, `text`
Optional fields: `model`, `voice_id`, `language`, `speed`, `voice_settings`

Notes:
- `voice_id` references a voice profile created in the Audio Generator's Voice Design tab or available as a platform default.
- `text` max length: 5000 characters. For longer narrations, split into multiple requests.
- Output is an audio asset (typically MP3).

### Music Generation Request (Text-to-Music)

```json
{
  "generator": "music",
  "mode": "txt_to_music",
  "model": "music-v1",
  "prompt": "Playful Mozart-style piano piece, major key, light and cheerful",
  "duration": 30,
  "output_format": "mp3_44100_192"
}
```

Required fields: `generator`, `mode`, `prompt`
Optional fields: `model`, `duration`, `output_format`

**`output_format` is the canonical field** for specifying audio output format. Accepted values: `mp3_22050_32`, `mp3_44100_64`, `mp3_44100_96`, `mp3_44100_128`, `mp3_44100_192`, `pcm_16000`, `pcm_22050`, `pcm_44100`, `pcm_48000`, `opus_48000_32`, `opus_48000_64`, `opus_48000_96`, `opus_48000_128`, `opus_48000_192`, `ulaw_8000`, `alaw_8000`. The legacy `format` shorthand (e.g. `"mp3"`, `"wav"`, `"opus"`) is still accepted and normalized (e.g. `"mp3"` → `"mp3_44100_192"`, `"wav"` → `"pcm_44100"`). Unsupported values return `400`.

Notes:
- `duration` is in seconds (default: 30).
- For sound effects, use short durations (2-10s) with descriptive prompts.
- Output is an audio asset.

### Asset ID Resolution

The route resolves asset IDs to internal URLs before dispatching. All referenced assets must belong to the same project or the request returns `400`.

Built-in resolutions:
- `image_asset_id` -> `image_url`
- `start_image_asset_id` -> `start_image_url`
- `end_image_asset_id` -> `end_image_url`
- `reference_image_asset_ids[]` -> `reference_image_urls[]`
- `elements[].frontal_asset_id` -> `frontal_image_url`
- `elements[].additional_asset_ids[]` -> `reference_image_urls[]`

Stored resource resolution:
- `element_ids[]` -> provider-ready Kling element references
- `character_ids[]` -> provider-ready Seedance/MuAPI character references

You can also pass URLs directly (`start_image_url`, `end_image_url`, `reference_image_urls[]`, `reference_video_urls[]`, `reference_audio_urls[]`) instead of asset IDs.

### Submission Response

```json
{
  "task_id": "task_xyz123",
  "status": "queued",
  "estimated_seconds": 120,
  "credits_cost": 147.0
}
```

- `task_id` -- use for polling
- `status` -- usually `queued` or `started`
- `estimated_seconds` -- optional estimate
- `credits_cost` -- optional and nullable; do not assume it is always populated

**Note on task status:** The `provider` and `model_id` fields on initial task objects may be `null` -- this does not indicate a dispatch failure. The task transitions through `queued` -> `started`/`running` -> `succeeded`/`failed` as normal.

---

