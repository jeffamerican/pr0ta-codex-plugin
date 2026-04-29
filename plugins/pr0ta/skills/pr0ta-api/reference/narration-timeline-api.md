# Narration Timeline API — Endpoint Reference

The narration timeline is a **separate system from the post-production timeline**. It stores a `narration_timeline.json` in GCS at `{gcs_prefix}/Documents/narration_timeline.json` — a different file and data structure from the post-production `timeline_v2.json`. There is no browser UI for the narration timeline; it is API-only. The post-production timeline (browser Timeline page) does not render narration timeline data.

**Base path:** `/api/v2/projects/{project_id}/narration-timeline/`

`{project_id}` accepts either the project UUID or slug. All endpoints require authentication (PAT or JWT).

---

## Data Model

```
Timeline
├── config
│   ├── narration_offset (seconds)
│   ├── pre_roll_duration (seconds)
│   ├── frame_rate
│   ├── resolution (width × height)
│   └── coordinate_space_default
│
├── transcript
│   ├── narration_asset_id
│   ├── words[]  ─── { index, text, start, end, confidence }
│   ├── sentences[]  ─── { start_word_index, end_word_index }
│   ├── paragraphs[]  ─── { start_word_index, end_word_index, text_preview }
│   └── content_tags[]  ─── { start_word_index, end_word_index, tag, description }
│
├── assets[]
│   ├── asset_id, asset_type (still_image | video_clip | title_card)
│   ├── duration (nullable), description, affinity_tags[]
│   ├── usage_status (unused | placed | placed_multiple)
│   ├── dimensions, aspect_ratio, frame_rate
│   └── source
│
├── cuts[]
│   ├── cut_id, position (sequence order)
│   ├── start_time, end_time (final-video coordinates)
│   ├── asset_id → assets[]
│   ├── transcript_anchor { start_word_index, end_word_index, anchor_text }
│   ├── rationale (why this visual for this narration)
│   ├── motion (Ken Burns: start_crop, end_crop, zoom_direction)
│   └── transition (type, duration)
│
├── markers[]
│   ├── marker_id, time (final-video coordinates)
│   ├── type (beat | annotation | qc_flag)
│   └── note
│
├── audio_layers
│   ├── narration { asset_id, offset }
│   ├── music { asset_id, offset, duck_level, duck_attack, duck_release }
│   └── sfx[] { asset_id, time, volume }
│
└── snapshots[]
    ├── name, created_at
    └── state (frozen copy of cuts + markers + audio_layers)
```

---

## Coordinate Spaces

All timestamps stored in the timeline are in **final-video time** (zero = first frame of delivered file). Three coordinate spaces are supported:

| Space | Zero point | Conversion |
|-------|-----------|------------|
| **final** (default) | First frame of delivered file | stored as-is |
| **sequence** | First frame after pre-roll | final − pre_roll_duration |
| **narration** | First audio sample | final − pre_roll_duration − narration_offset |

Every query endpoint that returns timestamps accepts `?coordinate_space=narration|sequence|final`.

---

## Endpoint Reference

### Full Timeline

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/` | Full timeline object |

### Config

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/config` | Coordinate space config (narration_offset, pre_roll_duration, frame_rate, resolution) |
| PUT | `/config` | Update config |

```json
{
  "narration_offset": 4.0,
  "pre_roll_duration": 4.0,
  "frame_rate": 30.0,
  "resolution": {"width": 1920, "height": 1080}
}
```

### Transcript Layer

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/transcript` | Full transcript with words, sentences, paragraphs, content_tags |
| POST | `/transcript/populate` | Build transcript from asset transcription (manual trigger) |
| GET | `/transcript/words?from=&to=` | Words in time range (default coordinate_space=narration) |
| PUT | `/transcript/tags` | Set content tags (full replacement — send complete set each time) |

**Auto-population hook:** When transcription completes via `POST /api/audio/transcription/start`, the narration timeline's transcript layer is auto-populated with word-level timestamps, sentence boundaries (by punctuation), and paragraph boundaries (by silence gaps > 0.5s). If auto-population fails (e.g. project doesn't exist yet), transcription still succeeds — use the manual `POST /transcript/populate` endpoint as fallback.

**Re-population:** If narration is regenerated, call `POST /transcript/populate` with the new `narration_asset_id` to re-populate. Cuts whose transcript anchors may have shifted will be flagged.

**Content tags request:**
```json
[
  { "start_word_index": 0,   "end_word_index": 42,  "tag": "market_size",      "description": "Global microdrama market overview" },
  { "start_word_index": 43,  "end_word_index": 89,  "tag": "reelshort_stats",  "description": "ReelShort download and revenue numbers" }
]
```

### Asset Registry

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/assets` | List assets (filterable: `?affinity=tag&status=unused`) |
| POST | `/assets` | Register an asset |
| PATCH | `/assets/{asset_id}` | Update asset metadata |
| GET | `/assets/suggest?transcript_range=44.0-52.0` | Suggest matching assets for a time range |

**Register asset:**
```json
{
  "asset_id": "<pr0ta_asset_id>",
  "asset_type": "still_image",
  "description": "Bar chart showing $7B market size with 2025-2030 projection",
  "affinity_tags": ["market_size", "growth_projection"],
  "source": "generated"
}
```

Usage tracking is automatic: placing an asset in a cut flips `usage_status` from `unused` → `placed`. Place it twice → `placed_multiple`.

