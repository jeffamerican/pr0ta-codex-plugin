## Video Reference Field Matrix (Unified API)

**This is the validator-derived reference-field contract enforced by the unified video request validator (`POST /api/v2/projects/{project_id}/generate`).** Source: PR0TA API team, April 2026. Treat it as the copy-paste-safe surface; provider behavior downstream can still be stricter in specific cases, so always cross-check against the Provider-Certified matrix below for Kling variants.

### Field Families

**Image reference fields:**
- `start_image_asset_id`, `start_image_url`
- `image_asset_id`, `image_url`
- `end_image_asset_id`, `end_image_url`
- `reference_image_asset_ids[]`, `reference_image_urls[]`
- `references[]` with image-like entries
- `element_ids[]`, `elements[]`

**Omni reference extensions (Seedance Omni only):**
- `reference_video_urls[]`
- `reference_audio_urls[]`
- `references[]` with video/audio entries
- `character_id`, `character_ids[]`

**Kling-only adjunct controls:**
- `camera_control`
- `voice_ids[]`

### Per-Model Matrix

| Model | Modes | Prompt | Required Refs | Accepted Reference Fields | Notes |
|---|---|---|---|---|---|
| `muapi/seedance-v2.0-t2v` | `txt_to_vid` only | Required | None | No refs needed | Pure text-to-video |
| `muapi/seedance-v2.0-i2v` | Image-to-video | Required | ≥1 image ref | Image fields only | **No** video/audio/character refs |
| `muapi/seedance-2.0-omni-reference` | All video modes | Required | ≥1 omni ref | **All** image fields + `reference_video_urls[]`, `reference_audio_urls[]`, `references[]`, `element_ids[]`, `elements[]`, `character_id`, `character_ids[]` | **Broadest reference surface** — preferred for reference-heavy work |
| `muapi/seedance-2-character` | Character-construction path | Not enforced | ≥1 image ref (up to 3) | Image fields only | **Character-sheet training.** Requires `character_name` + `outfit_description`. Async; returns Omni token in `result_refs.character_id` for later omni-reference calls. |
| `muapi/seedance-2-omni-reference-train` | Omni-token training path | Not enforced | ≥1 image ref | Image fields only | **Single-portrait training.** Requires `character_name`. Async; returns Omni token in `result_refs.character_id` for later omni-reference calls. Fastest path into Omni when one clean portrait is enough. See `pr0ta-consistency` → `reference/provider-consistency-systems.md` → "Creating A Seedance Character Token". |
| Kling I2V / ref-to-vid (`kling/*`, `fal-ai/kling-video/*`) | `ref_to_vid` / txt/video | Usually | Generic video rules | Image fields, `element_ids[]`, `elements[]`, `references[]` image entries | **Plus** `camera_control` and `voice_ids[]` (Kling only) |

### Validator Rules That Matter In Practice

**1. Generic `ref_to_vid` requires ≥1 image-bearing reference.** Accepted fields: `start_image_asset_id`, `start_image_url`, `image_asset_id`, `image_url`, `reference_image_asset_ids[]`, `reference_image_urls[]`, `element_ids[]`, `elements[]`.

**2. `txt_to_vid` with refs is NOT equivalent to pure text-to-video.** If you include any reference field (image, video, audio, character, element, references[]) on a `txt_to_vid` request, the unified resolver may prefer a reference-capable default model instead of the pure t2v path. If you truly want pure text-to-video, send only `prompt` — no reference fields of any kind.

**3. `character_id` / `character_ids[]` are restricted to `muapi/seedance-2.0-omni-reference`.** The validator rejects stored character refs on every other video model. If you need character continuity, route through Seedance Omni.

**4. `camera_control` and `voice_ids[]` are Kling-only.** The validator rejects them on any non-Kling model.

### Copy-Paste-Safe Payloads

**Pure text-to-video — `muapi/seedance-v2.0-t2v`:**

```json
{
  "generator": "video",
  "mode": "txt_to_vid",
  "model": "muapi/seedance-v2.0-t2v",
  "prompt": "...self-contained scene description...",
  "duration": 5,
  "aspect_ratio": "9:16"
}
```
Do not include image/video/audio/character refs. Any ref present will likely route you to a different model.

**Image-to-video from a single still — `muapi/seedance-v2.0-i2v`:**

```json
{
  "generator": "video",
  "mode": "ref_to_vid",
  "model": "muapi/seedance-v2.0-i2v",
  "prompt": "...self-contained scene description enumerating every state change...",
  "start_image_asset_id": "a73b9aad-...",
  "duration": 5,
  "aspect_ratio": "9:16"
}
```
Do **not** include `reference_video_urls[]`, `reference_audio_urls[]`, or `character_id`.

**Reference-heavy / character continuity / audio-synced — `muapi/seedance-2.0-omni-reference` (preferred default):**

