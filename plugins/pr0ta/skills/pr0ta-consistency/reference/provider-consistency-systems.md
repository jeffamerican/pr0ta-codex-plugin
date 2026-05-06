# Provider Consistency Systems

Read this only when creating, registering, or troubleshooting provider-level consistency resources for recurring subjects. Keep `SKILL.md` as the routing and rule surface; this file carries lifecycle details and payload recipes.

## Kling Elements (V3 / O3 / Omni)

### What Is An Element?

An Element is a reference bundle representing a single subject -- a character, prop, location, or object. Each Element consists of:

- **1 frontal/hero image** -- the primary, clearest view of the subject (front-facing preferred)
- **1-3 additional reference images** -- different angles, poses, or views of the same subject

The frontal image tells the model "this is the subject." The additional references give the model more information about the subject's appearance from other angles, which dramatically improves consistency -- especially for characters that move, turn, or appear from multiple perspectives.

### Building Strong Element Bundles

**Characters:** frontal face/body shot + profile view + 3/4 angle + back view (if available)
**Props/Objects:** hero product shot + side angle + detail close-up
**Locations/Sets:** establishing wide shot + key detail angles

All images in a single Element must depict the **same subject**. Do not mix different characters or objects into one Element -- create separate Elements for each distinct subject.

### Creating Elements via API

```json
POST /api/v2/projects/{project_id}/elements
{
  "name": "Protagonist - Sarah",
  "provider": "kling",
  "provider_resource_id": "101",
  "reference_asset_ids": ["uuid-frontal", "uuid-profile", "uuid-three-quarter"]
}
```

This stores the Element in the project. Use the returned `id` in subsequent generations via `element_ids[]`.

### Using Elements In Generation

Reference stored Elements by their project IDs:

```json
{
  "generator": "video",
  "mode": "ref_to_vid",
  "model": "kling_o3_pro",
  "prompt": "@Element1 walks into the room and looks around nervously...",
  "start_image_asset_id": "uuid-scene-frame",
  "element_ids": ["element-uuid-sarah", "element-uuid-desk-prop"],
  "duration": 10
}
```

You can also pass inline Elements for one-off references:

```json
"elements": [
  {
    "frontal_asset_id": "uuid-frontal",
    "additional_asset_ids": ["uuid-profile", "uuid-three-quarter"]
  }
]
```

**Token reference in prompts:** `@Element1` = first element, `@Element2` = second element. `@Image1` = Start Image. Never use pronouns -- always reference subjects by token or label.

### Element Best Practices

1. **Create Element bundles at project start** -- before video generation, build all recurring character/prop/location Elements.
2. **Reuse the same Elements across all generations** -- this is the primary Kling consistency mechanism.
3. **Use Refs slider at 140%+** -- higher values mean stronger visual fidelity to references.
4. **Four reference images per character is ideal** -- frontal + profile + 3/4 + back.
5. **Generate reference images first** -- use Nano Banana 2 by default, or GPT Image 2 for character consistency edits.
6. **Upload real-world references when available** -- actor headshots, product photos, location scouts, or storyboard scans can be ingested through direct image upload, then reused in Elements and generation payloads.
7. **Do multiple takes** -- generate 4-6+ variations of every reference image and select the strongest. The quality of your references sets the ceiling for the entire production.

## Seedance 2.0 Characters (MuAPI)

### What Is A Seedance Character?

Seedance 2.0 Omni supports persistent character identity through the MuAPI character system. A Seedance character is constructed from:

- **1 frontal image** -- a clear, front-facing photo of the character (the identity anchor)
- **1 character sheet** -- a multi-panel reference showing front, back, side profile, action pose, and/or expressions (generated at 4K 21:9 resolution)
- **Optionally 1-2 additional images** -- supplementary angles or poses for stronger identity lock

The character sheet is the critical differentiator from Kling Elements. It gives the model a comprehensive understanding of the character's full appearance in a single image -- multiple angles, expressions, and details laid out as a professional character reference sheet.

### Generating Strong Character Sheets

Use Nano Banana 2 to generate the character sheet before creating the Seedance character:

```text
Professional character reference sheet for [character description].
4K resolution, 21:9 ultra-wide layout. Panels showing: front-facing portrait,
back view, left profile, right three-quarter view, action pose, facial
expression range. Clean white background, consistent studio lighting across
all panels. Character design sheet for animation production.
```

Generate 4-6+ variations and select the best. The character sheet is the foundation of all subsequent Seedance generations; every quality flaw propagates forward.

Strong character sheets have clear rendering in every panel, consistent appearance across angles, visible distinctive features, a neutral background, and coverage of front, back, side profile, and at least one expressive pose.

