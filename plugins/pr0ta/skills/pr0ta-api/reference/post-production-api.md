# PR0TA Post-Production API Reference

**Date:** 2026-04-21  
**Audience:** API users and integrators  
**Scope:** Current post-production timeline, render, transcription, metering, and editorial contracts

This is the current backend-facing reference for PR0TA's post-production API surface. It is intended for direct API consumers. The companion skills-facing migration memo is:

- `Documentation/dev_notes/PR0TA_API_SKILLS_DEVELOPER_UPDATE_2026-04-21.md`

The base prefix for the routes below is:

- `/api/post-production/{project_name}`

Asset metadata routes referenced here use:

- `/api/assets/{project_name}`
- `/api/v2/projects/{project_id}/assets/{asset_id}/download` for stable direct downloads

## 1. Stable Rules

- Post-production state is persisted server-side. Most edit, preview, and render routes operate on the saved sequence, usually `sequence_id=timeline_v2`.
- `GET /preview` is now sequence-resolution by default unless low/preview quality is explicitly requested.
- `POST /render` is the timeline preview render route used by the current toolbar workflow.
- `POST /export` is the final-export route.
- Transcript-word anchoring, marks, trims, 3-point edits, and link groups are now real backend contracts rather than proposed-only features.
- Link groups are the current grouped-editing primitive. There is not yet a higher-level edit-group abstraction beyond them.

## 2. Authentication

Use the same PAT bearer authentication used by the rest of the PR0TA API:

```bash
Authorization: Bearer pat_...
```

## 3. Timeline Read and Patch

### Read timeline

`GET /api/post-production/{project_name}/timeline?sequence_id=timeline_v2`

Timeline clips may now include:

```json
{
  "id": "clip_123",
  "assetId": "asset_123",
  "assetUrl": "/api/assets/...",
  "sourceMedia": {
    "width": 1660,
    "height": 1244,
    "aspectRatio": "4:3",
    "duration": 5.0,
    "fitsSequence": false
  },
  "generation_context": {
    "prompt": "A dramatic close-up of ...",
    "model": "kling-v3"
  }
}
```

`sourceMedia` is best-effort source-asset metadata for editorial decisions.  
`generation_context` is truncated provenance for prompt/model awareness.

### Timeline analysis

`GET /api/post-production/{project_name}/timeline/analysis?sequence_id=timeline_v2`

Returns machine-readable timeline diagnostics for API users:

```json
{
  "sequenceId": "timeline_v2",
  "version": 42,
  "duration": 181.5,
  "summary": {
    "trackCount": 4,
    "clipCount": 53,
    "markerCount": 6,
    "gapCount": 3,
    "reusedMediaCount": 2
  },
  "gaps": [
    {
      "kind": "gap",
      "trackId": "video",
      "trackLabel": "Primary Video",
      "trackType": "video",
      "start": 42.0,
      "end": 44.5,
      "duration": 2.5
    }
  ],
  "reusedMedia": [
    {
      "mediaKey": "asset:asset_123",
      "assetId": "asset_123",
      "clipCount": 2,
      "clips": [
        {"clipId": "clip_a", "trackId": "video", "start": 12.0, "end": 16.0},
        {"clipId": "clip_b", "trackId": "video", "start": 80.0, "end": 84.0}
      ]
    }
  ],
  "markers": []
}
```

Use this before render/export to catch unintended holes and repeated media. `GET /timeline/clips` also annotates each clip with `mediaUsageCount` and `isReusedMedia`.

### Track targeting

`GET /api/post-production/{project_name}/timeline/tracks?sequence_id=timeline_v2`

Returns ordered track metadata with stable raw ids plus NLE-style aliases:

```json
{
  "tracks": [
    {
      "id": "video",
      "type": "video",
      "label": "Primary Video",
      "alias": "V1",
      "aliases": ["V1"],
      "index": 0,
      "kindIndex": 0,
      "clipCount": 12
    },
    {
      "id": "dialogue",
      "type": "audio",
      "label": "Dialogue",
      "alias": "A1",
      "aliases": ["A1"],
      "index": 1,
      "kindIndex": 0,
      "clipCount": 1
    }
  ],
  "trackTargets": [
    {"id": "video", "type": "video", "label": "Primary Video", "alias": "V1"},
    {"id": "dialogue", "type": "audio", "label": "Dialogue", "alias": "A1"}
  ],
  "version": 12
}
```

