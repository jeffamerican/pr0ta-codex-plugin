---
name: pr0ta-image
description: "PR0TA image generation — Nano Banana 2 (default for speed and cost), GPT Image 2 (for challenging prompt adherence and character consistency edits), image editing modes (img_to_img, ref_to_img, edit_img), fan-out recipe for hard shots, resolution constraints, and model-specific parameter guidance. Read when generating any image, creating key frames for video animation, editing existing images, generating title cards or flash cards, creating stills for Ken Burns, producing character reference sheets, or choosing between image models. Also read when uploading existing images as references or when a text-heavy still needs the Line-Locked Poster pattern from pr0ta-prompting."
---

# Image Generator Reference

> **See also:** For using generated images as Element/Character source material for multi-shot consistency, read `pr0ta-consistency`. For prompt engineering (self-contained prompts, prompt bible, Line-Locked Poster pattern), read `pr0ta-prompting`.

## Model Selection: Nano Banana 2 is the Default

**Nano Banana 2 is the default image model in PR0TA** — fast, cost-effective, and produces excellent results for the vast majority of shots. API model string: **`"nano_banana_2"`** (underscore, not hyphen). Best combination of speed, dimension control, and value. Default to Nano Banana 2 for both generation and editing unless you hit one of the escalation triggers below.

**Escalate to GPT Image 2 when:**
- **Challenging prompt adherence** — complex compositions where Nano Banana 2 isn't capturing the detail you need. GPT Image 2 follows dense prose prompts more faithfully.
- **Character consistency image edits** — `img_to_img` and `ref_to_img` operations where preserving identity across edits matters. GPT Image 2 (`openai/gpt-image-2/edit`) is far superior at maintaining character likeness through edit passes.
- **Fan-out for hard shots** — include GPT Image 2 in the fan-out model list for text-heavy or high-stakes shots (see "Fan-Out and Pick" below).

API model strings for GPT Image 2: **`"openai/gpt-image-2"`** for text-to-image, **`"openai/gpt-image-2/edit"`** for image editing. These are Fal queue endpoint IDs. (This is *GPT Image 2*, not the legacy GPT-2 text LM.)

**Fall back to other models when:**
- You need uncensored content that Nano Banana 2 or GPT Image 2 rejects → Flux 2 PRO / Flux 2 MAX (excellent for permissive work), GPT Image 1.5 (also flagged UNCENSORED)
- You need specialized reasoning-based image generation → GLM Image
- Budget is extremely tight → Kling Image V3/O3 (2.94 credits)

For most reference images, key frames, and production stills — **default to Nano Banana 2**. Escalate to GPT Image 2 for character consistency edits and challenging prompt adherence.

**⚠️ Nano Banana 2 outputs native resolution (~768px wide), not the requested pixel dimensions.** That's fine — the post-production timeline normalizes every clip to the delivery resolution automatically when you add it (`POST /timeline/clips`). You do not need to pre-upscale before adding a still to the timeline. If you need the still at delivery resolution *outside* the timeline (e.g. as a thumbnail), regenerate with the target aspect ratio and accept the native resolution.

### API Quick Reference — Complete Image Generation Examples

**Copy-paste ready.** For the full parameter reference, see `pr0ta-api`. Use `GET /api/crew/model_defaults?model_id={model_id}` for the authoritative parameter list and types for any model.

