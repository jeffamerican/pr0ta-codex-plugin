---
name: pr0ta-consistency
description: "PR0TA visual consistency for recurring characters, locations, props, and multi-shot continuity. Read when creating or using Kling Elements, Seedance Characters, consistency bundles, reference pipelines, or repeat-subject generation."
---

# Visual Consistency & Continuity Reference

This reference covers how to maintain character, set, prop, and style consistency across multi-shot AI productions in PR0TA. It documents the two primary consistency systems (Kling Elements and Seedance Characters), the professional reference pipeline, and practical workflows.

## Consistency Systems Overview

PR0TA supports two model-family-specific consistency systems, both managed as persistent project-scoped resources via the API:

| System | Provider | Best For | API Resource |
|--------|----------|----------|-------------|
| **Elements** | Kling (V3, O3, Omni) | Character/prop/location bundles with multi-angle references | `POST /api/v2/projects/{project_id}/elements` |
| **Characters** | Seedance 2.0 / MuAPI | Persistent character identity from 1-3 photos | `POST /api/v2/projects/{project_id}/characters` |

Both are stored per-project and resolved server-side when referenced in generation requests via `element_ids[]` or `character_ids[]`.

## Kling Elements (V3 / O3 / Omni)

### What is an Element?

An Element is a reference bundle representing a single subject -- a character, prop, location, or object. Each Element consists of:

- **1 frontal/hero image** -- the primary, clearest view of the subject (front-facing preferred)
- **1-3 additional reference images** -- different angles, poses, or views of the same subject

The frontal image tells the model "this is the subject." The additional references give the model more information about the subject's appearance from other angles, which dramatically improves consistency -- especially for characters that move, turn, or appear from multiple perspectives.

### Building Strong Element Bundles

**Characters:** frontal face/body shot + profile view + 3/4 angle + back view (if available)
**Props/Objects:** hero product shot + side angle + detail close-up
**Locations/Sets:** establishing wide shot + key detail angles

All images in a single Element must depict the **same subject**. Don't mix different characters or objects into one Element -- create separate Elements for each distinct subject.

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

### Using Elements in Generation

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

1. **Create Element bundles at project start** -- before any video generation, build all recurring character/prop/location Elements
2. **Reuse the same Elements across all generations** -- this is the primary consistency mechanism
3. **Use Refs slider at 140%+** -- higher values = stronger visual fidelity to references
4. **4 reference images per character is ideal** -- frontal + profile + 3/4 + back
5. **Generate reference images first** -- use Nano Banana 2 (default) or GPT Image 2 (for character consistency edits) to create clean character reference sheets, then use those as Element references
6. **Upload real-world references when available** -- actor headshots, product photos, location scouts, or storyboard scans can be ingested directly via `POST /api/v2/projects/{project_id}/assets/upload` (multipart, images only). The returned asset IDs go straight into `reference_asset_ids` when creating an Element, or into `start_image_asset_id` / `reference_image_asset_ids[]` for generation. See `pr0ta-image` → "Uploading Existing Images" and `pr0ta-api` → "Project Image Upload" for the full spec.
6. **Do multiple takes** -- generate 4-6+ variations of every reference image and select the strongest. The quality of your references sets the ceiling for the entire production. Never settle for "good enough" on references.

## Seedance 2.0 Characters (MuAPI)

### What is a Seedance Character?

Seedance 2.0 Omni supports persistent character identity through the MuAPI character system. A Seedance character is constructed from:

- **1 frontal image** — a clear, front-facing photo of the character (the identity anchor)
- **1 character sheet** — a multi-panel reference showing front, back, side profile, action pose, and/or expressions (generated at 4K 21:9 resolution)
- **Optionally 1-2 additional images** — supplementary angles or poses for stronger identity lock

The character sheet is the critical differentiator from Kling Elements. It gives the model a comprehensive understanding of the character's full appearance in a single image — multiple angles, expressions, and details laid out as a professional character reference sheet.

### Generating Strong Character Sheets

Use Nano Banana 2 to generate the character sheet before creating the Seedance character:

```
Prompt: "Professional character reference sheet for [character description].
4K resolution, 21:9 ultra-wide layout. Panels showing: front-facing portrait,
back view, left profile, right three-quarter view, action pose, facial
expression range. Clean white background, consistent studio lighting across
all panels. Character design sheet for animation production."
```

**Generate 4-6+ variations and select the best.** The character sheet is the foundation of all subsequent Seedance generations — every quality flaw propagates forward.

