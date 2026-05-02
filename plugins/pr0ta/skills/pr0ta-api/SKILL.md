---
name: pr0ta-api
description: "PR0TA REST API reference for auth, raw endpoint schemas, task polling, assets, model discovery, timeline/debug APIs, review-room APIs, and MCP setup. Read when a domain skill does not include the exact route contract or when debugging API failures."
---

# PR0TA API Reference

This reference covers the PR0TA REST API endpoints available for programmatic access.

## Authentication

PR0TA supports two authentication methods:

### Personal Access Tokens (Required)

**A PAT is required for reliable API workflows.** PATs are long-lived tokens that don't require email/password. Always ensure you have a PAT before starting any API work.

**If the user doesn't have a PAT, help them create one:**

1. **Ask the user** for their PR0TA PAT (starts with `pat_`).
2. **If they don't have one**, guide them to create it:
   - Navigate to `app.pr0ta.com/settings` in the browser
   - Go to the **General** tab → **API Keys** section
   - Click **"Generate New Key"**
   - Name it (e.g., "Codex plugin") and copy the token immediately
   - **The token is only shown once** — if they miss it, they need to generate a new one

**Using a PAT:**
```bash
curl -H "Authorization: Bearer pat_xxxxxxxxxxxxx" https://app.pr0ta.com/api/v2/projects
```

**Store the PAT for the session:**
```bash
export PR0TA_PAT="pat_xxxxxxxxxxxxx"
# Then use in all requests:
curl -H "Authorization: Bearer $PR0TA_PAT" https://app.pr0ta.com/api/v2/projects
```

**Managing PATs (requires JWT session -- PATs cannot manage PATs):**

Create:
```
POST /api/auth/personal-access-tokens
```
```json
{
  "name": "Skill Runner",
  "expires_in_days": 180
}
```
Response includes the full `token` (only shown once) and a `token_record` with `id`, `name`, `token_prefix`, `created_at`, `expires_at`.

List:
```
GET /api/auth/personal-access-tokens
```

Revoke:
```
DELETE /api/auth/personal-access-tokens/{token_id}
```

### JWT (Fragile Fallback — Avoid)

JWT extraction from the browser is a fragile fallback. **Always prefer a PAT.** Only use JWT if the user explicitly cannot create a PAT.

```bash
# Get bearer token (fragile — expires, requires email/password)
TOKEN=$(curl -s -X POST https://app.pr0ta.com/api/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"user@example.com","password":"password"}' | jq -r '.access_token')

# Use token in subsequent requests
curl -H "Authorization: Bearer $TOKEN" https://app.pr0ta.com/api/v2/projects/PROJECT_ID/assets
```

**Important:** The `/download` and `/thumbnail` endpoints are public and do NOT require auth. All other endpoints require either a PAT (`pat_xxx`) or JWT bearer token.

### Rate Limits (Per-Minute, Per-Authenticated-User)

PR0TA applies a global per-minute request limit at the subscription-tier level. There is no dedicated generate-only concurrency limit published on the unified route itself; this same budget covers generation, polling, asset reads, etc.

| Tier | Requests / minute |
|---|---|
| `FREE` | 50 |
| `CREATOR` | 100 |
| `PRO` | 200 |
| `ENTERPRISE` | 500 |

**Operational rule:** 3–5 parallel generations with 2s polling is comfortably inside any tier's budget. Keep per-request polling intervals at ≥2s and avoid tight event-listener loops that hammer `/events`. If you hit a 429, back off — the platform does not certify a specific concurrency guarantee beyond the tier budget above.

---

## API Base URL

Both `app.pr0ta.com` and `api.pr0ta.com` accept API requests (the app domain proxies to the API domain). **Use `app.pr0ta.com` as the canonical base URL** — it's what the platform documentation uses and it works for both browser and API access. All examples in this skill use `app.pr0ta.com`.

```bash
# Canonical (use this)
BASE_URL="https://app.pr0ta.com"

# Also works (proxied), but not canonical
# https://api.pr0ta.com
```

---

## Minimal Python Client (Copy-Paste Ready)

The complete Python client with all 5 core functions (`upload_images`, `submit_generation`, `poll_task`, `download_asset`, `list_assets`) plus a fan-out example is at **`reference/python-client.py`**. Copy it into your project as `pr0ta_client.py` and run it.

