## Asset Management (Auth Required)

### List Project Assets

```
GET /api/v2/projects/{project_id}/assets
```

Supported filters: `offset`, `limit`, `kind`, `type`, `category`, `source`, `subject`, `origin_system`, `ingest_channel`, `external_project_id`, `is_imported`, `music_only`, `folder_path`, `recursive`, `sort`, `sort_by=scene_shot_take`, `q`, `task_id`, `created_after`, `created_before`

**Important:** Response uses nested shape:
```json
{
  "assets": [
    {
      "asset": {
        "id": "c4f3bdf3-472a-4d6a-ad08-ea3872b8ed0c",
        "kind": "video",
        "category": "generated"
      },
      "download": {
        "url": "/api/v2/projects/project-1/assets/c4f3bdf3.../download"
      }
    }
  ]
}
```

Read the asset ID from `.assets[i].asset.id`, not `.assets[i].id`.

**Note on asset metadata:** Asset objects from the listing endpoint may return empty `prompt`, `model`, and `params` fields. To retrieve the original generation parameters for an asset, query the task metadata instead: `GET /api/tasks/{task_id}` → `metadata.provider_request.parameters`.

### ⚠️ Asset Listing Pagination — Always Iterate to Exhaustion

**Do not assume page 1 is exhaustive.** The asset listing endpoint paginates, and any project with more than ~50 assets will span multiple pages. Field-tested failure mode: an agent looked at page 1, didn't find `img_01`, concluded the asset was deleted — it was on page 2.

**Canonical pagination contract for the project-scoped API:** offset-based with `next_offset`.

```
GET /api/v2/projects/{project_id}/assets?offset=0&limit=100
```

Response shape:

```json
{
  "assets": [ ... ],
  "next_offset": 100,
  "total": 247
}
```

- `assets` — the page of results
- `next_offset` — offset to pass on the next request; **`null` when the listing is exhausted**
- `total` — total count of assets matching the filters (useful for progress reporting)

**Rule:** When searching for a known asset ID or name, iterate until `next_offset` is `null` (or the returned page is empty) before concluding the asset doesn't exist.

```python
import subprocess, json

def list_all_assets(project_id: str, pat: str, kind: str | None = None) -> list[dict]:
    """Iterate every page of the project-scoped asset listing until exhausted."""
    all_assets: list[dict] = []
    offset, limit = 0, 100
    while True:
        params = f"offset={offset}&limit={limit}" + (f"&kind={kind}" if kind else "")
        url = f"https://app.pr0ta.com/api/v2/projects/{project_id}/assets?{params}"
        resp = json.loads(subprocess.run(
            ["curl", "-sSL", "--fail", url, "-H", f"Authorization: Bearer {pat}"],
            check=True, capture_output=True, text=True,
        ).stdout)
        all_assets.extend(resp.get("assets", []))
        next_offset = resp.get("next_offset")
        if next_offset is None:
            break
        offset = next_offset
    return all_assets

def find_asset_by_name(project_id: str, pat: str, name: str) -> dict | None:
    for wrapper in list_all_assets(project_id, pat):
        a = wrapper.get("asset", {})
        if a.get("name") == name or a.get("display_name") == name:
            return a
    return None  # truly not in the project
```

**Legacy cursor pagination:** The older (non-project-scoped) assets route at `/api/v2/assets` still supports `cursor`/`nextCursor` pagination. **Prefer the project-scoped endpoint with offset/next_offset for all new code** — it's the canonical contract going forward.

**Tip:** For productions with dozens or hundreds of assets, maintain a local `assets.json` map (see the `pr0ta` hub skill) so you don't need to re-iterate the listing every time you look up an ID.

### Download Asset

```
GET /api/v2/projects/{project_id}/assets/{asset_id}/download
```

This endpoint is public (no auth required) and works reliably for all asset types (image, video, audio).

**Defense-in-depth fallback:** If a download ever returns 0 bytes, use the authenticated `storage_uri` fallback (this bug was fixed April 2026, but the fallback is good practice):

1. Get asset metadata: `GET /api/v2/projects/{project_id}/assets?kind=video`
2. Read the `storage_uri` field from the asset object
3. Download with auth: `curl -L -H "Authorization: Bearer $PAT" "https://app.pr0ta.com${storage_uri}" -o video.mp4`

### Get Asset Thumbnail (Public -- No Auth Required)

```
GET /api/v2/projects/{project_id}/assets/{asset_id}/thumbnail
```

---

## Batch Workflow Pattern

For multi-shot productions, avoid one polling loop per task.

Recommended pattern:

1. Submit each generation and immediately persist `{scene_key, shot_key, task_id}` in your orchestration state.
2. Poll `GET /api/v2/projects/{project_id}/events?limit=200` with `since=` or `cursor=` on a shared cadence. **Always set `limit=200`** for batch workflows — the default of 50 drops later completions.
3. Match returned events by `task_id`. **Some tasks may succeed without generating events** — also poll individual tasks via `GET /api/tasks/{task_id}` for any that don't appear in events after the expected timeout.
4. Attach `asset_id` / `asset_ids` back to your scene or shot keys.
5. Use `GET /api/v2/projects/{project_id}/assets?task_id=$TASK_ID` for direct task-to-asset reconciliation, or broader filters like `kind=video` for audit passes.
6. Use `created_after` / `created_before` on the assets endpoint to distinguish current runs from earlier failed or experimental batches.
7. Normalize final video dimensions after download when your edit pipeline requires strict output sizes.

Minimal orchestration state example:
```json
{
  "scene_012_shot_03": {
    "task_id": "task_xyz123",
    "generator": "video",
    "mode": "ref_to_vid",
    "requested_asset_ids": ["c4f3bdf3-472a-4d6a-ad08-ea3872b8ed0c"],
    "completed_asset_id": null
  }
}
```

---

