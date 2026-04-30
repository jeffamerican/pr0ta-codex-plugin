---
name: pr0ta-video
description: "PR0TA video generation guide for Seedance, Kling, references, multi-shot continuity, video extension, camera/voice control, Elements/Characters, duration limits, and provider fallback. Read when generating, extending, or troubleshooting video."
---

# Video Generator Reference

For consistency across multi-shot productions, read the `pr0ta-consistency` skill first.

## Model Selection: Seedance and Kling V3/O3 Are Co-Equal Alternatives

**Seedance 2.0 Omni and Kling V3/O3 with multi-shot are co-equal defaults.** Both are first-class options for serious video work. The right choice depends on the shot, not a global preference. For consistency and continuity challenges, **it's often worth generating the same shot in both models and comparing** — the variance between Seedance and Kling is sometimes exactly what gives you the take you need.

**Seedance 2.0 Omni** is strongest for:
- **Quad-modal references** — images + video + audio + character IDs in one call. Rhythm-synced motion matched to an audio reference.
- **Character identity locking** across shots via `character_id` / `character_ids[]`.
- **Narrow, well-defined action** where you want the model to honor the reference bundle strictly.
- **Audio-driven visual timing** — music videos, rhythm-matched content.

**Kling V3 Pro and O3 Pro with multi-shot** are strongest for:
- **Detailed prompt control** — Kling responds exceptionally well to explicit cinematography language, shot labels, and action-timeline structure. When you can describe the shot precisely, Kling gives you the shot precisely.
- **Multi-shot continuity in a single generation** — Kling V3 supports up to 5 shots per generation, Kling O3 supports up to 6 camera cuts per generation. All shots share one visual context, which is the cheapest path to character and scene continuity you can buy.
- **Structured `camera_control` API parameters** (Kling V3 only) — dolly, pan, tilt as first-class config instead of prose.
- **Element bundles with 4+ reference images per subject** — multi-angle composition flexibility.
- **Motion Brush** (Kling V3) — selective region animation.
- **Budget-sensitive work** — Kling at 14.70 credits/s vs Seedance at 63.00 credits/s.

**⚠️ Seedance Omni requires at least one reference.** Despite the `txt_to_vid` mode name, Seedance Omni always requires at least one image, video, or audio reference via `@Image1`/`@Video1`/`@Audio1` tokens. For truly text-only video generation (no reference images at all), use **LTX-2.3** or the **Seedance T2V** variant. For narration-first pipelines where you generate images before video, this is not a blocker — use the generated images as references.

### Try Both — Variety Is a Technique

For any shot where consistency, continuity, or precise intent matter, **generate the shot in both Seedance and Kling and pick the better take**. The cost of two generations is trivial compared to the cost of shipping the wrong shot. Different models have different failure modes; comparing takes exposes which model is right for *this* shot. This is not a fallback — it's a production technique.

### Decision Tree

- **Need character consistency across shots →** Seedance Omni with `character_id` **or** Kling multi-shot (pick the model that gave you the better lock in a test pair).
- **Need up to 6 camera cuts in one generation →** Kling O3 Pro (6 cuts) or Kling V3 Pro (5 shots). Seedance does not support as many discrete cuts in one call.
- **Need structured `camera_control` API parameters →** Kling V3 (only model with structured camera control).
- **Need quad-modal references (image + video + audio) →** Seedance Omni.
- **Need audio-driven rhythm matching →** Seedance Omni.
- **Need a long continuous sequence (30s+) with consistent characters/audio →** Seedance Omni via **extension chaining** — use "Text with Reference" with the previous clip as `@video1` to seamlessly continue from the last frame. See `reference/seedance-omni.md` → "Seamless Video Extension".
- **Need to extend an existing clip as new generated motion →** use unified video extension: `generator=video`, `mode=extend_video`, a source `video_asset_id`/`video_url`, prompt, and an extension model such as `fal-ai/pixverse/v6/extend`, `fal-ai/veo3.1/extend-video`, `fal-ai/vidu/q2/video-extension/pro`, `fal-ai/magi/extend-video`, or `kling/v3/video-extend`.
- **Need Motion Brush →** Kling V3.
- **Budget is tight →** Kling (14.70/s) over Seedance (63.00/s).
- **Text-only, no references →** LTX-2.3 (6.30/s) or Seedance T2V variant.
- **Need a zoom/push into a still image →** Lyra 2 Zoom (`fal-ai/lyra-2/zoom`, `mode: ref_to_vid`). Always requires a source image + text prompt. Check `model_defaults` for zoom_direction, resolution, and other params.
- **Have a start image, need a single continuous shot →** Either works. Test both.
- **You already know exactly what the shot looks like →** Kling. Its prompt adherence for precise cinematography is excellent.
- **Seedance or Kling rejected an allowed shot on provider safety →** treat it as a provider false positive and use the fallback ladder below without hiding the original error.