**What makes a good character sheet:**
- Clear, sharp rendering in every panel (no blur or artifacts)
- Consistent appearance across all angles (same hair, clothing, proportions)
- Distinctive features clearly visible (scars, jewelry, unique hair, tattoos)
- Clean white or neutral background (no distracting elements)
- Good coverage: front, back, side profile, and at least one expressive pose

### Creating a Seedance Character Token — Two Paths

**You do not upload a character directly to `POST /characters`. You first *train* a character token on MuAPI, then persist the returned token into the project character store.** Both training paths run through the unified generation endpoint and return an Omni token in `result_refs.character_id` on completion.

**Decision:** pick by the reference material you have.

| You have... | Use this training model | Required inputs |
|---|---|---|
| One clean frontal portrait | `muapi/seedance-2-omni-reference-train` | `image_url` (or `image_asset_id`) + `character_name` |
| A character sheet or 1-3 curated approved stills | `muapi/seedance-2-character` | `images_list[]` (1-3 URLs) + `character_name` + `outfit_description` |

**Do not mix hairstyles, outfits, makeup, or ages in one training build** — providers average ambiguous references, and you will get drift in every downstream shot. One identity, one era/look, one wardrobe concept per build.

#### Path A — Single Portrait Training (`muapi/seedance-2-omni-reference-train`)

Fastest path into Omni Reference when you have one strong hero portrait.

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

- Async job — poll `GET /api/v2/projects/{project_id}/tasks/{task_id}` until `status: "succeeded"`.
- Required fields: `image_url` (or `image_asset_id`) and `character_name`.
- The portrait must be a single clean face-forward image. One identity, no compositing.
- `description` is optional but helps downstream identity lock.

#### Path B — Character Sheet Training (`muapi/seedance-2-character`)

Better fit when you have a real character sheet (see "Generating Strong Character Sheets" above) or multiple approved stills.

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

- Async job — poll to `succeeded` like Path A.
- Accepts up to 3 stills in `images_list[]`.
- `outfit_description` is **required** (validator enforces it on this path).
- Designed for multiple approved references plus wardrobe context.

#### Async Completion Shape

When training succeeds, the task result exposes the Omni token:

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

The `character_id` string is the Omni token. **Prefer `result` over `result_refs` for unified-generation clients when both are present** — the normalized shape surfaces the same identifier as `result.character_id`.

#### Persisting the Token — Path C

Save the Omni token into the project character store so you can reference it by UUID in future generations:

```json
POST /api/v2/projects/{project_id}/characters
{
  "name": "Maya",
  "provider": "muapi",
  "provider_resource_id": "omni-maya-token"
}
```

The response returns a project-scoped UUID. From this point forward, reference Maya in generations by that UUID via `character_ids[]` (see "Using Characters in Generation" below). You only train once per identity — every subsequent shot reuses the stored character. After persisting, tag the source portrait/sheet assets as `character_reference` (see "Tagging Assets as Character References" below) so the consistency bundle can find them.

### Using Characters in Generation

```json
{
  "generator": "video",
  "mode": "txt_to_vid",
  "model": "muapi/seedance-2.0-omni-reference",
  "prompt": "@image1 — Sarah walks through a bustling Tokyo market at golden hour. Camera tracks from behind.",
  "character_ids": ["project-character-uuid-sarah"],
  "reference_image_urls": ["https://example.com/scene-ref.png"],
  "duration": 10
}
```

**Current limitation:** The unified generation route currently resolves exactly one stored character per request.

### Seedance Omni Multi-Modal References

Seedance 2.0 Omni is a **quad-modal** model supporting text + up to 9 images + 3 videos + 3 audio inputs (12 reference files total). Each reference type serves a distinct purpose:

**What the model extracts from each reference type:**

| Reference Type | Max Count | What the Model Extracts | Use For |
|---------------|-----------|------------------------|---------|
| **Images** (`@image1`–`@image9`) | 9 | Character features, composition, lighting, color palette, pose, environment | Character identity, scene composition, style reference, location |
| **Videos** (`@video1`–`@video3`) | 3 | Camera motion paths, movement speed, pacing, choreography | Camera trajectory, motion style, pacing reference |
| **Audio** (`@audio1`–`@audio3`) | 3 | Rhythm, beat patterns, tonal mood, timing cues | Music-synced motion, voiceover lip sync, rhythmic pacing |

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

**Reference strategy tips:**
- **Character + environment:** Use `@image1` for the character and `@image2` for the location/set. Assign them explicitly in the prompt.
- **Motion matching:** Upload a reference video clip and reference it with `@video1` to transfer its camera movement and pacing to the new generation.
- **Music-driven content:** Upload the music track as `@audio1` — the model will sync character motion to the rhythm and beat pattern.
- **Combined:** "Match @image1 as the character, shoot in the style of @image2, use @video1 camera movement, sync to @audio1 beat pattern." This is the full power of quad-modal generation.

