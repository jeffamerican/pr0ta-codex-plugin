# Native Audio & Sound Control — Reference

**Start here:** this file is the deep dive on native video audio. The decision rule ("native audio vs separate TTS") lives in `pr0ta-video/SKILL.md`. Read this file when you actually need to prompt for sync dialogue, enforce the post-generation transcription gate on `sound: "on"` video, or extract an audio track from a generated clip.

---

## Native Audio & Sound Control

### When to Use Native Audio vs Separate TTS

This is a critical production decision. **Generating separate TTS and overlaying it on silent video is an anti-pattern for dialogue clips.** It produces no lip sync, no ambient sound matching, and sounds obviously fake.

| Clip Type | `sound` Setting | Why |
|-----------|----------------|-----|
| **Dialogue (speaker visible)** | `"on"` | Native audio gives lip sync, ambient sound, and natural speech timing |
| **Narration over footage (speaker NOT visible)** | `"off"` | Layer ElevenLabs TTS narration in post — higher quality voice control |
| **B-roll / montage** | `"off"` | Layer music and SFX in post for precise timing control |
| **Ambient / atmosphere** | `"on"` | Native ambient sound adds realism (rain, crowd, traffic) |

### Sound Parameter

All video generation requests should explicitly set `sound`:

```json
{
  "sound": "on"
}
```

- `"on"` -- generate native audio baked into the video (speech, ambient, effects). Models that support this: **Seedance 2.0 Omni, Seedance 2.0 T2V, Kling O3 Pro, Kling V3 Pro, Veo 3.1**
- `"off"` -- silent video output for post-production audio layering

**Always set this explicitly.** Omitting it may produce unexpected results. For Seedance, the API passes `generate_audio: false` to the provider when `sound: "off"`.

### Mandatory Time-Indexing for Video with `sound: "on"`

**Every video asset generated with `sound: "on"` must be transcribed before it enters the post-production timeline.** Video with dialogue, diegetic sound, or ambient speech falls on the speech side of the two-path gate — transcribe it with Scribe V2. This is the same hard rule that applies to pure audio assets — see `pr0ta-audio` → "Mandatory Time-Indexing Rule (Two Paths)" for the full policy.

Why this matters specifically for video-with-audio:

- **Dialogue cuts need word-level timing.** If you intend to cut a line in half, shorten a beat of dialogue, or match a cut to the word the character says, you need Scribe V2 word timing on the video asset itself.
- **Speaker IDs drive multi-character dialogue tracks.** Scribe V2's automatic diarization routes lines to the right speaker so the editor can cut a conversation reliably.
- **Audio events mark cuttable moments.** Breaths, silences, laughter, and emphasis are editorial hooks — without the transcription, they're invisible.

**Two ways to transcribe a video asset — pick the right one.**

**Option 1 — Direct video transcription (simple case).** `POST /api/v2/projects/{project_id}/transcribe` now accepts video asset IDs and video file uploads directly. PR0TA extracts a derived audio asset under the hood and queues transcription against it in a single call. Use this when you only need the transcript and don't need the audio track as a standalone reusable asset. The response surfaces the derivation so you can see what happened:

```json
{
  "task_id": "task-id",
  "status": "queued",
  "asset_id": "transcription-audio-asset-id",
  "input_kind": "asset",
  "created_asset": false,
  "download_url": "/api/v2/projects/{project_id}/assets/{transcription-audio-asset-id}/download",
  "source_asset_id": "original-video-asset-id",
  "source_kind": "video",
  "extracted_audio_asset_id": "transcription-audio-asset-id"
}
```

For direct audio inputs, `source_asset_id` equals `asset_id`, `source_kind` is `audio`, and `extracted_audio_asset_id` is `null`.

