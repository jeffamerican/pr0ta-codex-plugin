# Editorial Primitives — Reference

The post-production timeline now exposes a first-class editorial primitive surface: **asset marks**, **program marks**, **3-point edits**, **trim operations**, and **clip link groups**. These are real shipped backend contracts, not proposed features.

**For workflow guidance** (when to use marks vs hard-coded seconds, editorial judgment, pacing), see `pr0ta-timeline` and `pr0ta-editorial`. This file documents the API shapes.

---

## Asset Marks

Source-media marks stored on the asset. These travel with the asset and can be referenced in timeline edit operations.

**Endpoints:**

```
GET    /api/v2/projects/{project_id}/assets/{asset_id}/marks
POST   /api/v2/projects/{project_id}/assets/{asset_id}/marks
PATCH  /api/v2/projects/{project_id}/assets/{asset_id}/marks/{mark_id}
DELETE /api/v2/projects/{project_id}/assets/{asset_id}/marks/{mark_id}
```

**Create request:**

```json
{
  "name": "hook",
  "in": 1.0,
  "out": 3.5,
  "note": "Best source section"
}
```

**Behavior:**

- Marks are persisted on the asset's metadata.
- `in` and `out` are optional individually, but at least one must be present.
- If both are present, `out` must be greater than `in`.
- Asset marks can be referenced in 3-point edit `source.in` / `source.out` fields using `@mark:<name>` syntax.

---

## Program Marks

Program-time marks on the post-production timeline. These can be absolute (time-based) or transcript-word anchored.

**Endpoints:**

```
GET    /api/post-production/{project_name}/timeline/marks
POST   /api/post-production/{project_name}/timeline/marks
PATCH  /api/post-production/{project_name}/timeline/marks/{marker_id}
DELETE /api/post-production/{project_name}/timeline/marks/{marker_id}
```

### Time-based mark

```json
{
  "name": "carry_landing",
  "time": 8.4
}
```

### Transcript-word anchored mark

```json
{
  "name": "carry_landing",
  "anchorTo": {
    "type": "transcript_word",
    "assetId": "dialogue-asset-id",
    "clipId": "clip_dialogue_7",
    "wordIndex": 42
  }
}
```

**Behavior:**

- Anchored marks resolve program time from the currently placed clip for that dialogue asset.
- Anchors may target by `assetId`, by `clipId`, or by both together.
- Resolved time is exposed on reads as `time`.
- Read responses may include runtime-only fields: `resolvedTime`, `resolvedClipId`, `resolvedAssetId`, `resolvedWordStart`. These are derived and should not be treated as persistent write fields.
- Anchored marks follow timeline changes — when the underlying word's program time shifts (e.g. from a ripple edit), the mark's resolved time updates automatically.

### clipId disambiguation

**When the same dialogue asset is placed multiple times on the timeline**, the backend resolves the earliest matching clip whose source window contains the referenced word — unless `clipId` narrows it first.

- Send `clipId` without `assetId` when you already know the exact placed clip.
- Send both `assetId` and `clipId` when you have both — this keeps intent explicit and guards against stale clip references.
- `clipId` is the preferred disambiguation field for reused dialogue assets.

---

## 3-Point Edit Operations

NLE-standard 3-point editing: specify three of the four edit points (source in/out, program in/out) and the backend computes the fourth.

**Endpoints:**

```
POST /api/post-production/{project_name}/timeline/edits/preview
POST /api/post-production/{project_name}/timeline/edits
```

**Request shape:**

```json
{
  "mode": "insert",
  "source": {
    "assetId": "asset-src",
    "in": "@mark:hook",
    "out": 3.5
  },
  "program": {
    "in": "@mark:carry_landing"
  },
  "track": "video",
  "affectedTracks": ["overlay", "captions"],
  "label": "Inserted clip"
}
```

### Rules

