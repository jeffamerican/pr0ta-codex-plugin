---
name: pr0ta-timeline
description: "PR0TA post-production timeline guide for clip/track editing, Ken Burns, audio mix, preview/render, snapshots, editorial primitives, source shortfalls, fitToFill, and frame-aware diagnostics. Read when assembling or editing a cut."
---

# Post-Production Timeline

> **This is the primary and only editing surface.** The post-production timeline is a persistent, shared editing state that both AI agents (via the API) and human collaborators (via the browser) work on together. The agent adds clips, sets Ken Burns presets, configures audio, and previews segments through the API. The user opens the same timeline in their browser, scrubs through, reorders, trims, and approves. Both operate on the same persistent state — no rebuild required.
>
> **Assemble on the PR0TA post-production timeline.** All clip assembly, Ken Burns, audio mix, preview, and render happens through the app's timeline API. If the timeline is missing a capability you need for a production, file a bug with PR0TA platform engineering so it gets built into the app — the goal is to keep the full production loop inside PR0TA rather than shipping parallel local build pipelines.
>
> **This is the post-production timeline, not the narration timeline.** The narration timeline (`/api/v2/projects/{id}/narration-timeline/`) is a separate transcript-anchored system for building verified cut lists. Once your narration cuts are verified, you **materialize** them into the post-production timeline and continue editing from there. See "Narration Materialization" below.

## Why Timeline-First

The old workflow required writing a full build script for every edit. A single-shot fix — swap one image, adjust one cut point — meant rebuilding the entire pipeline. The timeline eliminates this:

- **Persistent state.** Add a clip, it stays. Trim it, the trim persists. No rebuild.
- **Incremental edits.** A single-shot fix is a single API call, not a full pipeline re-run.
- **Fast preview.** Verify a 10-second segment in seconds instead of rendering the full piece.
- **Collaboration.** The user makes taste decisions (pacing, ordering) directly. The agent handles generation, motion, and mix.
- **Ken Burns as a property.** The platform owns zoompan rendering — super-resolution, FPS consistency, and duration-aware formulas are handled internally. The agent never writes a zoompan expression.
- **Audio mix as metadata.** Ducking, volume, crossfades are timeline properties you set with a single API call.

## API Endpoints

Base prefix: `/api/post-production/{project_id}`

Full request/response schemas are in `pr0ta-api` → "Post-Production Timeline API". This section covers the workflow.

### Core Rule: Concurrent Audio on Separate Tracks

PR0TA enforces NLE-standard track separation: **one track is one linear lane.** If narration and music should play at the same time, they must be on different audio tracks. Overlapping audio clips on the same track are invalid — the renderer will fail with a clear error.

**Recommended track layout:**

| Track ID | Type | Purpose |
|----------|------|---------|
| `video` | video | Visual clips |
| `dialogue` | audio | Narration / dialogue |
| `music` | audio | Score / background music |
| `sfx` | audio | Sound effects / foley |
| `titles` | title | Title cards / lower thirds |

**Always create audio tracks before adding clips.** Use `POST /timeline/tracks` (below) to create tracks individually — do not rewrite the full `tracks[]` array through `PATCH /timeline`, which is error-prone because stale payloads can restore deleted clips.

### Track Creation

| Endpoint | Purpose |
|----------|---------|
| `POST /timeline/tracks?sequence_id=timeline_v2` | Create an empty track |

```json
{
  "id": "dialogue",
  "type": "audio",
  "label": "Dialogue",
  "position": 2
}
```

- `id` — stable, caller-controlled identifier
- `type` — `video`, `audio`, or `title`
- `position` — optional; if omitted, the new track is appended
- Creates an empty track only — add clips separately via `POST /timeline/clips`

**Typical flow for narration + music:**
1. `POST /timeline/tracks` → `{"id": "dialogue", "type": "audio", "label": "Dialogue"}`
2. `POST /timeline/tracks` → `{"id": "music", "type": "audio", "label": "Music"}`
3. Post narration clips to `dialogue` track
4. Post music clips to `music` track