```bash
# Generate an image via API (Nano Banana 2 — default)
curl -X POST "https://app.pr0ta.com/api/v2/projects/$PROJECT_ID/generate" \
  -H "Authorization: Bearer $PR0TA_PAT" \
  -H "Content-Type: application/json" \
  -d '{
    "generator": "image",
    "mode": "txt_to_img",
    "model": "nano_banana_2",
    "prompt": "Dark navy infographic showing global market growth, gold accent text, clean vector style.",
    "width": 1920,
    "height": 1080,
    "format": "png"
  }'

# Character consistency edit via API (GPT Image 2 Edit — best for identity preservation)
curl -X POST "https://app.pr0ta.com/api/v2/projects/$PROJECT_ID/generate" \
  -H "Authorization: Bearer $PR0TA_PAT" \
  -H "Content-Type: application/json" \
  -d '{
    "generator": "image",
    "mode": "img_to_img",
    "model": "openai/gpt-image-2/edit",
    "prompt": "Keep the subject, relight as moody neon noir portrait with blue rim light.",
    "image_asset_id": "uuid-source-image"
  }'

# GPT Image 2 text-to-image (for challenging prompt adherence)
curl -X POST "https://app.pr0ta.com/api/v2/projects/$PROJECT_ID/generate" \
  -H "Authorization: Bearer $PR0TA_PAT" \
  -H "Content-Type: application/json" \
  -d '{
    "generator": "image",
    "mode": "txt_to_img",
    "model": "openai/gpt-image-2",
    "prompt": "Dark navy infographic showing global market growth, gold accent text, clean vector style."
  }'

# Returns: { "task_id": "...", "status": "queued" }
# Poll task, then download via result.asset_id (see pr0ta-api)
```

**For Nano Banana 2 via API, always use `width`/`height` in pixels** (e.g., 1920x1080). The `image_size` parameter behavior is inconsistent across models — `width`/`height` is the reliable path. For GPT Image 2, use `image_size`, `quality`, `num_images`, and `output_format` — check `model_defaults` for the full parameter list.

| API Model String | Human Name | Generator | Mode | Credits |
|-----------------|------------|-----------|------|---------|
| `nano_banana_2` | **Nano Banana 2** | image | txt_to_img | 8.40/image |
| `fal-ai/nano-banana-2/edit` | **Nano Banana 2 Edit** | image | img_to_img | 8.40/image |
| `openai/gpt-image-2` | GPT Image 2 | image | txt_to_img | varies |
| `openai/gpt-image-2/edit` | GPT Image 2 Edit | image | img_to_img, ref_to_img, edit_img | varies |
| `fal-ai/gpt-image-1/edit-image` | GPT Image 1.5 Edit | image | edit_img | varies |
| `kling/o1/image-edit` | Kling Image Edit | image | ref_to_img | 2.94/image |

## Modes (Tabs across the top)

### 1. Txt to Img (Text-to-Image)
Generate images from text prompts.

**Default model: Nano Banana 2** (8.40 credits/image, HQ, FAST, PRECISE, ACCURATE) — fast, cost-effective, excellent dimension control. Escalate to GPT Image 2 for challenging prompt adherence or character consistency edits.

**Key parameters:** prompt, ratio (auto, 1:1, 16:9, 9:16, 4:3, 3:4, 3:2, 2:3, etc.), resolution (1K, 2K, 4K), seed (optional, for reproducibility), number of images (default: 1), format (jpeg, png, webp), tolerance (1-6 range, default 4; some models cap at 5 -- controls prompt adherence and content-safety filtering). **Raise tolerance to the model's max (6 where available, 5 otherwise) if a legitimate creative prompt is being soft-blocked or rewritten.** If max tolerance still rejects, fall back to a less-restrictive image model: **Flux 2 PRO** and **Flux 2 MAX** are excellent for uncensored work; GPT Image 1.5 is also flagged UNCENSORED in the model list; Grok Imagine and LTX-family image modes are additional permissive options. See `pr0ta-video` → "Content-Restriction Fallback Ladder" for the same pattern on the video side.

**Available Txt-to-Img models:**
- **Nano Banana 2** (8.40 credits/image) -- HQ, FAST, PRECISE, ACCURATE -- **recommended default** — best speed, cost, and dimension control
- OpenAI GPT Image 2 (varies) -- HQ -- escalate for challenging prompt adherence or character consistency edits
- Qwen Image 2 Pro (Text-to-Image) (7.88 credits/image)
- GPT Image 1.5 (varies) -- HQ, CHEAP, UNCENSORED
- FLUX.2 Pro -- HQ, UNCENSORED (excellent for permissive creative work)
- FLUX.2 Max (7.35 credits/megapixel) -- HQ, UNCENSORED (excellent for permissive creative work)
- ByteDance SeeDream v4.5 (4.20 credits/image) -- HQ
- GLM Image (5.25 credits/megapixel) -- HQ, REASONING
- Kling Image V3 (Text-to-Image) (2.94 credits/image) -- NEW
- Kling Image O3 (Text-to-Image) (2.94 credits/image) -- NEW

