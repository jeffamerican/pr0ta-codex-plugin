# Client Review Room API

> **See also:** For editorial judgment on incorporating review feedback, read `pr0ta-editorial`. For the MCP server that exposes these tools to external agents, read `reference/mcp-server.md`.

## Overview

Skills users can submit one or more project assets to a PR0TA client review room without using the web UI. PR0TA returns a public review link that can be sent to a reviewer. After the reviewer adds comments, time-coded notes, annotations, or approval/change-request decisions, the skills user retrieves that feedback through the MCP tool surface or REST API.

This workflow is exposed through **PR0TA agent/MCP tools** (`enable_studio_mode`, `submit_assets_for_review`, `get_review_annotations`). The review tools are available to `editor`, `director`, `producer`, and `script_supervisor` roles.

## Studio Mode Setup

Review-room creation requires Studio mode on the project. API-only skills can enable it without using the PR0TA web UI.

### MCP Tool: `enable_studio_mode`

Enables Studio mode for the current project. The caller must authenticate as the project owner.

```json
{}
```

Response:

```json
{
  "project_id": "project-id-or-slug",
  "studio_enabled": true,
  "studio_role": "supervisor",
  "message": "Studio mode is enabled for this project."
}
```

### REST Equivalent

```http
PATCH /api/v2/projects/{project_id}/studio
Content-Type: application/json

{ "enabled": true }
```

The response is the normal `ProjectRead` payload. `studio_enabled: true` confirms that review-room endpoints can create submissions, review rounds, and share links.

## Review Room Capabilities

The public review room supports video-first review:

- Smooth signed/proxy asset playback through the existing PR0TA asset delivery path
- Timestamped text comments on the active asset
- Visual annotations on paused frames: **pin**, **region/box**, **drawing/freehand**
- Reviewer display names for public share-link reviewers (no PR0TA account required)
- **Decisions:** `approved`, `approved_with_notes`, `changes_requested`
- Comment and annotation persistence across reloads
- Feedback representable as timeline review markers in the PR0TA UI

Coordinates are normalized to the displayed media frame. Time values use seconds from the beginning of the reviewed asset.

---

## Tool: `submit_assets_for_review`

Creates or reuses studio submissions for the supplied assets, publishes them to a public client review room, creates a share link, and returns the share URL.

### Required Access

The caller must be an authenticated PR0TA project user with a role allowed to use editor-style agent tools. Allowed roles: `editor`, `director`, `producer`, `script_supervisor`.

The MCP server requires `project_id` on every project-scoped tool call. Local stdio clients may provide `access_token` per call or via `PR0TA_MCP_ACCESS_TOKEN`; remote MCP connectors use OAuth bearer flow.

### Arguments

```json
{
  "project_id": "project-id-or-slug",
  "asset_ids": ["asset-123", "asset-456"],
  "title": "Client review - opening sequence",
  "description": "Review the cutdown options.",
  "review_notes": "Please focus on pacing, color, and final frame.",
  "allow_download": false,
  "webhook_url": "https://example.com/pr0ta/review-complete",
  "webhook_secret": "optional-shared-secret"
}
```

Field notes:

- `asset_ids` — required, at least one project asset ID.
- `title`, `description`, `review_notes` — optional reviewer-facing context.
- `allow_download` — defaults to `false`.
- `webhook_url` — optional, must be a public HTTPS URL. PR0TA rejects localhost, private-network, link-local, reserved, multicast, unspecified, and `.internal` hosts.
- `webhook_secret` — optional. Sent in the `X-PR0TA-Webhook-Secret` header on outbound webhook delivery.

### Response

```json
{
  "review_round_id": "round-uuid",
  "share_link_id": "link-uuid",
  "share_token": "public-token",
  "review_url": "https://app.pr0ta.com/review/public-token",
  "submission_ids": ["submission-uuid-a", "submission-uuid-b"],
  "submissions": [
    {
      "id": "submission-uuid-a",
      "asset_id": "asset-123",
      "status": "sent_to_client",
      "client_visible": true
    }
  ],
  "review_round": {
    "id": "round-uuid",
    "title": "Client review - opening sequence",
    "status": "active",
    "share_links": [
      {
        "token": "public-token",
        "allow_comment": true,
        "allow_download": false
      }
    ]
  },
  "webhook": {
    "enabled": true,
    "event": "review_round_completed"
  }
}
```

Store the returned `review_url` for the reviewer and the `submission_ids` for later feedback filtering.

---

## Reviewer Workflow

The reviewer opens `review_url` in a browser. Public share-link reviewers do not need a PR0TA account, but they must provide a display name before creating comments, annotations, or decisions.

Expected reviewer actions:

1. Play or scrub the asset.
2. Pause at the relevant frame.
3. Add a timestamped comment, pin, region, or drawing annotation.
4. Mark the asset approved, approved with notes, or changes requested when their review is complete.