### Timeline State

| Endpoint | Purpose |
|----------|---------|
| `GET /timeline` | Returns the main sequence |
| `POST /timeline` | Save/merge timeline-level fields — merges submitted keys into the existing timeline state (does not replace keys you omit) |
| `PATCH /timeline` | Partial update of timeline-level fields — preferred for targeted changes like updating `audioMix` without touching anything else |
| `GET /timeline/state?sequence_id=timeline_v2` | Normalized timeline state plus `_clip_index` |
| `GET /timeline/clips?sequence_id=timeline_v2` | Flattened clip list with track metadata |

**`POST /timeline` is a merge, not a replace.** Submitting `{ "audioMix": { ... } }` updates `audioMix` without touching clips, snapshots, or other timeline fields. You do not need to send the full timeline payload every time. `PATCH /timeline` behaves identically for partial updates and is the preferred endpoint when you are updating a single field.

Both endpoints return the updated `version` (integer, incremented on every save) and `lastSaved` (ISO 8601 datetime with timezone offset, e.g. `2026-04-12T19:39:30.991013+00:00`).

Use `GET /timeline/state` to read the full current edit. Use `GET /timeline/clips` when you only need the clip list (lighter response, easier to iterate).

### Clip CRUD

| Endpoint | Purpose |
|----------|---------|
| `POST /timeline/clips?sequence_id=timeline_v2` | Create a clip with placement instructions |
| `PATCH /timeline/clips/{clip_id}?sequence_id=timeline_v2` | Update clip properties, move to another track |
| `DELETE /timeline/clips/{clip_id}?sequence_id=timeline_v2&ripple=true` | Delete a clip with optional ripple shift |
| `POST /timeline/clips/reorder?sequence_id=timeline_v2` | Batch reorder clips (placement and start updates) |

**Ripple delete** (`ripple=true`): removes the clip and shifts subsequent clips on the same track to close the gap. Without ripple, a gap is left.

**Canonical `POST /timeline/clips` payload:**

```json
{
  "clip": {
    "assetId": "asset_123",
    "start": 0,
    "duration": 2.5,
    "kenBurns": { "preset": "push_in" }
  },
  "placement": {
    "track_id": "video",
    "position": 0
  }
}
```

The clip data is nested under a `clip` key and placement data under a `placement` key. Use `track_id` (not `track`) in `placement`. Legacy flat payloads (where clip and placement fields are mixed at the top level) may still be accepted for compatibility, but the nested form above is the canonical contract.

**`POST /timeline/clips` always creates a new clip — it does not upsert.** Running the same edit logic twice doubles your clips. If you are iterating and may have already added a clip for a given shot, read the current clip list via `GET /timeline/clips` first. To update a clip's `start` / `duration` / `kenBurns`, use `PATCH /timeline/clips/{clip_id}`. To replace a clip, `DELETE` the old one (with `ripple=true` if you want subsequent clips to shift) and then `POST` the new one. Field-observed failure mode: ~30 intended clips ballooned to 72 after iterative append-only POSTs.

### Timing and Duration Semantics

There are two distinct levels of duration in the timeline:

**Sequence-level duration** is the total length of the edited sequence — derived from the last clip's end time. It is not a field you set directly; it is computed from the clip arrangement. Returned in `GET /timeline` and `GET /timeline/state`.

**Clip-level timing** is authoritative and expressed in seconds:

- `start` — the clip's start position on the timeline, in seconds.
- `duration` — the clip's playback duration on the timeline, in seconds.

Some API responses also include `start_ms` and `duration_ms` — these are millisecond-precision equivalents provided as compatibility/precision helpers. They are **not a separate conflicting model**: `start_ms = start × 1000`, `duration_ms = duration × 1000`. When both are present, treat the seconds fields as canonical and the ms fields as convenience accessors. Do not assume that `start` is always `0.0` or `duration` is always `1.0` — these are real clip-level values derived from the actual edit.

