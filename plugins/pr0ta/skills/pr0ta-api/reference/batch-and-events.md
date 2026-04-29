## Batch Generation

Submit multiple generation requests in a single call.

### Submit Batch (Auth Required)

```
POST /api/v2/projects/{project_id}/generate/batch
```

Request:
```json
{
  "requests": [
    { "generator": "image", "mode": "txt_to_img", "prompt": "..." },
    { "generator": "image", "mode": "txt_to_img", "prompt": "..." }
  ]
}
```

**CRITICAL: All parameters go at the top level of each request object.** Do NOT nest parameters inside a `"params"` object — this is a common mistake that causes `"prompt is required"` errors. Each request in the array has the same flat structure as a single `POST /generate` request.

```json
// ✅ CORRECT — flat structure
{ "generator": "video", "mode": "ref_to_vid", "model": "kling_o3_pro", "prompt": "...", "duration": 10 }

// ❌ WRONG — nested params object
{ "generator": "video", "mode": "ref_to_vid", "params": { "model": "kling_o3_pro", "prompt": "...", "duration": 10 } }
```

**Guardrails:**
- Maximum 10 requests per batch. Exceeding this returns `413`.
- Empty `requests` array returns `400`.

Response:
```json
{
  "tasks": [
    { "index": 0, "task_id": "task_x", "status": "queued", "estimated_seconds": null, "credits_cost": null }
  ],
  "total_credits_cost": null
}
```

Each task can be polled individually via the events or task endpoints.

---

## Generation Event Queue (Primary Completion Path)

The event queue is the **preferred method** for detecting when generations complete. It replaces per-task polling for automation workflows.

### List Generation Events

```
GET /api/v2/projects/{project_id}/events
```

Returns terminal generation events for the project, newest first.

**Query parameters:**
- `since` -- ISO timestamp; only events after this time
- `status` -- filter by status (`succeeded`, `failed`)
- `generator` -- filter by generator type (`image`, `video`, `audio`, `music`)
- `task_id` -- filter to a specific task
- `limit` -- max events per page (default: 50). **For batch workflows (10+ clips), always set `limit=200` or higher.** The default of 50 will silently drop later completions from the response.
- `cursor` -- pagination cursor from previous response. Use `has_more` + `cursor` to paginate through large result sets.

**Example response:**
```json
{
  "events": [
    {
      "id": "evt_abc123",
      "event": "generation.succeeded",
      "task_id": "task_xyz123",
      "project_id": "project-1",
      "generator": "video",
      "mode": "ref_to_vid",
      "model": "kling_o3_pro",
      "status": "succeeded",
      "asset_id": "asset_abc123",
      "asset_ids": ["asset_abc123"],
      "download_url": "/api/v2/projects/project-1/assets/asset_abc123/download",
      "created_at": "2026-03-30T14:22:03Z"
    }
  ],
  "cursor": "opaque-cursor",
  "has_more": false
}
```

**Useful filter patterns:**
- `generator=video&status=succeeded` -- completed videos only
- `generator=audio` -- narration/TTS completions
- `task_id=$TASK_ID` -- reconciling a single job
- `cursor=$CURSOR` -- consuming a long event stream page by page

**Batch workflow pagination:** The server now defaults to `limit=200` (previously 50). For very large batches (200+ events), still check `has_more` in the response and paginate with `cursor`. Events also now backfill missing terminal events from task history, so the previous gap where tasks succeeded without emitting events has been closed.

### Wait Strategy

Recommended wait times before first event poll:
- Image: 15 seconds (image events and task reconciliation are now reliable; asset-listing fallback is retained as defense-in-depth)
- Video: 60 seconds, then 30-second intervals
- Audio: 10 seconds
- Music: 20 seconds

**Note:** Image generation events and task status reconciliation have been hardened (April 2026). Events now backfill from task history, and tasks reconcile to `succeeded` from persisted assets. The asset-listing fallback remains as defense-in-depth for any edge cases.

---