## Multi-Prompt / Multi-Shot Generation

Both Kling V3/O3 and Seedance support multi-prompt mode for generating multiple timed shots within a single video. This is critical for continuity -- the model maintains consistency across all shots because they're generated in one pass.

### Using Multi-Prompt via API

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

**Key points:**
- Set `prompt_mode: "multi_prompt"` to activate multi-prompt
- `multi_prompt` is an array of prompt segment objects
- Kling V3 supports up to 5 shots per generation
- Kling O3 supports up to 6 camera cuts
- Elements are shared across all segments -- the model maintains character consistency throughout

### When to Use Multi-Prompt vs Separate Generations

**Use multi-prompt when:**
- Shots are sequential in the same scene/location
- Character consistency within the sequence is critical
- You need smooth camera transitions between beats
- Total duration fits within one generation (5-15s)

**Use separate generations when:**
- Shots are in different locations
- Different characters appear in different shots
- You need maximum control over each shot independently
- Total sequence exceeds maximum generation duration

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

For productions requiring high consistency, follow this pipeline to generate and manage references before any shot generation:

### Step 1: Generate Character Reference Sheets

Use Nano Banana 2 to create multi-angle character reference images:

```
Prompt: "Character reference sheet for [character description]. Four views: front-facing portrait,
left profile, three-quarter right view, back view. Clean white background, consistent lighting,
full body visible. Professional character design sheet layout."
```

**Generate multiple takes (4-6 variations minimum) and carefully select the best.** Reference images are the foundation of every subsequent generation — a mediocre reference propagates through the entire production. Evaluate each take for clarity, consistency of features across angles, lighting quality, and faithfulness to the creative brief. Only promote the strongest take to an Element bundle.

### Step 2: Generate Location/Set References

Use Nano Banana 2 to create establishing shots for key locations:

```
Prompt: "Establishing shot of [location description]. Wide angle, cinematic lighting,
[time of day], [weather/mood]. No people visible. Production design reference."
```

Create Element bundles for locations that will recur across multiple shots.

### Step 3: Generate Prop References

For important recurring props, generate clean reference images:

```
Prompt: "Product/prop reference for [prop description]. Clean studio lighting,
multiple angles visible, high detail. White background."
```

### Step 4: Tag References, Create All Elements and Characters

Tag approved reference images as `character_reference` assets (see "Tagging Assets as Character References"), then create all consistency resources before any video generation:

```bash
# Create character elements
curl -X POST "$BASE/api/v2/projects/$PID/elements" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "Sarah - Protagonist", "provider": "kling", "reference_asset_ids": ["uuid-front", "uuid-profile", "uuid-3q"]}'

# Create Seedance characters (if using Seedance)
curl -X POST "$BASE/api/v2/projects/$PID/characters" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "Sarah", "provider": "muapi", "provider_resource_id": "char_sarah_v1"}'
```

### Step 5: Generate Scene Key Frames

For each scene in the cue sheet, generate a key frame using Nano Banana 2 with Element references or image-to-image editing to ensure the correct characters/props appear in the correct locations.

### Step 6: Generate Videos with Consistency

Now generate all videos using the stored Elements/Characters:

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

## Image Edit for Consistency Correction

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

This is particularly useful for:
- Fixing character appearance drift in key frames before video generation
- Adjusting lighting/style to match a production look
- Correcting props or wardrobe inconsistencies

## Choosing Between Seedance and Kling

**Seedance 2.0 Omni and Kling V3/O3 are co-equal defaults** — pick based on the shot's needs, not a global preference. For continuity-critical work, generate the same shot in both and compare.

| Criterion | Seedance 2.0 Omni | Kling V3/O3 |
|-----------|---------------------|------------------|
| **Character system** | Frontal + character sheet + 1-2 extras | Element bundles: 1 frontal + 1-3 angles |
| **Reference capacity** | 12 files: 9 images + 3 video + 3 audio | Images + text only |
| **Multi-modal input** | Image + video + audio + text (quad-modal) | Image + text |
| **Multi-shot in one generation** | Yes (native multi-shot) | Yes (V3: 5 shots, O3: 6 cuts) |
| **Camera control** | Prompt-driven + video reference for trajectory | Structured `camera_control` API parameter |
| **Audio sync** | Native audio references — rhythm-synced motion | No audio input |
| **Character persistence** | Per-character ID, per-project | Per-element, per-project |
| **Best for** | Most productions — character narratives, music videos, rhythm-matched content | Precise camera control, Motion Brush, budget-sensitive productions |

