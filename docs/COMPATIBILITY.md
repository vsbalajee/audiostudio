# Use Audio Studio with ChatGPT, Claude, Gemini and other AI assistants

**As of November 2026.** The skill now starts with a short conversational setup when invoked in a compatible host. Agent Skills use a portable `SKILL.md` format, but LLM product interfaces are not interchangeable. **Installing skill instructions does not magically install FFmpeg, provide your voice files, or open the Tkinter form inside a chat.**

## First-read welcome (eight lines)

When the AI assistant can read the skill ZIP and the user has not begun a project, it is instructed to present an exact **eight-line welcome** from [`forms/welcome-message.md`](../forms/welcome-message.md), ending with **Type “Start Audio Studio” to begin.** If a platform does nothing when a ZIP is simply attached, prompt it with: **“Read the attached Audio Studio ZIP and follow SKILL.md.”** Uploading a ZIP does **not** guarantee a response without a user message, because attachment behavior differs across products.

## Chat-first activation

After installing/attaching a skill where supported, tell the AI **“Start Audio Studio.”** It should request missing voice/music attachments, remember explicit preferences, show an actual validated timeline and request approval before generating an MP3. It cannot force a native file-upload form into a platform that does not support one. [Step-by-step examples](CHAT_FIRST.md).

## Download the right file

- **Installable AI skill:** [`dist/audio-studio-skill.zip`](../dist/audio-studio-skill.zip). It contains one folder named `audio-studio/` with `SKILL.md` and the engine.
- **Complete repository source:** select **Code → Download ZIP** on GitHub. It also includes the development tests, contribution docs, and CI configuration.

## ChatGPT

In a ChatGPT environment with skill upload/import, attach the installable ZIP in the supported skill workflow. Alternatively, upload it as a file to a chat and ask the assistant to inspect `SKILL.md`. Whether the assistant can **execute** Python/FFmpeg and access folders or connected storage depends on your product, plan, enabled tools and current session.

**Example prompt:** “Start Audio Studio. Ask me for the missing audio attachments, preserve my settings and show the proposed timeline before rendering. Use Python/FFmpeg only when available; otherwise explain the local desktop option.”

## Claude / Claude Code

Claude supports user-uploaded skill ZIPs in eligible offerings with code execution. In Claude.ai, follow **Customize → Skills → Upload a skill**, where available. For Claude Code, place the `audio-studio` folder under `~/.claude/skills/` or a supported project skill location. Verify that the execution environment includes FFmpeg before attempting a render.

## Gemini / Gemini CLI

**Gemini CLI** supports the Agent Skills format. One documented installation command is:

```bash
gemini skills install https://github.com/vsbalajee/audiostudio.git
```

Alternatively extract the installable ZIP to `~/.gemini/skills/audio-studio/` and check `/skills list` in Gemini CLI. These **CLI** instructions do not guarantee that the Gemini consumer web chat accepts a ZIP as a native executable skill.

## Other LLMs

If the assistant can read attached files, provide `SKILL.md` and ask it to follow the documented workflow. If it cannot run local Python or FFmpeg, the skill can only **guide** you, not render the audio. Run `python scripts/form.py` locally instead.

## Privacy and permissions

Review any skill code before enabling execution. Local processing is preferred for private recordings. Do not grant cloud or account permissions solely to produce a local MP3.

## Current reliable references

- Open Agent Skills specification: https://agentskills.io/specification
- Claude custom skills: https://support.claude.com/en/articles/12512198-how-to-create-custom-skills
- Gemini CLI agent skills: https://github.com/google-gemini/gemini-cli/blob/main/docs/cli/skills.md
- FFmpeg: https://ffmpeg.org/

We intentionally avoid promises of universal one-click installation or automatic audio playback analysis.
