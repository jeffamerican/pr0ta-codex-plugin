#!/usr/bin/env python3
"""
PR0TA Minimal Python Client (Copy-Paste Ready)
===============================================

Use this as the starting point for any Python-based PR0TA automation. It
bakes in the Cloudflare-safe download path (curl via subprocess — urllib
is 403'd by Cloudflare's bot fingerprint), the PAT bearer pattern, the
structured validation-error contract for unified v2 (with a defensive
task_id=None fallback for legacy/internal paths), and a polling helper.

Every gotcha in the skill pack that costs debug time is handled here on
the first copy-paste.

Five core functions:
  - upload_images()       — multipart image upload into a project
  - submit_generation()   — unified /generate with structured error handling
  - poll_task()           — project-scoped polling with async provider errors
  - download_asset()      — Cloudflare-safe curl download
  - list_assets()         — paginated asset listing

Environment setup:
  pip install requests
  export PR0TA_PAT="pat_xxxxxxxxxxxxx"
  export PR0TA_PROJECT_ID="your-project-uuid"
  python pr0ta_client.py

What this client deliberately does NOT do:
  - No retry loop on validation errors. Fix the payload instead.
  - No urllib / urlretrieve. Cloudflare will 403 it.
  - No silent fallback to api.pr0ta.com. Stick to app.pr0ta.com.
  - No implicit rate limiting. Poll interval is 2s; per-minute limits
    apply by tier (FREE 50, CREATOR 100, PRO 200, ENTERPRISE 500).

Extend per-project with domain helpers (cue sheet loaders, assets.json
writers, post-production timeline helpers) but keep the five core
functions as the reliable backbone.
"""

import json
import os
import subprocess
import time
from pathlib import Path
from typing import Any

import requests  # pip install requests

BASE_URL = "https://app.pr0ta.com"
PAT = os.environ["PR0TA_PAT"]  # pat_xxxxxxxxxxxxx
HEADERS = {"Authorization": f"Bearer {PAT}", "Content-Type": "application/json"}


class PR0TAError(RuntimeError):
    pass


def submit_generation(project_id: str, payload: dict[str, Any]) -> str:
    """Submit a unified /generate payload and return a validated task_id.

    Handles both the unified v2 structured validation-error contract
    (``{"detail": {"error_code": "validation_error", "reason": ...}}``, the
    primary contract as of April 2026) and the legacy ``task_id=None``
    shape that may still surface from internal/lower-level service paths.

    See pr0ta-video -> "Per-Model Duration Constraints" and
    "Validation Errors Are Now Structured" for common causes (discrete
    duration values, aspect ratio, forbidden reference fields, etc.).
    """
    url = f"{BASE_URL}/api/v2/projects/{project_id}/generate"
    r = requests.post(url, headers=HEADERS, json=payload, timeout=30)
    # Don't raise_for_status yet — 4xx bodies carry the structured error.
    body = r.json() if r.content else {}
    # Primary contract: structured validation error on unified v2.
    detail = body.get("detail") if isinstance(body, dict) else None
    if isinstance(detail, dict) and detail.get("error_code"):
        raise PR0TAError(
            f"Validation error ({detail.get('error_code')}): {detail.get('reason')}\n"
            f"Payload: {json.dumps(payload, indent=2)}"
        )
    r.raise_for_status()
    task_id = body.get("task_id")
    if not task_id:
        # Legacy fallback: internal/lower-level paths may still return this shape.
        raise PR0TAError(
            f"Generation rejected (no task_id and no structured error). "
            f"Check model/duration/aspect_ratio/refs against pr0ta-video skill.\n"
            f"Payload: {json.dumps(payload, indent=2)}\n"
            f"Response: {json.dumps(body, indent=2)}"
        )
    return task_id


def poll_task(project_id: str, task_id: str, *, timeout_s: int = 600, interval_s: float = 2.0) -> dict[str, Any]:
    """Poll a task until it reaches a terminal state (completed / failed).

    Uses the project-scoped route (preferred). On terminal failure,
    surfaces ``error``, ``error_reason``, and ``error_detail`` so the
    caller can distinguish retryable provider timeouts from fatal
    issues like insufficient provider credits.
    """
    url = f"{BASE_URL}/api/v2/projects/{project_id}/tasks/{task_id}"
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        r = requests.get(url, headers=HEADERS, timeout=30)
        r.raise_for_status()
        task = r.json()
        status = task.get("status")
        if status in {"completed", "succeeded", "failed", "error", "cancelled", "canceled"}:
            if status in {"failed", "error"}:
                detail = task.get("error_detail") or {}
                reason = task.get("error_reason", "unknown")
                msg = task.get("error", "No error message")
                raise PR0TAError(
                    f"Task {task_id} failed ({reason}): {msg}\n"
                    f"error_detail: {json.dumps(detail, indent=2)}"
                )
            return task
        time.sleep(interval_s)
    raise PR0TAError(f"Task {task_id} did not complete within {timeout_s}s")


