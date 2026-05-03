#!/usr/bin/env sh
set -eu

if ! command -v codex >/dev/null 2>&1; then
  echo "Codex CLI was not found on PATH." >&2
  echo "Open Codex and connect the PR0TA MCP server from the plugin UI, or install the Codex CLI and retry." >&2
  exit 127
fi

echo "Starting PR0TA MCP OAuth login..."
echo "If the browser does not open automatically, copy the printed authorization URL into your browser."
exec codex mcp login pr0ta --scopes mcp