It bakes in the Cloudflare-safe download path (`curl` via subprocess — `urllib` is 403'd by Cloudflare), the PAT bearer pattern, the structured validation-error contract for unified v2, async provider error surfacing (`error_detail`), and paginated asset listing. Every gotcha in the skill pack that costs debug time is handled on the first copy-paste.

```bash
pip install requests
export PR0TA_PAT="pat_xxxxxxxxxxxxx"
export PR0TA_PROJECT_ID="your-project-uuid"
python pr0ta_client.py
```

Rate limits by tier: FREE 50/min, CREATOR 100/min, PRO 200/min, ENTERPRISE 500/min.

---

## Project, Model, and Resource Management — Reference

For the full endpoint catalogue covering **project CRUD** (list, create, rename, set active, delete), **model discovery** (`GET /api/v2/models` with `generator`/`image_kind` filters, `GET /api/crew/model_defaults`, `GET /api/crew/model_pricing`, capability flags, pricing), and **reusable consistency resources** (Elements, Characters, element bundles, character profiles, create/list/update/delete), **Read `reference/projects-models-resources.md`** (sibling file in this skill directory).

Essential facts for any call:

- **All endpoints require auth** (PAT bearer or JWT). The only public endpoints are `/download` and `/thumbnail`. Model discovery (`GET /api/v2/models`) is also public.
- **Project ID is required in the path** for every project-scoped endpoint. Use `GET /api/v2/projects` to list, then pick the one you need.
- **Default image model: Nano Banana 2** (`nano_banana_2`) — fast and cost-effective. Escalate to **GPT Image 2** (`openai/gpt-image-2` / `openai/gpt-image-2/edit`) for challenging prompt adherence or character consistency edits. Use `GET /api/crew/model_defaults?model_id={model_id}` for authoritative parameter schemas.
- **Elements** are reusable image bundles for Kling. **Characters** are reusable MuAPI identities for Seedance. Do not mix.
- **Character consistency bundles** — before multi-shot character generation, read `GET /characters/{id}/consistency` or `GET /characters/consistency?name=...` to get all approved references, Kling Elements, Seedance tokens, and provider-ready payloads in one call. Tag approved portraits/sheets with `reference_type: "character_reference"` via `PATCH /annotations`. See `reference/projects-models-resources.md` → "Character Consistency Bundles" and `pr0ta-consistency` → "Character Consistency Bundles".
- **Set-active-project** is a separate endpoint (`POST /api/v2/projects/{id}/select`) and must be called before generations that rely on the active-project context.

For actual request/response shapes and worked examples, Read the reference file.

## Unified Generation API — Reference

The primary way to trigger all generation programmatically: a single `POST /api/v2/projects/{project_id}/generate` endpoint that dispatches to the image, video, audio, or music stack and returns a task ID.

**Essential facts:**
- **`generator` is required on every request.** Sending only `model` and `mode` fails validation. Valid generators: `image`, `video`, `audio`, `music`.
- **Supported generator/mode pairs:** `image` (`txt_to_img`, `img_to_img`, `ref_to_img`, `edit_img`), `video` (`ref_to_vid`, `txt_to_vid`, `extend_video`/`video_extend`), `audio` (`txt_to_speech`), `music` (`txt_to_music`). Unsupported combinations return `400`.
- **Mode/model compatibility is validated.** Kling models are reference-only (`ref_to_vid`). Seedance and LTX support `txt_to_vid`. Crossing these returns `400`.
- **Asset IDs resolve server-side** to internal URLs. All referenced assets must belong to the same project. You can also pass URLs directly (`start_image_url`, `reference_image_urls[]`, etc.).
- **Stored consistency resources** resolve server-side too: `element_ids[]` → Kling element references, `character_ids[]` → Seedance/MuAPI character references. Do not mix — Elements are Kling, Characters are Seedance.
- **Prompt token rules:** use `@Image1` for Start Image, `@Element1`/`@Element2` for elements, `@Video1`/`@Audio1` for Seedance Omni refs. **Never use `@Image2`** — the End Image is structural, not promptable.
- **`sound` must be explicit on every video request** (`"on"` or `"off"`). Omitting it produces unpredictable audio.
- **Video extension is first-class:** use `generator=video`, `mode=extend_video`, a source `video_url` or `video_asset_id`, a prompt, and an extension-capable model such as `fal-ai/pixverse/v6/extend`, `fal-ai/veo3.1/extend-video`, `fal-ai/vidu/q2/video-extension/pro`, `fal-ai/magi/extend-video`, or `kling/v3/video-extend`.
- **Submission returns a task**, never a finished asset. Extract `task_id` and poll — do not assume 200 on submit means the job succeeds. Async provider errors surface only at terminal polling. The initial task may have `provider: null` / `model_id: null`; this is normal, not a failure.

**Full contract — request/response shapes for every generator, model-capability matrix, image resolution constraints, multi-prompt and camera-control fields, asset-ID resolution rules, submission response fields:** Read `reference/unified-generation.md`.

## Batch Generation and Event Queue — Reference

For the full endpoint specs covering **batch generation** (`POST /api/v2/projects/{id}/generate/batch`, n-way fan-out, batch status) and the **generation event queue** (`GET /events?generator=<type>`, server-sent-event semantics, completion signaling, known gaps), **Read `reference/batch-and-events.md`** (sibling file in this skill directory).

Essential facts:

- **Events are an acceleration path, not the primary completion signal.** Image events in particular are best-effort and sometimes empty even after completion. Always use task polling (below) as the authoritative completion signal.
- **`POST /api/v2/projects/{id}/generate/batch` is the first-class fan-out mechanism.** One request can carry multiple generation payloads (up to **10** items per batch). Validation happens up front; submissions are processed item-by-item; partial-success reporting can occur if an early item is accepted and a later one fails. Oversized batches return `413`.
- **Batch vs. loop:** Use the batch route when you have N distinct payloads you want to queue in a single round-trip. Use independent `/generate` calls in a loop when you want finer-grained retry/cancel logic or when submissions are driven by incremental decisions.
- **Rate limits apply at the global per-minute tier level** (see "Authentication" section). There is no dedicated generate-only concurrency limit; 3–5 parallel generations is well within normal limits for any authenticated tier, but "well within limits" is not a certified concurrency guarantee.
- **Cost is model-dependent.** Image fan-out across Nano Banana 2 / GPT Image 2 / Ideogram is cheap enough to treat as a first-class editorial tool. Video fan-out across Kling or Seedance can add up quickly — use it deliberately, not reflexively.

For the full request/response shapes, Read the reference file.

## Task Polling — Reference

**Task polling is the primary completion signal.** Always poll a submitted task to terminal state — a 200 from `POST /generate` only means queued, not succeeded. Async provider errors (insufficient credits, model unavailable, provider timeout) surface only at terminal status.

**Endpoints** (project-scoped preferred):
```
GET  /api/v2/projects/{project_id}/tasks/{task_id}         ← preferred
POST /api/v2/projects/{project_id}/tasks/{task_id}/cancel  ← preferred
```

**Terminal states:** `succeeded`, `failed`, `canceled`/`cancelled` (both spellings normalized server-side).

**`result` is the canonical completion contract — read from `result`, not `result_refs`.** The canonical shape is `{ type, asset_id, asset_ids, download_url, urls, variant_count }`. `result_refs` is legacy compatibility only.

**Stall detection and cross-provider pivot** (reliability contract step, covered fully in `pr0ta-video`):
1. Same `progress` for >3 minutes → cancel via `POST /tasks/{task_id}/cancel`.
2. Resubmit identical payload (queue-reset often fixes it).
3. If the retry also stalls, pivot to the other video provider — Seedance → Kling V3 I2V, or Kling → Seedance Omni. Do not burn a third attempt on the same backend.
4. If both providers stall, surface status before degrading to a Ken Burns push on the still.

**Error-reason taxonomy** — use `error_reason` to decide retry vs fail-fast:
- `provider_timeout` → retry (transient).
- `provider_error` + `error_detail.code: 402` → do **not** retry; fix provider account credits first.
- `invalid_parameters` → do not retry; fix the payload.

**Full contract — route table, in-progress/succeeded/failed response shapes with full field lists, cancellation semantics, `created_at`/`submitted_at`/`error`/`error_reason`/`error_detail` field definitions, and the canonical `result` envelope spec:** Read `reference/task-polling.md`.

## Asset Management and Batch Workflow — Reference

For the full endpoint specs covering **asset management** (listing with `offset`/`limit` pagination, filtering by kind/task_id/tag, asset metadata including `storage_uri`, deletion, tagging) and the **canonical batch workflow pattern** (submit → poll → collect → download → ledger), **Read `reference/asset-management.md`** (sibling file in this skill directory).

**Asset listing pagination:** `GET /api/v2/projects/{id}/assets` supports `offset`/`limit` pagination. Response includes `total` (total matching assets) and `next_offset` (for the next page, or `null` if no more). Default limit applies server-side; always check `next_offset` to paginate through large asset sets.

Essential facts:

- **Canonical pagination is `offset`/`next_offset`** — iterate until `next_offset` is `null`. The minimal Python client's `list_assets()` does this correctly. Do not hand-roll with `cursor`/`nextCursor` (that's the legacy shape for a non-project-scoped route).
- **Asset downloads must go through `curl` via subprocess** — see `pr0ta-downloading` for the Cloudflare bypass rationale. `urllib` will 403.
- **Assets now expose `generation_context`.** `GET /api/v2/projects/{project_id}/assets/{asset_id}` surfaces a `generation_context` block with `prompt`, `model`, `negative_prompt`, `seed`, `task_id`, `submitted_at`, `completed_at`, `status` when recoverable. This means assets are no longer opaque — you can walk backwards from an asset to the job that produced it via the API.
- **Provenance is a single local ledger (`assets.json`) plus the API-side `generation_context` fallback.** `assets.json` is the production-scoped ledger defined in the `pr0ta` hub. `generation_context` is the retrospective API lookup for any asset. There is no separate `results.json` file — it was dropped to avoid duplication.