**Option 2 — Extract audio first, then act on the audio asset.** When you want the audio track as a reusable asset (for music analysis, separate dialogue editing, waveform generation, future stem work) call `POST /api/v2/projects/{project_id}/assets/{asset_id}/extract-audio` first, then pass the extracted audio asset to the transcription endpoint (or to `POST /api/audio/transcription/start` for narration-timeline auto-population, or to the music analysis endpoint if it's an instrumental track). See "Audio Extraction From Video" below for the extract-audio endpoint details.

**Enforcement:**

1. After any video generation with `sound: "on"` reaches `succeeded`, route the asset to the correct path:
   - **Narration-timeline productions:** extract audio first (or use direct transcription), then call `POST /api/audio/transcription/start` with the audio asset so the narration timeline's transcript layer auto-populates.
   - **Standalone transcription (no narration timeline):** call `POST /api/v2/projects/{project_id}/transcribe` with the video asset directly.
   - Always pin Scribe V2: `model_id: "fal-ai/elevenlabs/speech-to-text/scribe-v2"`.
2. Poll the transcription task. Do not mark the video asset "ready for editing" until its transcription task has reached `succeeded`.
3. Verify via `GET /api/v2/projects/{project_id}/assets/{asset_id}/transcription` that `status: "ready"` with populated `words[]`. Use whichever asset ID was actually transcribed — that will be the extracted audio asset, not the source video.
4. Only then add the video to the post-production timeline.

**If the video has no audio stream, extraction and transcription will fail with a validation error.** Silent B-roll should be generated with `sound: "off"` from the start.

**For `sound: "off"` video (silent B-roll), transcription is not required** — there is no audio to transcribe. Silent clips go straight to the timeline.

### Audio Extraction From Video

Sometimes you want the audio track of a video as a reusable, standalone asset — for music analysis on a scored clip, for separate dialogue editing, for waveform generation, or for future stem and cleanup workflows. PR0TA exposes a dedicated extraction endpoint for this.

```
POST /api/v2/projects/{project_id}/assets/{asset_id}/extract-audio
Authorization: Bearer $PAT
```

Request body:

```json
{
  "codec": "wav",
  "category": "extracted_audio",
  "subject": "Optional label",
  "folder_path": "/optional/folder"
}
```

Response:

```json
{
  "success": true,
  "source_asset_id": "video-asset-id",
  "extracted_asset_id": "audio-asset-id",
  "download_url": "/api/v2/projects/{project_id}/assets/{audio-asset-id}/download",
  "asset": {
    "...": "standard AssetRead payload"
  }
}
```

**Provenance fields on the derived audio asset.** Extracted assets carry provenance metadata so downstream skills can reason about origin:

- `derived_from_asset_id`
- `source_video_asset_id`
- `derivation_type: "extracted_audio"`
- `source_kind: "video"`
- `extracted_audio_codec`

These fields live in asset metadata and labels.

**When to use extract-audio vs direct video transcription:**

- **Use `extract-audio`** when you want an audio-only editing surface from a video, when you want to run music analysis on the audio track of a scored video clip, or when you want a reusable dialogue/music asset separate from picture.
- **Use `transcribe` directly on video** when you only need timing/transcript output and don't want to manually call extraction first.

**Important:** Video transcription is not "direct video transcription" in the implementation. It is "video → derived audio asset → transcription." PR0TA handles this under the hood, but the extracted audio asset is the thing that is actually transcribed and indexed. This is intentional: the derived audio asset is reusable by other workflows and preserves editorial clarity.

### Prompting for Native Sync Audio (Dialogue)

When using `sound: "on"` with dialogue, embed the speech directly in the prompt. The model generates lip-synced speech with matching ambient sound.

**Seedance 2.0 — embed dialogue naturally in the prompt:**
```
@image1 — A woman in a red coat stands in a rainy alley. She turns to the camera
and says "We don't have much time. Follow me." Camera holds on her face as she
speaks, then she turns and walks into the rain. Ambient city sounds, rain on
pavement, distant traffic.
```

**Kling O3/V3 — dialogue in quotes within the scene description:**
```
@Element1 sits across the table in a dimly lit café. He leans forward and says
"I've been waiting for you." Camera slowly pushes in. Ambient café sounds,
soft jazz, clinking glasses.
```

**Tips for sync audio prompts:**
- Put dialogue in quotation marks within the natural scene description
- Describe ambient sound alongside the dialogue ("rain on pavement", "crowd noise", "wind")
- Keep dialogue short per clip — one or two lines. Long speeches drift.
- Include emotional/tonal cues: "whispers urgently", "shouts angrily", "says softly"
- For multi-character dialogue, use multi-prompt mode with separate dialogue per segment

### Native Audio Language Limitations

**Native video audio works best for English.** For non-English dialogue:

- **Write dialogue in the actual target language**, not phonetic transliterations. For Hebrew, write actual Hebrew text (`"אומר בקול: 'סבא שלי אמר שיש הבטחה'"`), not English transliterations ("speaking aloud: 'Saba sheli omer...'"). Transliterations are almost always ignored — the model generates English speech or ambient sound instead.
- **Non-English results are still inconsistent.** Even with actual language text, some models may default to English or produce garbled speech. Test with a short clip first.
- **For reliable non-English dialogue:** Generate silent video (`sound: "off"`) and use ElevenLabs TTS separately (see `pr0ta-audio` skill). ElevenLabs v3 supports multilingual voices and gives you precise language control. Layer the TTS in post-production. This is more work but far more reliable for non-English dialogue.
- **For non-English narration over footage:** Always use separate ElevenLabs TTS — native audio language control is too unreliable for narration.

### Parameter Mapping: `sound` vs `with_audio`

The PR0TA unified API uses `sound: "on"` / `sound: "off"`. Some provider-level documentation references `with_audio: true/false` or `generate_audio: true/false` — these are the raw provider parameters that PR0TA maps internally. **Always use `sound` in PR0TA API calls.** The mapping:

| PR0TA API | Provider-level equivalent |
|-----------|--------------------------|
| `"sound": "on"` | `with_audio: true` / `generate_audio: true` |
| `"sound": "off"` | `with_audio: false` / `generate_audio: false` |