**Timestamp fields** across the timeline API use ISO 8601 datetimes with timezone offsets (e.g. `2026-04-12T19:39:30.991013+00:00`). This applies to `lastSaved`, `history[].timestamp`, and `snapshots[].created_at`.

### Ken Burns as a Clip Property

Set Ken Burns on any clip via `POST` (create) or `PATCH` (update). The platform renders it at export time using MLT `affine` filters with super-resolution handled internally.

**Preset:**
```json
{ "kenBurns": { "preset": "push_in" } }
```

Available presets: `push_in`, `pull_back`, `drift_left`, `drift_right`, `ken_burns_slow`, `hold`, `zoom_in_extreme`, `push_in_fast`

**Custom parameters:**
```json
{
  "kenBurns": {
    "start_zoom": 1.0,
    "end_zoom": 1.15,
    "pan": [0, 0],
    "easing": "linear"
  }
}
```

Easing options: `linear`, `ease_in_out`

**What the platform handles:** super-resolution (2x + lanczos), FPS consistency, duration-aware zoom formulas, dimension normalization to timeline delivery resolution. The agent sends a preset name or custom params — nothing else.

### Audio Mix

Audio mix properties are set at the timeline level via `POST /timeline` (or `PATCH /timeline`):

```json
{
  "audioMix": {
    "ducking": [
      {
        "sourceTrack": "music",
        "keyTrack": "dialogue",
        "duckedGain": 0.35,
        "attackMs": 300,
        "releaseMs": 500
      }
    ],
    "narrationOffsetMs": 1500
  }
}
```

**`ducking` is an array of rules**, not a single object. Each rule specifies one ducking relationship (e.g. music ducks under dialogue). You can have multiple rules to duck different source tracks against different key tracks.

**`duckedGain` is the canonical ducking field.** It is the fraction of nominal source-track volume while the key track is active: `1.0` = no ducking, `0.5` ≈ −6 dB, `0.0` = full mute. The old `threshold` field is a deprecated alias — the backend still accepts it but normalizes it to `duckedGain`. Always send `duckedGain` in new code.

**camelCase is the documented standard** for all audioMix fields (`sourceTrack`, `keyTrack`, `duckedGain`, `attackMs`, `releaseMs`, `narrationOffsetMs`). Legacy snake_case forms may still be accepted for compatibility, but always send camelCase in new code.

Per-clip and per-track volume is set via clip properties. At render time, ducking is applied as generated gain automation on affected clips (not a true sidechain compressor — the platform uses animated MLT gain envelopes). Crossfades and dissolves between adjacent clips are synthesized at render time via overlay playlists.

### Audio Level Keyframes (`volumeKeyframes`)

For fine-grained mix control beyond ducking, use `volumeKeyframes` — available on both audio tracks and individual audio clips.

**Track-level** (`PATCH /timeline/tracks/{track_id}`) — keyframe times are absolute program time. Use for broad lane moves: lower the music bed from 20s–35s, ramp SFX under a title.

**Clip-level** (`PATCH /timeline/clips/{clip_id}`) — keyframe times are relative to clip start. Use for source-specific moves: fade in a music clip, boost dialogue at the end.

The renderer multiplies both: `final gain = track gain × clip gain`. Each keyframe has `time` (seconds), `value` (linear gain: `1.0` = unchanged, `0.5` ≈ −6 dB, `0.0` = silence; clamped 0–4), and optional `interpolation` (`linear` or `hold`). The backend also accepts `db`/`decibels` values (converted to linear). `/audio/analyze` now returns each segment's `render_gain_envelope` using the same frame/gain path that MLT render uses; `/audio/meter` renders through MLT and meters the actual mix. See `pr0ta-api` → `reference/timeline-api.md` → "Audio Level Keyframes" for the full field contract and compatibility aliases.