For the full request/response shapes and the end-to-end batch workflow walk-through, Read the reference file.

## Asset Tagging, Readability Filters, and Timeline Analysis — Reference

Assets are not just media files — they carry editorial intent. Tagging, annotating, and curating assets is how agents and users communicate which assets are hero takes, which are references (and for what), which are approved, and which should never be used. Without active curation, a project with dozens of assets becomes opaque to the next agent or collaborator who picks it up.

**For the full endpoint contracts** covering asset readability filters (`?favorite=true`, `?tag=`, `?reference_type=`), annotation mutation (`PATCH /annotations`), timeline mark labels/descriptions, timeline analysis (gaps, overlaps, reused media, track coverage), and per-clip reuse flags, **Read `reference/asset-tags-and-analysis.md`**.

Essential facts:

- **Filter by favorites, tags, or reference type** — `GET /api/assets/{project_name}?favorite=true`, `?tag=hero&tag=approved` (AND-joined), `?reference_type=character_reference`. Use these instead of fetching the full library and filtering client-side.
- **Annotate assets with `PATCH /api/assets/{project_name}/annotations`** — write `tags`, `notes`, `reference_type`, `character_name`/`set_name`/`prop_name`/`look_name`, `scene_number`/`shot_number`/`take_number`. Use `tags` for general readability (`approved`, `hero`, `do_not_use`), `reference_type` for durable semantic classification.
- **Timeline marks now support `label` and `description`** — use these fields (not the legacy `name`/`note` aliases) for editorial annotations on the timeline.
- **Timeline diagnostics (`GET /timeline/debug-report`)** — preferred agent preflight before render/export. It bundles track coverage, primary visual gaps, source shortfalls, retime state, audio asset presence, keyframe counts, and render-risk warnings. Use `GET /timeline/analysis` when you only need the raw gaps/overlaps/reuse/shortfall analysis.
- **Per-clip `isReusedMedia` and `sourceShortfall` flags** — available on the standard clip listing for lightweight reuse and shortfall checks without full timeline analysis.
- **Source shortfalls** — when a source clip is shorter than the requested program range, PR0TA inserts only the available source and leaves a real gap (no freeze-padding). For I2V card edits, compare source duration vs beat duration before placement; use `/timeline/edits` with `fitToFill: true`, generate/extend a longer clip, or warn about transparent/checkerboard tails. Analysis and debug reports include frame-safe timing (`renderedProgramFrames`, `renderedProgramDuration`) and render-risk warnings. See `reference/source-shortfalls-and-fit-to-fill.md` for the full contract.

