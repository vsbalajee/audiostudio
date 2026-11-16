# Changelog

## 1.2.1 — 2026-11-16

- Added a single canonical **exactly eight-line** first-read welcome with project overview and the **Start Audio Studio** prompt.
- On the first readable skill ZIP attachment, compatible assistants are instructed to show the welcome before setup; already-started workflows skip it.
- Updated instructions, platform guidance, and tests; no claim that a ZIP can force an automatic response from an unsupported chat interface.

## 1.2.0 — 2026-11-16

- Introduced a **chat-first** default activation: “Start Audio Studio” now asks only for missing media and reuses all explicit user settings.
- Added compact chat form and quick-start examples with honest platform capability boundaries.
- Added a tested standard-library `chat_bridge.py` that maps short user choices into full engine settings, including correct handling of `mute_music_during_final_voice: false` and a single gap value applied to every clip boundary.
- Added chat-session example, regression tests, and updated portable skill ZIP.
- Kept the desktop editor and underlying FFmpeg mixing workflow unchanged.


## 1.1.0 — 2026-11-14

- Prepared public open-source repository with installation guides, security information, contributions, GitHub Actions and Dependabot.
- Added reproducible, separately packaged Agent Skill ZIP for compatible AI clients.
- Added multi-clip regression tests and stricter JSON configuration validation.
- Corrected ZIP-import ordering: voice files now follow numeric filenames rather than ZIP entry order.
- Protected temporary ZIP sources when closing a form during rendering.
- Improved output-name collision handling and retained non-destructive defaults.

## 1.0.0 — 2026-11-14

- Initial offline audio engine and five-step Tkinter form.
- Voice sequencing, configurable gaps, gentle leveling, optional cleanup and background music automation.
- 320 kbps MP3 output, optional synchronized WAV stems and JSON processing report.