### Creating A Seedance Character Token

You do not upload a character directly to `POST /characters`. You first train a character token on MuAPI, then persist the returned token into the project character store. Both training paths run through the unified generation endpoint and return an Omni token in `result_refs.character_id` on completion.

| You have... | Use this training model | Required inputs |
|---|---|---|
| One clean frontal portrait | `muapi/seedance-2-omni-reference-train` | `image_url` or `image_asset_id` + `character_name` |
| A character sheet or 1-3 curated approved stills | `muapi/seedance-2-character` | `images_list[]` + `character_name` + `outfit_description` |

Do not mix hairstyles, outfits, makeup, or ages in one training build. Providers average ambiguous references, and you will get drift in every downstream shot. One identity, one era/look, one wardrobe concept per build.

#### Path A -- Single Portrait Training

```json
POST /api/v2/projects/{project_id}/generate
{
  "generator": "video",
  "mode": "ref_to_vid",
  "model": "muapi/seedance-2-omni-reference-train",
  "image_url": "https://example.com/hero-portrait.jpg",
  "character_name": "Maya",
  "description": "Female lead, black leather jacket, studio portrait, neutral expression"
}
```

- Async job -- poll `GET /api/v2/projects/{project_id}/tasks/{task_id}` until `status: "succeeded"`.
- Required fields: `image_url` (or `image_asset_id`) and `character_name`.
- The portrait must be a single clean face-forward image. One identity, no compositing.
- `description` is optional but helps downstream identity lock.

#### Path B -- Character Sheet Training

```json
POST /api/v2/projects/{project_id}/generate
{
  "generator": "video",
  "mode": "ref_to_vid",
  "model": "muapi/seedance-2-character",
  "prompt": "Create a reusable character profile for later Seedance Omni Reference shots.",
  "images_list": [
    "https://example.com/maya-sheet-front.jpg",
    "https://example.com/maya-sheet-profile.jpg",
    "https://example.com/maya-sheet-closeup.jpg"
  ],
  "character_name": "Maya",
  "outfit_description": "Black leather jacket, white tee, dark jeans"
}
```

- Async job -- poll to `succeeded` like Path A.
- Accepts up to 3 stills in `images_list[]`.
- `outfit_description` is required and validator-enforced on this path.
- Designed for multiple approved references plus wardrobe context.

#### Async Completion Shape

```json
{
  "status": "succeeded",
  "result_refs": {
    "character_id": "omni-maya-token",
    "character_name": "Maya",
    "reference_urls": ["https://example.com/hero-portrait.jpg"]
  }
}
```

The `character_id` string is the Omni token. Prefer `result` over `result_refs` for unified-generation clients when both are present; the normalized shape surfaces the same identifier as `result.character_id`.

#### Persisting The Token

Save the Omni token into the project character store so you can reference it by UUID in future generations:

```json
POST /api/v2/projects/{project_id}/characters
{
  "name": "Maya",
  "provider": "muapi",
  "provider_resource_id": "omni-maya-token"
}
```

The response returns a project-scoped UUID. From this point forward, reference Maya in generations by that UUID via `character_ids[]`. You only train once per identity; every subsequent shot reuses the stored character. After persisting, tag the source portrait/sheet assets as `character_reference` so the consistency bundle can find them.

### Using Characters In Generation

```json
{
  "generator": "video",
  "mode": "txt_to_vid",
  "model": "muapi/seedance-2.0-omni-reference",
  "prompt": "@image1 -- Sarah walks through a bustling Tokyo market at golden hour. Camera tracks from behind.",
  "character_ids": ["project-character-uuid-sarah"],
  "reference_image_urls": ["https://example.com/scene-ref.png"],
  "duration": 10
}
```

**Current limitation:** The unified generation route currently resolves exactly one stored character per request.

## Seedance Omni Multi-Modal References

Seedance 2.0 Omni is a quad-modal model supporting text + up to 9 images + 3 videos + 3 audio inputs (12 reference files total).

| Reference Type | Max Count | What the Model Extracts | Use For |
|---------------|-----------|------------------------|---------|
| Images (`@image1`-`@image9`) | 9 | Character features, composition, lighting, color palette, pose, environment | Character identity, scene composition, style reference, location |
| Videos (`@video1`-`@video3`) | 3 | Camera motion paths, movement speed, pacing, choreography | Camera trajectory, motion style, pacing reference |
| Audio (`@audio1`-`@audio3`) | 3 | Rhythm, beat patterns, tonal mood, timing cues | Music-synced motion, voiceover lip sync, rhythmic pacing |

Use the `references[]` array for typed multi-modal input:

