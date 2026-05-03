---
name: pr0ta
description: "PR0TA orchestration hub for creative media production on app.pr0ta.com. Use first for multi-asset productions, AI video/image/audio/music workflows, timeline assembly, review, and final export; then load only the specific companion skill needed for the next action."
---

# PR0TA Creative Production Skill

> **CRITICAL: This is the orchestration hub. Detailed documentation lives in companion skills.**
> Use this file to choose the next production action, then load the one companion skill that owns that action. Load `pr0ta-api` only when you need endpoint/auth/schema details not already covered by the execution skill.
>
> **Preferred defaults:** Image → **Nano Banana 2** (`nano_banana_2`) — fast, cost-effective, excellent for most shots; escalate to **GPT Image 2** (`openai/gpt-image-2` / `openai/gpt-image-2/edit`) for challenging prompt adherence or character consistency edits. Video → **Seedance 2.0 Omni** and **Kling V3/O3 with multi-shot** are co-equal alternatives — pick per shot based on the shot's needs, and test pairs when continuity matters. Transcription → **ElevenLabs Scribe V2**. Assembly → **post-production timeline** (NLE-first).

## Mandatory Steps — Do Not Skip

The following steps are **non-negotiable** in any multi-asset production. Skipping them has caused production failures in field testing. If you find yourself thinking "I'll skip this to save time," stop — the time saved will be lost many times over in debugging.

1. **Use progressive disclosure.** Read this hub first, then the narrowest companion skill for the next action. Load `pr0ta-api` for auth, raw endpoint contracts, MCP setup, or route details; otherwise prefer the domain skill (`pr0ta-video`, `pr0ta-timeline`, `pr0ta-audio`, etc.) that owns the workflow.
2. **Use MCP first when available.** The Codex plugin bundles the PR0TA remote MCP connector. Prefer MCP tools (`list_projects`, `generation_submit`, `tasks_get`, `assets_list`, `post_sequence_get`, `post_sequence_save`, `post_render_start`, `narration_timeline_get`, `narration_materialize_to_post`, `review_submit_assets`, etc.) over ad hoc REST/curl calls. Use REST only for routes not exposed through MCP, high-volume scripts, or asset-download fallbacks.
3. **Assemble on the PR0TA post-production timeline.** The timeline is the supported editing surface for PR0TA productions — it handles Ken Burns rendering, audio ducking, crossfades, dimension normalization, and persistent edit state. The agent edits via MCP/API; the user collaborates via the same timeline in the browser. If the timeline has a gap that blocks a production, file a bug with PR0TA platform engineering so it gets built into the app — that's better for every future production than one-off local workarounds. See `pr0ta-timeline`.
4. **Every audio-bearing asset must be time-indexed before editing — two paths, no exceptions.** Every asset that carries sound must be passed through the correct time-indexing endpoint before it is eligible for the timeline. There are two paths:
   - **Path A — Speech (TTS narration, dialogue clips, music with vocals, video with dialogue/ambient):** transcribe with Scribe V2 via `POST /api/audio/transcription/start` (`model_id: "fal-ai/elevenlabs/speech-to-text/scribe-v2"`). Output: word-level timing, speaker IDs, speech-adjacent audio events (breath, laughter, applause, speaker_change).
   - **Path B — Instrumental music (score beds, underscore, any asset with no speech):** analyze with `POST /api/v2/projects/{project_id}/music/analyze`. Output: `music_analysis.editorial_anchors`, `downbeat_times`, `beat_times`, `transients[]`, `tempo_bpm`, `beat_confidence`. This is the `whisper_index` analogue for music — Scribe V2 does **not** produce beat or downbeat data and must not be used for this.
   - **Video inputs:** `POST /api/v2/projects/{project_id}/transcribe` now accepts video assets directly — it extracts a derived audio asset and transcribes it in one call. If you want a reusable audio asset for music analysis, downstream editing, or both, call `POST /api/v2/projects/{project_id}/assets/{asset_id}/extract-audio` first and then pass the extracted audio asset into the transcription or music-analyze endpoint.

   Assets that have not been time-indexed (transcribed or music-analyzed) are **not available to the editor** — do not add them to the post-production timeline until their indexing task has succeeded. See `pr0ta-audio` → "Mandatory Time-Indexing Rule (Two Paths)".