Track selector fields now accept:

- exact raw track ids, e.g. `video`, `dialogue`, `music`, `production`
- NLE aliases from `/timeline/tracks`, e.g. `V1`, `V2`, `A1`, `A2`
- unique track labels, e.g. `Dialogue`, when only one track has that label

If a label is duplicated, the backend rejects the selector as ambiguous. Use the raw `id` or alias in that case.

Selector-aware fields include:

- `POST /timeline/clips` -> `placement.track_id` / `placement.track`
- `PATCH /timeline/clips/{clip_id}` -> `track_id`
- `POST /timeline/clips/reorder` -> operation `track_id`
- `POST /timeline/edits` and `/preview` -> `track`, `affectedTracks`
- `POST /timeline/edits/{clip_id}/trim` and `/preview` -> `affectedTracks`
- linked move maps -> `linkedTrackMap` / `trackMap` values
- audio preview/meter/render solo track query values where a `tracks=` list is accepted

### Create and update tracks

Create a new track:

`POST /api/post-production/{project_name}/timeline/tracks?sequence_id=timeline_v2`

```json
{
  "id": "sfx",
  "type": "audio",
  "label": "SFX",
  "position": 4
}
```

Rename or update a track by raw id, alias, or unique label:

`PATCH /api/post-production/{project_name}/timeline/tracks/{track_id_or_alias}?sequence_id=timeline_v2`

```json
{
  "label": "Production Dialogue",
  "locked": true,
  "position": 2
}
```

Protected fields cannot be patched directly: `id`, `type`, `clips`, `alias`, `aliases`, `index`, `kindIndex`.

### Patch timeline

`PATCH /api/post-production/{project_name}/timeline`

Accepted body shapes:

Flat patch:

```json
{
  "audioMix": {
    "ducking": [
      {
        "sourceTrack": "music",
        "keyTrack": "dialogue",
        "duckedGain": 0.55
      }
    ]
  }
}
```

Wrapped patch:

```json
{
  "updates": {
    "audioMix": {
      "ducking": [
        {
          "sourceTrack": "music",
          "keyTrack": "dialogue",
          "duckedGain": 0.55
        }
      ]
    }
  }
}
```

Invalid mixed payloads now return `400` instead of silently no-oping.

### Ducking field

Canonical field:

```json
{
  "duckedGain": 0.55
}
```

Compatibility alias still accepted and still emitted on reads:

```json
{
  "threshold": 0.55
}
```

Current normalized reads include both:

```json
{
  "duckedGain": 0.55,
  "threshold": 0.55
}
```

`duckedGain` means the fraction of normal source-track volume while the key track is active:

- `1.0` = no ducking
- `0.5` = roughly -6 dB duck
- `0.0` = full mute under key track

## 4. Preview and Final Render

### Sequence-based preview

`GET /api/post-production/{project_name}/preview?from=X&to=Y`

Current quality behavior:

- omit `quality` -> full saved sequence resolution
- `quality=full` -> full saved sequence resolution
- `quality=low` -> lower-resolution preview
- `quality=preview` -> alias of `low`

If the saved sequence is `1080x1920`, omitting `quality` now yields `1080x1920`, not half-resolution.

### Render Preview

`POST /api/post-production/{project_name}/render`

Current behavior:

- this is a preview-task endpoint, not the final-export endpoint
- it queues a `timeline_render` task
- if the request body contains only render-control fields, the backend loads the saved post-production sequence automatically
- if the resolved timeline has zero clips, the route returns `400` instead of queueing an empty stub render
- if required render tooling is unavailable, the route returns `503`

Normal control-only request bodies are valid:

```json
{}
```

```json
{"from": 0, "to": 212}
```

```json
{"resolution": "full"}
```

```json
{"quality": "full", "width": 1080, "height": 1920, "format": "mp4"}
```

Use `POST /api/post-production/{project_name}/export` for final master exports.