**Interaction with ducking:** Ducking generates clip-level `volumeKeyframes` on ducked clips. If both manual keyframes and ducking are present, PR0TA merges them. Use `audioMix.ducking` for automatic dialogue-aware ducking; use `volumeKeyframes` for intentional manual mix moves.

**Post-render music check:** After any render with music automation, verify that music remains audible in narration gaps. Use `/audio/analyze` to inspect `render_gain_envelope`, `/audio/meter` to meter the same MLT path, or a rendered preview/audio export around at least one narration-quiet window. If the full mix is silent during a gap where music should be present, treat the render as failed and file the render task ID with the gain-envelope payload.

### Transitions

Set transitions on clips via `PATCH`:

```json
{ "transition": { "type": "dissolve", "duration_ms": 500 } }
```

Supported types: `dissolve`, `crossfade`, `fade-up`, `fade-to-black`, `wipe`

Adjacent same-track dissolves and crossfades are synthesized as outgoing-tail overlay playlists with timed fade filters. Wipes use directional incoming overlays. This is limited to adjacent cuts — it's not a full transition engine yet, but it covers the common editorial cases.

### Preview, Audio Preview, and Render

| Endpoint | Purpose |
|----------|---------|
| `GET /preview?from={s}&to={s}&sequence_id=timeline_v2` | Video+audio preview (defaults to full sequence resolution) |
| `GET /preview/audio?from={s}&to={s}&sequence_id=timeline_v2` | Audio-only preview (`.wav`) — fast, no picture render |
| `GET /audio/analyze?from={s}&to={s}&sequence_id=timeline_v2` | Render-envelope audio prediction — levels, ducking impact, mix balance, `render_gain_envelope` (no media render) |
| `GET /audio/meter?from={s}&to={s}&sequence_id=timeline_v2` | Actual LUFS/LRA/true-peak metering (renders audio via MLT + ebur128) |
| `POST /render` | Preview render — loads saved timeline automatically (control-only body is valid) |
| `POST /export` | Final export — master delivery render |
| `GET /render/{task_id}/status` | Poll render/preview task status |

**Preview quality:** If `quality` is omitted, preview renders at **full sequence resolution**. Send `quality=low` or `quality=preview` for a lightweight half-res preview. Send `quality=full` (or omit) for pixel-accurate checks.

### Frame-Accurate Picture Cuts

Treat video/title edits as frame-native NLE intervals, not decimal-second guesses. PR0TA normalizes picture clips to `[startFrame, endFrame)` on save/render and derives seconds from the sequence frame rate.

- Use `startFrame`, `durationFrames`, `sourceInFrame`, and `sourceOutFrame` for frame-critical repairs.
- Same-track picture gaps or overlaps of 1-2 frames are editorial drift. Preserve the incoming cut frame and adjust the outgoing side.
- For narration/beat-aligned edits, do not pull incoming cut-ins earlier unless the user asks for a timing change.
- Boundary checkerboard repairs should use an outgoing tail handle/underlap, usually 4-8 frames, under the beat-locked incoming shot.
- Do not fix render-boundary defects by holding the last frame. Trim, retime, extend/regenerate source media, add an outgoing tail handle, or replace the shot.
- After a repair, read `/timeline/clips` and verify `startFrame`, `endFrame`, `endFrameInclusive`, and `durationFrames` match the intended cut.

**Render preview:** `POST /render` is the preview-task route. It loads the saved post-production timeline automatically. Send an empty body `{}` or control-only fields (`from`, `to`, `resolution`, `width`, `height`, `format`). You do not need to send full timeline JSON. If the timeline contains zero clips, the route returns `400`.

**Final export:** `POST /export` is the final-export route for master delivery renders. Use `POST /render` during editorial iteration; use `POST /export` when the cut is locked and ready for delivery.

