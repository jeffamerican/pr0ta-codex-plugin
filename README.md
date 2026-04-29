# PR0TA Codex Plugin

Codex plugin for PR0TA creative production workflows. It packages 12 PR0TA skills that help Codex generate images, videos, voiceovers, music, and sound effects, then assemble, review, download, and refine PR0TA timelines.

## What's Included

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

Restart or reload Codex after installing so the skills are discovered.

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
2. Open PR0TA Application Settings, then API Keys.
3. Create a Personal Access Token and copy it immediately.
4. Provide the token to Codex for API workflows, or export it in your shell:

```bash
export PR0TA_PAT=pat_xxxxxxxxxxxxxxxx
```

Do not commit PATs, OAuth tokens, `.env` files, project data, or local credentials.

## Repository Layout

```text
.agents/plugins/marketplace.json
plugins/pr0ta/.codex-plugin/plugin.json
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
