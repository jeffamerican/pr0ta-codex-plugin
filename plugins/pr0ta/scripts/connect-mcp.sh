#!/usr/bin/env sh
set -eu

MCP_NAME="${PR0TA_MCP_NAME:-pr0ta}"
MCP_URL="${PR0TA_MCP_URL:-https://app.pr0ta.com/api/mcp/mcp}"

if ! command -v codex >/dev/null 2>&1; then
  echo "Codex CLI was not found on PATH." >&2
  echo "Open Codex and connect the PR0TA MCP server from the plugin UI, or install the Codex CLI and retry." >&2
  exit 127
fi

if ! codex mcp get "$MCP_NAME" >/dev/null 2>&1; then
  echo "PR0TA MCP server is not registered in Codex. Adding $MCP_URL ..."
  codex mcp add "$MCP_NAME" --url "$MCP_URL"
fi

echo "Starting PR0TA MCP OAuth login..."
echo "If the browser does not open automatically, copy the printed authorization URL into your browser."
set +e
LOGIN_OUTPUT="$(codex mcp login "$MCP_NAME" --scopes mcp 2>&1)"
LOGIN_STATUS=$?
set -e

printf '%s\n' "$LOGIN_OUTPUT"
if [ "$LOGIN_STATUS" -eq 0 ]; then
  exit 0
fi

if printf '%s\n' "$LOGIN_OUTPUT" | grep -qi "No authorization support detected"; then
  echo "" >&2
  echo "Codex could not detect PR0TA OAuth support from the MCP endpoint." >&2
  if command -v curl >/dev/null 2>&1 && curl -fsSL "https://app.pr0ta.com/.well-known/oauth-authorization-server/api/mcp/mcp" | grep -q '"none"'; then
    echo "The live PR0TA endpoint advertises public PKCE OAuth correctly." >&2
    echo "This Codex CLI build may not run OAuth for plugin-provided MCP entries." >&2
    echo "Use the Codex plugin/app install-auth flow, then start a fresh Codex session and retry tool discovery." >&2
  else
    echo "Verify that $MCP_URL returns a WWW-Authenticate resource_metadata value and that the authorization metadata advertises token_endpoint_auth_methods_supported including 'none'." >&2
    echo "After the server fix is deployed, rerun this script and restart Codex so the PR0TA tools can load." >&2
  fi
fi

exit "$LOGIN_STATUS"