**Escalation pattern — cheapest check first:**
1. **`/audio/analyze`** — instant render-envelope diagnostic. Use to check: is narration much louder than music? Did ducking attenuate a track? Is a segment effectively silent? Returns per-track `source_mean_db`, `predicted_mean_db`, `predicted_peak_db`, `render_gain_envelope`, ducking flags, and an overall mix summary.
2. **`/audio/meter`** — actual loudness metering. Renders audio through MLT and measures with `ffmpeg ebur128`. Returns `integrated_lufs`, `range_lu`, `true_peak_dbfs`, and a `short_term_lufs_timeline`. Use when verifying the mix meets loudness spec (e.g. −14 LUFS for streaming).
3. **`/preview/audio`** — ear-based review. Renders a `.wav` preview. Use `tracks=dialogue,music` to solo specific tracks. Use when you need to actually hear the mix.
4. **`/preview`** — full picture+sound verification. Use only when you need to see visuals alongside audio.

For music beds, include at least one narration-gap check after the render. A practical pattern is: identify a quiet narration interval, meter or listen to that window, and confirm the music track is above the noise floor. Do not rely only on whole-file loudness.

All audio endpoints (`/preview/audio`, `/audio/analyze`, `/audio/meter`) accept an optional `tracks` parameter (comma-separated track IDs) to solo specific tracks.

**Preview is the verification gate.** Before handing off to the user, preview key segments to confirm sync, motion quality, and pacing. A 10-second preview takes seconds, not the 15–20 minutes of a full rebuild.

**If a full render returns `"Cannot run the event loop while another loop is running"`**, you have hit the nested-asyncio bug observed in field production (SINGULARITY_The_Festival_1775984660, April 2026). This is a platform bug — file it with PR0TA engineering rather than working around it with a local ffmpeg pipeline. Keeping productions on the timeline is the point; parallel local assembly is how we end up with two codebases drifting. If the bug is blocking a delivery, snapshot the timeline and coordinate with platform engineering before resorting to a local render.

### Editorial Primitives: Marks, Edits, Trims, Link Groups

The post-production timeline now exposes a first-class editorial primitive surface for precise, mark-driven editing. **For the full API shapes and endpoint contracts, Read `pr0ta-api` → `reference/editorial-primitives.md`.** This section covers the workflow.

#### Asset Marks and Program Marks

**Use marks instead of hard-coding seconds whenever possible.** Marks are persisted anchors that survive timeline edits — hard-coded seconds break when clips move.

- **Asset marks** (`POST /api/v2/projects/{id}/assets/{asset_id}/marks`) — source-media in/out points stored on the asset. Use to mark the "best section" of a clip before placing it on the timeline.
- **Program marks** (`POST /timeline/marks`) — story anchors on the timeline. Can be absolute (time-based) or **transcript-word anchored** — anchored marks follow timeline changes automatically when the underlying word's program time shifts.

**`clipId` is the preferred disambiguation field** for transcript-word anchored marks when the same dialogue asset appears multiple times on the timeline. Always send `clipId` (and `assetId` when you have it) to keep intent explicit.

#### 3-Point Edits

NLE-standard 3-point editing: specify three of the four edit points (source in/out, program in/out) and the backend computes the fourth.

```
POST /timeline/edits/preview   — inspect downstream impact without committing
POST /timeline/edits           — commit the edit
```

Supported modes: `insert` (ripples downstream), `overwrite` (replaces in range). Source and program points can reference marks with `@mark:<name>` syntax. Optional `affectedTracks` extends the edit to additional tracks.

**Source shortfall behavior:** If the source media is shorter than the requested program range, PR0TA inserts only the available source and leaves a real gap — no freeze-padding. The edit response includes a `source_shortfall` warning with `requestedDuration`, `insertedDuration`, `shortfallDuration`, `gapStart`, and `gapEnd`. Surface this to the user. To retime the source to fill the program range instead, send `fitToFill: true` — this writes a `speed` value on the clip (`< 1.0` = slow motion, `> 1.0` = speed-up). `fitToFill` also supports true four-point edits (source in/out + program in/out). Before render, confirm the clip read/list output shows `fitToFill`, `speed`, `sourceSpan`, `programDuration`, and `effectivePlaybackDuration`; if the effective duration does not cover the program duration, treat it as a render-risk and fix the source/edit rather than shipping. See `pr0ta-api` → `reference/source-shortfalls-and-fit-to-fill.md` for the full contract.