```json
{
  "references": [
    { "type": "image", "image_url": "https://example.com/hero.png" },
    { "type": "image", "image_url": "https://example.com/style-ref.png" },
    { "type": "video", "video_url": "https://example.com/camera-motion.mov" },
    { "type": "audio", "audio_url": "https://example.com/rhythm-track.wav" }
  ],
  "reference_image_urls": ["https://example.com/hero.png", "https://example.com/style-ref.png"],
  "reference_video_urls": ["https://example.com/camera-motion.mov"],
  "reference_audio_urls": ["https://example.com/rhythm-track.wav"]
}
```

Reference strategy:
- **Character + environment:** Use `@image1` for the character and `@image2` for the location/set. Assign them explicitly in the prompt.
- **Motion matching:** Upload a reference video clip and reference it with `@video1` to transfer its camera movement and pacing to the new generation.
- **Music-driven content:** Upload the music track as `@audio1` so the model can sync character motion to rhythm and beat.
- **Combined:** "Match @image1 as the character, shoot in the style of @image2, use @video1 camera movement, sync to @audio1 beat pattern."

## Multi-Prompt / Multi-Shot Generation

Both Kling V3/O3 and Seedance support multi-prompt mode for generating multiple timed shots within a single video. This is critical for continuity because the model maintains consistency across all shots in one pass.

```json
{
  "generator": "video",
  "mode": "ref_to_vid",
  "model": "kling/o3/image-to-video",
  "prompt": "Hero navigates the warehouse",
  "prompt_mode": "multi_prompt",
  "multi_prompt": [
    { "prompt": "Hero steps cautiously into a dark warehouse. Camera follows from behind." },
    { "prompt": "Hero spots something across the room. Camera pushes in on their face." },
    { "prompt": "Hero turns and exits into fog. Camera holds as they disappear." }
  ],
  "element_ids": ["element-uuid-hero"],
  "duration": 15
}
```

Key points:
- Set `prompt_mode: "multi_prompt"` to activate multi-prompt.
- `multi_prompt` is an array of prompt segment objects.
- Kling V3 supports up to 5 shots per generation.
- Kling O3 supports up to 6 camera cuts.
- Elements are shared across all segments, which maintains character consistency throughout.

Use multi-prompt when shots are sequential in the same scene/location, character consistency within the sequence is critical, smooth camera transitions matter, and the total duration fits within one generation. Use separate generations when shots are in different locations, different characters appear in different shots, the total sequence exceeds maximum generation duration, or each shot needs independent control.

## Camera Control (Kling V3)

Kling V3 supports structured camera control parameters:

```json
{
  "camera_control": {
    "type": "simple",
    "config": { "horizontal": 5 }
  }
}
```

This provides programmatic camera movement rather than relying on prompt text alone. Combine with multi-prompt for precise shot choreography.

## Professional Reference Pipeline

For productions requiring high consistency, follow this pipeline before any shot generation:

1. **Generate character reference sheets.** Use Nano Banana 2 to create multi-angle character reference images. Generate 4-6 variations minimum and select the strongest.
2. **Generate location/set references.** Create establishing shots for recurring locations and set geometry.
3. **Generate prop references.** Create clean multi-angle references for recurring props.
4. **Tag references and create resources.** Tag approved reference images as `character_reference`, then create all Element bundles and Character profiles before video generation.
5. **Generate scene key frames.** Use image-to-image with Element references so the right characters/props appear in the right locations.
6. **Generate videos with consistency resources.** Use `element_ids[]` or `character_ids[]` from the consistency bundle on every generation.

Example final video payload:

```json
{
  "generator": "video",
  "mode": "ref_to_vid",
  "model": "kling_o3_pro",
  "prompt": "@Image1 -- @Element1 enters frame from the left...",
  "start_image_asset_id": "uuid-keyframe-scene-1",
  "element_ids": ["element-uuid-sarah", "element-uuid-briefcase"],
  "duration": 10
}
```

## Image Edit For Consistency Correction

When a generated image almost matches your reference but has inconsistencies, use the unified image edit modes to correct it:

```json
{
  "generator": "image",
  "mode": "img_to_img",
  "model": "fal-ai/nano-banana-2/edit",
  "prompt": "Keep the composition and pose but match the character appearance from the reference exactly. Same hair color, same jacket.",
  "image_asset_id": "uuid-generated-frame-with-issues",
  "reference_image_asset_ids": ["uuid-character-reference"],
  "element_ids": ["element-uuid-character"]
}
```

Use this for fixing character appearance drift in key frames before video generation, adjusting lighting/style to match a production look, and correcting props or wardrobe inconsistencies.