5. **Ken Burns is a clip property.** On the timeline, set Ken Burns via preset name (`push_in`, `pull_back`, `drift_left`, etc.) or custom params — the platform handles super-resolution, FPS consistency, and duration-aware formulas internally. You never write a zoompan expression. See `pr0ta-timeline` → "Ken Burns as a Clip Property".
6. **Verify alignment before final export.** Use `GET /preview?from=&to=&quality=low` to verify key segments — seconds, not minutes. For narration-timeline productions, also call `GET /narration-timeline/verify` before materializing. Do not ship without a verification pass.
7. **Snapshot before major passes.** On the timeline, create a named snapshot before agent edit passes, user review rounds, or any operation that touches many clips. See `pr0ta-timeline`.
8. **Maintain `assets.json` from the first generation.** Append to the asset ledger immediately after every successful generation — not in a batch at the end. See "Project Structure & Asset Management" below.
9. **Run the editorial discipline.** Read `pr0ta-editorial` before any cut. Five-pass rewrite loop, seven ship criteria. A technically assembled cut is not a finished production.

## Quick Start (First-Time Users)

If this is your first PR0TA production: (1) Connect the bundled PR0TA MCP connector, or get a PAT token for REST/local stdio fallback — see "Before You Begin" below. (2) Read `pr0ta-prompting` to learn the self-contained prompt rule, prompt bible pattern, and Technique 4 (positive framing — video models silently drop `don't` / `no` / `does not` from prose). (3) Try generating a single image with `pr0ta-image` to verify your setup works. (4) When ready for multi-asset work, come back to this hub and follow the full pipeline below.

---

PR0TA (app.pr0ta.com) is an AI-powered creative production platform. This skill drives PR0TA through the **bundled MCP connector first**, then the REST API for routes that are not exposed through MCP or for high-volume scripting. Supports text-to-image, image-to-image editing, video generation via **Seedance 2.0 Omni or Kling V3/O3 (co-equal alternatives, both support multi-shot continuity)**, text-to-speech, text-to-music, and transcription (Scribe V2 preferred). Includes persistent consistency resources (Characters for Seedance, Elements for Kling), the post-production timeline API for assembly, and project-scoped task polling for completion detection.

The platform uses a credit-based system. Each generation costs credits depending on the model and output parameters.

## Agent Task Reference

| Task | Preferred Agent Surface | Notes |
|------|-----------|-------|
| Image generation (Nano Banana 2, GPT Image 2) | `generation_submit` | `generator=image`, `mode=txt_to_img` |
| Image editing (img-to-img, ref-to-img) | `generation_submit` | `mode=img_to_img`, `mode=ref_to_img`, `mode=edit_img` |
| Video generation (Seedance 2.0 Omni) | `generation_submit` | **Co-equal default.** `mode=txt_to_vid`, character ID, quad-modal refs |
| Video generation (Kling O3/V3 multi-shot) | `generation_submit` | **Co-equal default.** `prompt_mode: multi_prompt`, up to 5-6 cuts per generation, Elements, camera control |
| Audio generation (Gemini Flash TTS) | `generation_submit` | `generator=audio`, `mode=txt_to_speech`; ElevenLabs v3 fallback |
| Music generation (ElevenLabs Music) | `generation_submit` | `generator=music`, `mode=txt_to_music` |
| Task polling/cancel | `tasks_get`, `tasks_cancel` | Submit tools return task IDs, not finished assets |
| Asset list/upload/download links | `assets_list`, `assets_upload_start`, `assets_get_download_link` | Download bytes with normal HTTP/curl from returned link |
| Element/Character management | REST CRUD endpoints | Persistent project-scoped consistency resources |
| Timeline editing | `post_sequence_get`, `post_sequence_save` | Agent edits via MCP; user collaborates via the same timeline in the browser |
| Timeline render | `post_render_start` | Returns a render task ID |
| Narration materialization | `narration_timeline_get`, `narration_materialize_to_post` | Build/verify narration cuts, then materialize |
| Client review | `review_submit_assets` | Submit assets and get a review link |
| Project discovery | `list_projects` | Use before project-scoped MCP calls |
| Model discovery | `models_list`, `models_get_defaults` | Query live availability and schemas |

