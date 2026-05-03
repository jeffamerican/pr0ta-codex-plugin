# PR0TA Codex Plugin

Codex plugin for PR0TA creative production workflows. It packages 12 PR0TA skills plus the PR0TA remote MCP connector so Codex can generate images, videos, voiceovers, music, and sound effects, then assemble, review, download, and refine PR0TA timelines.

## What's Included

- Bundled MCP connector: `https://app.pr0ta.com/api/mcp/mcp`
- `pr0ta` -- production hub and workflow orchestration.
- `pr0ta-api` -- API auth, `/generate`, tasks, assets, review rooms, MCP, and client references.
- `pr0ta-video` -- Seedance, Kling, multi-shot continuity, camera control, and reference video.
- `pr0ta-image` -- image generation, edits, references, title cards, and key frames.
- `pr0ta-audio` -- voice generation, cloning, STS, transcription, and time indexing.
- `pr0ta-music` -- music and sound effect generation.
- `pr0ta-consistency` -- character consistency bundles, Kling Elements, and Seedance Characters.
- `pr0ta-prompting` -- production-grade prompt patterns and model-specific guidance.
- `pr0ta-sync` -- cue sheets, narration-first or visual-first planning, and sync strategy.
- `pr0ta-timeline` -- timeline assembly, clips, tracks, preview, render, and analysis.
- `pr0ta-editorial` -- review discipline and final-cut verification.
- `pr0ta-downloading` -- reliable asset download and export patterns.

## Install From GitHub

Add this repository as a Codex plugin marketplace:

```text
/plugin marketplace add jeffamerican/pr0ta-codex-plugin
```

Then install the PR0TA plugin:

```text
/plugin install pr0ta@pr0ta-codex
```

Restart or reload Codex after installing so the skills and bundled MCP connector are discovered.

The plugin declares the PR0TA MCP server in `plugins/pr0ta/.mcp.json`. Codex should load it with the plugin; users still authorize PR0TA through the normal remote MCP/OAuth flow when the client asks.

If PR0TA tools do not appear in Codex yet, connect the MCP server explicitly:

```bash
codex mcp login pr0ta --scopes mcp
```

Codex should open, or print, a PR0TA authorization URL. Complete that login in the browser, then start a new Codex session and check for `list_projects`. Tool discovery will not expose PR0TA tools until the MCP connector is authenticated.

## Local Development Install

Clone this repository:

```bash
git clone https://github.com/jeffamerican/pr0ta-codex-plugin.git ~/plugins/pr0ta-codex-plugin
```

For a home-local install, copy or sync the plugin folder:

```bash
mkdir -p ~/plugins ~/.agents/plugins
rsync -a ~/plugins/pr0ta-codex-plugin/plugins/pr0ta/ ~/plugins/pr0ta/
```

Then make sure `~/.agents/plugins/marketplace.json` contains:

```json
{
  "name": "local",
  "interface": {
    "displayName": "Local Plugins"
  },
  "plugins": [
    {
      "name": "pr0ta",
      "source": {
        "source": "local",
        "path": "./plugins/pr0ta"
      },
      "policy": {
        "installation": "AVAILABLE",
        "authentication": "ON_INSTALL"
      },
      "category": "Productivity"
    }
  ]
}
```

## PR0TA Setup

1. Sign in or create an account at [app.pr0ta.com](https://app.pr0ta.com).
2. Prefer the bundled PR0TA MCP connector for agent workflows. If Codex does not prompt automatically, run `codex mcp login pr0ta --scopes mcp`.
3. For REST fallback or local stdio workflows, open PR0TA Application Settings, then API Keys.
4. Create a Personal Access Token and copy it immediately.
5. Provide the token to Codex for REST fallback workflows, or export it in your shell:

```bash
export PR0TA_PAT=pat_xxxxxxxxxxxxxxxx
```

Do not commit PATs, OAuth tokens, `.env` files, project data, or local credentials.

## Repository Layout

```text
.agents/plugins/marketplace.json
plugins/pr0ta/.codex-plugin/plugin.json
plugins/pr0ta/.mcp.json
plugins/pr0ta/skills/pr0ta/SKILL.md
plugins/pr0ta/skills/pr0ta-api/SKILL.md
plugins/pr0ta/skills/pr0ta-video/SKILL.md
...
```

## Updating

After a new release, refresh the marketplace and update the plugin:

```text
/plugin marketplace update pr0ta-codex
/plugin update pr0ta@pr0ta-codex
```

## License

MIT
