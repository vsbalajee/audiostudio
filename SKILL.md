---
name: audio-studio
description: Start Audio Studio through a simple chat-first setup; collect voice recordings and optional music, review clip order and gaps, then clean, mix and export MP3 with local FFmpeg when tools are available. Use for podcasts, poetry, speeches, narration, audiobooks, ads and tributes. Ask only for missing attachments; do not force a desktop form into chat or claim to hear emotional performance.
license: MIT
compatibility: Python 3.10+ with FFmpeg and FFprobe for rendering. Tkinter desktop GUI is optional and requires a graphical environment. AI chat hosts need file access and execution tools.
metadata:
  author: vsbalajee
  version: "1.2.0"
---

# Audio Studio — Chat-First Audio Production Skill

## 1. Activation: **Start Audio Studio**

**This is the default entry point.** When the user says **“Start Audio Studio”**, asks to use the skill, or uploads this ZIP and requests audio editing, begin with a friendly **chat-first workflow**, not installation instructions. Read [`forms/chat-form.md`](forms/chat-form.md) for the concise interface and [`docs/CHAT_FIRST.md`](docs/CHAT_FIRST.md) for examples.

- **Ask only for missing** voice recordings and optional background instrumental. Accept individual media files, a ZIP, or a folder/link **only if** the host can actually read it. Never invent file-picker controls or pretend a link is downloaded.
- **Preserve explicit choices** from the current chat: name, voice order, music level, gap length, noise cleanup, normalization, intro/outro behavior and music-mute rules. In particular, `mute_music_during_final_voice: false` means music is **allowed**, overriding the default `true`.
- **Brief welcome when files are absent:** “**Audio Studio is ready.** Please attach your voice recordings (individual files or a ZIP). You can optionally add background music. I’ll inspect the files, show the proposed timeline, and ask for approval before processing.” If preferences were already given, summarize them in a single sentence; do not ask again.
- If attachments are already provided, skip the welcome/upload request; validate the available sources and continue to timeline review.
- If the chat host supports a genuine native form, it may present a compact form based on `forms/chat-form.md`. Otherwise **use ordinary conversation**. Do not launch Tkinter into a headless chat or promise that a graphical form will automatically open on every LLM platform.
- **Do not process yet.** First inspect real filenames and audio durations, show order, gaps, music placement and exclusions, and request user approval of the proposed timeline. Never invent timings.

## 2. After uploads: confirm the actual timeline

1. Resolve user attachments to actual readable files; a URL by itself is not evidence of access. Verify with available tools (`ffprobe` for audio streams and lengths when executable).
2. Use supplied ordering, or numerical filename order if user requests it. Confirm any ambiguities instead of guessing.
3. Apply a user-specified **“3 seconds between clips”** to *every* recording boundary, including after the first voice clip, **unless an explicit different introduction gap is supplied**. The desktop legacy defaults are 5 seconds after voice 0 and 3 seconds between later clips when no global gap is given.
4. Show a concise timeline (voice filenames, measured durations, gap lengths) and whether music plays under the first/final voice; note optional music-only outro (default 5 seconds when music is provided).
5. Clarify only real conflicts or unsupported requests, then ask for approval before first render.

## 3. Processing with the executable engine

- **Prerequisites:** actual voice/audio bytes, Python 3.10+, FFmpeg and FFprobe in PATH, and permission to write output files. Check prerequisites. The skill instructions alone do not install FFmpeg or provide source recordings.
- For simple chat selections use [`scripts/chat_bridge.py`](scripts/chat_bridge.py) to map the compact chat setup onto actual engine keys, preventing silent changes to explicitly provided values. See [`examples/chat-session.example.json`](examples/chat-session.example.json). The bridge requires real resolved paths; it does not access unsupported remote URLs.
- Validate the resulting `project.json` **before** rendering:

```bash
python scripts/chat_bridge.py --config chat-session.json --output project.json
python scripts/audio_studio.py validate --config project.json
# Only after timeline approval:
python scripts/audio_studio.py render --config project.json
```

