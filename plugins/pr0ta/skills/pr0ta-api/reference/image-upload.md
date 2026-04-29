# Project Image Upload — Reference

Direct-multipart image ingestion into a PR0TA project. Use this for existing photos, screenshots, key frames, or real-world references before generation.

## Project Image Upload (Direct Multipart)

Upload local still images directly into a project without the prepare/proxy/finalize workflow. This is the preferred path for skills that need to ingest existing photos, screenshots, key frames, or real-world references before generation.

```
POST /api/v2/projects/{project_id}/assets/upload
Content-Type: multipart/form-data
Authorization: Bearer <PAT>
```

### Request

Multipart fields:

| Field | Required | Default | Notes |
|-------|----------|---------|-------|
| `files` | yes | — | One or more image files. **Field name is `files` (plural), not `file`.** Non-image files are rejected with `400`. |
| `category` | no | `imported` | Freeform string. |
| `subject` | no | — | Freeform string. |
| `labels` | no | — | JSON **object** encoded as a string (not an array, not bare text). |

**Complete curl example (copy-paste ready):**

```bash
# Upload a single image — field name MUST be "files" (plural), not "file"
curl -X POST "https://app.pr0ta.com/api/v2/projects/$PROJECT_ID/assets/upload" \
  -H "Authorization: Bearer $PR0TA_PAT" \
  -F "files=@hero-frame.png"

# Upload multiple images in one request
curl -X POST "https://app.pr0ta.com/api/v2/projects/$PROJECT_ID/assets/upload" \
  -H "Authorization: Bearer $PR0TA_PAT" \
  -F "files=@hero-frame.png" \
  -F "files=@location-ref.jpg" \
  -F "category=reference"
```

Using `file` (singular) instead of `files` returns `422`. This is a confirmed field name.

### Response

```json
{
  "success": true,
  "assets": [
    {
      "id": "asset-id",
      "project_id": "project-id",
      "kind": "image",
      "status": "ready",
      "storage_uri": "/api/v2/projects/project-id/assets/asset-id/download",
      "canonical_name": "hero-frame.png",
      "labels": { "source": "upload_api", "ingest_channel": "api", "...": "..." }
    }
  ]
}
```

`assets[]` uses the standard `AssetRead` shape. `id` is the field you need for follow-up generation calls.

### Usage patterns

1. **Reference images for video generation:** Upload a still, then pass its `id` as `start_image_asset_id` in a `/generate` payload (`ref_to_vid` mode).
2. **Element/Character source material:** Upload real-world photos, then create an Element bundle or Character profile from the uploaded asset IDs.
3. **Image editing:** Upload a source image, then use `img_to_img`, `ref_to_img`, or `edit_img` mode against the uploaded asset.
4. **Batch upload:** Send multiple `files` fields in one request — the response contains one `AssetRead` per file.

### Error cases

- `400` — no files, non-image file, missing filename, `labels` not valid JSON or not an object
- `401` — missing/invalid bearer token
- `404` — project not found or inaccessible
- `500` — upload registered but asset could not be reloaded (transient)

### Scope

This route accepts **images only** today. For audio/video/document direct upload, use the legacy prepare/proxy/finalize flow (`/assets/uploads/prepare` → `/proxy` → `/finalize`).

---