**Always preview before committing** when reasoning from marks rather than explicit seconds — preview is cheap, commit is permanent.

#### Trim Operations

Fine-grained clip boundary adjustments:

```
POST /timeline/edits/{clip_id}/trim/preview
POST /timeline/edits/{clip_id}/trim
```

Four modes: `ripple`, `roll`, `slip`, `slide`. All four support `linked: true` to apply the same trim to linked companion clips across tracks. Only `ripple` currently supports `affectedTracks` for explicit multi-track participation.

#### Clip Link Groups

Persisted cross-track editorial relationships — use for linked A/V pairs where video and audio clips must move and trim together.

```
POST /timeline/links           — create a link group
GET  /timeline/links           — list link groups
```

Key behaviors:
- Link groups persist `linkGroupId` on clip objects.
- **`locked` is enforced, not passive metadata** — when a group is locked, all mutating operations against its members are rejected until unlocked.
- Grouped move supports `delta`, absolute `{clipId, start}` placement, and `trackMap` for cross-track remapping.
- Standard clip endpoints (`PATCH /timeline/clips/{id}`, `DELETE /timeline/clips/{id}`, `POST /timeline/clips/reorder`) accept `linked: true` and optional `linkedTrackMap`.

**Typical A/V sync workflow:**
1. Place video clip on `video` track, dialogue clip on `dialogue` track
2. `POST /timeline/links` with both clip IDs → creates a link group
3. All subsequent moves and trims on either clip propagate to its linked partner
4. Lock the group (`PATCH .../links/{id}` with `locked: true`) when sync is confirmed

### Snapshots and History

| Endpoint | Purpose |
|----------|---------|
| `GET /timeline/history?sequence_id=timeline_v2` | Recent mutation/save history (reverse chronological) |
| `POST /timeline/snapshot?sequence_id=timeline_v2` | Create or replace a named snapshot |
| `GET /timeline/snapshots?sequence_id=timeline_v2` | List saved snapshots |
| `POST /timeline/snapshot/{name}/restore?sequence_id=timeline_v2` | Restore a snapshot into the active sequence |
| `GET /timeline/snapshot/{name}/diff?sequence_id=timeline_v2` | Diff current state vs a snapshot (added/removed/modified clips) |

**Always snapshot before major passes.** Create a named snapshot before the agent does a big edit pass, before user review, or before any operation that touches many clips. If something goes wrong, restore to the snapshot instead of rebuilding.

## Narration Materialization

If you're building a narration-driven production (documentary, explainer, anything with a transcript), start in the narration timeline, then materialize:

```
POST /api/v2/projects/{project_id}/narration-timeline/materialize-to-post-production
```

Response includes `timeline`, `clip_count`, and `sequence_name`.

The materializer:
- Reads narration timeline cuts in order
- Resolves matching assets to stable PR0TA asset URLs
- Creates post-production clips with stable IDs
- Preserves transcript anchor provenance under `metadataOverrides.origin`
- Converts narration motion into `kenBurns` metadata
- Converts supported narration transitions into post-production transition metadata
- Creates narration and music audio clips when audio layers exist
- Writes narration offset and ducking intent into `timeline.audioMix`

After materialization, the narration timeline's job is done. All further editing happens on the post-production timeline.

## Standard Production Workflow

### 1. Generate Assets
Generate images, video, narration, and music via the PR0TA API (unchanged from before).

### 2. Create Tracks
Before adding any clips, create the tracks you need via `POST /timeline/tracks`. At minimum: `video`, `dialogue`, `music`. Add `sfx` and `titles` if your production uses them. Never stack concurrent audio on the same track.

### 3. Build the Edit
**If narration-driven:** build and verify cuts in the narration timeline, then materialize to post-production.