For multi-asset review rooms, PR0TA considers the whole review round complete when every submitted asset has a reviewer decision.

---

## Tool: `get_review_annotations`

Retrieves review feedback visible to the authenticated project user. This includes visual annotations and review events (comments, approval/change-request decisions).

### Arguments

```json
{
  "project_id": "project-id-or-slug",
  "review_round_id": "optional-round-uuid",
  "submission_id": "optional-submission-uuid",
  "resolution_status": "open"
}
```

Field notes:

- `review_round_id` — optional. Use it to retrieve feedback for one review room.
- `submission_id` — optional. Filter feedback to one submitted asset.
- `resolution_status` — optional. Accepted values: `open`, `addressed`, `wont_fix`. Omit to return all states.

### Response

```json
{
  "review_annotations": [
    {
      "id": "annotation-uuid",
      "submission_id": "submission-uuid-a",
      "asset_id": "asset-123",
      "review_round_id": "round-uuid",
      "review_event_id": "event-uuid",
      "annotation_type": "pin",
      "resolution_status": "open",
      "body": "Please trim this beat.",
      "actor_name": "Client Reviewer",
      "author_user_id": null,
      "start_time_seconds": 12.5,
      "end_time_seconds": null,
      "geometry": {
        "x": 0.5,
        "y": 0.25,
        "width": null,
        "height": null
      },
      "metadata": {
        "color": "#7c3aed",
        "tool": "pin"
      },
      "created_at": "2026-04-24T18:00:00+00:00",
      "updated_at": "2026-04-24T18:00:00+00:00"
    }
  ],
  "review_events": [
    {
      "id": "event-uuid",
      "review_round_id": "round-uuid",
      "submission_id": "submission-uuid-a",
      "event_type": "comment",
      "body": "Please trim this beat.",
      "actor_name": "Client Reviewer",
      "actor_user_id": null,
      "metadata": {
        "review_annotation_id": "annotation-uuid"
      },
      "created_at": "2026-04-24T18:00:00+00:00",
      "updated_at": "2026-04-24T18:00:00+00:00"
    }
  ]
}
```

### Event Types

Review events returned by `get_review_annotations`:

- `comment` — timestamped text or annotation-attached comment
- `approved` — reviewer approved the asset
- `approved_with_notes` — approved with caveats
- `changes_requested` — reviewer requests revisions

The internal `published` event is intentionally omitted from this tool response.

---

## Completion Webhook

If `webhook_url` is supplied to `submit_assets_for_review`, PR0TA sends one best-effort POST after every submitted asset in the review round has a reviewer decision.

### Headers

```text
Content-Type: application/json
X-PR0TA-Event: review_round_completed
X-PR0TA-Webhook-Secret: optional-shared-secret
```

### Payload

```json
{
  "event": "review_round_completed",
  "project_id": "project-id",
  "review_round_id": "round-uuid",
  "review_round_title": "Client review - opening sequence",
  "review_event_id": "event-uuid",
  "submission_id": "submission-uuid-b",
  "event_type": "changes_requested",
  "actor_name": "Client Reviewer",
  "body": "Please revise the final shot.",
  "review_complete": true,
  "decided_submission_ids": ["submission-uuid-a", "submission-uuid-b"],
  "pending_submission_ids": [],
  "created_at": "2026-04-24T18:00:00+00:00"
}
```

### Webhook Behavior

- Sent once per review round, only after all submissions have decision events.
- Delivery is best effort — no retry queue currently.
- Delivery validates the callback as a public HTTPS URL and does not follow redirects.
- PR0TA records that the webhook was sent in review-round metadata.
- The `webhook_secret` is redacted from serialized review-round payloads.

**Recommended receiver behavior:** Verify `X-PR0TA-Event` and `X-PR0TA-Webhook-Secret`. Call `get_review_annotations` with the returned `review_round_id`, or use stored `submission_ids` for per-asset filtering. Treat the webhook as a wake-up signal, not as the complete feedback.

---

## Integration Pattern

1. Upload or locate project assets through the normal asset workflow.
2. Call `submit_assets_for_review` with the asset IDs and optional webhook URL.
3. Send `review_url` to the client reviewer.
4. Wait for webhook or poll `get_review_annotations`.
5. Pull annotations and review events.
6. Apply open feedback in the timeline/editor workflow using editorial primitives (see `pr0ta-editorial`, `reference/editorial-primitives.md`).
7. Mark feedback addressed in PR0TA when supported by the reviewing workflow.

---

## Current Limits

- Public reviewers can create comments and visual annotations, but full threaded replies and edit history are not part of this API contract yet.
- Webhook delivery is best effort with no retry queue.
- Importing review feedback into normal timeline markers is intentionally separate from the review overlay workflow.
- API clients should persist `review_round_id`, `share_token`, and `submission_ids` — do not rely on scraping the public review page.
