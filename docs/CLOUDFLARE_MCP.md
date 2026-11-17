# Audio Studio v2.0 preview — Cloudflare MCP + browser

This is a **preview integration**, not a replacement for the Python/FFmpeg production engine. It provides a genuine remote stateless MCP endpoint at `/mcp`, a browser form at `/`, and a health endpoint at `/health`.

## Architecture

- One Cloudflare Worker hosts both MCP tools and static browser assets.
- The browser form selects files **locally**, reads metadata where supported, lets users reorder recordings, preview the timeline and download JSON settings. It does **not** upload audio or render MP3.
- MCP tools are read-only: `start_audio_studio`, `get_audio_studio_defaults`, and `preview_audio_timeline`. No audio bytes are processed or stored by the Worker.
- The existing `scripts/audio_studio.py` remains the separately working Python/FFmpeg rendering engine. A full browser-native mixer is a subsequent development phase.
- MCP tools cannot automatically pop up a new browser tab. The host assistant should provide a clickable link to the browser URL.

## Cloudflare GitHub connection

**Important:** Authorizing Cloudflare access to the GitHub repository is not the same as creating a Worker or deploying this code. Check that a Worker project has been created under Workers & Pages.

1. Review and merge this branch into `main` only after the changes are approved.
2. Cloudflare dashboard → **Workers & Pages → Create application → Import Git repository**. Select `vsbalajee/audiostudio`. If a Worker already exists, use **Worker → Settings → Builds → Connect** and select the same repo.
3. Project root directory: `/` (repository root), build command: `npm install`, deploy command: `npm run deploy`, production branch: `main`.
4. The Worker name in Cloudflare must match `name` in `wrangler.jsonc` (`audio-studio-mcp`). If you previously created a Worker with another name, change the config name before deploying.
5. Select **Free**. You do not need to purchase a domain or share a Cloudflare API token for the integrated GitHub deployment.
6. When deployment succeeds, confirm:
   - `https://<worker-name>.<account-subdomain>.workers.dev/health` returns a JSON status.
   - `https://<worker-name>.<account-subdomain>.workers.dev/` opens the actual Audio Studio browser form.
   - `https://<worker-name>.<account-subdomain>.workers.dev/mcp` is the MCP endpoint, to test with an MCP Inspector over Streamable HTTP. Do not judge MCP connectivity by visiting `/mcp` in an ordinary browser.
7. To connect to ChatGPT, use the custom MCP app/plugin creation workflow **only if your ChatGPT plan and workspace support it**. An Agent Skill ZIP alone cannot automatically install this hosted service.

## Local development

Requires Node.js and npm. At the repository root:

```bash
npm install
npm run typecheck
npm run dev
```

- App: `http://localhost:8787/`
- Health: `http://localhost:8787/health`
- MCP: `http://localhost:8787/mcp`

## Privacy and next steps

The MCP endpoint is currently publicly callable and **does not implement login/OAuth**. Only publish non-sensitive, read-only tools until OAuth and access control are added. Never transmit private voice recordings or credentials through these tools. Add authentication before storing projects, accepting uploads, or exposing user-specific information. Browser-side audio processing, MP3 encoding and comprehensive mixing tests are not implemented in this preview.

## Pre-existing CI issue

On version 1.2.1, the pre-existing GitHub Actions Python tests pass but the packaged skill check fails because `dist/audio-studio-skill.zip` contains a stale `Start_Audio_Studio_Windows.bat`. This is unrelated to Cloudflare and should be fixed by rebuilding and committing the distributed ZIP using `python scripts/build_skill_zip.py`.
