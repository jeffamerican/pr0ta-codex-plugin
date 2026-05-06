---
name: pr0ta-consistency
description: "PR0TA visual consistency for recurring characters, locations, props, global visual bibles, Seedance storyboard chunks, and multi-shot continuity. Read when creating or using Kling Elements, Seedance Characters, consistency bundles, reference pipelines, or repeat-subject generation."
---

# Visual Consistency & Continuity Reference

This reference covers how to maintain character, set, prop, and style consistency across multi-shot AI productions in PR0TA. It documents the two primary consistency systems (Kling Elements and Seedance Characters), the professional reference pipeline, and practical workflows.

## Non-Negotiable Character Consistency Rule

If the same character appears in more than one generated image or video shot, character consistency is an absolute requirement. Do not proceed with free-text-only prompts for repeat characters.

Before any multi-shot media generation with recurring characters:

1. Use existing approved casting portraits, contact sheets, character sheets, wardrobe/look references, and performance notes from PR0TA prep.
2. Create or reuse provider consistency resources: Seedance Characters for Seedance workflows, Kling Elements for Kling workflows.
3. Read the character consistency bundle before generation so requests use the approved asset IDs, Element IDs, Character IDs, and provider-ready payload snippets.
4. Repeat the same concrete character description in every prompt, alongside the provider resource token. The resource locks identity; the prose keeps the model oriented.

If approved references or provider resources are missing, generate and approve them first. A character appearing in multiple shots without a consistency resource is a workflow error, not an acceptable shortcut.

## Existing PR0TA Prep Context First

When a project already has a script, script breakdown, casting work, production-designer looks, propmaster references, stylist looks, or casting contact/character sheets, **use those as the source of truth before creating new references**. Do not maintain a separate private JSON ledger for continuity unless the user explicitly asks for an external export.

Use the MCP tool:

```json
production_context_get({
  "project_id": "project_id_here",
  "scene_number": 12,
  "shot_number": 3,
  "include_provider_guidance": true
})
```

It returns:
- script-supervisor scene context and director shotlist data
- casting characters with approved portraits, character sheets, contact-sheet style references, Seedance IDs, and voice config when available
- production-designer set/location looks
- stylist wardrobe/look references
- propmaster prop references
- provider guidance for Seedance and Kling, including missing-reference warnings

Workflow for skill users:
1. Fetch `production_context_get` for the target scene/shot.
2. Use existing approved cast/set/prop/look references first.
3. Generate only missing references, then save them back to PR0TA assets/resources.
4. For Kling, create or reuse Elements for recurring characters, props, and locations.
5. For Seedance, use one stored character lock for the primary character and pass supporting people/sets/props as image/video references unless multi-character lock support is confirmed by the API.
6. For reference-heavy Seedance productions, create or reuse one approved global visual bible from PR0TA prep assets and pass it as `@image1`; generate chunk-specific chronological storyboard reference sheets with `storyboard_chunks_list` and `storyboard_reference_sheet_generate`, then keep those sheets and local refs after the bible in the reference stack. See `pr0ta-video` -> `reference/seedance-global-storyboard.md`.
7. Keep the asset ledger tied to PR0TA asset IDs, Element IDs, Character IDs, and review links; do not fork the production state into a parallel notes file.

## Provider Consistency Systems

PR0TA supports two model-family-specific consistency systems, both managed as persistent project-scoped resources via the API:

| System | Provider | Best For | Generation field |
|--------|----------|----------|------------------|
| **Elements** | Kling (V3, O3, Omni) | Character/prop/location bundles with multi-angle references | `element_ids[]` |
| **Characters** | Seedance 2.0 / MuAPI | Persistent character identity from 1-3 photos or a character sheet | `character_ids[]` |

Use Kling Elements for Kling generations and Seedance Characters for Seedance generations. Do not mix the systems.

Core rules:
- Create one resource per distinct subject, era/look, and wardrobe concept.
- Use approved PR0TA prep references first; generate only missing views or sheets.
- Reuse the same resource IDs across every shot where the subject recurs.
- Keep the prose description consistent in every prompt even when the provider resource is present.
- Read the character consistency bundle before generation and use its `provider_payloads` directly.

**For detailed lifecycle recipes** — Element bundle construction, Seedance token training, `POST /elements`, `POST /characters`, multi-modal references, multi-prompt payloads, camera control, reference-pipeline examples, and image-edit correction payloads — **Read `reference/provider-consistency-systems.md`**.

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
- Missing Seedance token → train one (see `reference/provider-consistency-systems.md` → "Creating A Seedance Character Token"), then `POST /characters` to persist it

After creating the missing resource, re-read the bundle — it will now include the new resource in `provider_payloads`.

## Quick Reference: Consistency Workflow

1. **Resolve existing context:** Call `production_context_get` for the target scene/shot and use existing breakdown, casting, character-sheet/contact-sheet, set, prop, and look references first.
2. **Fill gaps only:** Generate multiple takes (4-6+) only for missing character/location/prop references with Nano Banana 2 (or GPT Image 2 for character consistency edits). Select the best.
3. **Tag approved references:** Use `PATCH /annotations` with `reference_type: "character_reference"` and `category: "portrait"` or `"character_sheet"` on each approved image.
4. **Register resources:** Create Element bundles (Kling) and Character profiles (Seedance) via project API. Train Seedance tokens if needed.
5. **Read the consistency bundle:** `GET /characters/{id}/consistency` or `GET /characters/consistency?name=...` — returns all references, Elements, tokens, and provider-ready payloads in one call.
6. **Global visual bible + storyboard sheets (Seedance-heavy productions):** Create or reuse one approved production bible/contact sheet as `@image1`; list beat chunks with `storyboard_chunks_list`; generate 3-5 chronological storyboard reference sheet variations with `storyboard_reference_sheet_generate`; then add the approved sheet and chunk references after the bible. See `pr0ta-video` -> `reference/seedance-global-storyboard.md`.
7. **Key frames:** Generate scene key frames using image-to-image with Element references
8. **Video generation:** Use `provider_payloads.kling.element_ids` or `provider_payloads.seedance.character_ids` from the bundle in all generation requests
9. **Multi-shot sequences:** Use `multi_prompt` for continuous sequences requiring intra-shot consistency
10. **Long continuous sequences (30s+):** Use Seedance Omni **extension chaining** — feed the previous clip as `@video1` via "Text with Reference" plus static character reference images to fortify consistency. See `pr0ta-video` → `reference/seedance-omni.md` → "Seamless Video Extension".
11. **Correction passes:** Use image edit modes to fix any consistency drift before final video generation
12. **Reuse across project:** All Elements and Characters persist for the project lifetime -- reuse them for reshoots, additional scenes, and variations
