## Asset Readability Filters, Annotations, and Timeline Analysis

This reference covers the asset-tagging/readability and timeline-analysis endpoints. These tools help agents and users curate assets, communicate editorial intent, and verify timeline integrity before rendering.

---

### Asset Readability Filters

All filters apply to the standard asset listing endpoint and return the normal paginated asset-list payload.

#### Favorite assets

```
GET /api/assets/{project_name}?favorite=true
```

Returns assets the user or agent has marked as favorites.

#### Filter by tag

```
GET /api/assets/{project_name}?tag=hero
GET /api/assets/{project_name}?tag=hero&tag=approved
```

Repeated `tag` parameters are AND-joined. Matching is case-insensitive after trimming whitespace.

#### Filter by reference type

```
GET /api/assets/{project_name}?reference_type=character_reference
GET /api/assets/{project_name}?reference_type=set_reference
GET /api/assets/{project_name}?reference_type=prop_reference
GET /api/assets/{project_name}?reference_type=style_reference
```

Use this for long projects where the agent needs the current character/set/prop/look reference pool.

#### Include timeline-library items

```
GET /api/assets/{project_name}?include=timeline
GET /api/assets/{project_name}?include=all
```

- `include=timeline` — timeline-library clip assets only.
- `include=all` — normal SQL assets plus timeline-library items.

---

### Asset Annotations (Metadata Mutation)

#### Favorite / unfavorite

```
POST /api/assets/{project_name}/favorite?asset_id={asset_id}&favorite=true
POST /api/assets/{project_name}/favorite?asset_id={asset_id}&favorite=false
```

Response:

```json
{
  "success": true,
  "favorites": ["asset_1", "asset_2"]
}
```

#### Write tags, notes, and reference metadata

```
PATCH /api/assets/{project_name}/annotations
```

Minimal tag update:

```json
{
  "asset_id": "asset_123",
  "tags": ["hero", "approved"],
  "notes": "Primary approved Kondiaronk portrait."
}
```

Mark a character reference:

```json
{
  "asset_id": "asset_123",
  "reference_type": "character_reference",
  "character_name": "Kondiaronk",
  "subject": "Kondiaronk",
  "tags": ["reference", "hero", "approved"],
  "notes": "Use as the primary likeness reference."
}
```

Supported reference types: `character_reference`, `set_reference`, `prop_reference`, `style_reference`, `reference` (generic).

Supported metadata fields: `asset_id` (or `url`/`asset_url`), `tags`, `notes`, `labels`, `keywords`, `category`, `reference_type`, `character_name`, `set_name`, `prop_name`, `look_name`, `subject`, `scene_number`, `shot_number`, `take_number`.

Field usage guidance:

- **`tags`** — general project readability (`approved`, `hero`, `needs_review`, `do_not_use`, `best_take`, `alt`).
- **`reference_type`** — durable semantic classification for assets that serve as references.
- **`subject`** + specific name field (`character_name`, `set_name`, `prop_name`, `look_name`) — when the asset represents a named production entity.
- **`scene_number` / `shot_number` / `take_number`** — for shot-tracking in structured productions.

---

### Timeline Mark Labels and Descriptions

Marks now support `label` and `description` fields for richer editorial annotation.

#### Create a mark with label and description

```
POST /api/post-production/{project_name}/timeline/marks?sequence_id=timeline_v2
```

```json
{
  "label": "Credits In",
  "description": "Credits should begin here.",
  "time": 175.56,
  "type": "program_mark"
}
```

The backend mirrors fields for compatibility: `label` ↔ `name`, `description` ↔ `note`.

