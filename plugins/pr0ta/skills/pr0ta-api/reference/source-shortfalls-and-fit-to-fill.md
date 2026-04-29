## Source Shortfalls and Fit To Fill

PR0TA treats too-short source media like a professional NLE: it cuts only the available source and leaves a real timeline gap for the unfilled tail. Retiming is never implicit — it must be requested explicitly via `fitToFill`.

For generated I2V card edits, compare the generated source duration to the intended beat duration before placement. If the source is shorter, either generate/extend a long enough animation or place it through `/timeline/edits` with `fitToFill: true`. Do not place a 3-5s animation into an 8-10s beat through raw clip creation and hope the renderer will pad it.

---

### Default Behavior: Source-Accurate Edits

When the requested program range is longer than the available source media, PR0TA inserts only the available source and leaves a gap.

**Example:** If `asset_short` is 3 seconds long and the edit requests 5 seconds:

```json
{
  "mode": "overwrite",
  "track": "V1",
  "source": {"assetId": "asset_short", "in": 0},
  "program": {"in": 52.0, "out": 57.0},
  "label": "Short source edit"
}
```

The inserted clip is 3 seconds. The interval from 55.0 to 57.0 remains a real timeline gap.

**Edit response includes a `source_shortfall` warning:**

```json
{
  "edit": {
    "computed": {
      "source": {"assetId": "asset_short", "in": 0.0, "out": 3.0},
      "program": {"in": 52.0, "out": 57.0},
      "clipDuration": 3.0,
      "editDuration": 5.0,
      "fitToFill": false
    },
    "warnings": [
      {
        "kind": "source_shortfall",
        "assetId": "asset_short",
        "requestedDuration": 5.0,
        "insertedDuration": 3.0,
        "availableSourceDuration": 3.0,
        "shortfallDuration": 2.0,
        "gapStart": 55.0,
        "gapEnd": 57.0
      }
    ]
  }
}
```

**Skill guidance:**

- Treat `source_shortfall` as user-visible editorial information — always surface it.
- Do not assume PR0TA filled the duration with a freeze frame. It did not.
- If the user did not ask for retiming, preserve the gap and report it.
- If the user wants the gap filled, offer retiming (`fitToFill`) or a different media choice.

---

### Timeline Analysis: Source Shortfalls

`GET /api/post-production/{project_name}/timeline/analysis?sequence_id=timeline_v2`

The analysis response includes source-shortfall diagnostics in `summary.sourceShortfallCount` and the `sourceShortfalls[]` array:

```json
{
  "summary": {
    "gapCount": 3,
    "reusedMediaCount": 2,
    "sourceShortfallCount": 1
  },
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
      "renderRisk": "transparent_or_checkerboard_tail",
      "recommendation": "Use fitToFill=true on a three-point edit or set clip speed explicitly if retiming is desired."
    }
  ]
}
```

**Recommended skill behavior before render/export:**

1. Call `/timeline/analysis`.
2. If `summary.sourceShortfallCount > 0`, warn the user.
3. Present the affected clips, tracks, and gap intervals.
4. Treat `renderRisk: "transparent_or_checkerboard_tail"` as a visible failure risk, especially for image-labeled I2V videos.
5. Ask whether to leave the gap, choose another source, generate/extend a longer clip, or retime with fit-to-fill.

For complete agent preflight, call:

```
GET /api/post-production/{project_name}/timeline/debug-report?sequence_id=timeline_v2
```

The debug report bundles track coverage, primary visual gaps, source-duration-vs-program-duration, retime state, audio asset presence, keyframe counts, and render-risk warnings in one response.

---

### Per-Clip Shortfall Metadata

`GET /api/post-production/{project_name}/timeline/clips?sequence_id=timeline_v2`

When a clip exceeds available source media, the clip entry includes `sourceShortfall`:

```json
{
  "id": "clip_short",
  "label": "Short source edit",
  "trackId": "video",
  "trackAlias": "V1",
  "trackType": "video",
  "trackLabel": "Primary Video",
  "duration": 5.0,
  "sourceShortfall": {
    "kind": "source_shortfall",
    "requestedDuration": 5.0,
    "availableSourceDuration": 3.0,
    "shortfallDuration": 2.0,
    "gapStart": 55.0,
    "gapEnd": 57.0
  }
}
```

Use `/timeline/clips` when working clip-by-clip. Use `/timeline/analysis` for full preflight diagnostics.

Clip reads/lists also expose retime state when known: `fitToFill`, `speed`, `sourceDuration`, `programDuration`, `sourceInPoint`, `sourceOutPoint`, `sourceSpan`, `effectivePlaybackDuration`, and `retimeReason`.

---

### Explicit Retiming: `fitToFill`

When the user explicitly wants the source fit to the requested program range, send `fitToFill: true` on 3-point or 4-point edits.

**Endpoints:**

```
POST /api/post-production/{project_name}/timeline/edits
POST /api/post-production/{project_name}/timeline/edits/preview
```

Raw `POST /timeline/clips` is not the canonical retiming path. It can accept `fitToFill` only when the payload also provides `outPoint`, `sourceMedia.duration`/`sourceDuration`, or an explicit positive `speed`; otherwise it returns a validation error so agents know to use `/timeline/edits`.

#### Three-Point Fit To Fill (Slow Motion)

Source is shorter than the program range → PR0TA slows the clip to fill:

```json
{
  "mode": "overwrite",
  "track": "V1",
  "source": {"assetId": "asset_short", "in": 0},
  "program": {"in": 52.0, "out": 57.0},
  "label": "Retimed short source",
  "fitToFill": true
}
```

If the available source is 3 seconds and the program range is 5 seconds:

```json
{
  "duration": 5.0,
  "inPoint": 0.0,
  "outPoint": 3.0,
  "fitToFill": true,
  "speed": 0.6
}
```

#### Four-Point Fit To Fill (Speed Up)

`fitToFill` also supports true four-point edits: source in/out plus program in/out.

```json
{
  "mode": "overwrite",
  "track": "V1",
  "source": {"assetId": "asset_long", "in": 0, "out": 8},
  "program": {"in": 10, "out": 14},
  "label": "Four-point fit",
  "fitToFill": true
}
```

This maps 8 seconds of source into 4 seconds of timeline:

```json
{
  "duration": 4.0,
  "inPoint": 0.0,
  "outPoint": 8.0,
  "fitToFill": true,
  "speed": 2.0
}
```

#### Speed Semantics

- `speed = 1.0` — normal speed (no retiming).
- `speed < 1.0` — slow motion. Source plays slower to fill a longer program range.
- `speed > 1.0` — speed-up. Source plays faster to fit a shorter program range.

#### Without `fitToFill`

Edit requests remain strict 3-point edits: exactly three of `source.in`, `source.out`, `program.in`, and `program.out` must be supplied.

---

### Skill Guidance

- **Default (no `fitToFill`):** Use when the user wants source-accurate cutting and a visible/diagnosable gap. The gap appears in `/timeline/analysis` and can be addressed later.
- **`fitToFill: true`:** Use only when the user explicitly wants automatic retiming. The written `speed` value is part of the clip state and affects the renderer.
- **Manual `speed`:** Use when the user wants a specific slow-motion or speed-up value rather than automatic calculation.
- **Do not rely on freeze frames as padding.** PR0TA does not freeze-pad. If a clip is too short and `fitToFill` is not set, the tail is a real gap.
- **Verify transparent/checkerboard tails.** Black-frame scans are not enough. Render a preview and sample frames around every `programDuration > sourceDuration` beat or every `sourceShortfall` warning.

### User-Facing Copy Recommendations

When source is too short:

> The selected source only has 3.0s available, but the edit requested 5.0s. PR0TA inserted the available media and left a 2.0s gap from 55.0s to 57.0s. I can leave the gap, choose a different source, or fit the shot to the duration with a speed change.

When using `fitToFill`:

> I retimed the source to fit the requested timeline range. The clip now plays at 0.6x speed to fill 5.0s without freeze-padding.