### Cut List

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/cuts` | All cuts |
| POST | `/cuts` | Add a cut |
| PATCH | `/cuts/{cut_id}` | Update a cut |
| DELETE | `/cuts/{cut_id}` | Remove a cut |
| POST | `/cuts/reflow` | Close gaps / redistribute after edits |
| GET | `/cuts/audit` | Alignment audit (per-cut drift report) |

**Add a cut:**
```json
{
  "position": 14,
  "start_time": 44.2,
  "end_time": 52.1,
  "asset_id": "<reelshort_stats_image_id>",
  "transcript_anchor": {
    "start_word_index": 43,
    "end_word_index": 89
  },
  "rationale": "Shows ReelShort statistics while narrator mentions '1 billion downloads'",
  "motion": {
    "zoom_direction": "in",
    "speed": 1.0,
    "start_crop": {"x": 0.0, "y": 0.0, "w": 1.0, "h": 1.0},
    "end_crop": {"x": 0.1, "y": 0.1, "w": 0.8, "h": 0.8}
  },
  "transition": {
    "type": "crossfade",
    "duration": 0.5
  }
}
```

`anchor_text` is auto-denormalized from word indices — no need to provide it.

**Incremental edit:** `PATCH /cuts/{cut_id}` to change one field (e.g. swap an asset) without rebuilding the entire cut list. Follow with `POST /cuts/reflow` to close gaps.

### Alignment Verification

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/verify` | Full alignment verification report |

**Response:**
```json
{
  "total_cuts": 49,
  "misaligned_cuts": 2,
  "average_drift_seconds": 0.3,
  "gaps": [
    { "after_cut": "abc", "before_cut": "def", "gap_seconds": 3.2, "from": 120.0, "to": 123.2 }
  ],
  "overlaps": [],
  "cuts": [
    {
      "cut_id": "abc123",
      "position": 22,
      "start_time": 135.6,
      "end_time": 142.5,
      "anchor_start": 168.2,
      "anchor_end": 172.9,
      "anchor_text": "UFO Film and Television Studios, over thirty years in the industry",
      "overlap_ratio": 0.0,
      "drift_seconds": 31.5,
      "status": "misaligned",
      "issues": ["Drift of 31.5s", "0% overlap between cut and anchor"]
    }
  ]
}
```

This is the **quality gate**: call before rendering, fix flagged cuts, re-verify, then export.

### Markers

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/markers` | List markers (filterable: `?type=qc_flag&from=120.0&to=180.0`) |
| POST | `/markers` | Add a marker |
| DELETE | `/markers/{marker_id}` | Remove a marker |

Marker types: `beat` (narration emphasis), `annotation` (user notes), `qc_flag` (automated quality checks).

### Snapshots

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/snapshot` | Save named snapshot |
| GET | `/snapshots` | List all snapshots |
| POST | `/snapshot/{name}/restore` | Restore a snapshot |
| GET | `/snapshot/{name}/diff` | Diff snapshot vs current state |

### Materialize to Post-Production

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/materialize-to-post-production` | Convert narration cuts into post-production timeline clips |

This is the terminal step for any narration-first production. Cuts, Ken Burns metadata, transitions, narration/music audio tracks, and ducking intent are all written into the post-production timeline as persistent state. From that point, both the agent and the user collaborate on the post-production timeline — see `pr0ta-timeline`.

Response:

```json
{
  "timeline": { /* materialized post-production timeline object */ },
  "clip_count": 42,
  "sequence_name": "narration_materialized_v1"
}
```

All rendering happens through the post-production timeline's preview and render endpoints — the narration timeline's terminal step is always materialization into the post-production timeline.

---

## Quick Reference — All 26 Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/` | Full timeline object |
| GET | `/config` | Coordinate space config |
| PUT | `/config` | Update config |
| GET | `/transcript` | Full transcript with words |
| POST | `/transcript/populate` | Build transcript from asset transcription |
| GET | `/transcript/words?from=&to=` | Words in time range |
| PUT | `/transcript/tags` | Set content tags |
| GET | `/cuts` | All cuts |
| POST | `/cuts` | Add a cut |
| PATCH | `/cuts/{cut_id}` | Update a cut |
| DELETE | `/cuts/{cut_id}` | Remove a cut |
| POST | `/cuts/reflow` | Close gaps / redistribute |
| GET | `/cuts/audit` | Alignment audit |
| GET | `/verify` | Full alignment verification |
| GET | `/assets` | List assets (filterable) |
| POST | `/assets` | Register an asset |
| PATCH | `/assets/{asset_id}` | Update asset metadata |
| GET | `/assets/suggest?transcript_range=` | Suggest matching assets |
| GET | `/markers` | List markers (filterable) |
| POST | `/markers` | Add a marker |
| DELETE | `/markers/{marker_id}` | Remove a marker |
| POST | `/snapshot` | Save named snapshot |
| GET | `/snapshots` | List all snapshots |
| POST | `/snapshot/{name}/restore` | Restore a snapshot |
| GET | `/snapshot/{name}/diff` | Diff snapshot vs current |
| POST | `/materialize-to-post-production` | Materialize cuts into the post-production timeline |

---

## Differences From the Post-Production Timeline

| | Narration Timeline | Post-Production Timeline |
|---|---|---|
| **API path** | `/api/v2/projects/{id}/narration-timeline` | `/api/post-production/{name}/timeline` |
| **Storage** | `narration_timeline.json` | `timeline_v2.json` |
| **Browser UI** | None (API-only) | Timeline page at `app.pr0ta.com/timeline` |
| **AAF export** | No (materializes into post-production for render) | Yes (via `export_routes` module) |
| **Data model** | Transcript-anchored cuts with rationale | Tracks, clips, sequence metadata |
| **Primary consumer** | Skills agent (programmatic assembly) | Both agent and human editor |
| **Render path** | Materialize → render on post-production timeline | Browser render / AAF export to NLE |

The two systems share the same GCS project prefix (`{gcs_prefix}/Documents/`) but are completely independent. There is currently no sync between them.
