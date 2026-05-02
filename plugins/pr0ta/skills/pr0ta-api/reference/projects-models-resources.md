## Project Management (Auth Required)

### List Projects
```
GET /api/v2/projects
```
Returns all projects the authenticated user can access. Each project includes: `id`, `name`, `created_at`, `asset_count`, `settings`, `is_active_project`.

### Create Project
```
POST /api/v2/projects
```
```json
{
  "name": "Turtle Videos",
  "description": "Automation workspace"
}
```
Add `?select=true` to auto-set as the active project: `POST /api/v2/projects?select=true`

**PAT limitation:** `?select=true` only works with JWT session tokens. PATs will receive `"Active project selection requires an interactive session token"`. When using a PAT, create the project without `?select=true` and use the returned `id` directly in all subsequent API calls -- active project selection is only needed for browser-side workflows.

### Get Project
```
GET /api/v2/projects/{project_id}
```

### Update Project
```
PATCH /api/v2/projects/{project_id}
```

### Delete Project
```
DELETE /api/v2/projects/{project_id}
```

### Archive Project
```
POST /api/v2/projects/{project_id}/archive
```

### Set Active Project
```
POST /api/v2/projects/{project_id}/select
```
Sets the project as the user's active project.

### Clear Active Project
```
DELETE /api/v2/projects/active
```

### Get Current User Info (includes active project)
```
GET /api/auth/me
```
Returns user info including `active_project_id`.

---

## Model Discovery

### Filtered Catalog

```
GET /api/v2/models
GET /api/v2/models?generator=image
GET /api/v2/models?generator=image&image_kind=text_to_image
GET /api/v2/models?generator=image&image_kind=image_edit
GET /api/v2/models?generator=video
GET /api/v2/models?generator=audio
GET /api/v2/models?generator=music
```

No auth required. Returns available models with identifiers, pricing, and capabilities. Filter by `generator` and optionally by `image_kind` for the image modality. Image rows include `image_kind` (`text_to_image` or `image_edit`) and `supported_modes` (e.g. `["txt_to_img"]` for T2I, `["img_to_img", "ref_to_img", "edit_img"]` for edit models). Upscaling models stay out of image lists (they use `/api/upscale_image`).

### Provider and Defaults Discovery

```
GET /api/crew/providers                           — full provider list (all modalities)
GET /api/crew/model_defaults?model_id={model_id}  — OpenAPI-driven defaults + JSON Schema for a model
GET /api/crew/model_pricing?model_id={model_id}   — billable / display pricing hint
```

Use `model_defaults` to discover the authoritative parameter list and types for any model before calling `/generate`. This is especially useful for newly added models where parameter names differ from established ones.

### Common Model Identifiers

| Generator | UI Display Name | API `model` string |
|-----------|----------------|-------------------|
| **Image** | **GPT Image 2** | **`openai/gpt-image-2`** |
| **Image Edit** | **GPT Image 2 Edit** | **`openai/gpt-image-2/edit`** |
| Image | Nano Banana 2 | `nano_banana_2` |
| Image Edit | Nano Banana 2 Edit | `fal-ai/nano-banana-2/edit` |
| Image Edit | GPT Image 1 Edit | `fal-ai/gpt-image-1/edit-image` |
| Image Edit | Kling Image Edit | `kling/o1/image-edit` |
| Video | Kling Video O3 Pro | `kling_o3_pro` |
| Video | Kling O3 (advanced) | `kling/o3/image-to-video` |
| Video | Kling V3 Pro | `kling_v3_pro` |
| Video | Seedance 2.0 Omni | `muapi/seedance-2.0-omni-reference` |
| Video | Seedance 2.0 T2V | `muapi/seedance-v2.0-t2v` |
| Video | Lyra 2 Zoom (i2v) | `fal-ai/lyra-2/zoom` |
| Audio | Gemini 3.1 Flash TTS | `fal-ai/gemini-3.1-flash-tts` |
| Audio | Eleven v3 fallback | `eleven_v3` |
| Music | Eleven Music | `music-v1` |

**Default recommendation:** For image work, **Nano Banana 2** (`nano_banana_2` for T2I, `fal-ai/nano-banana-2/edit` for editing) is the default — fast and cost-effective. Escalate to **GPT Image 2** (`openai/gpt-image-2` / `openai/gpt-image-2/edit`) for challenging prompt adherence or character consistency edits where GPT Image 2's superior identity preservation is needed.

