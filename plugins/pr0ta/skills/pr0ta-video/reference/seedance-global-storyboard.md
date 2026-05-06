# Seedance Global Visual Bible + Storyboard Chunk Workflow

Use this for reference-heavy Seedance 2.0 Omni productions where one global style/continuity reference is reused across many 10-15 second story chunks, and each chunk also gets its own storyboard, character, location, prop, audio, or motion references.

This is not a replacement for PR0TA prep. First call `production_context_get` and reuse approved casting, contact sheets, production-design looks, stylist looks, props, and shotlist/storyboard data. Build new references only for missing pieces.

## Pattern

Seedance responds well when the reference stack has clear roles:

| Token | Role |
|---|---|
| `@image1` | Global visual bible: approved world, cast lineup, style, palette, wardrobe, locations, key props |
| `@image2` | Primary character or hero subject for this chunk |
| `@image3` | Location or set reference |
| `@image4` | Prop, wardrobe, vehicle, creature, or object reference |
| `@image5`..`@image9` | Storyboard frames for this 10-15 second chunk |
| `@video1` | Optional motion/camera/reference clip |
| `@audio1` | Optional narration, dialogue, music, or rhythm reference |

The global bible keeps the production world coherent. The chunk-specific references tell Seedance what to do now.

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

Chunk the story into 10-15 second narrative units. Each chunk should cover one clean beat of action, not an arbitrary duration bucket.

For each chunk, prepare:

- `chunk_id` and target duration
- transcript or screenplay excerpt
- 2-5 storyboard frames showing the major visual beats
- required character, location, prop, and wardrobe references
- audio reference if motion should follow narration, music, or timing
- a short shot list with exact action progression

Annotate storyboard frames with:

```json
{
  "reference_type": "storyboard_chunk_frame",
  "chunk_id": "chunk_012",
  "tags": ["storyboard", "reference", "approved"]
}
```

## Prompt Template

Use explicit token role assignment at the top. Do not rely on implicit order.

```text
@image1 is the global visual bible for the entire film: preserve its cast identity, wardrobe logic, locations, props, palette, lens style, and production design.
@image2 is [primary character/subject] for this chunk.
@image3 is [location/set] for this chunk.
@image4 is [prop/wardrobe/object] for this chunk.
@image5 through @image8 are storyboard frames for the intended composition and action progression.

Generate a [duration]-second continuous Seedance 2.0 Omni video chunk.
Story chunk: [one-sentence narrative purpose].
Timeline:
0.0-3.0s: [first action beat]
3.0-7.0s: [second action beat]
7.0-12.0s: [third action beat]

Maintain the global visual bible from @image1 throughout. Follow the storyboard frame sequence for composition and blocking, but keep the motion cinematic and continuous. Preserve character identity, set geometry, wardrobe, prop design, color palette, and lens texture. No unrequested new characters, props, locations, logos, or text.
```

## Payload Sketch

Use the existing unified generation fields. If richer role metadata is not available on the live API, keep roles in the prompt and asset annotations.

```json
{
  "generator": "video",
  "mode": "ref_to_vid",
  "model": "muapi/seedance-2.0-omni-reference",
  "prompt": "@image1 is the global visual bible...",
  "reference_image_asset_ids": [
    "global-bible-asset-id",
    "primary-character-asset-id",
    "location-asset-id",
    "prop-asset-id",
    "storyboard-frame-1",
    "storyboard-frame-2",
    "storyboard-frame-3"
  ],
  "duration": 12,
  "aspect_ratio": "9:16",
  "sound": "off"
}
```

## Failure Modes

- Too many references can conflict. Remove lower-priority references before rewriting the core prompt.
- If Seedance copies the global bible layout literally, make `@image1` role-only in the prompt and move composition control to the storyboard frames.
- If storyboard frames become frozen slides, add explicit motion and camera progression per time range.
- If character locking conflicts with references, use one stored Seedance character lock for the primary character and keep supporting characters as image references unless the API confirms multi-character locks for that model/request.
- Text-heavy cards should not use this path. Generate exact text as stills and animate on the timeline unless the user explicitly accepts model text drift.