## Before You Begin

### For MCP and API Workflows

**Default path:** Use the PR0TA MCP connector bundled with this plugin. Start with `list_projects`, choose a `project_id`, submit long-running work with `generation_submit` or `generation_batch_submit`, then poll with `tasks_get`. All project-scoped MCP tools require `project_id`.

**Fallback path:** Use REST/curl only when a route is not exposed through MCP, when writing high-volume automation, or when downloading files from a signed link. Keep `curl` as the asset-download fallback because CDN behavior can differ by HTTP client.

**Step 0 — Auth.** Remote MCP clients use the host's PR0TA OAuth flow. For REST fallback or local stdio MCP, use a Personal Access Token (PAT). Before REST/local stdio work, check if the user has a PAT available (it starts with `pat_`). If they don't have one:

1. **Ask the user** if they have a PR0TA API token. Explain that a PAT is required for reliable REST fallback or local stdio workflows.
2. **If they don't know how to get one**, tell the user: *"Go to app.pr0ta.com → Settings → General → API Keys → Generate New Key. Copy the token (starts with `pat_`) and paste it here. It's only shown once."*
3. **Store the PAT** in an environment variable for the session: `export PR0TA_PAT="pat_xxxxxxxxxxxxx"`

**Do not proceed with REST fallback workflows without a PAT.** JWT extraction from browser localStorage is a fragile fallback — always prefer a PAT. Remote MCP OAuth does not require a PAT pasted into the chat.

**Sub-agent delegation:** If you dispatch sub-agents (parallel tasks) for generation work, **pass the PAT via the environment variable** (`$PR0TA_PAT`), not inline in the prompt. Inline tokens in prompts may trigger security refusals. The environment variable is inherited by sub-agents and avoids this issue.

1. **Authenticate** -- Use the MCP host OAuth flow, or use the PAT as `Authorization: Bearer pat_xxxxxxxxxxxxx` for REST/local stdio. See the `pr0ta-api` skill for full auth details.
2. **Create or select a project** -- Prefer `list_projects` for existing projects. For REST fallback, call `POST /api/v2/projects` to create a dedicated project for the task, or `GET /api/v2/projects` to list existing ones. Use the returned `id` directly in all subsequent calls. **Note:** PATs cannot use `?select=true` or the `/select` endpoint -- active project selection requires a JWT session token. This is fine for API workflows since you pass the project ID explicitly.
3. **Set up consistency resources** -- For multi-shot productions, create Element bundles and Character profiles before any generation. See the `pr0ta-consistency` skill.
4. Load `pr0ta-api` only when the active domain skill does not include the endpoint detail, auth nuance, or request schema you need.

### Companion Skill Router

This file is an orchestration overview. For each next action, load the relevant companion skill below. Avoid loading several large skills speculatively; keep context focused on the action you are about to perform.

| Skill | What It Contains | When to Read |
|-------|-----------------|--------------|
| **`pr0ta-api`** | Auth, raw endpoint schemas, route contracts, reliability rules, MCP setup, and API reference files | When the domain skill does not include the needed endpoint detail |
| **`pr0ta-video`** | Video model comparison, Seedance prompting guide with @tokens, Kling prompting guide, multi-prompt, camera control, native audio, duration/aspect ratio per model | **Before generating video** |
| **`pr0ta-image`** | Image models (Nano Banana 2 default, GPT Image 2 for prompt adherence / character consistency), resolution constraints, fan-out recipe, image editing modes | **Before generating images** |
| **`pr0ta-audio`** | Gemini Flash TTS, ElevenLabs v3 fallback, voice discovery, voice cloning, STS, Scribe V2 transcription | **Before generating narration/dialogue** |
| **`pr0ta-music`** | Music generation, composition workspace | **Before generating music/SFX** |
| **`pr0ta-editorial`** | Five-pass rewrite loop, ship criteria, story spine, mark-driven editing, editorial primitives | **Before any cut or edit pass** |
| **`pr0ta-consistency`** | Kling Elements, Seedance Characters (two training paths), character consistency bundles, reference pipeline, multi-modal references | **Before any multi-shot production** |
| **`pr0ta-sync`** | Cue sheets, visual-first vs narration-first pipeline strategy, continuous audio generation, **narration timeline API workflow**, montage best practices | **Before planning any multi-asset production** |
| **`pr0ta-prompting`** | Self-contained prompt writing, model-specific techniques | **Before writing any generation prompt** |
| **`pr0ta-downloading`** | Asset download methods, video storage_uri fallback | **Before downloading assets** |
| **`pr0ta-timeline`** | **Post-production timeline (primary editing surface):** clip CRUD API, Ken Burns as clip property, audio mix, preview/render, snapshots, narration materialization | **Before any post-production editing** |