```json
{
  "generator": "video",
  "mode": "ref_to_vid",
  "model": "muapi/seedance-2.0-omni-reference",
  "prompt": "...self-contained scene description...",
  "reference_image_asset_ids": ["a73b9aad-..."],
  "character_ids": ["char_dario_v1"],
  "reference_audio_urls": ["https://.../beat.wav"],
  "duration": 5,
  "aspect_ratio": "9:16"
}
```
This is the broadest reference surface in the unified API. Prefer this when you have any combination of images + character sheet + audio references.

**Character-sheet training — `muapi/seedance-2-character`** (use when you have 1-3 approved stills or a real character sheet):

```json
{
  "generator": "video",
  "mode": "ref_to_vid",
  "model": "muapi/seedance-2-character",
  "images_list": [
    "https://example.com/maya-sheet-front.jpg",
    "https://example.com/maya-sheet-profile.jpg"
  ],
  "character_name": "Maya",
  "outfit_description": "charcoal three-piece suit, cream dress shirt, burgundy tie, oxford lace-ups"
}
```
Async. Returns an Omni token in `result_refs.character_id` on completion. `outfit_description` is **required**. Accepts up to 3 stills.

**Single-portrait training — `muapi/seedance-2-omni-reference-train`** (use when you have one clean hero portrait):

```json
{
  "generator": "video",
  "mode": "ref_to_vid",
  "model": "muapi/seedance-2-omni-reference-train",
  "image_url": "https://example.com/hero-portrait.jpg",
  "character_name": "Maya",
  "description": "Female lead, black leather jacket, studio portrait, neutral expression"
}
```
Async. Returns an Omni token in `result_refs.character_id` on completion. Fastest path into Omni Reference when a single clear face-forward image is enough. Persist the returned token via `POST /characters` (provider: `muapi`) for later reuse via `character_ids[]` on `muapi/seedance-2.0-omni-reference`. See `pr0ta-consistency` → `reference/provider-consistency-systems.md` → "Creating A Seedance Character Token" for the full lifecycle.

**Kling image-to-video (cinematic continuation):**

```json
{
  "generator": "video",
  "mode": "ref_to_vid",
  "model": "kling_o3_pro",
  "start_image_asset_id": "a73b9aad-...",
  "prompt": "...self-contained scene description...",
  "camera_control": { "type": "push_in", "strength": 0.4 },
  "duration": 5,
  "aspect_ratio": "9:16"
}
```
`camera_control` and `voice_ids[]` are allowed on Kling only.

### Provider-Certified Reference Fields (Source: Provider OpenAPI Specs)

**The unified validator accepts a broad reference-field surface, but provider endpoints downstream have stricter, per-variant contracts.** The following matrix comes from provider-native OpenAPI specs (fal.ai for Kling, MuAPI for Seedance) and is the authoritative source for "what the provider actually wants."

Read this as a two-layer contract:

1. **What the provider endpoint requires** (provider-native field names)
2. **What PR0TA must translate into that shape** (unified field → provider field)

PR0TA's unified fields are convenience fields, not provider-native fields. A unified request like `start_image_asset_id: "abc"` is only valid downstream **if PR0TA resolves the asset and translates it to the specific provider-native field name that endpoint expects**.

| Provider Model | Provider Endpoint | Required | Provider Reference Fields |
|---|---|---|---|
| **Kling V3 Pro (I2V)** | `POST /fal-ai/kling-video/v3/pro/image-to-video` | `start_image_url` | `start_image_url`, `end_image_url`, `elements[]`, `voice_ids[]`, `multi_prompt` |
| **Kling O3 Pro (I2V)** | `POST /fal-ai/kling-video/o3/pro/image-to-video` | `image_url` | `image_url`, `end_image_url`, `multi_prompt` |
| **Kling O3 Pro (Ref-to-Video)** | `POST /fal-ai/kling-video/o3/pro/reference-to-video` | prompt + refs | `start_image_url`, `image_urls[]`, `elements[]`, `end_image_url`, `multi_prompt` |
| **Seedance 2.0 T2V** | `POST /api/v1/seedance-v2.0-t2v` | `prompt` | (none) |
| **Seedance 2.0 I2V** | `POST /api/v1/seedance-v2.0-i2v` | `prompt`, `images_list` | `images_list[]` |
| **Seedance 2.0 Omni Reference** | `POST /api/v1/seedance-2.0-omni-reference` | `prompt` | `images_list[]`, `video_files[]`, `audio_files[]` |
| **Seedance 2.0 Video Edit** | `POST /api/v1/seedance-v2.0-video-edit` | `prompt`, `video_urls` | `video_urls[]`, optional `images_list[]` |

### Critical Findings From Provider Specs

**1. Kling variants do NOT share a universal reference contract.** This is the most important takeaway. They expose materially different reference fields at the provider level:

| Kling variant | Primary image field |
|---|---|
| Kling V3 Pro I2V | `start_image_url` (required) |
| Kling O3 Pro I2V | `image_url` (required — **not** `start_image_url`) |
| Kling O3 Pro Reference-to-Video | `start_image_url` + `image_urls[]` + `elements[]` |