**If not narration-driven:** add clips directly via `POST /timeline/clips` with Ken Burns presets and placement. Place narration clips on the `dialogue` track and music clips on the `music` track.

### 4. Configure Audio
Set ducking rules (array), narration offset, and per-clip volume via `POST /timeline` or `PATCH /timeline` (timeline-level) and `PATCH /timeline/clips/{id}` (clip-level). Use camelCase field names (`sourceTrack`, `keyTrack`, `attackMs`, `releaseMs`). For fine-grained level automation, write `volumeKeyframes` on tracks (`PATCH /timeline/tracks/{id}`) for lane-wide moves or on clips (`PATCH /timeline/clips/{id}`) for source-specific fades and ramps.

### 5. Check the Mix
Use the escalation pattern — cheapest check first:
1. `GET /audio/analyze` — quick render-envelope level/balance diagnostic
2. `GET /audio/meter` — actual LUFS/LRA/true-peak if you need loudness spec compliance
3. `GET /preview/audio` — listen to the audio mix without rendering video
4. `GET /preview` — full picture+sound only when needed (omit `quality` for full-res, `quality=low` for fast)

### 6. Mark Key Points
Place program marks on story anchors (key words, beat changes, section boundaries) via `POST /timeline/marks`. Use `label` and `description` fields to communicate editorial intent — a mark labeled "Credits In" with description "Credits should begin here" is immediately actionable for any future agent or collaborator. Use transcript-word anchoring when possible — these marks survive timeline edits. Place asset marks on source clips to tag best-use sections.

### 7. Analyze Before Render
Call `GET /timeline/analysis` before any render or export. This returns gaps, overlaps, reused media, source shortfalls, frame coverage, and track coverage — the same diagnostics a professional NLE surfaces before output. Warn on unintended gaps on primary tracks, on reused visual media (same asset in multiple clips) unless deliberate, and on source shortfalls where clips are shorter than their program range. If `summary.sourceShortfallCount > 0`, present the affected clips and ask whether to leave the gap, choose another source, or retime with `fitToFill`. For retimed I2V clips, also inspect clip timing metadata or the debug report and verify `effectivePlaybackDuration >= programDuration` within frame tolerance. Use `trackCoverage` to distinguish critical gaps from empty overlay lanes. Render/export responses can return `timelineMediaGaps[]` for deterministic no-media coverage and `renderedPixelGaps[]` for post-render transparent/checkerboard frames. Treat both as hard review items and repair by frame range, not by loose timestamp. See `pr0ta-api` → `reference/asset-tags-and-analysis.md` for the full response shape and `reference/source-shortfalls-and-fit-to-fill.md` for source shortfall details.

### 8. Snapshot
Create a named snapshot: `POST /timeline/snapshot` with `{ "name": "agent-pass-1" }`.

### 9. Hand Off to User
Tell the user the timeline is ready for review. They open it in the browser at `app.pr0ta.com/timeline`, scrub through, and make direct adjustments — reorder, trim, swap clips, adjust pacing.

### 10. Read Back and Address Notes
After the user makes changes, read the updated state with `GET /timeline/state`. See what changed. Address remaining notes with targeted clip edits, not a full rebuild.

### 11. Final Export
Use `POST /export` for final delivery. Use `POST /render` for preview-task rendering during editorial iteration.

## Collaborative Model

| Actor | Works Via | Does What |
|-------|-----------|-----------|
| AI Agent | Timeline API | Generates assets, adds to timeline, sets Ken Burns and ducking, verifies alignment via preview |
| Human User | Browser UI | Scrubs, reorders, trims, swaps clips, adjusts pacing, approves or rejects |
| AI Agent (round 2) | Timeline API | Reads current state, sees user changes, addresses remaining notes, re-renders only what changed |

The agent's job is **editorial judgment** — what goes where, what motion, what pacing. Not mechanical assembly. The user gets to collaborate rather than request-and-wait.

## Sequence Settings