## Project Image Upload — Reference

Direct-multipart upload of local still images into a project, without the prepare/proxy/finalize workflow. Preferred path for ingesting existing photos, screenshots, key frames, or real-world references before generation.

```
POST /api/v2/projects/{project_id}/assets/upload
Content-Type: multipart/form-data
```

**Critical field-name gotcha:** the multipart field is `files` (plural), not `file`. Sending `file` returns `422`. Accepts one or more image files per request; non-image files are rejected with `400`.

**Response:** `assets[]` array using the standard `AssetRead` shape. The `id` on each asset is what you pass as `start_image_asset_id` / `reference_image_asset_ids[]` / etc. in follow-up `/generate` calls.

**Scope:** images only. For audio/video/document direct upload, use the legacy prepare/proxy/finalize flow (`/assets/uploads/prepare` → `/proxy` → `/finalize`).

**Full contract — request fields table, copy-paste curl examples (single and multi-file), response shape, usage patterns (reference images, Element/Character source material, image-editing input, batch upload), error cases:** Read `reference/image-upload.md`.

## Post-Production Timeline API — Reference

The **post-production timeline** is the primary editing surface for both AI agents and human collaborators — it stores clip state, Ken Burns presets, audio mix, and supports incremental edits. Base prefix: `/api/post-production/{project_id}`.

**For workflow guidance** (when to add clips, Ken Burns presets, preview/render loop, snapshot handoff), see `pr0ta-timeline`. **For the full API shapes** (timeline state, track creation, clip CRUD, audio mix, audio preview/analysis, snapshots, data model, and the `POST /timeline/clips` never-upserts gotcha), **Read `reference/timeline-api.md`**. **For the canonical backend-facing endpoint reference** (all post-production routes, contracts, and limits), **Read `reference/post-production-api.md`**. **For source shortfalls and fit-to-fill** (default gap behavior, `fitToFill`, four-point edits, speed semantics), **Read `reference/source-shortfalls-and-fit-to-fill.md`**.