## Full Pipeline Orchestration

When the user describes a creative vision that requires multiple asset types (video + narration + music + SFX), follow this production workflow. The key principles are: **plan timing first, set up consistency resources, generate visuals first, score to picture, then edit ruthlessly.**

For multi-asset productions, start with `pr0ta-sync` for timing, `pr0ta-prompting` for prompt construction, and `pr0ta-consistency` only when recurring characters/locations/props matter. Read `pr0ta-editorial` before the first real cut or review pass.

0. **Cue Sheet** — Build a structured timing plan before any generation: scenes with target durations, named markers (reveals, impacts, transitions), narration text mapped to time windows, music arc, SFX point events. Write self-contained prompts for every shot. Present the cue sheet to the user for approval. Timing changes are cheap here and expensive after generation. See `pr0ta-sync` and `pr0ta-prompting`.
1. **Project Setup** — `POST /api/v2/projects` with a descriptive name; use the returned `id` for all calls.
2. **Upload Real-World References (if any)** — If the production uses existing photos, actor headshots, product shots, storyboard scans, or other pre-existing media, ingest them now via `POST /api/v2/projects/{project_id}/assets/upload` (multipart, images only). The returned asset IDs feed straight into Element/Character creation (step 3) and generation payloads (steps 4-5). See `pr0ta-image` → "Uploading Existing Images" and `pr0ta-api` → "Project Image Upload".
3. **Consistency Setup** — Generate character/location/prop references with Nano Banana 2 (or GPT Image 2 for challenging character consistency), or use uploaded references from step 2. Tag approved references as `character_reference` via `PATCH /annotations`. Create Element bundles (Kling) and Character profiles (Seedance). Before generation, read each character's consistency bundle (`GET /characters/{id}/consistency`) for provider-ready payloads. See `pr0ta-consistency`.
4. **Key Frame Generation** — Use `img_to_img` or `ref_to_img` with Element/Character references to produce scene key frames.
5. **Video Generation** — Animate key frames with **Seedance 2.0 Omni** (`character_ids[]` and multi-modal references) or **Kling V3/O3 multi-shot** (`element_ids[]` with `prompt_mode: "multi_prompt"` and 2–6 shots per generation). Both are co-equal defaults — pick per shot based on the shot's needs, and for continuity-critical work, **generate the same shot in both and compare**. Use `multi_prompt` for continuous sequences. Set `sound: "on"` for dialogue clips where the speaker is visible; `sound: "off"` for B-roll and narration-over-footage. See `pr0ta-video`.
6. **Continuous Music** — Generate one music piece covering the full production, with the arc described against real timestamps. See `pr0ta-music`.
7. **Narration** — Generate narration for segments where the speaker is **not** visible. English dialogue uses native video audio (step 5). Non-English dialogue uses Gemini Flash TTS by default, with ElevenLabs v3 fallback for specific ElevenLabs voices or legacy tag workflows. See `pr0ta-audio`.
8. **Time-index EVERY audio-bearing asset (mandatory gate — two paths).** Before anything can enter the editing phase, route each asset through the right indexing endpoint. Speech-bearing assets (narration, dialogue clips, video with audio) go through `POST /api/audio/transcription/start` with `model_id: "fal-ai/elevenlabs/speech-to-text/scribe-v2"`. Instrumental music (score beds, underscore) goes through `POST /api/v2/projects/{project_id}/music/analyze`. Video-with-sound can either be transcribed directly (PR0TA extracts audio under the hood) or split first via `POST /api/v2/projects/{project_id}/assets/{asset_id}/extract-audio` for reuse. This is a hard gate: no asset moves to step 10 (timeline) until its indexing task has succeeded. For narration-first productions, the primary narration asset's transcription auto-populates the narration timeline's transcript layer with word-level timing, speaker IDs, and speech-adjacent audio events; tag transcript segments with content labels, register visual assets with affinity tags, build the cut list with transcript anchors, and verify alignment — all via the narration timeline API. For music-driven beats, use `music_analysis.downbeat_times` / `editorial_anchors` as the beat stream. See `pr0ta-audio` → "Mandatory Time-Indexing Rule (Two Paths)" and "Music Analysis API", `pr0ta-sync` → "Narration Timeline API", and `pr0ta-api` → "Narration Timeline API" and "Music Analysis API".
9. **Point SFX** — Short isolated clips at specific cue-sheet marker timestamps. Added to the post-production timeline as audio clips aligned to marker times.
9b. **Curate Assets** — Tag and annotate assets as they're generated: mark hero takes with `approved`/`hero`, tag rejects with `do_not_use`, set `reference_type` on reference images, add `notes` explaining why each asset matters, and favorite the assets destined for the timeline. Use `PATCH /api/assets/{project_name}/annotations`. Future agents and collaborators will rely on these labels to navigate the asset library. See `pr0ta-editorial` → "Asset Curation" and `pr0ta-api` → "Asset Tagging, Readability Filters, and Timeline Analysis".
10. **Materialize to the Post-Production Timeline** — For narration-timeline productions: call `POST /narration-timeline/materialize-to-post-production` to convert verified cuts into post-production timeline clips with Ken Burns presets, audio config, and transcript provenance. For other productions: add clips directly via `POST /timeline/clips`. Configure ducking and narration offset as timeline properties (`POST /timeline`). Preview key segments with `GET /preview`. Snapshot before major passes. See `pr0ta-timeline`.
11. **User Collaboration** — Hand off the timeline for user review in the browser at `app.pr0ta.com/timeline`. The user scrubs, reorders, trims, swaps clips, adjusts pacing. Read back the updated state with `GET /timeline/state` and address remaining notes with targeted clip edits — not a full rebuild.
11b. **Client Review (optional)** — For external stakeholder feedback, enable Studio mode on the project (`enable_studio_mode`), submit assets to a PR0TA review room via `review_submit_assets`, share the `review_url` with the reviewer, then retrieve timestamped comments, annotations, and approval decisions via `get_review_annotations`. Apply open feedback using editorial primitives. See `pr0ta-api` → "Client Review Room API".
12. **Editorial** — Five-pass rewrite loop against the story spine. Use `GET /preview` on key segments as the verification gate between passes. Six ship criteria before calling the cut finished. See `pr0ta-editorial`.
13. **Final Export** — Use `POST /export` for final delivery. Use `POST /render` for preview-task rendering during editorial iteration.