Set sequence resolution before adding clips. Common presets:
- **1920×1080 @ 30fps** — standard HD
- **1080×1920 @ 30fps** — vertical / social media
- **3840×2160 @ 24fps** — 4K cinematic

The timeline normalizes all clips to the delivery resolution automatically. No manual dimension normalization needed. The user can view and edit the timeline at `app.pr0ta.com/timeline` — API changes appear in the browser on refresh, and vice versa.

## Tips

- **Create separate audio tracks first.** Always `POST /timeline/tracks` for `dialogue`, `music`, and `sfx` before adding clips. Concurrent audio on the same track is invalid and the renderer will reject it.
- **Use track aliases for readability.** Tracks expose NLE aliases (`V1`, `A1`, `A2`) alongside raw IDs. Use `GET /timeline/tracks` to read the alias map, then use raw IDs in scripts and aliases in human-facing output. See `pr0ta-api` → `reference/timeline-api.md` → "Track Targeting".
- **Use `/audio/analyze` before rendering.** Catch level imbalances and ducking issues instantly, without waiting for a render. Escalate to `/preview/audio` for ear-based checks, then full `/preview` only when you need picture.
- **Snapshot before every major pass.** Agent pass, user review, big reorder — always snapshot first.
- **Preview, don't render.** Use the preview endpoint to check segments. Only render when you're ready for final delivery.
- **Read state after user edits.** The user may have reordered, trimmed, or swapped clips. Read `GET /timeline/state` before making further API edits.
- **Ken Burns presets cover most cases.** Use `push_in` for emphasis, `pull_back` for reveal, `drift_left`/`drift_right` for lateral movement, `hold` for static shots. Custom params only when you need specific zoom ranges.
- **Ducking is an array of gain-automation rules, not sidechain.** Each ducking rule in the `ducking[]` array generates animated gain envelopes at render time. It works well for standard narration-over-music but isn't a full compressor graph. Multiple rules can coexist for different track pairs.
- **Use `volumeKeyframes` for manual mix moves.** Track-level keyframes (absolute time) for lane-wide automation (lower the music bed). Clip-level keyframes (clip-relative time) for source-specific fades. Both multiply at render time. For dB input, use `{"time": 3.0, "db": -6.0}` — the backend converts to linear gain.
- **Use `POST /timeline/tracks`, not `PATCH /timeline` to add tracks.** Rewriting the full `tracks[]` array through PATCH is error-prone — stale payloads can restore deleted clips.
- **Use marks instead of hard-coded seconds.** Asset marks and program marks survive timeline edits. Hard-coded seconds break when clips move. Use `@mark:<name>` syntax in 3-point edits for robust mark-driven editing.
- **Preview before committing edits.** Use `/edits/preview` and `/trim/preview` to see the diff before the change is permanent. Especially important when reasoning from marks.
- **Link A/V pairs early.** Create link groups as soon as you place synced video+audio clips. Linked clips move and trim together, preventing sync drift.
- **Lock link groups after sync confirmation.** A locked group rejects all mutating operations, protecting confirmed sync from accidental edits.
- **Source shortfalls leave real gaps — no freeze-padding.** If you edit in a clip that's shorter than the program range, PR0TA inserts only the available media and leaves the tail as a gap. Check edit response warnings for `source_shortfall`. To fill the gap with retimed media, re-edit with `fitToFill: true`. To fill it with different media, overwrite the gap region with a new source.
- **Render warnings need adjudication.** For every `timelineMediaGaps[]` or `renderedPixelGaps[]` item, use `startFrame`, `endFrame`, and timecode, attach the thumbnail or frame path to your notes, classify the warning, and record the clip/frame-range repair. Do not clear warnings based only on black-frame checks.
- **Use the app's timeline for assembly.** Clip CRUD, Ken Burns, audio mix, preview, and render all live on the post-production timeline. If you hit something the timeline can't handle, file a bug with PR0TA platform engineering so it gets fixed in the app — that's better for every future production than one-off local workarounds.