Essential facts:
- **Concurrent audio on separate tracks.** Overlapping audio clips on the same track are invalid — the renderer rejects them. Create separate tracks (`dialogue`, `music`, `sfx`) via `POST /timeline/tracks` before adding clips.
- **Track creation** — `POST /timeline/tracks` creates individual tracks without rewriting the full `tracks[]` array. Preferred over `PATCH /timeline` for adding tracks.
- **Track targeting** — tracks support three selector forms: raw ID (`dialogue`), NLE alias (`A1`), or unique label (`Dialogue`). `PATCH /timeline/tracks/{id_or_alias}` renames, locks, or repositions tracks. Read `GET /timeline/tracks` first and use raw IDs in persisted scripts.
- **`duckedGain` is the canonical ducking field** (fraction of nominal volume: `1.0` = no duck, `0.0` = mute). `threshold` is a deprecated alias.
- **Audio level keyframes** — `volumeKeyframes` on tracks (absolute time) and clips (clip-relative time) for fine-grained mix automation. The renderer multiplies both. Supports `db`/`decibels` input, and negative gain-like values are treated as dB attenuation. `/audio/analyze` exposes the same frame/gain envelope that render uses; verify music with `/preview/audio`, `/audio/meter`, or a short render around a narration gap. See `reference/timeline-api.md` → "Audio Level Keyframes".
- **Audio analysis** — `GET /audio/analyze` returns render-envelope prediction, ducking impact, mix balance, and per-segment `render_gain_envelope` instantly (no media render).
- **Audio metering** — `GET /audio/meter` returns actual LUFS/LRA/true-peak via MLT + ffmpeg ebur128. Use for loudness spec compliance.
- **Audio-only preview** — `GET /preview/audio` renders a `.wav` without picture cost. Supports `tracks` param to solo specific tracks.
- **Preview defaults to full sequence resolution.** Send `quality=low` for lightweight previews; omit for pixel-accurate.
- **Render preview** — `POST /render` is the preview-task route (queues `timeline_render`). Loads saved timeline automatically. Control-only body (empty `{}` or `from`/`to`/`resolution`) is valid. Zero-clip timelines return `400`.
- **Final export** — `POST /export` is the final-export route for master delivery. Use `/render` for iteration, `/export` when the cut is locked.
- **Clip metadata** — timeline clips now expose `sourceMedia` (width, height, aspectRatio, duration, fitsSequence) and `generation_context` (prompt, model) for aspect-fit auditing and provenance checks.
- **Source shortfalls** — when source media is shorter than the requested edit duration, PR0TA inserts only the available source and leaves a real gap. No freeze-padding. Use `fitToFill: true` to retime explicitly, then verify the frame-safe fields and preview-render warnings. See `reference/source-shortfalls-and-fit-to-fill.md`.
- **Fresh sequence rebuilds** — use `POST /sequences` for a new explicit sequence, or `POST /timeline/fork` to preserve settings/audio/mix before clearing clips for a rebuild. Use `POST /timeline?sequence_id={id}` only when intentionally replacing a full sequence payload. Render/export/review scripts must pass and record the intended `sequence_id`. See `reference/timeline-api.md` → "Create Fresh Sequence".
- **Clip at review timestamp** — use `GET /timeline/clip-at?sequence_id={id}&time={seconds}` to map review notes to active clip/asset/track context.
- **Image fit and semantic reuse** — image clips accept `fitMode`/`background` for contain/cover/fill poster handling, and analysis reports `semanticReuse[]` for repeated `sourceGroup` / `usageFamily` families even when asset IDs differ.

## Editorial Primitives — Reference

The post-production timeline now exposes a first-class editorial primitive surface: **asset marks**, **program marks**, **3-point edits**, **trim operations**, and **clip link groups**. These are real shipped backend contracts.

**For workflow guidance** (when to use marks, editorial judgment), see `pr0ta-timeline` and `pr0ta-editorial`. **For the full endpoint contracts** (all CRUD endpoints, request/response shapes, mark anchoring, edit modes, trim modes, linked behavior, lock enforcement), **Read `reference/editorial-primitives.md`**.

Essential facts:
- **Asset marks** — source-media in/out points stored on the asset (`POST /api/v2/projects/{id}/assets/{asset_id}/marks`). Referenced in 3-point edits via `@mark:<name>` syntax.
- **Program marks** — story anchors on the timeline. Can be absolute (time-based) or transcript-word anchored. Anchored marks follow timeline changes automatically.
- **`clipId` is the preferred disambiguation field** for transcript-word anchored marks when the same dialogue asset appears multiple times.
- **3-point edits** — `POST /timeline/edits` (`insert`, `overwrite`). Specify three of four points; backend computes the fourth. Source/program points can reference marks.
- **Trim operations** — `POST /timeline/edits/{clip_id}/trim` (`ripple`, `roll`, `slip`, `slide`). All four modes support `linked: true` for linked companion clips. Only `ripple` supports `affectedTracks`.
- **Clip link groups** — persisted cross-track relationships (`POST /timeline/links`). `locked: true` is enforced — all mutating operations are rejected until unlocked.
- **Preview before committing.** `/edits/preview` and `/trim/preview` return the diff without persisting. Always preview when reasoning from marks.