def download_asset(project_id: str, asset_id: str, out_path: Path) -> Path:
    """Download an asset via ``curl`` subprocess.

    IMPORTANT: Do NOT use urllib / urlretrieve here. PR0TA asset URLs sit
    behind Cloudflare, which 403s Python's default user-agent. ``requests``
    works sometimes. ``curl``'s default user-agent works every time. This
    is the single most common "why does my Python download fail" cause
    across the skill pack.
    """
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    url = f"{BASE_URL}/api/v2/projects/{project_id}/assets/{asset_id}/download"
    cmd = [
        "curl", "-sSL", "--fail",
        "-H", f"Authorization: Bearer {PAT}",
        "-o", str(out_path),
        url,
    ]
    subprocess.run(cmd, check=True)
    if out_path.stat().st_size == 0:
        raise PR0TAError(f"0-byte download for asset {asset_id}")
    return out_path


def upload_images(
    project_id: str,
    paths: list[str | Path],
    *,
    category: str = "imported",
    subject: str | None = None,
    labels: dict[str, str] | None = None,
) -> list[dict[str, Any]]:
    """Upload one or more local images into a PR0TA project.

    Returns the list of created AssetRead objects. Each asset's ``id``
    can be used immediately in generation payloads (e.g.
    ``start_image_asset_id``, Element/Character source images, or
    ``ref_to_img`` references).
    """
    url = f"{BASE_URL}/api/v2/projects/{project_id}/assets/upload"
    files = [("files", (Path(p).name, open(p, "rb"))) for p in paths]
    data: dict[str, str] = {"category": category}
    if subject:
        data["subject"] = subject
    if labels:
        data["labels"] = json.dumps(labels)
    # Multipart — do not send Content-Type: application/json.
    r = requests.post(
        url, headers={"Authorization": f"Bearer {PAT}"}, files=files, data=data, timeout=60,
    )
    r.raise_for_status()
    body = r.json()
    return body.get("assets", [])


def list_assets(project_id: str, *, kind: str | None = None) -> list[dict[str, Any]]:
    """List all assets in a project, iterating the canonical offset/next_offset pagination."""
    url = f"{BASE_URL}/api/v2/projects/{project_id}/assets"
    params: dict[str, Any] = {"limit": 100}
    if kind:
        params["kind"] = kind
    out: list[dict[str, Any]] = []
    offset = 0
    while True:
        params["offset"] = offset
        r = requests.get(url, headers=HEADERS, params=params, timeout=30)
        r.raise_for_status()
        body = r.json()
        out.extend(body.get("assets", []))
        next_offset = body.get("next_offset")
        if next_offset is None:
            return out
        offset = next_offset


# --- Example: fan-out and pick (see pr0ta-image skill) ---
# NOTE: PR0TA also exposes a first-class batch route —
#   POST /api/v2/projects/{id}/generate/batch  (max 10 items per request,
#   up-front validation, item-by-item submission, partial-success reporting).
# The loop below is the simpler "independent submits" pattern; use the
# batch route when you want one request that carries many payloads.
if __name__ == "__main__":
    project_id = os.environ["PR0TA_PROJECT_ID"]

    prompt = """The poster text must read EXACTLY the following:
Line 1 (small white caps): EXAMPLE HEADER
Line 2 (HUGE bold amber-gold): EXAMPLE TITLE
Flat vector poster on deep navy. No other text. 9:16."""

    tasks: dict[str, str] = {}
    for model in ("nano_banana_2", "gpt_image_1_5", "ideogram"):
        try:
            tasks[model] = submit_generation(project_id, {
                "generator": "image",
                "mode": "txt_to_img",
                "model": model,
                "prompt": prompt,
                "aspect_ratio": "9:16",
            })
        except PR0TAError as e:
            print(f"[WARN] {model}: {e}")

    for model, task_id in tasks.items():
        task = poll_task(project_id, task_id)
        asset_id = (task.get("result_refs") or {}).get("asset_id")
        if asset_id:
            download_asset(project_id, asset_id, Path(f"out/{model}.png"))