### Model Resolution Constraints

Not all models support the full range of aspect ratios. Check constraints before generating:

| Model | Supported Resolutions | Notes |
|-------|----------------------|-------|
| **Nano Banana 2** | All ratios (auto, 1:1, 16:9, 9:16, 4:3, 3:4, 3:2, 2:3, 21:9, 4:5, 5:4, etc.) up to 4K | Most flexible — supports the full ratio dropdown |
| **GPT Image 1.5** | **1024x1024** (1:1), **1536x1024** (3:2 landscape), **1024x1536** (2:3 portrait) only | **Ignores `image_size` parameter.** Always outputs 1024x1024 regardless of what you request via API. |
| Other models | Verify against `GET /api/v2/models` | Constraints vary by provider |

**Important — GPT Image 1.5:** This model ignores the `image_size` / dimension parameters via API and always outputs 1024x1024. If you need controlled dimensions, use Nano Banana 2 instead.

**Important — Nano Banana 2 portrait orientation bug:** Requesting `portrait_4_3` currently returns a landscape image (1408x768) instead of the expected portrait orientation. If you need a portrait 4:3 image, generate at a supported portrait ratio (e.g., `3:4` or `9:16`) or generate landscape and crop/rotate in post-processing.

### 2. Img to Img (Image-to-Image)
Transform existing images with a prompt.

**Default model: Nano Banana 2 Edit** (`fal-ai/nano-banana-2/edit`, 8.40 credits/image) for general edits. **Escalate to GPT Image 2 Edit** (`openai/gpt-image-2/edit`) for character consistency edits where preserving identity through the edit is critical — GPT Image 2 is far superior at maintaining likeness.

**Key parameters:** reference images (with reference strength 0-140%+), image URLs, plus the same prompt and settings as Txt to Img.

### 3. LoRA Txt2Img / LoRA Img2Img
Generate with custom LoRA models trained on specific styles or subjects.

**Models:** Qwen Image 2512 (LoRA), Z-Image Turbo (LoRA)

**Additional controls:**
- **LoRA Library** -- Browse and search installed LoRAs
- **LoRA weight slider** (0.00 - 1.00+, default: 0.80)
- **Triggers** -- LoRA-specific trigger words

## Image Editing Tools (Below the generate button)

These tools work on selected images in the Canvas:

| Tool | Description |
|------|-------------|
| **Ref to Img** | Generate a new image using an existing one as reference |
| **Img to 3D** | Convert a 2D image to a 3D model |
| **Txt to World** | Generate a 3D world/environment from text |
| **Img to World** | Generate a 3D world from an image |
| **Vid to World** | Generate a 3D world from a video |
| **Inpaint** | Edit specific regions of an image |
| **Outpaint** | Extend an image beyond its borders |
| **Roto Bg** | Remove/replace backgrounds |
| **Face** | Face-specific editing and enhancement |
| **Upscale** | Increase image resolution |
| **Crop** | Crop images |
| **Collage** | Combine multiple images |
| **Annotate** | Add annotations to images |
| **Metadata** | View/edit image metadata |

## API Image Edit Modes

The unified generation API now supports image editing beyond text-to-image:

| Mode | Description | Example Model |
|------|-------------|---------------|
| `txt_to_img` | Text-to-image (standard) | `nano_banana_2` |
| `img_to_img` | Prompt-based image editing | `fal-ai/nano-banana-2/edit` |
| `ref_to_img` | Reference-driven generation | `kling/o1/image-edit` |
| `edit_img` | Direct image editing | `fal-ai/gpt-image-1/edit-image` |