- An alternative is to populate the documented full engine config directly (see `examples/project.example.json`) and call its `validate` and `render` actions.
- After rendering, inspect the actual output files and JSON report. Share real files only after verifying they exist and any claimed measurements were made. Ask the user to judge the artistic result by listening.
- **If audio processing cannot execute in the current chat, say so frankly**, and offer the standalone desktop option: extract the ZIP, install Python/Tkinter and FFmpeg as needed, run `python scripts/form.py` or the Windows/Mac/Linux launcher. Don't pretend processing happened in the host.

## 4. What the audio engine actually supports

- Ordered FFmpeg-readable MP3/WAV/M4A/MP4 and other supported recordings; one optional music source.
- Gentle recording-level gain balancing (capped at ±7 dB), optional 70 Hz high-pass rumble removal, optional FFT denoising **with artifact risk**, optional conservative edge trimming (off by default).
- Exact configured gaps, short anti-click voice fades, quiet music under enabled sections, stronger music during gaps, a possible music-only outro, and a music-free final voice when requested.
- Output 320 kbps stereo MP3 at 48 kHz, JSON report, optional synchronized independent WAV stems. A standard MP3 is *not* a multitrack editable file.
- No transcription, professional emotional listening, unlicensed music generation, or native Movavi `.mepx` output.

### Compact chat field → full engine setting

| Short chat setting | Actual engine setting |
| --- | --- |
| `project_name` | `project_name` |
| `voice_files` or `voice_folder` | Existing ordered local paths / sorted folder |
| `music_file` | Existing music path, or `""` for no music |
| `gap_seconds` | Both `after_intro_seconds` and `between_seconds` |
| `after_intro_seconds`, `between_seconds`, `outro_seconds` | Specific overrides where provided |
| `music_level` | Very quiet: -32 dB, Quiet: -25 dB, Balanced: -20 dB, More prominent: -16 dB beneath voice (gap levels adjusted separately) |
| `gentle_noise_reduction` | `gentle_cleanup` (low-rumble high-pass; **not** full denoising) |
| `normalize_voice` | `normalize_voice` |
| `mute_music_during_final_voice` | Exactly the Boolean supplied, including `false` |
| `additional_instructions` | **Unexecuted notes** for review only |

More advanced supported engine values are listed in `forms/form.schema.json`. Unknown options must not be silently ignored; inform the user what is unsupported.

## 5. Capability boundaries and non-negotiable safety

- **Never claim to have heard** a user's emotional performance, recognized artistic quality, or chosen the perfect score by listening unless a genuine listening capability was used.
- **Never claim to have downloaded, processed or uploaded** audio without successfully accessing and processing the actual bytes.
- Technical waveform/loudness measurements do not prove emotional interpretation or acceptable artistic results.
- Preserve original source files, spoken words, intentional pauses, pitch and rate; do not add music or sound effects without authorization.
- The `additional_instructions` text box **does not drive edits automatically**. Before rendering, explicitly map any supported extra requests into settings and flag anything unimplemented. Never quietly mark free-text instructions completed.
- Work non-destructively, do not publish private voice or music files, and respect music licensing.
- Do not imply that a generic skill ZIP creates a cross-platform native upload form. An assistant may render native controls only when its platform supports them.

## 6. Development, distribution and verification

- The package includes a portable `audio-studio/SKILL.md`, FFmpeg engine, local Tkinter form, and a compact chat setup. Installable ZIP: `dist/audio-studio-skill.zip`. GitHub source ZIP is the full repository and has a different layout.
- Run `python -m unittest discover -s tests -p 'test*.py' -v`, `python scripts/build_skill_zip.py`, then `python scripts/build_skill_zip.py --check` when changing files included in the distributed ZIP.
- Platform-specific instructions: `docs/COMPATIBILITY.md`; workflow examples: `docs/CHAT_FIRST.md`; application README: `README.md`.