## 5. Transcription Retrieval

`GET /api/v2/projects/{project_id}/assets/{asset_id}/transcription`

Response shape:

```json
{
  "success": true,
  "asset_id": "asset-123",
  "project_id": "project-1",
  "text": "Full transcript text",
  "segments": [],
  "words": [],
  "segment_count": 12,
  "word_count": 418,
  "timestamp_granularity": "word",
  "transcription_options": {},
  "transcription_summary": {}
}
```

Behavior:

- returns stored transcript text when available
- synthesizes `text` from segment text on the fallback label-based path if stored top-level transcript text is missing
- returns segments
- returns flattened words
- falls back to older label-based transcript storage when possible

This is now the supported retrieval path for asset-level word timing.

## 6. Audio Metering

`GET /api/post-production/{project_name}/audio/meter`

Example:

```bash
curl -H "Authorization: Bearer pat_..." \
  "https://app.pr0ta.com/api/post-production/$PROJ/audio/meter?from=0&to=212&tracks=dialogue,music&format=lufs"
```

Representative response fields:

```json
{
  "integrated_lufs": -16.2,
  "range_lu": 4.8,
  "true_peak_dbfs": -1.4,
  "short_term_lufs_timeline": [
    {"time": 0.0, "lufs": -15.7}
  ]
}
```

This endpoint uses the actual post-production mix path. Use it when you need loudness numbers instead of ear-check previewing.

Failure behavior:

- returns `503` if MLT/render tooling is unavailable
- returns `400` for invalid request windows or parameters
- returns `404` if the referenced sequence does not exist

## 7. Program Marks

Endpoints:

- `GET /api/post-production/{project_name}/timeline/marks`
- `POST /api/post-production/{project_name}/timeline/marks`
- `PATCH /api/post-production/{project_name}/timeline/marks/{marker_id}`
- `DELETE /api/post-production/{project_name}/timeline/marks/{marker_id}`

Marks may be absolute program-time marks or transcript-word anchored marks.

