# Seedance Global Visual Bible + Storyboard Chunk Workflow

Use this for reference-heavy Seedance 2.0 Omni productions where one global style/continuity reference is reused across many 4-15 second story chunks, and each chunk also gets its own dense chronological storyboard reference sheet, character, location, prop, audio, or motion references.

This is not a replacement for PR0TA prep. First call `production_context_get` and reuse approved casting, contact sheets, production-design looks, stylist looks, props, and shotlist/storyboard data. Build new references only for missing pieces.

## Pattern

Seedance responds well when the reference stack has clear roles:

| Token | Role |
|---|---|
| `@image1` | Global visual bible: approved world, cast lineup, style, palette, wardrobe, locations, key props |
| `@image2` | Primary character or hero subject for this chunk |
| `@image3` | Location or set reference |
| `@image4` | Prop, wardrobe, vehicle, creature, or object reference |
| `@imageN` | Storyboard frames or one generated storyboard reference sheet for this 4-15 second chunk |
| `@video1` | Optional motion/camera/reference clip |
| `@audio1` | Optional narration, dialogue, music, or rhythm reference |

The global bible keeps the production world coherent. The chunk storyboard sheet tells Seedance what happens now and in what order. Treat the sheet as the visual ordering map, not just mood art.

`@imageN` is not literal. It means: build the final `reference_image_asset_ids` order first, then calculate the storyboard sheet token from its one-based position in that array. If the array is `[global_bible, character, storyboard_sheet]`, the sheet is `@image3`. If it is `[global_bible, character, location, prop, storyboard_sheet]`, the sheet is `@image5`. Never write `@image5` unless the sheet is actually the fifth image reference.

## MCP Storyboard Sheet Workflow

Prefer the MCP tools for Skills users and agent workflows.

### 1. List Beat Chunks

```json
storyboard_chunks_list({
  "project_id": "project-uuid-or-slug",
  "scene_number": 12,
  "scene_range_end": 12,
  "max_duration_seconds": 15
})
```

Each returned chunk includes `id`, `duration_seconds`, `panel_count`, `source_scene_ids`, `source_shot_ids`, `screenplay_beat`, `reference_summary`, `missing_references`, `reference_image_urls`, `storyboard_sheet_prompt`, `seedance_prompt`, `omni_reference_prompt`, and `motion_continuity_prompt`.

### 2. Generate Storyboard Reference Sheets

```json
storyboard_reference_sheet_generate({
  "project_id": "project-uuid-or-slug",
  "chunk_id": "scene-12-chunk-3",
  "variation_count": 4,
  "reference_asset_ids": ["asset-character", "asset-location"],
  "reference_image_urls": [],
  "include_chunk_reference_urls": true
})
```

Use approved PR0TA cast, set, prop, wardrobe, and style assets as `reference_asset_ids` whenever possible. With references, the default image model is `openai/gpt-image-2/edit`; without references, it is `openai/gpt-image-2`. The tool returns a task; poll with `tasks_get`.

### 3. Select the Approved Sheet

```json
storyboard_reference_sheets_list({
  "project_id": "project-uuid-or-slug",
  "chunk_id": "scene-12-chunk-3",
  "include_download": true
})
```

Generated sheet assets are registered with `reference_type: "seedance_storyboard_sheet"`, `asset_category: "storyboard"`, `operation: "seedance_storyboard_sheet"`, `chunk_id`, `panel_count`, `source_scene_ids`, and `source_shot_ids`.

### REST Mirrors

Use REST only when MCP is unavailable or for external automation:

```http
GET /api/v2/projects/{project_id}/storyboard/chunks?scene_number=12&max_duration_seconds=15
POST /api/v2/projects/{project_id}/storyboard/reference-sheets/generate
GET /api/v2/projects/{project_id}/storyboard/reference-sheets?chunk_id=scene-12-chunk-3&include_download=true
```

## Build The Global Visual Bible

Create one high-density still or contact sheet for the whole production. It should contain only approved references:

- main characters with names
- recurring locations and set dressing
- hero props and wardrobe
- color palette, lighting, lens/texture notes
- one or two approved style frames

Store it as a normal PR0TA asset and annotate it so future agents can find it:

```json
{
  "reference_type": "global_visual_bible",
  "category": "production_bible",
  "tags": ["reference", "global", "approved"],
  "notes": "Use as @image1 for Seedance 2.0 Omni storyboard chunks."
}
```

If a casting-director contact sheet, production-design board, or script-breakdown reference board already exists, prefer that as the starting point instead of creating a new parallel artifact.

## Build Storyboard Chunks

Chunk the story into 4-15 second narrative units. Each chunk should cover one clean beat of action, not an arbitrary duration bucket.

For each chunk, prepare or retrieve through `storyboard_chunks_list`:

- `chunk_id` and target duration
- transcript or screenplay excerpt
- one generated storyboard reference sheet or 2-5 storyboard frames showing the major visual beats in strict chronological order
- required character, location, prop, and wardrobe references
- audio reference if motion should follow narration, music, or timing
- a short shot list with exact action progression
- `seedance_prompt`, `omni_reference_prompt`, and `motion_continuity_prompt` from the chunk response

Annotate storyboard frames with:

```json
{
  "reference_type": "storyboard_chunk_frame",
  "chunk_id": "chunk_012",
  "tags": ["storyboard", "reference", "approved"]
}
```

## Prompt Template

Use explicit token role assignment at the top. Do not rely on implicit order. Derive every `@image` token from the final `reference_image_asset_ids` order.

```text
@image1 is the global visual bible for the entire film: preserve its cast identity, wardrobe logic, locations, props, palette, lens style, and production design.
[character_token] is [primary character/subject] for this chunk, if included.
[location_token] is [location/set] for this chunk, if included.
[prop_token] is [prop/wardrobe/object] for this chunk, if included.
[storyboard_sheet_token] is the chronological storyboard reference sheet for this chunk. It controls panel order, action progression, staging, composition, and final state.

Generate a [duration]-second continuous Seedance 2.0 Omni video chunk.
Story chunk: [one-sentence narrative purpose].
Timeline:
0.0-3.0s: [first action beat]
3.0-7.0s: [second action beat]
7.0-12.0s: [third action beat]

Critical instruction: animate the storyboard sheet in [storyboard_sheet_token] in strict chronological panel order. Start with Panel 1, pass through each panel in sequence, and end on the final panel state. Do not skip panels or reorder the story.

Maintain the global visual bible from @image1 throughout. Follow the storyboard sheet for composition and blocking, but keep the motion cinematic and continuous. Preserve character identity, set geometry, wardrobe, prop design, color palette, and lens texture. No unrequested new characters, props, locations, logos, or text.
```

## Payload Sketch

Use the existing unified generation fields. If richer role metadata is not available on the live API, keep roles in the prompt and asset annotations. Build `reference_image_asset_ids` first, then substitute the correct one-based Seedance tokens into the prompt. Do not keep the placeholder token names in the final request.

```json
{
  "generator": "video",
  "mode": "ref_to_vid",
  "model": "muapi/seedance-2.0-omni-reference",
  "prompt": "@image1 is the global visual bible... [storyboard_sheet_token] is the chronological storyboard reference sheet...",
  "reference_image_asset_ids": [
    "global-bible-asset-id",
    "primary-character-asset-id",
    "location-asset-id",
    "prop-asset-id",
    "storyboard-sheet-asset-id"
  ],
  "duration": 12,
  "aspect_ratio": "9:16",
  "sound": "off"
}
```

If a chunk does not include a location or prop reference, remove that asset from `reference_image_asset_ids` and renumber the prompt tokens before submission. Token correctness is part of the prompt, not a cosmetic detail.

## Failure Modes

- Too many references can conflict. Remove lower-priority references before rewriting the core prompt.
- If Seedance copies the global bible layout literally, make `@image1` role-only in the prompt and move composition control to the storyboard frames.
- If the storyboard sheet becomes frozen slides, add explicit motion and camera progression per time range and use `motion_continuity_prompt` from the chunk response.
- If the action happens out of order, strengthen the "strict chronological panel order" instruction and reduce lower-priority references before changing the approved sheet.
- If character locking conflicts with references, use one stored Seedance character lock for the primary character and keep supporting characters as image references unless the API confirms multi-character locks for that model/request.
- Text-heavy cards should not use this path. Generate exact text as stills and animate on the timeline unless the user explicitly accepts model text drift.