Image edit modes require at least one input image. Valid inputs: `image_asset_id`, `image_url`, `start_image_asset_id`, `reference_image_asset_ids[]`, `element_ids[]`, `elements[]`.

**Example: Prompt-based image edit (restyle a character reference):**
```json
{
  "generator": "image",
  "mode": "img_to_img",
  "model": "fal-ai/nano-banana-2/edit",
  "prompt": "Keep the subject identity and pose, but relight as a moody neon noir portrait with blue rim light.",
  "image_asset_id": "uuid-source-image",
  "reference_image_asset_ids": ["uuid-style-ref"],
  "format": "png"
}
```

**Example: Reference-driven Kling image edit (consistency correction):**
```json
{
  "generator": "image",
  "mode": "ref_to_img",
  "model": "kling/o1/image-edit",
  "prompt": "Match the wardrobe and facial structure from the references exactly.",
  "reference_image_urls": ["https://example.com/hero-base.png"],
  "element_ids": ["project-element-uuid"]
}
```

These edit modes are particularly useful for consistency correction -- fixing character appearance drift in key frames before video generation. See the `pr0ta-consistency` skill.

**Image format validation:** The API accepts `png`, `jpeg`, `jpg`, and `webp`. The value `jpg` is normalized to `jpeg`. Unsupported formats (e.g., `tiff`, `bmp`) return `400`.

**Important caveat:** Nano Banana 2 may output PNG regardless of the requested format. Always check the actual file extension/content type of the returned asset rather than assuming it matches your request.

## Uploading Existing Images into a Project

You don't always need to generate an image — sometimes the best reference is a real photograph, a screenshot, a hand-drawn sketch, or a frame pulled from existing footage. Use the **direct image upload endpoint** to ingest local files:

```
POST /api/v2/projects/{project_id}/assets/upload
Content-Type: multipart/form-data
```

Send one or more `files` fields (images only). The response returns standard `AssetRead` objects whose `id` values can be used immediately in any generation payload:

- `image_asset_id` or `start_image_asset_id` in `img_to_img` / `ref_to_vid` modes
- `reference_image_asset_ids[]` for style or identity references
- Source material when creating Element bundles or Character profiles (see `pr0ta-consistency`)

```python
from pr0ta_client import upload_images

assets = upload_images(project_id, [
    "/path/to/actor-headshot.jpg",
    "/path/to/location-photo.png",
])
headshot_id = assets[0]["id"]
location_id = assets[1]["id"]
```

Optional metadata fields: `category` (default `"imported"`), `subject`, `labels` (JSON object). PR0TA auto-stamps `labels.source = "upload_api"` and `labels.ingest_channel = "api"`.

**When to upload vs generate:** Upload when you have real-world material that should anchor the production — actor likenesses, brand assets, location scouts, product photos, storyboard scans. Generate when you need new synthetic imagery. In practice, most multi-shot productions use both: uploaded references to establish identity, generated images to fill out the shot list.

For the full endpoint spec and error cases, see `pr0ta-api` → "Project Image Upload (Direct Multipart)".

## Image Genre Recipes

Image prompts are not one-size-fits-all. Different shot types have **opposite** requirements. The following recipes cover field-tested genres distinct from standard scene images.

### Flash Card Recipe (Sub-1-Second Shots)

Flash cards are designed to be **felt more than read** — year drops, name drops, impact beats, cut-in title slugs that appear for <1 second in a fast edit. They have opposite requirements from scene images.

**Requirements:**

- **Extreme color saturation.** Single dominant hue, pushed to maximum. Use color to differentiate adjacent flash cards in the cut (e.g., amber-gold for "2027", electric-blue for "2029"). The viewer should register color before content.
- **Massive type.** The text or number should consume 50–80% of the frame. If you can read it at thumbnail size, it is big enough.
- **Zero background detail.** Solid color field or, at most, a single subtle gradient. No textures, no props, no scene elements — background detail will be missed in sub-1-second shots and only adds noise.
- **Single typographic element.** One word, one number, one phrase. Multi-line flash cards don't work — the viewer can't read line 2.
- **Hard, flat lighting.** No dimensional shading on the type. Flat vector-style rendering reads faster than any attempt at realism.