## Client Review Room API — Reference

PR0TA exposes a client review workflow through three MCP/agent tools: **`enable_studio_mode`**, **`submit_assets_for_review`**, and **`get_review_annotations`**. Enable Studio mode on a project (required before first review), submit one or more project assets to a public review room, share the review URL with a client, and retrieve timestamped comments, visual annotations (pin, region, drawing), and approval/change-request decisions programmatically.

**For the full tool contracts** (arguments, response shapes, webhook payload, integration pattern, annotation types, resolution filtering), **Read `reference/review-room-api.md`**.

Essential facts:

- **`enable_studio_mode`** must be called before first review-room creation. Enables Studio mode on the project. REST equivalent: `PATCH /api/v2/projects/{project_id}/studio`.
- **`submit_assets_for_review`** creates a public review room and returns a `review_url` the reviewer opens in a browser — no PR0TA account required. Response includes `submissions[]` (per-asset status) and `review_round{}` (round metadata with share links).
- **`get_review_annotations`** retrieves all feedback: annotations with `annotation_type` (pin, region, drawing), time codes (`start_time_seconds`), normalized frame coordinates (`geometry`), and review events (`comment`, `approved`, `approved_with_notes`, `changes_requested`).
- **Fetch notes from a public review link** — parse the share token from the review URL and call `GET /api/public/workspace/review-rounds/{share_token}/annotations`. Use this read route for note ingestion; authenticated write-oriented annotation routes require body/geometry fields and are not the right first call.
- **Verify review asset identity** — after creating a review link, confirm the submitted/review asset ID is the export asset you intended to show.
- **Completion webhook** — optional `webhook_url` on submission triggers a `review_round_completed` POST after all submitted assets have decisions. Treat as a wake-up signal, then call `get_review_annotations` for the full payload.
- **Role access** — available to `editor`, `director`, `producer`, `script_supervisor` roles.
- **Integration loop:** submit → share URL → wait for webhook or poll → pull feedback → apply in timeline using editorial primitives (see `pr0ta-editorial`, `reference/editorial-primitives.md`).

## MCP Server & Agent Tools — Reference

PR0TA provides an MCP server that exposes project-scoped tools to external agents (Claude Code, Cursor, ChatGPT, Claude connectors). The same tool registry also powers internal Gemini-backed agents (Editor, Director, Storyboarder, etc.).

**For the full MCP server setup** (stdio/SSE/HTTP transports, Claude Code and Cursor configuration, remote OAuth connectors, available tools table, role-tool access matrix, internal agent integration, adding new tools, troubleshooting), **Read `reference/mcp-server.md`**.

Essential facts:

- **Local setup:** `python mcp_server.py` (stdio transport). Configure in `.claude/mcp.json` (Claude Code) or `.cursor/mcp.json` (Cursor).
- **Remote connectors:** `https://app.pr0ta.com/api/mcp/mcp` with PR0TA OAuth. Works with ChatGPT and Claude remote MCP connectors.
- **Auth:** Local clients use `PR0TA_MCP_ACCESS_TOKEN` env var or per-call `access_token`. Remote connectors use OAuth bearer.
- **All MCP tools except `list_projects` require `project_id`.** Use `list_projects` first to discover available projects.
- **Available tools:** `get_scene_breakdown`, `get_scene_shotlist`, `get_character_references`, `get_set_references`, `get_shot_assets`, `get_screenplay_text`, `enable_studio_mode`, `submit_assets_for_review`, `get_review_annotations`, plus MCP-only `list_projects` and `get_project_metadata`.

---

## Narration Timeline API — Reference

The **narration timeline** is a server-side timeline object per project that acts as the single source of truth for narration-driven productions. It ties together transcript word-level timing, visual asset registry with content affinity, a cut list with transcript anchors and editorial rationale, and alignment verification — all via API. Its output is materialized directly into the post-production timeline.

**The narration timeline feeds into the post-production timeline.** Build and verify your cut list in the narration timeline, then call `POST /narration-timeline/materialize-to-post-production` to convert it into a persistent post-production sequence with Ken Burns, transitions, and audio config already set. From that point, both agent and user collaborate on the post-production timeline.

**For the full endpoint reference, data model, request/response shapes, and worked examples, Read `reference/narration-timeline-api.md`.**

Essential facts:

- **Transcription auto-populates the transcript layer.** When `POST /api/audio/transcription/start` completes, the narration timeline's transcript is automatically built with word-level timestamps, sentence boundaries, and paragraph boundaries. Manual fallback: `POST /transcript/populate`.
- **Content tags bridge narration to visuals.** `PUT /transcript/tags` labels word ranges with content identifiers (e.g. `market_size`, `franchise_model`). Assets registered with matching `affinity_tags` become queryable: `GET /assets?affinity=market_size&status=unused`.
- **Every cut records a transcript anchor and rationale.** The cut list stores which words each visual is aligned to and why — enabling automated alignment verification (`GET /verify`) and human-readable audit trails.
- **Alignment verification is the quality gate.** `GET /verify` returns per-cut drift, gap detection, overlap detection, and misalignment flags. Call before rendering; fix flagged cuts; re-verify; then export.
- **Materialize to post-production.** `POST /narration-timeline/materialize-to-post-production` converts narration cuts into post-production timeline clips with stable IDs, Ken Burns metadata, transition metadata, narration/music audio clips, and ducking intent. Response includes `timeline`, `clip_count`, and `sequence_name`. This is the only supported output path for narration-first productions.
- **Snapshots replace the version-directory pattern** for timeline state. `POST /snapshot` saves a named snapshot; `GET /snapshot/{name}/diff` compares; `POST /snapshot/{name}/restore` rolls back.
- **All timestamps are stored in final-video time.** Query endpoints accept `?coordinate_space=narration|sequence|final` for conversion.

For the narration-first assembly workflow that consumes this API, see `pr0ta-sync`.

---

## Voice V2 API — Discovery, Clone, Design, STS — Reference

Voice discovery uses the ElevenLabs V2 API directly; clone, design, and STS are project-scoped PR0TA endpoints under `/api/v2/projects/{project_id}/voices/...`.

**For workflow guidance** (when to clone vs design vs STS, decision tree, limitations), see `pr0ta-audio` → "Voice V2 API". **For the full endpoint contracts** (request/response shapes for all routes, V3 compatibility contract, model-ID table), **Read `reference/voice-v2.md`**.

Essential facts:
- **Voice discovery** — `GET https://api.elevenlabs.io/v2/voices` (direct ElevenLabs endpoint, requires `xi-api-key` header). Supports search, pagination, category/type filters. **Do not** derive a `supports_v3` boolean — use try-and-fallback (attempt v3, fall back to v2 on failure).
- **Voice clone** (`POST /voices/clone`) is synchronous — returns `voice_id` directly, no task polling. Pass `sample_asset_ids[]` (project assets) or `sample_urls[]` (external).
- **Prompt voice design** is two-step: `POST /voices/design` returns ephemeral `previews[]`, then `POST /voices/design/commit` turns the chosen preview into a permanent `voice_id`.
- **Speech-to-speech** (`POST /voices/sts`) returns the output audio URL directly. Model: `eleven_multilingual_sts_v2`. Audio-to-audio only on the v2 surface.
- **Model discovery** (`GET /api/v2/models?generator=audio`) now includes voice-design and STS models alongside TTS. New mode hints: `voice_design`, `voice_to_voice`.

---

## Voice Listing and Transcription — Reference

For the full endpoint specs covering **voice listing** (now direct ElevenLabs V2 — see `reference/voice-v2.md`) and **transcription** (`POST /api/audio/transcription/start`, `POST /api/v2/projects/{id}/transcribe`, batch variant, asset_id/source_url/file inputs, `timestamp_granularity`, async task shape), **Read `reference/voice-and-transcription.md`** (sibling file in this skill directory).

Essential facts:

- **Scribe V2 is the default transcription provider.** Pass `model_id: "fal-ai/elevenlabs/speech-to-text/scribe-v2"` for speaker IDs, audio events, and per-word `event_type` classifications. Whisper (`fal-ai/whisper`) is still available as a fallback.
- **Transcription is the primary tool for any word-level timing, sync, subtitle, or dialogue-matching work.** See `pr0ta-audio` for the provider comparison and `pr0ta-sync` for the narration-timeline workflow that consumes the output.
- **Transcription is async.** Submit, get a task_id, poll to completion.
- **Retrieve word-level data from the dedicated transcription endpoint** (see below), not from asset metadata internals.
- **Voice listing uses the direct ElevenLabs V2 endpoint** (`GET https://api.elevenlabs.io/v2/voices`). See `pr0ta-audio` for the voice discovery workflow and `reference/voice-v2.md` for the full endpoint contract.

### Dedicated Transcription Retrieval (Preferred)

After transcription completes, retrieve word-level timing from the dedicated endpoint:

```
GET /api/v2/projects/{project_id}/assets/{asset_id}/transcription
```