**Model string formats:** Some models accept multiple string formats. The strings above are canonical. The tester also confirmed these work: `fal-ai/kling-video/o3/pro/image-to-video` (equivalent to `kling_o3_pro`). Always verify against the models endpoint.

Using incorrect model strings will return a `500` error. Always verify against the models endpoint.

---

## Reusable Consistency Resources

The project API exposes persistent, reusable consistency resources for maintaining character, prop, and location consistency across generations.

### Element Bundles (Kling)

Elements are project-scoped Kling reference bundles for character/prop/location consistency. Create them once, reuse across all generations in the project.

**Create Element:**
```
POST /api/v2/projects/{project_id}/elements
```
```json
{
  "name": "Lead Hero Element",
  "provider": "kling",
  "provider_resource_id": "101",
  "reference_asset_ids": ["c4f3bdf3-472a-4d6a-ad08-ea3872b8ed0c"]
}
```

**List Elements:**
```
GET /api/v2/projects/{project_id}/elements
```

**Get Element:**
```
GET /api/v2/projects/{project_id}/elements/{element_id}
```

**Update Element:**
```
PATCH /api/v2/projects/{project_id}/elements/{element_id}
```

**Delete Element:**
```
DELETE /api/v2/projects/{project_id}/elements/{element_id}
```

**Legacy Kling compatibility:** Older projects that used Kling-scoped element IDs in project metadata are automatically bootstrapped into the new `elements` table on first use. Both new internal project resource IDs and legacy provider element IDs are accepted during resolution.

### Character Profiles (Seedance / MuAPI)

Characters are project-scoped Seedance/MuAPI character identities for persistent character consistency. A Seedance character is constructed from a **frontal image** (identity anchor) + a **character sheet** (multi-panel reference at 4K 21:9 resolution showing front, back, side, poses, expressions) + optionally **1-2 additional images**. Generate the character sheet with Nano Banana 2 first (see `pr0ta-consistency`), then register the character here.

**Create Character:**
```
POST /api/v2/projects/{project_id}/characters
```
```json
{
  "name": "Lead Hero",
  "provider": "muapi",
  "provider_resource_id": "char_approved_hero_v1"
}
```

**List Characters:**
```
GET /api/v2/projects/{project_id}/characters
```

**Get Character:**
```
GET /api/v2/projects/{project_id}/characters/{character_id}
```

**Update Character:**
```
PATCH /api/v2/projects/{project_id}/characters/{character_id}
```

**Delete Character:**
```
DELETE /api/v2/projects/{project_id}/characters/{character_id}
```

### Character Consistency Bundles

Before multi-shot character-consistent generation, read the character's consistency bundle — a single endpoint that returns all approved reference assets, stored Kling Elements, stored Seedance/MuAPI tokens, and provider-ready payload snippets in one response.

**Get Consistency Bundle by Character ID:**
```
GET /api/v2/projects/{project_id}/characters/{character_id}/consistency
```

**Get Consistency Bundle by Character Name:**
```
GET /api/v2/projects/{project_id}/characters/consistency?name={character_name}
```

Response includes:
- `reference_assets[]` — approved portraits and turnaround sheets tagged as `character_reference`
- `kling_elements[]` — stored Kling Elements with `provider_resource_id`
- `seedance_characters[]` — stored Seedance/MuAPI characters with `provider_resource_id`
- `provider_payloads` — ready-to-use snippets:
  - `provider_payloads.assets` — `reference_asset_ids`, `portrait_asset_ids`, `turnaround_asset_ids`
  - `provider_payloads.kling` — `element_ids[]` for direct use in generation requests
  - `provider_payloads.seedance` — `character_ids[]` and `prompt_tokens[]` for Omni Reference

**Workflow:** Tag approved reference images with `reference_type: "character_reference"` and `category: "portrait"` or `"character_sheet"` via `PATCH /api/assets/{project_name}/annotations`. Store Kling Elements via `POST /elements` and Seedance tokens via `POST /characters`. Then read the bundle before generation and use the `provider_payloads` directly. See `pr0ta-consistency` → "Character Consistency Bundles" for the full workflow.

---