- **Supported modes:** `insert`, `overwrite`.
- **Exactly three** of these four points must be supplied: `source.in`, `source.out`, `program.in`, `program.out`. The backend computes the missing fourth.
- `source.in` / `source.out` can be numeric seconds or `@mark:<asset-mark-name>`.
- `program.in` / `program.out` can be numeric seconds or `@mark:<program-mark-name>`.
- `affectedTracks` is optional. If omitted, behavior is target-track only. If supplied, the backend always includes the target `track` and applies the edit window to the additional listed tracks too.
- `insert` ripples downstream clips on the affected tracks and shifts non-anchored program marks at or after the insertion point by the inserted duration.
- `overwrite` replaces material in the target range on the affected tracks.

### Preview response

`/edits/preview` returns without committing:

```json
{
  "preview": true,
  "diff": {
    "added_clips": [...],
    "removed_clips": [...],
    "modified_clips": [...],
    "shifted_markers": [...]
  },
  "timeline": { ... }
}
```

For committed edits, `edit.affected_track_ids` reports the final track set the backend used.

### Guidance

Use `/edits/preview` before `/edits` whenever the agent is reasoning from marks rather than explicit seconds, or when it needs to explain downstream impact before committing. Preview is cheap — commit is permanent.

### Error cases

- Fewer or more than three points → `400`
- Invalid mark references → `400`
- Negative source or program windows → `400`

---

## Trim Operations

Fine-grained clip boundary adjustments with NLE-standard trim modes.

**Endpoints:**

```
POST /api/post-production/{project_name}/timeline/edits/{clip_id}/trim/preview
POST /api/post-production/{project_name}/timeline/edits/{clip_id}/trim
```

**Request shape:**

```json
{
  "mode": "ripple",
  "edge": "tail",
  "delta": 0.12,
  "affectedTracks": ["overlay"],
  "linked": true
}
```

### Supported modes

| Mode | Behavior |
|------|----------|
| `ripple` | Changes clip boundary and ripples downstream timing on the same track |
| `roll` | Adjusts boundary between selected clip and adjacent clip (total duration unchanged) |
| `slip` | Moves source window inside the clip without changing clip duration or position |
| `slide` | Moves the clip while compensating with adjacent clips |

### Linked trims

All four modes support `linked: true`:

- **`ripple` + `linked`** — applies the same ripple trim to linked companion clips on other tracks.
- **`roll` + `linked`** — applies the same boundary roll to linked companion clips.
- **`slip` + `linked`** — applies the same source-window shift to linked companion clips.
- **`slide` + `linked`** — applies the same slide movement to linked companion clips.

Linked trims fail (rather than partially applying) if a linked companion track is missing the adjacent clips required by that trim mode.

### affectedTracks

Only `ripple` currently supports `affectedTracks`. When supplied, the backend applies the ripple timeline change to those additional tracks too.

### Mark interaction

Ripple trims shift non-anchored program marks with the ripple timeline change. Anchored marks update automatically via their anchor resolution.

### Preview

`/trim/preview` returns the edit diff without committing — same preview shape as 3-point edit previews.

### Current limitations

- Grouped behavior is strongest for `ripple`, `slip`, and `slide` with linked clips. `roll` is more limited.
- Linked trims require valid adjacent clips on each affected track when the trim mode depends on them.

---

## Clip Link Groups

Persisted cross-track editorial relationships — the primary grouped-editing primitive. Common use case: linked A/V pairs where video and audio clips must move and trim together.

### CRUD and membership

```
GET    /api/post-production/{project_name}/timeline/links
POST   /api/post-production/{project_name}/timeline/links
DELETE /api/post-production/{project_name}/timeline/links/{link_group_id}
PATCH  /api/post-production/{project_name}/timeline/links/{link_group_id}
POST   /api/post-production/{project_name}/timeline/links/{link_group_id}/clips
DELETE /api/post-production/{project_name}/timeline/links/{link_group_id}/clips/{clip_id}
```

### Group operations