Response:
```json
{
  "success": true,
  "asset_id": "asset-123",
  "project_id": "project-1",
  "text": "Full transcript text",
  "segments": [...],
  "words": [...],
  "segment_count": 12,
  "word_count": 418,
  "timestamp_granularity": "word",
  "transcription_options": {...},
  "transcription_summary": {...}
}
```

Returns stored transcription text, segment list, and a flattened word list. If stored top-level transcript text is missing, `text` is synthesized from segment text on the fallback label-based path. Falls back to older label-based transcript storage where possible. This is the correct retrieval path for word-level timing.

Status semantics: `pending` (asset exists, no transcription yet) or `ready` (word-level data persisted). Use `words[]` for flat word-level timing, or `segments[].words[]` for segment-grouped timing.

This is the **only supported retrieval path** for transcription word-level timing.

### Transcription Route — Field-Name Compatibility

`POST /api/audio/transcription/start` is the **preferred route** for kicking off transcription when you want the narration timeline's transcript layer to be auto-populated on completion. It accepts **both** camelCase and snake_case field names:

```json
{"assetId": "...", "projectId": "..."}
{"asset_id": "...", "project_id": "..."}
```

Both forms work. The batch variant (`POST /api/audio/transcription/batch`) similarly accepts both `assetIds`/`asset_ids` and `projectId`/`project_id`.

For the full request/response shapes, Read the reference file.

## Music Analysis API — Reference

The **music analysis API** is the instrumental-music analogue of transcription — Scribe V2 is speech-only and doesn't detect musical beats. Use this for any instrumental music asset (score bed, underscore, stinger) driving cut timing. It's the required time-indexing pass for Path B of the mandatory time-indexing rule in `pr0ta-audio`.

**For the full endpoint spec** (start analysis, get cached analysis, storage contract on `music_analysis` metadata, `editorial_anchors` consumer guidance), **Read `reference/music-analysis.md`** (sibling file in this skill directory).


## Audio Extraction and Video Transcription — Reference

PR0TA supports extracting a standalone audio asset from a project video (`POST /assets/{id}/extract-audio`), and `POST /transcribe` now accepts video assets, uploads, and source URLs in addition to audio assets. Video inputs are handled by extracting a derived audio asset first, then transcribing.

**For the full endpoint spec** (extract-audio request/response, provenance fields on derived assets, updated transcription behavior, when-to-use-each-path guidance, and failure modes), **Read `reference/voice-and-transcription.md`** → "Audio Extraction From Video Asset" (sibling file in this skill directory).

## Client Reliability Contract

For robust automation, route every generation call through a single wrapper that implements the full state machine, polling policy, asset correlation, download fallback, dead-task detection, and structured logging. **Read `reference/reliability-contract.md` for the complete specification, polling intervals/windows per generator, correlation scoring rules, acceptance tests, and a TypeScript reference implementation.**

Key rules to remember even before opening the reference:

- **Task polling is authoritative.** Events accelerate; assets correlate; only task status (or a validated asset+bytes) marks a job succeeded.
- **Always have a download fallback.** If `/assets/{id}/download` returns zero bytes, fall back to the authenticated `storage_uri` with redirect-following.
- **Detect stalls yourself.** Video tasks can freeze at 80-95%. If progress is unchanged for >3 minutes, cancel via `POST /api/tasks/{task_id}/cancel` and resubmit.
- **Handle both `canceled` and `cancelled` spellings** in terminal status checks.
- **Concurrency:** 5-7 parallel video tasks, 10-15 image, 3-5 audio/music.

For mixed image/video/audio/music batches, split event polling by `generator` where practical rather than scanning one mixed stream.

---

## Error Handling

Common responses:
- `400` -- unsupported generator/mode, invalid payload, invalid asset IDs, cross-project asset references
- `401` -- missing or invalid bearer token
- `402` -- insufficient credit balance
- `404` -- project or task not found
- `413` -- batch request exceeds maximum size (10 items)
- `500` -- incorrect model string (verify against `GET /api/v2/models`)
- `502` -- downstream provider returned no usable result

---

## Current Limitations

- The unified route is additive and does not replace older generation endpoints yet.
- `character_ids` currently resolves exactly one stored character per request.
- Higher-level `looks`, `cast`, `sets`, and `props` resources are not yet available via API.
- No dedicated `prompt_contains` or `name` filter on asset listing.
- Asset metadata `duration` is `number | null`. Never parse it as a string. Invalid duration values are normalized to `null` server-side.
- **Video output dimensions are provider-dependent and not guaranteed to match your requested aspect ratio in exact pixels.** Some providers output square (e.g., 1440x1440); others output close-but-not-exact dimensions. The post-production timeline normalizes all clips to the delivery resolution automatically — you don't need to rescale locally. Check `result_refs.output_diagnostics` if present for requested vs actual dimensions.
