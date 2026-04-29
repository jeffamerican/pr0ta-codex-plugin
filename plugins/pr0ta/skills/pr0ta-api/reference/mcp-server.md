# PR0TA MCP Server & Agent Tools

> **See also:** For review room tools exposed through this MCP surface, read `reference/review-room-api.md`. For the unified generation API, read `reference/unified-generation.md`.

## Overview

The PR0TA Agent Tool system provides a unified tool layer that serves two purposes:

1. **Internal agents** (Editor, Storyboarder, Director, etc.) use Gemini function calling to dynamically query project data on demand.
2. **External tools** (Claude Code, Cursor, ChatGPT, Claude connectors, etc.) connect via an MCP server to query and interact with PR0TA project data.

Both share a single provider-agnostic tool registry — each tool is defined once and consumed everywhere.

---

## Available MCP Tools

### Project-Scoped Tools (require `project_id`)

| Tool | Description | Key Parameters |
|------|-------------|----------------|
| `get_scene_breakdown` | Scene characters, locations, props, action, continuity notes | `scene_number` (required), `scene_range_end` (optional) |
| `get_scene_shotlist` | Director's shot list for a scene | `scene_number` (required) |
| `get_character_references` | Character portrait, voice config, wardrobe, look timeline | `character_name` (required) |
| `get_set_references` | Production design images and notes for a location/scene | `scene_number` (optional), `location` (optional) |
| `get_shot_assets` | Video/audio takes, storyboard frames for a shot | `scene_number` (required), `shot_number` (required) |
| `get_screenplay_text` | Preprocessed screenplay text for specific scene(s) | `scene_number` (optional — omit for full screenplay) |
| `enable_studio_mode` | Enable Studio mode so review-room tools can create submissions, rounds, and share links | (none) |
| `submit_assets_for_review` | Publish assets to a public client review room | `asset_ids` (required); `title`, `description`, `review_notes`, `allow_download`, `webhook_url`, `webhook_secret` (optional) |
| `get_review_annotations` | Retrieve review comments, annotations, and decisions | `review_round_id`, `submission_id`, `resolution_status` (optional) |

### MCP-Only Tools (not available to internal agents)

| Tool | Description | Parameters |
|------|-------------|------------|
| `list_projects` | List all available PR0TA projects | (none) |
| `get_project_metadata` | Project summary: logline, genre, tone, cast, visual approach | `project_id` (required) |

### Role-Tool Access Matrix

Not all roles have access to all tools. The registry enforces access per role.

| Tool | writer | producer | director | casting | script_supervisor | acting_coach | production_designer | stylist | propmaster | storyboarder | cinematographer | editor | story_editor |
|------|--------|----------|----------|---------|-------------------|--------------|---------------------|---------|------------|--------------|-----------------|--------|--------------|
| `get_scene_breakdown` | Y | | Y | | Y | Y | Y | Y | Y | Y | Y | Y | Y |
| `get_scene_shotlist` | | | Y | | | Y | Y | | | Y | Y | Y | |
| `get_character_references` | | | Y | Y | | Y | Y | Y | | Y | | Y | |
| `get_set_references` | | | Y | | | | Y | | | Y | Y | Y | |
| `get_shot_assets` | | | Y | | | | | | | | Y | Y | |
| `get_screenplay_text` | Y | | Y | | Y | Y | | | | | | Y | Y |
| `submit_assets_for_review` | | Y | Y | | Y | | | | | | | Y | |
| `get_review_annotations` | | Y | Y | | Y | | | | | | | Y | |

---

## MCP Server Setup

### Prerequisites

```bash
pip install mcp
```

### Local Transports

**stdio** (Claude Code, Cursor, and other local IDE integrations):

```bash
cd pr0ta_platform/backend
python mcp_server.py
```

**SSE** (legacy remote/testing):

```bash
python mcp_server.py --sse
```

**Streamable HTTP** (local HTTP testing):

```bash
python mcp_server.py --streamable-http
```

### Claude Code Configuration

Add the PR0TA MCP server to `.claude/mcp.json` at the project root:

```json
{
  "mcpServers": {
    "pr0ta": {
      "command": "python",
      "args": ["pr0ta_platform/backend/mcp_server.py"],
      "cwd": "/path/to/script2screen"
    }
  }
}
```

