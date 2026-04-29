# Music Analysis API — Reference

The **music analysis API** is the instrumental-music analogue of transcription. Scribe V2 is a speech model and does not detect musical beats or downbeats. This endpoint is PR0TA's first-party beat detector — asset → analysis task → `music_analysis.editorial_anchors`, persisted on asset metadata.

**When to use this:** for any instrumental music asset (score bed, underscore, stinger) that will drive cut timing. The output is the required time-indexing pass for Path B of the mandatory time-indexing rule in `pr0ta-audio`.

## Start Analysis

```
POST /api/v2/projects/{project_id}/music/analyze
Authorization: Bearer $PAT
```

Request body:

```json
{
  "asset_id": "asset-uuid",
  "min_bpm": 80,
  "max_bpm": 160,
  "beats_per_bar": 4,
  "include_transients": true,
  "include_beats": true,
  "include_downbeats": true
}
```

Response (async task):

```json
{
  "task_id": "task-uuid",
  "status": "queued",
  "asset_id": "asset-uuid",
  "analysis": null,
  "download_url": "/api/v2/projects/{project_id}/assets/{asset_id}/download"
}
```

This is an **async background task**. Poll with the same reliability contract as other generators. If analysis is already cached on the asset, the current cached payload may be included in `analysis` directly on the start response.

## Get Cached Analysis

```
GET /api/v2/projects/{project_id}/music/analyze/{asset_id}
```

Response:

```json
{
  "task_id": "cached",
  "status": "succeeded",
  "asset_id": "asset-uuid",
  "download_url": "/api/v2/projects/{project_id}/assets/{asset_id}/download",
  "analysis": {
    "analysis_version": 1,
    "generated_at": "2026-04-10T12:34:56.000000+00:00",
    "duration_seconds": 31.8421,
    "tempo_bpm": 118.73,
    "beat_confidence": 0.71,
    "beats_per_bar": 4,
    "beat_times": [0.0, 0.5061, 1.0122],
    "downbeat_times": [0.0, 2.0244, 4.0488],
    "transient_times": [0.0, 0.5061, 1.0122],
    "transients": [
      { "time": 0.0, "strength": 0.98 }
    ],
    "editorial_anchors": [
      { "time": 0.0, "kind": "section_start", "label": "Start" },
      { "time": 0.0, "kind": "downbeat", "label": "Bar 1" },
      { "time": 0.5061, "kind": "beat", "label": "Beat 2" }
    ],
    "summary": {
      "beat_count": 63,
      "downbeat_count": 16,
      "transient_count": 84,
      "anchor_count": 165
    }
  }
}
```

## Storage Contract

Analysis is persisted to the asset record in database metadata:

- `music_analysis` — full analysis payload.
- `music_analysis_options` — normalized request options.
- `music_analysis_summary` — compact summary for lightweight consumers.

This mirrors the dialogue-timing storage pattern (`whisper_index` on audio asset metadata after transcription).

## Consumer Guidance

- **`editorial_anchors`** is the normalized, word-like anchor stream. Use this as the primary cut-anchor source — it is the direct analogue to `whisper_index` for dialogue.
- **`downbeat_times`** for structural cuts, section resets, montage phrase starts.
- **`beat_times`** for rhythmic cut candidates and cadence snapping.
- **`transients[]`** (with per-hit `strength`) for sharp accents where the beat tracker is too coarse.
- Best results on instrumental tracks with a stable pulse. For rubato, ambient, orchestral, or meter-shifting music, fall back from `downbeat_times` to `transients` plus local context.

For the full policy on when to use this endpoint vs Scribe V2, see `pr0ta-audio` → "Mandatory Time-Indexing Rule (Two Paths)" and "Music Analysis API".