For the complete MCP/API pipeline (auth, tool contracts, per-endpoint REST fallbacks, reliability contract, download fallbacks, reference uploads, and UI navigation), read `pr0ta-api` and `pr0ta-downloading`. They carry the schemas and the state machine; this hub carries only the orchestration.

## Editorial Discipline — Read Before Any Cut

**Generation and assembly are mechanical. Editing is where a project becomes good or bad.** For any production beyond a single shot, read `pr0ta-editorial` before you start cutting. That skill is voice-forward, uncompromising, and has the full discipline: story spine specification, the five-pass rewrite loop, kill-your-darlings, the self-critique protocol, and the six-criteria ship gate. The irreducible minimum you cannot skip:

- Quality beats speed. There is no deadline worth shipping a mediocre cut.
- Every cut serves a one-sentence story spine. No spine, no cutting.
- Your first cut is a draft. Expect five passes before ship.
- **No reused assets.** Every generated image, video, and audio clip appears at most once. Generate a unique asset for every shot — never reuse the same image across multiple shots, even with different motion presets. This is non-negotiable.
- Story reads without dialogue, pacing breathes, no reuse, no stretches, every cut hits a beat, tail is deliberate, credits present — seven non-negotiables, and six out of seven is not ready.

Read `pr0ta-editorial` before editing. Read it again before calling a cut finished.

