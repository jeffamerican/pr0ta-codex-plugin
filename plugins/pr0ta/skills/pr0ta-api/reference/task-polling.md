# Task Polling — Reference

Full polling contract: routes, in-progress / succeeded / failed response shapes, the error-reason taxonomy, cancellation, and the `result` vs `result_refs` canonical contract.

## Task Polling (Primary Completion Signal)

**Task polling is the primary completion signal.** Poll until the task reaches a terminal state, then extract the asset ID from the response.

### Get Task Status

Two equivalent routes — prefer the project-scoped path so the project context is explicit:

```
GET /api/v2/projects/{project_id}/tasks/{task_id}   ← preferred
GET /api/tasks/{task_id}                              ← also valid
```

Both return the same task object. The project-scoped route was added April 2026; the global route has existed since launch.

### Async Provider Errors

When a generation reaches the provider but fails there (e.g. insufficient provider credits, model unavailable), the task will reach `status: "failed"` with:

- `error` — human-readable message (e.g. `"Insufficient credits"`)
- `error_detail` — full provider payload for diagnosis

These failures are **asynchronous** — the initial `POST /generate` returns 200 + `task_id` + `"running"` before the provider rejects the job. You will only see the error by polling the task to terminal state. **Always poll to terminal; never assume a 200 on submission means the generation will succeed.**

Example in-progress response:
```json
{
  "id": "task_xyz123",
  "type": "video_generation",
  "project_id": "project-1",
  "status": "running",
  "progress": 42,
  "message": "Generation submitted, waiting for webhook",
  "created_at": "2026-04-03T14:20:00Z",
  "submitted_at": "2026-04-03T14:20:01Z",
  "result_refs": {},
  "metadata": {
    "unified_generation": {
      "generator": "video",
      "mode": "ref_to_vid"
    }
  }
}
```

Example completed response:
```json
{
  "id": "task_xyz123",
  "type": "video_generation",
  "project_id": "project-1",
  "status": "succeeded",
  "progress": 100,
  "message": "Generation completed",
  "created_at": "2026-04-03T14:20:00Z",
  "submitted_at": "2026-04-03T14:20:01Z",
  "result_refs": {
    "asset_id": "asset_abc123",
    "type": "video",
    "download_url": "/api/v2/projects/project-1/assets/asset_abc123/download"
  },
  "result": {
    "type": "video",
    "asset_id": "asset_abc123",
    "asset_ids": ["asset_abc123"],
    "download_url": "/api/v2/projects/project-1/assets/asset_abc123/download",
    "urls": ["/api/v2/projects/project-1/assets/asset_abc123/download"]
  }
}
```

Example failed response (async provider error):
```json
{
  "id": "task_xyz123",
  "status": "failed",
  "progress": 0,
  "error": "Insufficient credits",
  "error_reason": "provider_error",
  "error_detail": { "provider": "muapi", "message": "Insufficient credits", "code": 402 },
  "created_at": "2026-04-06T03:00:00Z",
  "submitted_at": "2026-04-06T03:00:01Z"
}
```

Example failed response (provider timeout):
```json
{
  "id": "task_xyz123",
  "status": "failed",
  "progress": 95,
  "error": "Provider generation timeout",
  "error_reason": "provider_timeout",
  "created_at": "2026-04-03T14:20:00Z",
  "submitted_at": "2026-04-03T14:20:01Z"
}
```

**Task response fields:**
- `created_at` — when the task was created
- `submitted_at` — when it was submitted to the provider
- `error` — human-readable error message (present when `status=failed`)
- `error_reason` — machine-readable error category (present when `status=failed`)
- `error_detail` — full provider payload for diagnosis (present on async provider failures)

Use `created_at` for timing calculations in the reliability contract. Use `error_reason` to decide whether a failed task is worth retrying:
- `provider_timeout` → retry (transient)
- `provider_error` + `error_detail.code: 402` → do **not** retry; fix provider account credits first
- `invalid_parameters` → do not retry; fix the payload

**`result` is the canonical completion contract.** Always read asset information from `result`, not `result_refs`. The canonical shape for all succeeded generation tasks is:

```json
{
  "result": {
    "type": "video",
    "asset_id": "asset-uuid",
    "asset_ids": ["asset-uuid"],
    "download_url": "/api/v2/projects/{project_id}/assets/{asset_id}/download",
    "urls": ["/api/v2/projects/{project_id}/assets/{asset_id}/download"],
    "variant_count": 1
  }
}
```

- `result.asset_id` — primary single-output identifier
- `result.asset_ids` — complete list of asset-backed outputs
- `result.download_url` — primary retrieval URL
- `result_refs` — legacy compatibility; do not use as the preferred client contract

If a completed task does not expose `result.asset_id`, treat it as a platform bug and use the asset listing fallback (`GET /api/v2/projects/{id}/assets?kind=video` sorted by recency). The platform has hardened reconciliation so that tasks reaching `succeeded` without clean asset linkage are repaired from persisted assets.

### Cancel a Stuck Task

Two equivalent routes — prefer the project-scoped path:

```
POST /api/v2/projects/{project_id}/tasks/{task_id}/cancel   ← preferred
POST /api/tasks/{task_id}/cancel                              ← also valid
```

Cancels a running or stalled task. Use this when a video task has been stuck at the same `progress` for >3 minutes, or has exceeded the max polling window (20 min for video).

The backend normalizes both `canceled` and `cancelled` terminal states — completion side-effects are reliable for cancelled tasks.

**Cancellation in the reliability contract:**
1. Detect stall: same `progress` value for >3 minutes
2. Cancel: `POST /api/tasks/{task_id}/cancel`
3. Resubmit: identical generation request to the same provider (queue-reset often fixes it)
4. **If the retry also stalls, pivot to the other video provider** — Seedance → Kling V3 I2V, or Kling → Seedance Omni. Do not burn a third attempt on the same backend. See `pr0ta-video` → "Cross-Provider Pivot on Stall" for the field-translation cheat sheet.
5. If both providers stall, surface the status to the user before degrading to a Ken Burns push on the still — motion vs. no-motion is a creative call, not an infrastructure call.

---

