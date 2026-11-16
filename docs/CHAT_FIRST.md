# Chat-first Audio Studio — Quick Start

This is the **default** experience when an assistant with access to `SKILL.md` is asked to **Start Audio Studio**. It is designed for short interactions on ChatGPT, Claude, Gemini CLI and other capable AI environments.

## First interaction when the ZIP is read

When the AI host *actually reads* the uploaded Audio Studio skill and the user has not started editing, it should display **only the eight-line welcome** stored in [`forms/welcome-message.md`](../forms/welcome-message.md). This short introduction tells users what the project does and ends with **Type “Start Audio Studio” to begin.** Do not repeat it after activation, and do not claim the skill can force a message from a chat application that did not read the attachment.

## Three stages, not an intimidating questionnaire

**1. Gather audio.** Request voice attachments (individual files or one ZIP) and optional instrumental music. Honor all settings already in the conversation. Ask no questions whose answers are already present. If a native form is available, display a compact control group; otherwise use ordinary chat. The assistant must not draw a deceptive upload button when it cannot accept files.

**2. Review the timeline.** Once files are actually accessible, inspect audio streams and durations with tools; show the voice order, gaps, optional music-only outro, and music mute rules. Use numeric ordering where requested. Explain any conflict or unsupported instruction. Ask for approval **before the first render**.

**3. Process and deliver.** Only if Python/FFmpeg and source bytes are available, run the engine and check the output files. Share the finished MP3 and optional editable WAV stems and JSON report. If the runtime lacks FFmpeg or file access, stop and say so clearly; explain how to use the included local desktop form instead.

## Example: starting without audio files

**User:** Start Audio Studio.

**Assistant:**

> **Audio Studio is ready.** Please attach your voice recordings (individual audio files or a ZIP). You can also attach background music, or choose no music. I'll check the file sequence and show the editing timeline before processing.

Avoid a long checklist or instructions to install Python at the welcome stage.

## Example: user already specifies a configuration

**User:** Start Audio Studio. Project: My Audio Project. Gap: 3 seconds. Music: quiet. Gentle noise reduction: true. Normalize voice: true. Mute music during final recording: false.

**Assistant:**

> **Audio Studio is ready.** I've set *My Audio Project*: 3-second gaps, quiet music, gentle low-rumble cleanup and voice balancing. Music is **allowed during the final voice**. Please attach your voice recordings and optional instrumental. I'll inspect them and show the proposed timeline before rendering.

**Critical:** Explicit `mute_music_during_final_voice: false` overrides the default `true`. The value `gap: 3 seconds` applies to *all* recording boundaries unless the user separately specifies an intro gap.

## Example: timeline only after validating source files

> **Timeline to approve:** `0.mp4 (12.4 s) → 3 s → 1.mp4 (31.0 s) → 3 s → 2.mp4 (27.5 s)`. Background music: quiet during narration and raised during gaps. Final voice music: **on**. Outro: 5 s, music only. **These durations are examples, not measured data.**

Never use these sample timings as facts about a user's uploaded recordings.

## Fields and execution mapping

The small user-facing options are described in [`forms/chat-form.md`](../forms/chat-form.md). To avoid inconsistent model interpretations, the optional standard-library bridge [`scripts/chat_bridge.py`](../scripts/chat_bridge.py) converts `examples/chat-session.example.json` into the full engine JSON:

```bash
python scripts/chat_bridge.py --config chat-session.json --output project.json
python scripts/audio_studio.py validate --config project.json
# Only after the user approves the proposed timeline:
python scripts/audio_studio.py render --config project.json
```

Use actual local file paths, not fictional or unmounted chat URLs. Rendering requires FFmpeg/FFprobe. The bridge maps `gentle_noise_reduction` to a simple low-frequency rumble filter; it does **not** guarantee removal of all background noise.

## What this does NOT guarantee

- Native custom forms or file-upload widgets in every LLM chat.
- Automatic activation when the skill has merely been attached without being installed or read.
- Execution of the Python engine without a suitable environment.
- Musical taste assessment, emotional listening, speech transcription, or editor-native Movavi project generation.

These constraints are intentional; this project prioritizes an honest, predictable workflow.