Returned shape:

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Credits In",
  "label": "Credits In",
  "note": "Credits should begin here.",
  "description": "Credits should begin here.",
  "time": 175.56,
  "resolvedTime": 175.56,
  "type": "program_mark",
  "version": 42,
  "timelineDuration": 181.5
}
```

#### Update a mark

```
PATCH /api/post-production/{project_name}/timeline/marks/{marker_id}?sequence_id=timeline_v2
```

```json
{
  "label": "Credits Hold",
  "description": "Hold through the end of the reel."
}
```

Use `label` and `description` in all new code. Treat `name` and `note` as compatibility aliases that may appear in responses.

---

### Timeline Analysis

Pre-render diagnostic endpoint that gives agents machine-readable NLE health data.

```
GET /api/post-production/{project_name}/timeline/analysis?sequence_id=timeline_v2
GET /api/post-production/{project_name}/timeline/debug-report?sequence_id=timeline_v2
```

Use `/timeline/debug-report` as the default agent preflight before render/export. It wraps analysis with track coverage, primary visual gaps, source-duration-vs-program-duration, retime state, audio asset presence, keyframe counts, and render-risk warnings. Use `/timeline/analysis` when you need the raw analysis payload only.

#### Response shape

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
    "reusedMediaCount": 2,
    "sourceShortfallCount": 1
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
  "overlaps": [
    {
      "kind": "overlap",
      "trackId": "video",
      "trackLabel": "Primary Video",
      "trackType": "video",
      "start": 12.0,
      "end": 13.0,
      "duration": 1.0,
      "clipIds": ["clip_a", "clip_b"]
    }
  ],
  "reusedMedia": [
    {
      "mediaKey": "asset:asset_123",
      "assetId": "asset_123",
      "assetUrl": "/api/v2/projects/project/assets/asset_123/download",
      "clipCount": 2,
      "clips": [
        {
          "clipId": "clip_a",
          "label": "Shot A",
          "trackId": "video",
          "trackLabel": "Primary Video",
          "trackType": "video",
          "start": 12.0,
          "end": 16.0
        }
      ]
    }
  ],
  "sourceShortfalls": [
    {
      "kind": "source_shortfall",
      "clipId": "clip_short",
      "label": "Short source edit",
      "trackId": "video",
      "trackLabel": "Primary Video",
      "trackType": "video",
      "assetId": "asset_short",
      "requestedDuration": 5.0,
      "availableSourceDuration": 3.0,
      "shortfallDuration": 2.0,
      "gapStart": 55.0,
      "gapEnd": 57.0,
      "speed": 1.0,
      "recommendation": "Use fitToFill=true on a three-point edit or set clip speed explicitly if retiming is desired."
    }
  ],
  "trackCoverage": [
    {
      "trackId": "video",
      "trackLabel": "Primary Video",
      "trackType": "video",
      "trackIndex": 0,
      "clipCount": 12,
      "coveredDuration": 176.0,
      "gapCount": 1,
      "overlapCount": 0,
      "muted": false,
      "locked": false
    }
  ],
  "markers": []
}
```

#### Gap semantics

Gaps are reported per track. A gap on an overlay track (`V2`) may be fine if the primary track (`V1`) has coverage underneath. A gap on the only primary video track is usually a render problem.

#### Reused-media semantics

Keyed by `assetId` (preferred) or `assetUrl` (fallback). Any media used by more than one clip appears in `reusedMedia` — the same kind of repeated-source warning a professional NLE would surface.

---

### Clip Reuse Flags

The standard clip listing now includes per-clip reuse metadata:

```
GET /api/post-production/{project_name}/timeline/clips?sequence_id=timeline_v2
```

Each clip includes:

```json
{
  "id": "clip_a",
  "assetId": "asset_123",
  "trackId": "video",
  "trackAlias": "V1",
  "trackType": "video",
  "trackLabel": "Primary Video",
  "mediaUsageCount": 2,
  "isReusedMedia": true,
  "sourceShortfall": null
}
```

Use per-clip `isReusedMedia` and `sourceShortfall` when already listing clips and only need per-clip flags. Use `/timeline/analysis` when the agent needs full timeline diagnostics including `sourceShortfalls[]`. For the full source-shortfall and fit-to-fill contract (default gap behavior, `fitToFill` parameter, four-point edits, speed semantics), see `reference/source-shortfalls-and-fit-to-fill.md`.