With a virtual environment:

```json
{
  "mcpServers": {
    "pr0ta": {
      "command": "/path/to/script2screen/venv/bin/python",
      "args": ["pr0ta_platform/backend/mcp_server.py"],
      "cwd": "/path/to/script2screen"
    }
  }
}
```

### Cursor Configuration

**Project-level (recommended)** — `.cursor/mcp.json` in the repo root:

```json
{
  "mcpServers": {
    "pr0ta": {
      "command": "python3",
      "args": ["pr0ta_platform/backend/mcp_server.py"],
      "env": { "PYTHONPATH": "." }
    }
  }
}
```

Point `command` at your venv Python if using one. Restart Cursor after changing MCP config.

---

## Remote MCP Connectors (OAuth)

PR0TA exposes a remote MCP surface for ChatGPT and Claude-style connectors.

### Production URLs

- **Streamable HTTP:** `https://app.pr0ta.com/api/mcp/mcp`
- **OAuth metadata:** `https://app.pr0ta.com/api/mcp/.well-known/oauth-authorization-server`
- **Protected resource metadata:** `https://app.pr0ta.com/api/mcp/.well-known/oauth-protected-resource/api/mcp/mcp`

### Auth Model

- Remote connectors authenticate through PR0TA MCP OAuth.
- Users log in with their normal PR0TA account on the consent page.
- Connector tokens are user-scoped and enforce: active account, verified email, admin approval, billing/account lock checks.

### ChatGPT Setup

1. Enable ChatGPT Developer Mode / connectors.
2. Add a custom MCP connector with URL `https://app.pr0ta.com/api/mcp/mcp`.
3. Complete the PR0TA OAuth authorization flow when prompted.

### Claude Setup (Remote)

1. Add a custom MCP connector with URL `https://app.pr0ta.com/api/mcp/mcp`.
2. Complete the PR0TA OAuth authorization flow.

For Claude Code local development, prefer the stdio setup above.

### Local vs Remote Auth

- Local `stdio` clients: use `access_token` tool arguments or `PR0TA_MCP_ACCESS_TOKEN` env var.
- Remote connectors: use MCP OAuth bearer auth, not tool-level `access_token` arguments.

---

## Environment Requirements

The MCP server requires the same environment variables as the main backend:

```bash
GEMINI_KEY=<your-gemini-api-key>    # Required for internal agent tools
DATABASE_URL=<your-database-url>    # Required for project listing
```

---

## Internal Agent Integration

When tools are enabled for a role, the agent chat function:

1. Builds a slim context (project summary, scene index, character names) instead of the full context blob.
2. Converts tool definitions to Gemini `FunctionDeclaration` protos via the adapter.
3. Runs a multi-round function-calling loop (up to 5 rounds) until the model returns a text response.
4. Parses the final text response as JSON.

### Enabling/Disabling Tools

Tools are enabled by default for all core roles. Override per-project via `crew_config.json`:

```json
{
  "agent_tools": {
    "enabled": false,
    "roles_with_tools": []
  }
}
```

When `agent_tools.enabled` is `false`, the system falls back to the existing full context blob flow with zero behavioral change.

---

## Adding New Tools

1. **Define** — Add a `ToolDefinition` entry to `TOOL_CATALOG` in `registry.py` with `allowed_roles`.
2. **Implement** — Add a handler function in `implementations.py` and register it in `TOOL_HANDLERS`.
3. **Done** — The new tool is automatically available to internal agents (via `get_tools_for_role()`) and MCP clients (via `register_tools()` in the MCP bridge). No changes needed in the MCP server, agent chat service, or adapters.

---

## Troubleshooting

- **MCP server won't start:** Check Python path, install `mcp` SDK, verify `.env` for database and API keys.
- **Tools return empty results:** Verify `project_id` via `list_projects`. Check that the Producer/Director/Script Supervisor reads have been run — tools wrap existing services.
- **Function calling not working (internal agents):** Verify `agent_tools.enabled` is `true` and the role is in `roles_with_tools`. Only Gemini is supported for function calling. Use `gemini-3-flash-preview` or `gemini-3.1-pro-preview`.
- **MCP tool calls failing:** All MCP tools except `list_projects` require `project_id`. Internal tools get this from execution context; MCP tools need it explicitly.