You can use **both systems** in the same production — Seedance for the majority of shots, falling back to Kling for specific shots requiring structured camera control or Motion Brush.

## On-Screen Text Is NOT a Consistency Problem — It's an Animation Problem

**⚠️ Do not try to preserve on-screen text across a `ref_to_vid` call.** Element references, character IDs, and reference strength sliders do not protect text — consistency systems exist for faces, wardrobe, lighting, and style, not on-screen typography. Video models will semantically rewrite legible text during animation.

Generate title stills with a text-reliable image model (see `pr0ta-prompting` → "Line-Locked Poster"), then animate on the timeline with a Ken Burns preset instead of feeding the still back to a video model. See `pr0ta-video` → "On-Screen Text — Do NOT Animate Text Through a Video Model" and `pr0ta-timeline` → "Ken Burns as a Clip Property" for the full recipe.

## Character Consistency Bundles

Before generating multi-shot character-consistent content, **read the character's consistency bundle** — a single endpoint that returns all approved references, stored Kling Elements, stored Seedance tokens, and provider-ready payload snippets in one response.

```
GET /api/v2/projects/{project_id}/characters/{character_id}/consistency
GET /api/v2/projects/{project_id}/characters/consistency?name=Kondiaronk
```

The bundle response includes:
- `reference_assets[]` — approved portraits and turnaround sheets (with `reference_kind: "portrait"` or `"turnaround"`)
- `kling_elements[]` — stored Kling Elements with `provider_resource_id`
- `seedance_characters[]` — stored Seedance/MuAPI Omni tokens with `provider_resource_id`
- `provider_payloads` — ready-to-use snippets: `kling.element_ids[]`, `seedance.character_ids[]`, `seedance.prompt_tokens[]`

**Use the bundle's `provider_payloads` directly in generation requests** — it eliminates manual lookup of element IDs and character tokens. Pick `provider_payloads.kling` for Kling shots and `provider_payloads.seedance` for Seedance shots.

### Tagging Assets as Character References

For the bundle to find approved references, tag generated portraits and turnaround sheets using asset annotations:

```json
PATCH /api/assets/{project_name}/annotations
{
  "asset_id": "asset_portrait_123",
  "reference_type": "character_reference",
  "character_name": "Sarah",
  "category": "portrait",
  "tags": ["reference", "character", "portrait", "approved"],
  "labels": { "reference_kind": "portrait" }
}
```

Use `category: "portrait"` for front-facing hero images and `category: "character_sheet"` for multi-panel turnaround sheets. The bundle endpoint filters on `reference_type=character_reference` and the `approved` tag.

### When the Bundle Is Incomplete

If a bundle has reference assets but is missing a Kling Element or Seedance token, create the missing resource first:
- Missing Kling Element → `POST /elements` with the approved `reference_asset_ids`
- Missing Seedance token → train one (see "Creating a Seedance Character Token — Two Paths" above), then `POST /characters` to persist it

After creating the missing resource, re-read the bundle — it will now include the new resource in `provider_payloads`.

## Quick Reference: Consistency Workflow

1. **Pre-production:** Generate multiple takes (4-6+) of character/location/prop reference images with Nano Banana 2 (or GPT Image 2 for character consistency edits). Select the best.
2. **Tag approved references:** Use `PATCH /annotations` with `reference_type: "character_reference"` and `category: "portrait"` or `"character_sheet"` on each approved image.
3. **Register resources:** Create Element bundles (Kling) and Character profiles (Seedance) via project API. Train Seedance tokens if needed.
4. **Read the consistency bundle:** `GET /characters/{id}/consistency` or `GET /characters/consistency?name=...` — returns all references, Elements, tokens, and provider-ready payloads in one call.
5. **Key frames:** Generate scene key frames using image-to-image with Element references
6. **Video generation:** Use `provider_payloads.kling.element_ids` or `provider_payloads.seedance.character_ids` from the bundle in all generation requests
7. **Multi-shot sequences:** Use `multi_prompt` for continuous sequences requiring intra-shot consistency
8. **Long continuous sequences (30s+):** Use Seedance Omni **extension chaining** — feed the previous clip as `@video1` via "Text with Reference" plus static character reference images to fortify consistency. See `pr0ta-video` → `reference/seedance-omni.md` → "Seamless Video Extension".
9. **Correction passes:** Use image edit modes to fix any consistency drift before final video generation
10. **Reuse across project:** All Elements and Characters persist for the project lifetime -- reuse them for reshoots, additional scenes, and variations
