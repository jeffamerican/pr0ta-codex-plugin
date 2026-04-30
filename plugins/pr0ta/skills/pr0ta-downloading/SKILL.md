---
name: pr0ta-downloading
description: "PR0TA asset download/export guide. Read when downloading generated images, videos, or audio; handling signed URLs/storage_uri fallback; detecting 0-byte files; bulk exporting; or tracking asset provenance."
---

# Downloading & Exporting Assets Reference

> **See also:** The `pr0ta-api` skill's reliability contract (`reference/reliability-contract.md`) covers the full download fallback chain — including the `storage_uri` video workaround, asset correlation rules, and the 0-byte detection pattern that this skill's API download section implements.

Download assets from PR0TA using the API.

## API Download

PR0TA exposes a public download endpoint that does NOT require authentication. This is the standard download method when you have an asset ID.

### ⚠️ Use `curl` via subprocess — NOT Python urllib

**Field-tested reliability:** PR0TA asset URLs sit behind Cloudflare, which 403s Python `urllib.request.urlopen` on asset downloads. `requests` works sometimes. `curl` invoked via subprocess works every time. **Default to curl.**

```python
# ✅ RELIABLE — curl via subprocess
import subprocess
from pathlib import Path

def download_asset(project_id: str, asset_id: str, out_path: Path, pat: str | None = None) -> Path:
    """Download a PR0TA asset reliably via curl subprocess."""
    url = f"https://app.pr0ta.com/api/v2/projects/{project_id}/assets/{asset_id}/download"
    cmd = ["curl", "-sSL", "--fail", "-o", str(out_path), url]
    if pat:
        cmd.extend(["-H", f"Authorization: Bearer {pat}"])
    subprocess.run(cmd, check=True)
    # Validate byte count — 0-byte downloads should trigger storage_uri fallback
    if out_path.stat().st_size == 0:
        raise RuntimeError(f"0-byte download for asset {asset_id}")
    return out_path
```

```python
# ❌ DO NOT USE — Cloudflare will 403 this, often silently
import urllib.request
urllib.request.urlretrieve(url, out_path)  # 403 Forbidden
```

**Why:** Cloudflare's bot-protection fingerprints `urllib`'s default user-agent. `requests` passes sometimes but is inconsistent. `curl` with its default user-agent consistently passes the bot check. This is an environmental quirk of the CDN in front of PR0TA, not the API itself.

### Direct Download by Asset ID (curl)

```
GET /api/v2/projects/{project_id}/assets/{asset_id}/download
```

This endpoint is public (no auth needed). Use `curl` from the shell or via subprocess:

```bash
curl -sSL --fail "https://app.pr0ta.com/api/v2/projects/{project_id}/assets/{asset_id}/download" \
  -o output_filename.png
```

You can also request a specific size variant with `?size=thumbnail`.

### Video Download Fallback (storage_uri)

**Status (April 2026 — hardened):**
1. **Video 0-byte download — FIXED.** The `/download` endpoint now works reliably for all asset types including video.
2. **Task → asset correlation — HARDENED.** The canonical task completion contract now guarantees `result.asset_id`, `result.asset_ids`, `result.download_url`, and `result.urls` on all succeeded generation tasks. Terminal-task asset reconciliation ensures tasks that reach `succeeded` without clean asset linkage are repaired from persisted assets. If `result.asset_id` is missing on a completed task, treat it as a platform bug and use the asset listing fallback. See `pr0ta-api` → "Task Polling" for the canonical response shape.

**Preferred download path after task completion:**
```python
# After polling task to "succeeded":
asset_id = task_data["result"]["asset_id"]
download_url = f"https://app.pr0ta.com{task_data['result']['download_url']}"
# OR construct from asset_id:
download_url = f"https://app.pr0ta.com/api/v2/projects/{project_id}/assets/{asset_id}/download"
```

The `storage_uri` auth fallback below is retained as defense-in-depth but should no longer be needed in normal operation.

### Video Download Fallback (storage_uri) — Defense-in-Depth

If a video download ever returns 0 bytes, use the authenticated `storage_uri` fallback:

```bash
# 1) Get asset metadata to find storage_uri
curl "https://app.pr0ta.com/api/v2/projects/{project_id}/assets?kind=video" \
  -H "Authorization: Bearer $PAT"

# 2) Read storage_uri from the asset object, then download with auth
curl -L -H "Authorization: Bearer $PAT" \
  "https://app.pr0ta.com${storage_uri}" \
  -o video_output.mp4
```

**Important:** The `storage_uri` path involves a redirect — always use `curl -L` (follow redirects) when downloading via this path.