## Cross-Skill Pointers

This hub is an orchestration file. Detailed guidance for each moment of a production lives in a dedicated skill. Do not try to work from this file alone.

- **Writing prompts?** Read `pr0ta-prompting`. Self-contained prompts, Line-Locked Poster pattern, model-specific techniques, anti-patterns.
- **Generating images?** Read `pr0ta-image`. Nano Banana 2 (default), GPT Image 2 (for prompt adherence / character consistency edits), resolution constraints, fan-out and pick, image editing modes.
- **Generating video?** Read `pr0ta-video`. Seedance + Kling multi-shot co-equal decision framework, per-model duration/aspect matrix, Seedance Omni reference tokens, Kling multi-shot prompting playbook (shot labels, Element binding, camera grammar), camera control, native audio rules, structured validation errors.
- **Generating narration or dialogue?** Read `pr0ta-audio`. Gemini Flash TTS, ElevenLabs v3 fallback, voice discovery, voice cloning, STS, English vs non-English dialogue handling, Scribe V2 transcription.
- **Generating music or SFX?** Read `pr0ta-music`.
- **Multi-shot production?** Read `pr0ta-consistency` **before any generation**. Elements (Kling), Characters (Seedance), consistency bundles, reference pipeline, multi-modal refs.
- **Planning a multi-asset production?** Read `pr0ta-sync`. Cue sheets, visual-first vs narration-first strategy, narration timeline API workflow, montage best practices.
- **Assembling a final cut?** Read `pr0ta-timeline`. The post-production timeline is the only supported editing surface — clip CRUD, Ken Burns, audio mix, preview, snapshots, render. For editorial judgment, read `pr0ta-editorial`.
- **Downloading assets?** Read `pr0ta-downloading`. Curl-via-subprocess Cloudflare bypass, public vs authenticated paths.
- **Sending assets for client review?** Read `pr0ta-api` → "Client Review Room API". Enable Studio mode, submit assets with `review_submit_assets`, share review URLs, retrieve timestamped annotations and approval decisions, completion webhook.
- **Connecting external tools (Claude Code, Cursor, ChatGPT)?** Read `pr0ta-api` → "MCP Server & Agent Tools". Stdio/HTTP/OAuth setup, available tools, role-tool access matrix.
- **Making API calls?** Read `pr0ta-api`. Auth, structured validation errors, `/generate/batch`, rate limits, `generation_context`, async provider error surfacing (`error_detail`), reliability contract, post-production timeline API, narration timeline API (26 endpoints), music analysis API, audio extraction from video, client review room, MCP server.
- **Building a narration-driven production?** Build and verify cuts in the narration timeline (`pr0ta-sync` → "Narration Timeline API", `pr0ta-api` → "Narration Timeline API"), then materialize to the post-production timeline (`pr0ta-timeline`).

**QC is not a separate section.** Every skill above carries the quality bar for its own moment of the pipeline. The overall standard, and the editorial voice behind it, lives in `pr0ta-editorial`.

## Project Structure & Asset Management

Multi-shot productions need a local file structure and an asset map from the first generation. Ad-hoc organization breaks down around 10–15 assets and causes re-generation work that would have been avoided with ~5 minutes of setup.

### Recommended Local Layout

```
production_v1/
  assets.json              # local asset ID map (see below)
  cue_sheet.json           # scene timing plan (see pr0ta-sync)
  references/              # any user-uploaded reference images (optional)
```

The **post-production timeline on PR0TA is the source of truth for the edit itself.** Version-control of the cut lives in timeline snapshots (`POST /timeline/snapshot`), not in local directories. The local directory is for the cue sheet, asset map, and any reference uploads — not for rendered intermediates or per-version clip buckets.