```
POST /api/post-production/{project_name}/timeline/links/{link_group_id}/move
POST /api/post-production/{project_name}/timeline/links/{link_group_id}/move/preview
POST /api/post-production/{project_name}/timeline/links/{link_group_id}/trim
POST /api/post-production/{project_name}/timeline/links/{link_group_id}/trim/preview
DELETE /api/post-production/{project_name}/timeline/links/{link_group_id}/clips
POST /api/post-production/{project_name}/timeline/links/{link_group_id}/clips/preview
```

### Create request

```json
{
  "clipIds": ["clip_video", "clip_audio"],
  "linkGroupId": "link_sync",
  "metadata": {
    "label": "A/V Pair",
    "kind": "av_pair",
    "note": "Primary sync",
    "locked": true
  }
}
```

### Metadata fields

- `label` — display name
- `kind` — group type (e.g. `av_pair`)
- `note` — free-text annotation
- `locked` — when `true`, mutating clip-level and group-level editorial operations against the group are rejected until unlocked

### Membership behavior

- Creating a group rewrites the specified clips into that group. If `linkGroupId` is omitted, one is generated.
- `PATCH .../links/{id}` updates group metadata without changing membership.
- `POST .../links/{id}/clips` incrementally adds clips; returns `addedClipIds` and the refreshed group.
- `DELETE .../links/{id}/clips/{clip_id}` removes one clip. If only one member remains, the backend auto-dissolves the group, clears `linkGroupId` from the singleton, and removes group metadata.
- Linked clips expose `linkGroupId` on clip objects in timeline reads and clip listings.

### Locked groups

**`locked` is enforced, not passive metadata.** When `metadata.locked` is `true`:

- Mutating clip-level operations (move, trim, delete) against group members are rejected.
- Group-level operations (move, trim, membership changes) are rejected.
- Unlock the group first via `PATCH .../links/{id}` with `{ "metadata": { "locked": false } }`.

### Grouped move

Move by delta:
```json
{ "delta": 2.5 }
```

Move by absolute placement of one member (rest follow by implied delta):
```json
{ "clipId": "clip_video", "start": 10.0 }
```

Optional `trackMap` remaps selected group members to new tracks:
```json
{ "delta": 2.5, "trackMap": { "clip_audio": "sfx" } }
```

### Grouped trim

```json
{ "clipId": "clip_video", "mode": "ripple", "edge": "tail", "delta": 0.5 }
```

Validates that `clipId` belongs to the addressed link group before applying. Uses the linked trim engine.

### Linked behavior on standard clip endpoints

These standard clip endpoints also support link-group awareness:

- `PATCH /timeline/clips/{clip_id}` — accepts `linked: true` and optional `linkedTrackMap`.
- `DELETE /timeline/clips/{clip_id}` — accepts `linked=true` query param. With `ripple=true`, collapses each affected track and shifts unanchored program marks.
- `POST /timeline/clips/reorder` — accepts `linked: true` and optional `linkedTrackMap`.
- All trim endpoints (`/edits/{clip_id}/trim` and `/trim/preview`) — accept `linked: true` for all four modes.

When `linked: true` is used with a `start` change, the backend shifts other clips in the same link group by the same delta. `linkedTrackMap` moves named companion clips to named destination tracks before applying the shift.

### Preview endpoints

All group operation endpoints have `/preview` variants that return the timeline diff without committing. Same preview shape as other editorial operations (`diff.added_clips`, `diff.removed_clips`, `diff.modified_clips`, `diff.shifted_markers`).

### Error cases

- Fewer than two unique clip IDs on create → `400`
- Unknown clip IDs → `400`
- Operations against a locked group → rejected until unlocked

---

## Current Limitations

- No broader edit-group system beyond explicit link groups.
- No richer multi-group orchestration layer.
- Multi-track trim and grouped-edit semantics are still narrower than a full desktop NLE — strongest for `ripple`, more limited for `roll`/`slip`/`slide`.
- Transcript-anchor disambiguation is strongest when the caller supplies `clipId` for reused dialogue assets.