### Provider False-Positive Fallback Ladder

Seedance and Kling share (or overlap in) a strict content classifier. When an otherwise allowed creative shot — classical / Biblical art, story-relevant non-graphic violence, edgy character design, brand-sensitive source material — gets bounced by either, preserve the provider error and move through the fallback ladder. This is for false positives only. Do not use this ladder to bypass PR0TA policy, provider policy, legal constraints, or the user's safety requirements.

**Fallback models, in order of preference for allowed-content recovery:**

- **Grok Imagine** — first fallback when Seedance/Kling incorrectly reject an otherwise allowed shot on nudity, violence, or "risk control."
- **LTX 2.3** — open-weights lineage and also the right choice for truly text-only video with no references.
- **WAN 2.7 / 2.6 / 2.5** — useful when the shot is allowed but other providers keep false-positive rejecting it. If 2.7 is unavailable, step down to 2.6, then 2.5.

**Use tolerance settings only for allowed content.** For models that expose a content-safety / tolerance parameter (Nano Banana 2's `tolerance` field is the canonical example; video-side equivalents appear as `safety_level`, `content_filter`, or provider-specific flags), use the highest allowed value that still complies with PR0TA/provider policy and the user's brief. Do not describe this as bypassing safety; describe it as recovering from a false-positive provider classification.

**Workflow when a shot gets rejected:**

1. Confirm the rejection is content-policy (not prompt-structure or invalid-parameter) by reading the task's terminal error. Seedance returns *"sensitive content"*; Kling returns *"Failure to pass the risk control system."*
2. If the content is allowed, adjust the current model's tolerance within policy and retry once. If it passes, ship and move on.
3. If it still rejects, switch to the fallback ladder above — Grok Imagine first, then LTX 2.3, then WAN 2.7/2.6/2.5 — with policy-compliant tolerance on each.
4. Only fall back to client-side prompt rewrites (modesty substitution, softening descriptors) after the alternate providers also reject. Rewriting the shot is lossy; switching models is not.

For allowed content, this is usually classifier variance, not prompt engineering — positive framing (Technique 4 in `pr0ta-prompting`) will not fix a real provider safety rejection. Preserve the error and switch models when appropriate.

### Cross-Provider Pivot on Stall

Content rejection is one failure mode. The other is a **silent provider stall** — the task sits in `running` for 7+ minutes with no `progress` change and never completes. Seedance and Kling fail this way independently; when one is queued-hot, the other usually isn't.

**`pr0ta-api` already documents the cancel-and-resubmit pattern (same `progress` value for >3 minutes → treat as stalled). This is the pivot extension:** on the **second stall** of the same shot, do not retry on the same provider a third time — pivot.

**Stall escape ladder:**

1. **First stall (>3 min, no progress):** cancel, resubmit the identical request to the same provider. Sometimes a queue-reset fixes it.
2. **Second stall on the same shot:** cancel, and **resubmit to the other provider** (Seedance → Kling V3 I2V, or Kling → Seedance Omni). Do not burn a third attempt on the same backend.
3. **Both providers stall:** stop submitting. Surface the status to the user before trying a third model class or degrading to a Ken Burns push on the still. The user gets to decide whether motion is mandatory for that shot.

**Quick field-translation table for pivoting Seedance Omni ↔ Kling V3 Image-to-Video (the common pivot):**

| Intent | Seedance Omni (`muapi/seedance-2.0-omni-reference`) | Kling V3 I2V (`fal-ai/kling-video/v3/pro/image-to-video`) |
|---|---|---|
| Start image from project asset | `reference_image_asset_ids: ["..."]` or `image_asset_id` | `start_image_asset_id: "..."` |
| Start image by URL | `reference_image_urls: ["..."]` | `start_image_url: "..."` |
| Reference token in prompt | Optional (`@Image1` accepted, not required) | Include `@Image1` at head of prompt for best lock |
| Duration | Integer, provider-defined (verify per shot) | Integer 3–15 |
| Character lock | `character_ids: ["omni-token"]` | Not supported — use multi-shot + elements |
| Camera control API | Not exposed | `camera_control: { type: ..., strength: ... }` |

For the full, authoritative per-provider field contract see `reference/video-reference-field-matrix.md`.

**Do not pivot silently.** If the original shot has continuity constraints (locked character, matched motion, specific camera move), confirm with the user before switching providers — the pivot target may produce a visually different take even with the same inputs, and surfacing that is cheaper than shipping an inconsistency.

### API Quick Reference — Complete Video Generation Examples

**Copy-paste ready.** For the full parameter reference, see `pr0ta-api`.

```bash
# Seedance 2.0 T2V text-to-video
curl -X POST "https://app.pr0ta.com/api/v2/projects/$PROJECT_ID/generate" \
  -H "Authorization: Bearer $PR0TA_PAT" \
  -H "Content-Type: application/json" \
  -d '{
    "generator": "video",
    "mode": "txt_to_vid",
    "model": "muapi/seedance-v2.0-t2v",
    "prompt": "A woman walks through a rain-soaked neon city at night, reflections on wet pavement.",
    "duration": 5,
    "aspect_ratio": "16:9",
    "sound": "off"
  }'

# Kling O3 Pro image-to-video (co-equal alternative)
curl -X POST "https://app.pr0ta.com/api/v2/projects/$PROJECT_ID/generate" \
  -H "Authorization: Bearer $PR0TA_PAT" \
  -H "Content-Type: application/json" \
  -d '{
    "generator": "video",
    "mode": "ref_to_vid",
    "model": "kling_o3_pro",
    "prompt": "@Image1 -- camera slowly pulls back to reveal the full scene.",
    "start_image_asset_id": "uuid-of-uploaded-image",
    "duration": 5,
    "aspect_ratio": "16:9",
    "sound": "off",
    "cfg": 0.5
  }'

# Video extension from an existing source clip
curl -X POST "https://app.pr0ta.com/api/v2/projects/$PROJECT_ID/generate" \
  -H "Authorization: Bearer $PR0TA_PAT" \
  -H "Content-Type: application/json" \
  -d '{
    "generator": "video",
    "mode": "extend_video",
    "model": "fal-ai/pixverse/v6/extend",
    "prompt": "Continue the same camera move into denser fog while preserving the shot geometry.",
    "video_asset_id": "uuid-of-source-video",
    "duration": 5,
    "aspect_ratio": "9:16",
    "sound": "off"
  }'

# Returns: { "task_id": "...", "status": "queued" }
# Poll task (video can take up to 20 min), then download via result.asset_id
```

| API Model String | Human Name | Mode | Credits | Duration |
|-----------------|------------|------|---------|----------|
| `muapi/seedance-2.0-omni-reference` | Seedance 2.0 Omni | txt_to_vid | 63.00/s | Provider-defined integers |
| `kling_o3_pro` | Kling O3 Pro | ref_to_vid | 14.70/s | 3–15s |
| `kling/v3/image-to-video` | Kling V3 Pro | ref_to_vid | 14.70/s | 3–15s |

**Kling duration behavior:** Valid durations for Kling O3/V3 are integer seconds in the range 3–15. Invalid values return a provider error (not silently clamped). Durations are integer-oriented — do not pass fractional seconds. Check `GET /api/v2/models` for the authoritative per-model duration constraints. The actual output duration may differ from the requested duration by ±0.2s; the timeline accounts for this when you add the clip.

**⚠️ Output dimensions are not guaranteed to match your aspect ratio in exact pixels.** Kling O3 Pro videos requested as 9:16 may not return at exactly 1080×1920. **The post-production timeline normalizes all clips to the delivery resolution automatically** when you add them via `POST /timeline/clips` — set the sequence settings (1920×1080, 1080×1920, etc.) and the platform handles scale/pad/format. You do not need to pre-normalize before adding a clip to the timeline. See `pr0ta-timeline` → "Sequence Settings".

### Duration Overflow — When Narration Beats Exceed Model Limits

In narration-first pipelines, narration beats can easily exceed the video model's maximum duration (15s for Kling, varies for Seedance). A 20-second narration segment about a complex topic is completely normal in documentary work. Here are the strategies, in order of preference:

1. **Split the beat at a natural cut point.** Find a clause boundary or pause in the narration transcript and split into two sub-beats, each within the model's duration limit. Generate two separate video clips and crossfade between them on the post-production timeline. This produces the most natural result.

2. **Extend the video source when the motion should continue.** Use PR0TA's video extension modality (`extend_video` / provider-specific extension mode exposed through the unified API) when the beat needs the same moving shot to continue beyond the first generated clip. Extension is the correct repair when the composition, camera move, or action should remain continuous. Inspect the extended asset's true duration before placing it on the timeline.

3. **Generate max duration + crossfade to a deliberate companion visual.** Generate 15s of AI video for the opening of the beat, then crossfade to a companion shot, insert, map, diagram, or still with Ken Burns motion for the remainder. This should read as an editorial cut, not a hidden source tail.

4. **Ken Burns on the still as full fallback.** Use the AI-generated image with a Ken Burns preset on the post-production timeline for the entire beat duration. This always works regardless of duration but produces less dynamic results than AI video. Set the `kenBurns` clip property to `push_in`, `pull_back`, or `ken_burns_slow` — see `pr0ta-timeline` → "Ken Burns as a Clip Property".

5. **Kling multi-shot across the full beat.** If you're already planning multiple cuts within the beat, use a single Kling O3 multi-shot generation (up to 6 cuts, up to 15s total) instead of one long clip. You get multiple shots worth of coverage *and* the duration you need in a single call, with locked continuity.

**Planning guidance:** When building the cut list for a narration-first production, check each segment duration against the target model's limit. If multiple segments exceed 15s, consider re-segmenting the narration at natural paragraph or clause boundaries to create shorter segments. This is cheaper than generating extra clips.

## Modes

### 1. Txt to Vid (Text-to-Video)
Generate video from a text prompt only.

**Default model: LTX-2.3** (6.30 credits/second)

**Key parameters:** duration, prompt (single or multi-prompt for timed segments), aspect ratio (16:9, 9:16, 1:1, 4:3, etc.), frames per second (25 default), resolution (1080p default).

### 2. Img to Vid (Image-to-Video)
Animate a single image into video.

### 3. Img to Vid+ (Enhanced Image-to-Video)
Enhanced image-to-video with more control.

### 4. Ref to Vid (Reference-to-Video)
Generate video using reference images for character/scene consistency. This is the primary tool for high-quality AI video with visual references.

**Authoritative default:** Seedance 2.0 Omni and Kling V3/O3 are co-equal high-quality defaults. Pick from the decision tree at the top of this skill instead of assuming one global default.

**Key parameters:** start image (opening frame reference), end image (optional), element references (characters, props), reference strength (0-140%+, default 140%), prompt (single or multi-prompt), duration (5s default, 10s, 15s), negative prompt, cfg (classifier-free guidance, default 0.5). **Keep all negations in the negative prompt — never in the main prompt body.** Video models silently drop `don't` / `no` / `does not` from prose prompts and render the forbidden action. See `pr0ta-prompting` → Technique 4 ("Frame Motion and State Positively, Never Negatively") for the rewrite pattern.

**Model catalog:** Do not rely on this skill for live pricing or availability. Query `GET /api/v2/models` and `GET /api/v2/model_defaults` before a production pass, then apply the decision tree here. Stable defaults:
- **Kling O3/V3** — best for precise cinematography, multi-shot prompts, Elements, and camera control.
- **Seedance 2.0 Omni** — best for character ID locking, quad-modal references, and fast continuity tests.
- **LTX / WAN / Grok / Runway / Veo / Vidu** — use when the model list says they fit the needed mode, duration, reference behavior, cost, or provider fallback path.
- Kling Video O1 (Reference-to-Video) -- 11.76 credits/second

**API model strings for key models:**

| UI Name | API `model` string | Notes |
|---------|-------------------|-------|
| Kling Video O3 Pro | `kling_o3_pro` | Ref-to-vid, multi-prompt, sound, up to 15s |
| Kling O3 (advanced) | `kling/o3/image-to-video` | Multi-prompt, camera control, voice, up to 15s |
| Kling V3 Pro | `kling_v3_pro` | Multi-shot, camera controls, sound, up to 15s |
| Seedance 2.0 Omni | `muapi/seedance-2.0-omni-reference` | Quad-modal, character ID, sound, up to 15s |
| Seedance 2.0 T2V | `muapi/seedance-v2.0-t2v` | Text-to-video, sound control, up to 15s |

**Alternative model strings confirmed working:**
- `fal-ai/kling-video/o3/pro/image-to-video` (equivalent to `kling_o3_pro` / `kling/o3/image-to-video`)

Always verify current model strings against `GET /api/v2/models`.

### 5. FFLF (First Frame Last Frame)
Generate video interpolation between a start and end frame.

## Video Editing Tools (Below the generate button)

| Tool | Description |
|------|-------------|
| **Vid to Vid** | Transform an existing video with a prompt |
| **Mot to Vid** | Motion-to-video generation |
| **Dial to Vid** | Dialogue/lip-sync to video |
| **Dial to Lip** | Dialogue-driven lip sync |
| **Extend** | Extend a video clip's duration |
| **Inpaint** | Edit specific regions of a video |
| **Reframe** | Change video aspect ratio/framing |
| **Roto Bg** | Remove/replace video backgrounds |
| **Enhance** | Upscale/enhance video quality |
| **Upscale** | Increase video resolution |

## Kling V3 / O3 Pro Prompting — Reference

Kling uses an element-reference prompting system (`@Image1` = Start Image, `@Element1..N` = attached element bundles, action-timeline language, cinematic camera grammar) and its **multi-shot mode is the cheapest continuity buy available** — up to 5 shots (V3) or 6 shots (O3) in one visual context, 15s total.

**When writing a Kling prompt, or planning multi-shot coverage for a scene, Read `reference/kling-prompting.md`** (sibling file in this skill directory). It covers:

- `@Image1` / `@Element1..N` reference token contract (and why `@Image2` fails)
- Start Image vs End Image behavior (End Image is implicit, never tokenized)
- Element bundle construction (frontal + angles) and the `element_ids[]` persistence flow
- Prompt structure formula (Scene + Subject + Action + Camera + Atmosphere + Technical)
- Action timeline, camera language, character consistency rules
- **Multi-shot mode** — full API shape, per-shot prompting rules, shot-limit math, cinematic three-shot dialogue example
- Kling V3 legacy multi-prompt form
- Negative prompts, "resolve into" logo-reveal workflow, key tips

**Do not write a Kling multi-shot payload without reading this file first** — the shot-labeling and Element-token-per-shot rules are what separate a clean multi-shot take from a drifty one.


## Model Capabilities Quick Reference

| Model | Duration | Aspect Ratios | Multi-Prompt | Sound | Notes |
|-------|----------|---------------|-------------|-------|-------|
| **Kling O3 Pro** | 3–15s | `16:9`, `9:16`, `1:1` (o3 ref-to-video) | **Yes — up to 6 cuts** | Yes | **Co-equal default.** Best for VFX, precise camera, element refs, multi-shot continuity |
| **Kling V3 Pro** | 3–15s | `16:9`, `9:16`, `1:1` | **Yes — up to 5 shots** | Yes | **Co-equal default.** Camera controls, multi-shot, Motion Brush |
| **Seedance 2.0 Omni** | Integer; provider-defined | `21:9`, `16:9`, `4:3`, `1:1`, `3:4`, `9:16` | Yes | Yes | **Co-equal default.** Character ID locking, quad-modal input |
| Seedance 2.0 T2V / I2V | `5`, `10`, `15` | `16:9`, `9:16`, `4:3`, `3:4` | No | Yes | Text/image-to-video |

**Source:** PR0TA API team confirmation (April 2026) from bundled provider specs. The unified `/generate` route does not currently enforce per-model duration or aspect enums itself — values are passed through to the provider. Use the model-specific values above rather than a defensive global floor.

## Per-Model Duration Constraints

Duration is **not** a single global range. Each provider family publishes its own accepted values. Use this table when assembling payloads:

| Model | Accepted `duration` | Source |
|---|---|---|
| `muapi/seedance-v2.0-t2v` | `5`, `10`, `15` | Bundled provider spec (API team, Apr 2026) |
| `muapi/seedance-v2.0-i2v` | `5`, `10`, `15` | Bundled provider spec (API team, Apr 2026) |
| `muapi/seedance-2.0-omni-reference` | Integer; no strict enum published in local schema | Bundled provider spec (API team, Apr 2026) |
| `muapi/seedance-2-character` | n/a | Character builder, not a duration-bearing flow |
| `fal-ai/kling-video/v3/pro/image-to-video` | `3`..`15` | Bundled provider spec (API team, Apr 2026) |
| `fal-ai/kling-video/o3/pro/image-to-video` | `3`..`15` | Bundled provider spec (API team, Apr 2026) |
| `fal-ai/kling-video/o3/pro/reference-to-video` | `3`..`15` | Bundled provider spec (API team, Apr 2026) |
| Nano Banana 2 / GPT Image 1.5 | n/a | Image models — no duration field |

**Historical field note:** A prior field test on `seedance-v2.0-t2v` saw `duration=12` rejected. That is consistent with the discrete `{5, 10, 15}` Seedance t2v enum — `12` is simply not on the list. Treat Seedance as **discrete**, Kling Fal video endpoints as **integer range 3–15**, and Omni as **provider-defined integer** until a stricter validator lands.

**Rule of thumb:**
- Need a precise clip length that does not match the enum? Generate at the nearest supported value **above** your target and trim on the post-production timeline (`PATCH /timeline/clips/{id}` with `in_point`/`out_point`). Never send unsupported durations to the generator.
- For Kling Fal endpoints, `3..15` gives real editorial flexibility — use it instead of forcing Seedance beats.
- For animated-card or diagram-driven I2V, write a custom prompt per card. Preserve exact typography and composition, animate only the depicted scene/diagram elements, keep the requested aspect ratio (for example 9:16), and fall back per failed card rather than changing the whole batch strategy.
- Before placing I2V into a longer beat, compare source duration to the beat duration. If source is shorter, use `/timeline/edits` with `fitToFill: true` when the retime is intentional, generate/extend a longer animation, or add a deliberate still/companion visual as an actual timeline clip. Do not leave an empty tail, and do not rely on raw `/timeline/clips` to hide the mismatch.

## Prefer Longer Generations for Consistency

**Always prefer generating fewer, longer clips over many short ones.** A single 15-second generation (or multi-prompt generation) maintains far better visual and style consistency than three 5-second clips stitched together. Short clips tend to drift in lighting, color grade, and character appearance between generations.

Guidelines:
- Use the maximum duration the model supports (up to 15s) whenever your shot allows it
- Use multi-prompt mode for complex sequences within a single generation — this keeps all shots in one visual context
- Only split into separate generations when shots are in different locations, feature different characters, or require fundamentally different styles
- For productions requiring many clips, use stored Element bundles and Character profiles to mitigate inter-generation drift. Read the character's consistency bundle (`GET /characters/{id}/consistency`) before generation for provider-ready payloads. See `pr0ta-consistency`.

## Seedance 2.0 Omni (ByteDance Lynx) — Reference

Seedance 2.0 Omni (`muapi/seedance-2.0-omni-reference`) is one of the co-equal default models for reference-heavy video work. It supports text + up to 9 images + 3 videos + 3 audio references in a single generation, persistent character identities via `character_id`, native multi-shot continuity, and motion/rhythm matching via video and audio references.

**For the full deep-dive** — reference token system (`@image1`..`@image9`, `@video1`..`@video3`, `@audio1`..`@audio3`, `@character:<id>`), character identity workflow, multi-prompt structure, camera/motion control grammar, worked payloads, and field-tested prompting patterns — **Read `reference/seedance-omni.md`** (sibling file in this skill directory).

**Don't have a `character_id` yet?** There are two training paths — single clean portrait → `muapi/seedance-2-omni-reference-train`; character sheet or 1-3 approved stills → `muapi/seedance-2-character`. Both return an Omni token in `result_refs.character_id`. See `pr0ta-consistency` → "Creating a Seedance Character Token — Two Paths" for the full decision framework, payloads, and persistence flow.

Essential facts for any call (copy-paste-safe):

- **Duration:** integer; no strict enum is published in PR0TA's local schema for Omni. Treat as provider-defined and verify per shot. See the "Per-Model Duration Constraints" table above and `reference/seedance-omni.md`.
- **Aspect ratios:** `21:9`, `16:9`, `4:3`, `1:1`, `3:4`, `9:16` (per bundled provider spec). Note: this **Omni** list differs from the stricter Seedance T2V/I2V list (`16:9`, `9:16`, `4:3`, `3:4`).
- **Reference surface:** broadest of any video model — image + video + audio + character refs all valid on this model. See `reference/video-reference-field-matrix.md` for the validator-derived field contract.
- **Mode:** `ref_to_vid` for reference-based work; `txt_to_vid` for pure text-to-video (do not include any reference fields on pure t2v — the resolver will re-route).

**Minimal reference-to-video payload:**

```json
{
  "generator": "video",
  "mode": "ref_to_vid",
  "model": "muapi/seedance-2.0-omni-reference",
  "prompt": "...self-contained scene description...",
  "reference_image_asset_ids": ["a73b9aad-..."],
  "duration": 5,
  "aspect_ratio": "9:16"
}
```

For anything beyond this minimal payload — character IDs, multi-prompt choreography, video/audio references, camera control, voice control — Read the full Seedance Omni reference file before writing the payload.

## Video Reference Field Matrix — Reference

The unified video request validator (`POST /api/v2/projects/{project_id}/generate`) enforces a specific reference-field contract per model. There are two layers: the validator-derived matrix (what the unified API accepts at submission) and the provider-certified matrix (what the downstream provider endpoint actually wants). Both matter.

**For the full matrix** — per-model field whitelists, Seedance/Kling family differences, the provider-certified field names for Fal Kling V3 Pro / O3 Pro / Reference-to-Video and MuAPI Seedance T2V/I2V/Omni, the skills-facing compatibility quick reference, and copy-paste-safe payloads for every common path — **Read `reference/video-reference-field-matrix.md`** (sibling file in this skill directory).

**Essential facts for any reference-based payload:**

- **`character_id` / `character_ids[]` are restricted to `muapi/seedance-2.0-omni-reference`.** The validator rejects them on every other video model.
- **`camera_control` and `voice_ids[]` are Kling-only.** The validator rejects them on any non-Kling model.
- **Generic `ref_to_vid` requires at least one image-bearing reference.** Accepted fields: `start_image_asset_id`, `start_image_url`, `image_asset_id`, `image_url`, `reference_image_asset_ids[]`, `reference_image_urls[]`, `element_ids[]`, `elements[]`.
- **`txt_to_vid` with refs is not equivalent to pure text-to-video.** Reference fields on a t2v request route to a different model. If you want pure t2v, send only `prompt`.
- **Kling V3 Pro `start_image_asset_id` translation is fixed (April 2026)** — agents may use `start_image_asset_id` directly on V3 Pro. See the "Kling V3 Pro Caveat — RESOLVED" note in `reference/video-reference-field-matrix.md` for the full translation path.

For any reference-heavy payload where you are not certain which field maps to which provider shape, Read the full matrix file before submitting.

## Output Dimensions — Orientation May Not Match Input

**⚠️ Video output orientation may not match your input image.** This is a common surprise: submitting a portrait source image (e.g., 768x1376) for image-to-video may produce a landscape video (e.g., 1280x720). The model ignores the input image's orientation.

- Kling O3 Pro I2V often outputs 1440x1440 (square) regardless of input image dimensions
- Seedance respects the `aspect_ratio` parameter more closely, but still may not match the source image orientation
- Some models (e.g., m21k_v2) always produce landscape regardless of input

### Expected Output Dimensions by Aspect Ratio

Output dimensions are provider-dependent and do **not** match common delivery specs. **The post-production timeline normalizes clips to the sequence resolution automatically** when you add them via `POST /timeline/clips` — set the sequence to 1920×1080, 1080×1920, or 3840×2160 and the platform handles scale/pad/format. You do not need to pre-normalize.

| Aspect Ratio | Typical Output (Seedance) | Typical Output (Kling) | Notes |
|---|---|---|---|
| `21:9` | 1024×448 | 1024×448 | Ultra-wide — may vary |
| `16:9` | 1024×576 | 1280×720 or 1024×576 | Kling output varies by mode |
| `4:3` | 1024×768 | 1024×768 | |
| `1:1` | 1024×1024 | 1024×1024 or 1440×1440 | Kling O3 I2V often returns 1440×1440 |
| `3:4` | 768×1024 | 768×1024 | |
| `9:16` | 576×1024 | 576×1024 or 720×1280 | **Not** 1080×1920 — timeline normalizes on add |

**How to control output orientation:**
1. **Always set `aspect_ratio` explicitly** in the generation request — don't rely on the model inferring it from the input image.
2. For Seedance, pick a supported ratio for the specific variant: Omni accepts `{21:9, 16:9, 4:3, 1:1, 3:4, 9:16}`; T2V/I2V is narrower at `{16:9, 9:16, 4:3, 3:4}`. See the "Per-Model Duration Constraints" table earlier in this skill for the full matrix.
3. Compose input images with important content centered — the model may crop differently.
4. Set the sequence resolution on the post-production timeline (`POST /timeline`) to your delivery spec before adding clips.
5. Add clips with `POST /timeline/clips` — the platform normalizes scale, pad, format, and FPS to match the sequence.

When available, check `result_refs.output_diagnostics` in the task result for requested vs actual dimensions and any mismatch flags.

## Camera Control (Kling V3)

Kling V3 supports structured camera control as an API parameter, separate from prompt text:

```json
{
  "camera_control": {
    "type": "simple",
    "config": { "horizontal": 5 }
  }
}
```

This provides programmatic camera movement. Combine with multi-prompt for precise shot choreography.

## Native Audio & Sound Control

All video generation requests should explicitly set `sound: "on"` or `sound: "off"`. Omitting it may produce unexpected results.

**When to use which:**

| Clip type | `sound` | Why |
|---|---|---|
| Dialogue (speaker visible) | `"on"` | Native lip sync + matching ambient |
| Narration over footage | `"off"` | Layer ElevenLabs TTS in post |
| B-roll / montage | `"off"` | Layer music and SFX in post |
| Ambient / atmosphere | `"on"` | Native ambient adds realism |

**Hard rule for `sound: "on"` video:** every video generated with native audio must be transcribed with Scribe V2 before entering the post-production timeline. This is the same two-path time-indexing gate as pure audio — see `pr0ta-audio` → "Mandatory Time-Indexing Rule" for the full policy.

**For the deep dive** — prompting for sync dialogue in Seedance and Kling, the transcription enforcement flow, audio extraction endpoint (`POST /assets/{id}/extract-audio`), direct-video-transcription vs extract-first decision, native audio language limitations, and the `sound` vs provider-level `with_audio`/`generate_audio` parameter mapping — **Read `reference/native-audio.md`** (sibling file in this skill directory).

## Voice Control (Kling O3)

Kling O3 supports per-character voice control via the `voice_ids` parameter:

```json
{
  "voice_ids": ["voice-id-for-character"]
}
```

## Known Limitations and Workarounds

All video generation should use the **reliability contract** from the `pr0ta-api` skill, which handles these issues automatically via the state machine and fallback chain.

- **`start_image_asset_id` HTTP/HTTPS issue — FIXED (April 2026).** Both `start_image_asset_id` and `start_image_url` now work reliably on Kling O3 Pro. Use whichever is more convenient.
- **`kling_v3_pro` `start_image_asset_id` translation — FIXED (April 2026).** The unified layer now translates `start_image_asset_id` → provider-native `start_image_url` end-to-end for `fal-ai/kling-video/v3/pro/image-to-video` with regression test coverage. Agents may use `start_image_asset_id` directly on V3 Pro. The earlier `"Invalid reference index 1 for image. Only 0 images provided."` failure is no longer expected from this translation path.
- **Video public download 0 bytes — FIXED (April 2026).** The `/download` endpoint no longer returns empty responses. The `storage_uri` auth fallback in the reliability contract remains as defense-in-depth but should no longer be needed.
- **Video `task_id` asset filter — FIXED (April 2026).** Asset listing by `task_id` now falls back to `task.result_refs.asset_id`/`asset_ids`. The prompt/time correlation fallback in the reliability contract remains as defense-in-depth.
- **MuAPI/Seedance provider errors (e.g. "Insufficient credits").** If Seedance Omni (`muapi/seedance-2.0-omni-reference`) jobs fail silently or with `error: "Insufficient credits"` / `error_detail.code: 402`, the issue is on the MuAPI provider account side — not a PR0TA dispatch bug. PR0TA accepts the request, dispatches to MuAPI, and the failure surfaces asynchronously on the task. **Always poll tasks to terminal state** to catch these. Fix: check your MuAPI plan/tier/concurrency entitlement. After fixing, retest with a single request before scaling concurrency. See `pr0ta-api` → "Async Provider Errors" for the retry guidance by `error_reason`.
- **`credits_cost: null` on video submissions.** Video costing may be deferred (returned as `null` on the initial 200 response while image/audio/music return real costs immediately). Do not treat `null` as confirmation that dispatch failed — always poll the task for the authoritative outcome.
- **Output dimensions don't match requested aspect ratio.** See the "Output Dimensions" section above. The post-production timeline normalizes clips to the sequence resolution on add — set sequence resolution first, then add clips.
- **Always set `sound` explicitly** -- `"on"` for dialogue clips where the speaker is visible (native lip sync), `"off"` for B-roll and narration-over-footage. See the "Native Audio & Sound Control" section above.

## On-Screen Text — Do NOT Animate Text Through a Video Model

**⚠️ Video models will rewrite on-screen text during animation. This is the single most common way a polished title card gets destroyed between image generation and final render.**

Field-tested failure: a Nano Banana 2 still with perfect text reading `"THE GOVERNMENT CAN'T RUN OUT OF MONEY"` was passed to Seedance `ref_to_vid` for a subtle push-in and came back reading `"ECONOMIC PERSPECTIVE ON PUBLIC FINANCE"`. The video model didn't just blur the text — it semantically rewrote it. This happens even on models listed as "text-reliable" for stills (Nano Banana 2, GPT Image 1.5, Kling V3/O3). Text reliability at the image layer does **not** transfer to the video layer.

### The Only Reliable Pattern For Animated Title Cards

1. **Generate the still** with a text-reliable image model (Nano Banana 2 / GPT Image 1.5) using the "Line-locked poster" prompt pattern from `pr0ta-prompting`.
2. **Verify the text is pixel-perfect** on the still before doing anything else. If any character is wrong, regenerate — do not paint over it or try to fix it in video.
3. **Animate the still on the post-production timeline** by adding it as a clip with a Ken Burns preset (`push_in`, `push_in_fast`, `hold`, etc.). Never feed the still back into a video model for animation if preserving the exact text matters. See `pr0ta-timeline` → "Ken Burns as a Clip Property".

**Rule of thumb:** If the shot contains legible on-screen words the viewer will read, animate it on the timeline as a still with a Ken Burns preset. Reserve video models for shots where the text is decorative, off-screen, or absent.

This is the documented recipe — not a workaround. Trying to feed a title card through `ref_to_vid` is an anti-pattern regardless of model choice.