Read and write shape:

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "quote_in",
  "label": "Quote In",
  "description": "Cut to the close-up when this line begins.",
  "note": "Cut to the close-up when this line begins.",
  "time": 12.8,
  "type": "program_mark"
}
```

`name` is the canonical semantic field.  
`label` is mirrored to the same value for editor/UI compatibility.  
`description` and `note` are mirrored; use either field for human-readable mark notes.  
New backend-generated mark ids are UUID strings.

Representative anchored mark:

```json
{
  "name": "quote_in",
  "anchorTo": {
    "type": "transcript_word",
    "assetId": "asset_dialogue_1",
    "clipId": "clip_dialogue_main",
    "wordIndex": 128
  }
}
```

For reused dialogue assets, `clipId` is the preferred disambiguation field. Anchored marks follow timeline changes when the underlying word's program time shifts.

## 8. Asset Source Marks

Endpoints:

- `GET /api/v2/projects/{project_id}/assets/{asset_id}/marks`
- `POST /api/v2/projects/{project_id}/assets/{asset_id}/marks`
- `PATCH /api/v2/projects/{project_id}/assets/{asset_id}/marks/{mark_id}`
- `DELETE /api/v2/projects/{project_id}/assets/{asset_id}/marks/{mark_id}`

These are source-media marks stored on the asset, not program-time timeline marks.

## 9. Editorial Apply and Preview

### 3-point style edits

Endpoints:

- `POST /api/post-production/{project_name}/timeline/edits/preview`
- `POST /api/post-production/{project_name}/timeline/edits`

Current supported edit modes include:

- `insert`
- `overwrite`

The request can refer to program or asset marks by explicit ids or mark references.

Preview returns the edit diff without committing. Apply persists the change.

### Trim operations

Endpoints:

- `POST /api/post-production/{project_name}/timeline/edits/{clip_id}/trim/preview`
- `POST /api/post-production/{project_name}/timeline/edits/{clip_id}/trim`

Current trim modes:

- `ripple`
- `roll`
- `slip`
- `slide`

Current grouped behavior is strongest for `ripple`, `slip`, and `slide` with linked clips. Broader multi-track semantics are still more limited than a full NLE.

### Useful request flags

- `linked: true` -> operate through the link group for supported move/trim/delete paths
- `affectedTracks` -> explicit multi-track participation for supported edit and ripple-trim flows
- `linkedTrackMap` -> explicit destination-track remapping for linked companion clips

## 10. Link Groups

Endpoints:

- `GET /api/post-production/{project_name}/timeline/links`
- `POST /api/post-production/{project_name}/timeline/links`
- `PATCH /api/post-production/{project_name}/timeline/links/{link_group_id}`
- `DELETE /api/post-production/{project_name}/timeline/links/{link_group_id}`
- `POST /api/post-production/{project_name}/timeline/links/{link_group_id}/clips`
- `DELETE /api/post-production/{project_name}/timeline/links/{link_group_id}/clips/{clip_id}`
- `POST /api/post-production/{project_name}/timeline/links/{link_group_id}/move`
- `POST /api/post-production/{project_name}/timeline/links/{link_group_id}/move/preview`
- `POST /api/post-production/{project_name}/timeline/links/{link_group_id}/trim`
- `POST /api/post-production/{project_name}/timeline/links/{link_group_id}/trim/preview`
- `DELETE /api/post-production/{project_name}/timeline/links/{link_group_id}/clips`
- `POST /api/post-production/{project_name}/timeline/links/{link_group_id}/clips/preview`

Create request:

```json
{
  "clipIds": ["clip_video", "clip_audio"],
  "linkGroupId": "link_sync",
  "metadata": {
    "label": "A/V Pair",
    "kind": "av_pair",
    "note": "Primary sync",
    "locked": false
  }
}
```

Incremental membership add:

```json
{
  "clipIds": ["clip_music"]
}
```

Link-group metadata fields:

- `label`
- `kind`
- `note`
- `locked`

Timeline reads may also include top-level persisted metadata:

```json
{
  "linkGroups": [
    {
      "linkGroupId": "link_sync",
      "label": "A/V Pair",
      "kind": "av_pair",
      "note": "Primary sync",
      "locked": true
    }
  ]
}
```

Current behavior:

- creating a group rewrites the specified clips into that group
- adding clips preserves existing metadata
- removing one clip from a group is supported
- if a removal leaves only one member, the backend dissolves the group and clears the remaining singleton clip's `linkGroupId`
- `locked=true` blocks mutating clip-level and group-level editorial operations until unlocked

Grouped move behavior:

- move by `delta`
- or move by `{clipId, start}` to place one known member clip at an absolute start and move the rest by the implied delta
- optional `trackMap` can remap selected group members to new tracks

## 11. Music Output Format

Unified music generation now expects `output_format` as the canonical field.

Examples:

```json
{
  "output_format": "mp3_44100_192"
}
```

Legacy shorthands are normalized when used through supported paths:

- `format: "mp3"` -> `output_format: "mp3_44100_192"`
- `format: "wav"` -> `output_format: "pcm_44100"`
- `format: "pcm"` -> `output_format: "pcm_44100"`
- `format: "ogg"` -> `output_format: "opus_48000_128"`
- `format: "opus"` -> `output_format: "opus_48000_128"`
- `format: "ulaw"` -> `output_format: "ulaw_8000"`
- `format: "alaw"` -> `output_format: "alaw_8000"`

Unsupported values now return `400`.

## 12. Current Limits

The following are still not full-featured or not yet shipped as a higher-level abstraction:

- no broader edit-group system beyond explicit link groups
- no richer multi-group orchestration layer
- multi-track trim and grouped-edit semantics are still narrower than a full desktop NLE
- transcript-anchor disambiguation is strongest when the caller supplies `clipId` for reused dialogue assets

## 13. Recommended Integrator Workflow

For an editorial agent or integration working against the current backend:

1. Read the saved timeline.
2. Use asset marks and program marks instead of hard-coding seconds when possible.
3. Use `/edits/preview` or trim preview before committing larger moves.
4. Use link groups for persisted A/V or multi-track relationships.
5. Use `/preview` for picture-plus-sound validation and `/audio/meter` for loudness validation.
6. Use `POST /render` for preview-task rendering and `/export` for final exports.