The **reliability contract** in the `pr0ta-api` skill formalizes this as a two-step chain: try `/download` first, validate bytes (`content-length > 0`), then fall back to `storage_uri` if zero-byte. If both fail, the request is marked `ambiguous` for retry.

### Getting the Asset ID

Asset IDs (UUIDs like `59cba82d-503d-4c4a-8f62-b48288895342`) can be obtained from:

1. **The task result** -- `result.asset_id` on a succeeded generation task
2. **The API asset listing** (requires auth -- see below)
3. **Your local `assets.json` ledger** -- if you maintain one per the `pr0ta` hub guidance

### Authenticated API Endpoints

These endpoints require a bearer token obtained via `POST /api/auth/login`:

**List assets:**
```
GET /api/v2/projects/{project_id}/assets
```
Supported query parameters: `offset`, `limit`, `kind` (image/video/audio), `type`, `category`, `source`, `sort` (asc/desc), `sort_by`, `include_download`, `folder_path`, `recursive`, `music_only`, `is_imported`

**Get signed download URL:**
```
GET /api/v2/projects/{project_id}/assets/{asset_id}/download-link
```
Returns a signed URL payload. Use `?as_attachment=true` for download headers.

**Get asset metadata:**
```
GET /api/v2/projects/{project_id}/assets/{asset_id}/metadata
```

**Browse asset facets:**
```
GET /api/v2/projects/{project_id}/assets/facets
```

**Authentication flow:**
```bash
# 1) Get bearer token
TOKEN=$(curl -s -X POST https://app.pr0ta.com/api/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"user@example.com","password":"password"}' | jq -r '.access_token')

# 2) List project assets
curl "https://app.pr0ta.com/api/v2/projects/PROJECT_ID/assets?kind=image&sort=desc&limit=10" \
  -H "Authorization: Bearer $TOKEN"

# 3) Get signed download link
curl "https://app.pr0ta.com/api/v2/projects/PROJECT_ID/assets/ASSET_ID/download-link" \
  -H "Authorization: Bearer $TOKEN"
```

### Step-by-Step: Download an Asset via API

1. **Get the project ID** from the PR0TA URL or top nav bar (e.g., "Fight_Sequence_1772619326")
2. **Get the asset ID** -- from the task result, the asset listing API, or your local `assets.json`
3. **Download directly:**
   ```bash
   curl -sL "https://app.pr0ta.com/api/v2/projects/{project_id}/assets/{asset_id}/download" \
     -o desired_filename.ext
   ```
4. The file saves to the specified path

### When to Use

- **Always prefer this method** when you have the asset ID and want to save to a specific location
- Ideal for automation, batch scripting, and presenting files to the user
- Works from command line or subprocess
- Use the authenticated listing endpoint first if you need to discover asset IDs

## Tips

- **Always use API download** -- it lets you control the output filename and path precisely
- **For video downloads, the `storage_uri` fallback is available as defense-in-depth** -- the public `/download` endpoint now works reliably (fixed April 2026), but the fallback is good practice. See the Video Download Fallback section above.
- For large batches, use the authenticated asset listing API to get all IDs, then loop `curl` downloads. For video batches, validate byte count on each download and retry via `storage_uri` for any 0-byte results.
- For the complete download fallback chain and error handling, see the **reliability contract** in the `pr0ta-api` skill


## Provenance — Use `assets.json` + `generation_context`

Downloaded files land on disk with opaque UUID names. You need a way to answer "which prompt produced this file?" in under a minute, both during QC and after the project ships. There are two complementary sources of truth — use both:

**1. Local `assets.json` (production-scoped, human-readable).** Defined in the `pr0ta` hub skill, `assets.json` is the single canonical production ledger for any multi-shot job. It maps human-readable shot keys (`img_title`, `vid_newsroom_01`) to `pr0ta_asset_id`, `local_path`, `source_prompt`, `model`, `used_in_shots`, and any editorial notes. It is the file you read from when assembling the cut, and the file that ships with the final export. **Append to `assets.json` immediately after every successful generation** — not in a batch at the end of the production. See the `pr0ta` hub for the full schema.

**2. API-side `generation_context` (authoritative fallback).** As of April 2026, `GET /api/v2/projects/{project_id}/assets/{asset_id}` returns a `generation_context` block with `prompt`, `model`, `negative_prompt`, `seed`, `task_id`, `submitted_at`, `completed_at`, and `status` when recoverable. This is the source-of-truth fallback when your local `assets.json` is missing, stale, or lost. You don't need a second local ledger file — the API provides retrospective lookup for any asset you know the ID of.

**Do not maintain a separate `results.json` ledger.** Earlier versions of this skill prescribed one; it has been dropped to avoid duplication with `assets.json`. One local file + the API-side `generation_context` is the complete contract.