Do not assume a reference field that works on one Kling endpoint works on another. They are separate provider endpoints with separate schemas.

**2. Kling O3 Pro has two distinct endpoints: Image-to-Video and Reference-to-Video.** These are not interchangeable:
- I2V takes a single `image_url` for a basic start frame
- Reference-to-Video takes `start_image_url` + `image_urls[]` + `elements[]` for rich multi-reference composition

When you need richer reference composition on Kling, the Reference-to-Video endpoint is the correct target — not assumptions layered onto the I2V endpoint.

**3. Seedance I2V uses `images_list`**, not `image_url` or `images_urls`. PR0TA's unified `start_image_asset_id` / `reference_image_asset_ids[]` must resolve and map into `images_list` for the MuAPI Seedance I2V call.

**4. Seedance Omni Reference provider-native fields are `images_list[]`, `video_files[]`, `audio_files[]`.** These map to PR0TA's unified `reference_image_*`, `reference_video_urls[]`, and `reference_audio_urls[]` respectively.

### The Kling V3 Pro Caveat — RESOLVED (April 2026)

The previously field-tested failure (`kling_v3_pro` silently accepting `start_image_asset_id` and then failing downstream with `"Invalid reference index 1 for image. Only 0 images provided."`) is **now fixed end-to-end**.

**What changed:**
- Kling V3 Pro's provider endpoint **requires** `start_image_url`.
- PR0TA's unified layer now resolves `start_image_asset_id` → provider-native `start_image_url` via `input_asset_resolver.py` → `request_mapper.py` → `fal_request_builder.py`, which preserves the provider-native field name on the outbound Fal submission instead of rewriting it to a `first/last` alias.
- Targeted regression test coverage (`test_fal_request_builder.py`) now protects this outbound payload shape.

**Operational rule:** Agents may use `start_image_asset_id` (or `start_image_url`) directly on `fal-ai/kling-video/v3/pro/image-to-video`. If asset-backed project media is involved, `start_image_asset_id` is the cleanest unified field. The same fix applies to `end_image_asset_id` → `end_image_url`.

**If a future V3 Pro failure appears, do not assume the asset-id translation is the root cause.** Check `task.error_reason` and the actual provider response — the translation gap is closed.

Seedance 2.0 Omni is still the preferred default for reference-heavy work because it has the broadest multimodal surface (image + video + audio + character refs), but Kling V3 Pro is now a safe operational target when you specifically want Kling's atmospheric continuation.

### Failure-Mode Guidance

When a reference payload fails, **trust the error message.**

- **Validator rejection** surfaces as an explicit server-side error at submission time. Read the error text — it usually names the specific field that's wrong.
- **Downstream provider rejection** surfaces as a task failure after submission. Check `task.error_reason` for the provider's actual complaint — don't assume it's a known translation gap (the historical Kling V3 Pro case is now fixed).
- Neither failure mode is silent hallucination — if a shot silently produced the wrong content, the issue is prompting (see `pr0ta-prompting`), not a reference-field validation bug.

If in doubt, test the payload against a short 2-second generation before committing a full production to it.

### Skills-Facing Compatibility Quick Reference

This table is the copy-paste-safe surface for agents — what provider-native field each model requires, and which unified PR0TA field to send.

| Model | Provider-Native Required | Preferred PR0TA Unified Field | Alternates | Translation Implemented | Tested |
|---|---|---|---|---|---|
| `fal-ai/kling-video/v3/pro/image-to-video` | `start_image_url` | `start_image_asset_id` | `start_image_url`, `end_image_asset_id`, `end_image_url`, `elements[]` | Yes | Yes |
| `fal-ai/kling-video/o3/pro/image-to-video` | `image_url` | `image_asset_id` | `image_url`, `start_image_asset_id`, `start_image_url`, `end_image_asset_id`, `end_image_url` | Yes | Partial |
| `fal-ai/kling-video/o3/pro/reference-to-video` | practical: prompt + refs | `start_image_asset_id` + `reference_image_asset_ids[]` | `start_image_url`, `reference_image_urls[]`, `elements[]`, `end_image_*` | Yes | Partial |
| `muapi/seedance-v2.0-i2v` | `images_list[]` | `reference_image_asset_ids[]` | `reference_image_urls[]`, `start_image_asset_id`, `start_image_url` | Yes | Yes |
| `muapi/seedance-2.0-omni-reference` | `prompt` + multimodal refs | `reference_image_asset_ids[]`, `reference_video_urls[]`, `reference_audio_urls[]` | `reference_image_urls[]`, `elements[]`, `character_id`, `character_ids[]` | Yes | Yes |

**Legend:** *Implemented* = unified→provider translation is wired. *Tested* = targeted provider-specific outbound assertion exists. *Partial* = path looks wired but full provider-specific outbound assertion is not at the same confidence level as Fal Kling V3 Pro.

**Matrix status:** The validator-derived matrix is authoritative for submission-time validation. The provider-certified rows above are authoritative for what actually reaches the provider. Both are now in sync for the common paths.