**Prompt template:**

```
A full-frame flash card design. Solid [SINGLE DOMINANT COLOR] background, no other scene elements. Massive centered [TYPE: "2027" / "SINGULARITY" / etc.] in a [BOLD SANS-SERIF / CONDENSED DISPLAY / etc.] typeface, occupying approximately 60-70% of the frame height, rendered in [CONTRASTING COLOR]. Flat vector style, hard edges, no shadows, no gradient on the type. The single typographic element is the entire image. Poster graphic, not a photograph.
```

**Concrete field example:** For a "2027" year-drop flash card in a countdown documentary, amber-gold (#F5A623) background with deep navy numerals worked. For a paired "2029" card, electric-blue (#1E90FF) background with cream-white numerals worked. The saturation jump between the two cards does the editorial work at speed.

**Anti-pattern:** Scene-photography language ("a beautiful amber-toned photograph of the number 2027 on a textured wall"). This produces a scene, not a flash card. Use poster/graphic/flat/vector language instead.

### Scene Image (Default Genre)

The rest of this skill's prompting guidance applies: self-contained, specific subject/lighting/camera, grounded environment. This is the default.

### Title Card

For deliberate title shots (held 1.5–3 seconds with time to read), treat it as a **hybrid** — more typographic than a scene image but with more styling than a flash card. You can afford one subtle background element (a soft gradient, a faint glyph, a vignette) but the type still dominates. AI-generated title cards composed as still images (then animated via a timeline Ken Burns preset) beat any overlay text filter for production polish.

**For text-heavy title cards, use the "Line-Locked Poster" prompt pattern from `pr0ta-prompting`** (`Line N (style): EXACT TEXT` formatting with an `EXACTLY` directive). That pattern routes around the safety/softening pass that rewrites provocative copy into blander substitutes. Field-tested failure mode without it: `"CAN'T RUN OUT OF MONEY"` softened to `"CAN'T RUN OUT OF FUNDS"`.

### Hard Rule — Any Still With On-Screen Text

This is a reliability rule, not a style preference. **If the still has any rendered text — title card, brand name, tagline, credit line, flash card, sign visible in the scene — two steps are mandatory:**

1. **Use the Line-Locked Poster Prompt pattern.** Prose prompts with on-screen text fail in the wild often enough to treat as unreliable — common failure modes include duplicated lines ("WARBY" stacked above "WARBY PARKER"), garbled glyphs ("Lologobo" on a matte corporate card), softened or paraphrased copy, and character drop. The `Line N (style): EXACT TEXT` + `EXACTLY` directive pattern in `pr0ta-prompting` → Technique 3 routes around all of these.
2. **Post-gen glyph QC is mandatory.** After the image lands, read it and verify every character against the intended text — letter by letter, no skimming. Regen on any mismatch. A duplicated line or garbled glyph caught at QC costs one regeneration; caught at delivery it costs a re-edit or a slipped deadline.

**Fan out on any high-stakes text shot.** Brand names, exact-copy title cards, and anything a stakeholder will read at full size are cheap to fan out (3–5 text-reliable image models in parallel) and expensive to ship wrong. See "Fan-Out and Pick" below.

## Fan-Out and Pick — First-Class Recipe for Hard Shots

**When a shot is hard (exact text, complex composition, specific mood), submit the same prompt to 3–5 text-reliable models in parallel and pick the winner.** PR0TA's async job model makes this operationally cheap for *image* fan-out — the time cost is the same as a single generation because they run concurrently, and the credit cost for 3–5 image calls across Nano Banana / Ideogram / GPT Image 1.5 is small enough to treat fan-out as a first-class editorial tool.

**Cost discipline:** Image fan-out is cheap. **Video fan-out is not.** Kling and Seedance video calls cost real money — do not reflexively fan out 3–5 video generations for every hard shot. For video, prefer one well-prompted call (with Line-Locked poster stills animated on the timeline via Ken Burns presets where possible) and reserve fan-out for the few shots where the creative risk genuinely justifies the spend. "Almost free" is only accurate for image-class models.

**Batch route option:** PR0TA exposes a first-class batch endpoint (`POST /api/v2/projects/{id}/generate/batch`, max 10 items) for when you want one request that carries many payloads. The loop in the recipe below uses independent `/generate` calls for simpler per-item error handling; either pattern works.

**Field result:** On a failed title card where Nano Banana 2's first attempt softened the copy, fanning out to five models (Ideogram, Nano Banana 2 retry with a different seed, GPT Image 1.5, Kling V3, Kling O3) and selecting the best was the single highest-ROI move in the entire production. At least one model will almost always nail the shot; sequential retry on a single model is slower and less reliable.

**Recipe:**

```python
# Fan out the same prompt to N text-reliable models in parallel.
PROMPT = """<your Line-Locked Poster prompt here>"""

MODELS = [
    "nano_banana_2",         # default
    "openai/gpt-image-2",   # escalate for prompt adherence / character consistency
    "gpt_image_1_5",
    "ideogram",
    "kling_v3",              # image mode
    "kling_o3",              # image mode
]

task_ids = {}
for model in MODELS:
    resp = submit_generation({
        "generator": "image",
        "mode": "txt_to_img",
        "model": model,
        "prompt": PROMPT,
        "aspect_ratio": "9:16",
    })
    task_id = resp.get("task_id")
    if not task_id:
        print(f"[WARN] {model} rejected at validation: {resp}")
        continue
    task_ids[model] = task_id

# Poll all of them concurrently, download each result, then pick the winner by eye.
```

**Selection criteria, in order:**

1. **Exact text match.** Any card with softened or mutated copy is disqualified regardless of how pretty it is.
2. **Composition and hierarchy.** Hero line dominant, secondary lines clearly subordinate.
3. **Color integrity.** Requested palette actually on the output.
4. **Production polish.** Type rendering (no smeared letters), background cleanliness, aspect ratio fitness.

Log every attempt into `assets.json` (see the `pr0ta` hub → "assets.json — Local Asset ID Map") so you can audit which prompt + model + seed produced the winner and reuse it for consistent re-renders later.

**When NOT to fan out:** Routine B-roll, background plates, and any shot where Nano Banana 2 routinely succeeds on the first attempt. Fan-out is for hard shots, not every shot.

## Output Resolution — The Timeline Handles Upscaling

**⚠️ Image models return their native output resolution, not the pixel dimensions your aspect ratio implies.** Requesting `aspect_ratio: "9:16"` from Nano Banana 2 typically yields something like **768×1376**, not 1080×1920.

**This is fine.** The post-production timeline normalizes every clip — stills and video alike — to the sequence's delivery resolution automatically when you add it via `POST /timeline/clips`. Set the sequence settings once (e.g. 1080×1920 for vertical, 1920×1080 for horizontal) and the platform handles scale + pad + format internally with high-quality resampling. You do not need to pre-upscale stills before adding them to the timeline.

**When you *do* need a still at delivery resolution outside the timeline** (e.g. a standalone thumbnail export): regenerate with the appropriate aspect ratio at the closest supported model size and use the output as-is. Do **not** ask the model to produce a higher resolution by prompt — the native output is fixed per model and prompt language cannot override it.

## Known Limitations and Workarounds

All image generation should use the **reliability contract** from the `pr0ta-api` skill, which handles these issues automatically via the state machine and fallback chain.

- **Format parameter may be ignored by some models.** Nano Banana 2 typically outputs PNG regardless of `format` setting. Plan for PNG output.
- **Image generation events are best-effort (fixed April 2026, defense-in-depth retained).** Events now backfill from task history. The reliability contract still treats events as acceleration only — never as the sole completion signal.
- **Image task status stall (fixed April 2026, defense-in-depth retained).** Task reads now reconcile to `succeeded` when the asset exists. The reliability contract still polls with asset-discovery fallback as defense-in-depth.