### Version Control — Timeline Snapshots, Not Local Directories

Previous iterations of this skill recommended ephemeral version directories (`production_v1/`, `production_v2/`, ...) to hold per-version rendered clips. That pattern belonged to a local-build-script workflow that no longer exists. With the post-production timeline:

- **Snapshots replace version directories.** `POST /timeline/snapshot` with a name captures the full edit state server-side. `POST /timeline/snapshot/{name}/restore` rolls back.
- **Diffs replace A/B playback.** `GET /timeline/snapshot/{name}/diff` shows what changed between the current state and any snapshot.
- **No local clip buckets.** You do not download and manage per-shot rendered clips — the timeline references assets by ID and renders on demand.
- **User collaboration is live.** The user and the agent edit the same timeline. There are no "my version" and "their version" to reconcile.

Keep `assets.json` and `cue_sheet.json` locally as human-readable ledgers of what was generated and why. Keep everything about the cut on the timeline.

### assets.json — Local Asset ID Map

**Maintain a local JSON file mapping human-readable shot IDs → PR0TA asset IDs → local file paths from day one.** This is the single highest-ROI habit for any multi-shot production. It eliminates re-listing the asset API every time you look up an ID, survives pagination bugs, and becomes the single source of truth for what's in the project.

**Schema:**

```json
{
  "project_id": "SINGULARITY_V1_The_Countdown",
  "created_at": "2026-04-04T12:00:00Z",
  "assets": {
    "img_title": {
      "pr0ta_asset_id": "a73b9aad-8c4f-4d2e-b9a1-f3e5c2d1b0a4",
      "kind": "image",
      "local_path": "production_v1/sources/img_title.png",
      "purpose": "title card — full-frame 'THE COUNTDOWN' type",
      "source_prompt": "A full-frame title card. Solid deep navy background, massive centered display type reading 'THE COUNTDOWN' in bold condensed sans-serif, amber-gold fill, flat vector style, no shadows.",
      "model": "nano_banana_2",
      "version": "v1",
      "used_in_shots": [1]
    },
    "img_2027": {
      "pr0ta_asset_id": "b82c40de-1a5b-4e6f-9c7d-4e2f3a5b6c8d",
      "kind": "image",
      "local_path": "production_v1/sources/img_2027.png",
      "purpose": "flash card — year drop",
      "source_prompt": "A full-frame flash card design. Solid amber-gold background. Massive centered '2027' in bold condensed sans-serif, occupying ~65% of frame height, rendered in deep navy. Flat vector style, hard edges.",
      "model": "nano_banana_2",
      "version": "v1",
      "used_in_shots": [4]
    },
    "vid_newsroom": {
      "pr0ta_asset_id": "c93d5e0f-2b6c-4f7a-ad8e-5f3b4c6d7e9f",
      "kind": "video",
      "local_path": "production_v1/sources/vid_newsroom.mp4",
      "purpose": "B-roll — newsroom medium shot",
      "source_prompt": "Newsroom anchor desk, medium shot, warm tungsten key light, shallow depth of field. Hold the existing composition, minimal camera movement, only subtle head motion animates.",
      "model": "seedance_2_omni",
      "version": "v1",
      "used_in_shots": [5]
    }
  }
}
```

**Key rules:**

- **One file per production version.** `assets.json` lives inside `production_vN/` and captures what that version used.
- **Human-readable keys.** `img_title`, `vid_newsroom_01`, `aud_narration_full` — not UUIDs. The UUID lives inside the value.
- **Every entry records the source prompt** so you can re-generate or iterate.
- **`used_in_shots` reverse-links to the cut list** — when you want to drop a shot, you know exactly which assets it referenced.
- **Update the map at generation time, not at the end.** The skill contract is: append to `assets.json` immediately after any successful generation, before moving on to the next task.

When you need to find an asset by name, load `assets.json` first. Only fall back to the asset listing API (with full pagination — see `pr0ta-api`) if the local map is missing or stale.

For multi-shot productions, read `pr0ta-consistency` for the full Elements/Characters pipeline before generating any shots.
