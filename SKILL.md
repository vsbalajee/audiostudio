---
name: audio-studio
description: Mix, sequence, clean and balance voice recordings with music using local FFmpeg. Use for narrated poetry, podcasts, speeches, audiobooks, ads, tributes and voice-over production. Includes a five-step desktop form, exact gaps, final voice-only sections, WAV stems, MP3 output and processing reports. Never claim to have listened or judged emotions without actually doing so.
license: MIT
compatibility: Python 3.10+ with FFmpeg and FFprobe. Desktop form also requires Tkinter and a graphical environment. AI hosts must provide file access and executable tools to run audio rendering.
metadata:
  author: vsbalajee
  version: "1.1.0"
---

# Audio Studio — Portable Audio-Mixing Skill

Use this skill when the user wants technical audio production: order recordings, adjust volumes, add pauses, remove modest noise, duck/loop background music, make an outro, or export a finished MP3.

## Important capability boundaries

- **Can do:** Use FFmpeg to inspect, convert, sequence, gently process, mix, fade, and export recordings. Check durations, gap timings, signal levels and music-free regions. Create a reproducible JSON report.
- **Cannot assert without actual listening:** How moving the narration is, whether pronunciation is excellent, which music is emotionally best, or whether a transition sounds perfectly natural. Signal processing is not emotional listening.
- **Cannot promise:** One native skill-installation format works on every LLM host. This package contains portable instructions, a standard Python engine, and a standalone desktop form. Hosts vary in tool access and skill installation. Never invent compatibility or editor-project export.
- **Do not:** Rewrite narration, hallucinate transcripts, remove dramatic pauses by default, add unlicensed music, copy private recordings into public sharing locations, or claim to have processed files that are inaccessible.

## Minimum environment

- Python 3.10 or newer, including Tkinter if using the form.
- FFmpeg and FFprobe accessible via system PATH.
- No API keys, paid services or external Python packages required for the CLI engine or the desktop form.
- A computer with a graphical desktop for the form; in headless environments use CLI.

## User-facing quick workflow

1. Ask the user to provide the voice files and optional music. Accept numbered files, individual files, an accessible folder, or a ZIP. If the assistant cannot access the links, state that honestly.
2. Prefer the **simple local form**: run `python scripts/form.py`. Select voice files/folder/ZIP, sort/reorder, choose one music file, enter gaps, select checkboxes, choose output folder, click **Check project** then **Generate MP3**.
3. If no desktop GUI is available, create a JSON project config as in `examples/project.example.json` and run:
   - `python scripts/audio_studio.py validate --config project.json`
   - `python scripts/audio_studio.py render --config project.json`
4. Inspect the output JSON report and verify actual exported file exists. Share an actual verified download link only when the file is present in the runtime.
5. Explicitly ask the user to listen and approve artistic quality. Do not silently claim human-style listening.

## Default policy

- Voice files are kept in **supplied order**, except when the user requests numeric sorting. The form has a "Sort 0 → 7" button; a CLI user supplies an ordered array.
- Five seconds after voice 0, three seconds between remaining voice clips, optional five-second music outro.
- No background music under introduction or final voice **by default** (both configurable).
- Music is quiet beneath voice, stronger during gaps. Music is never placed inside a user-designated muted section.
- Original internal dramatic pauses are kept; edge-silence trimming is **off** by default.
- Gentle high-pass cleanup and modest clip-wide loudness leveling are on by default. Strong denoising is optional and must be verified for artifacts.
- Apply short 25 ms anti-click fades to voice edges. Longer creative fades must be approved.
- Final MP3 uses 320 kbps stereo at 48 kHz. Optional full-length WAV stems provide truly independent editable voice/music tracks.
- Do not claim MP3 contains independently editable tracks; standard MP3 is a combined mix.
- Supplementary free-text instructions are **recorded but NOT automatically executed** by the engine. An LLM may modify the project JSON only after converting the instructions into explicit supported values and telling the user what can and cannot be honored. If unsupported, report it before rendering. Do not pretend vague instructions were executed.

## Supported project settings

| Setting | Use |
| --- | --- |
| `project_name` | Output basename |
| `voice_files` | Ordered array of local source-file paths |
| `voice_folder` | Optional alternative to `voice_files`; numerically sorted |
| `music_file` | Optional background audio path |
| `output_dir` | Folder for the output |
| `after_intro_seconds` | Gap between first and second voice clips |
| `between_seconds` | Gap between subsequent voice clips |
| `outro_seconds` | Instrumental outro after the final voice (when music provided) |
| `music_under_intro` | Enable music beneath voice 0 |
| `mute_music_during_final_voice` | Zero music for final voice clip |
| `music_voice_db` | Background gain in dB during narration, e.g. -25 |
| `music_gap_db` | Background gain in dB during speech gaps/outro, e.g. -17 |
| `normalize_voice` | Gentle clip-wide gain balancing, with ±7 dB cap |
| `gentle_cleanup` | 70 Hz high-pass filter to reduce rumble |
| `denoise_voice` | Optional FFT denoising, may cause artifacts |
| `trim_edge_silence` | Optional conservative edge-only silence trimming |
| `export_stems` | Export synchronized WAV voice/music tracks |
| `additional_instructions` | Unexecuted notes preserved in report |

## Before processing

- Confirm sources exist and have audio streams; show any invalid/corrupt files.
- Confirm output location, intended voice order, exact gaps, and which voice clips must have no music.
- Clarify only actual conflicts or essential ambiguity. Do not transform a user's desired creative mood into an unsupported scientific claim.
- If importing a native Movavi project, state that no native project-import/export support is included in this version; import original recordings instead.

## Editing requirements

- Work non-destructively. Never overwrite original source files.
- Never silently shorten internal pauses or change pitch, speaking rate, or spoken words.
- Use a deterministic music level envelope and an absolute mute guard around voice-only final sections.
- Preserve a processing log with per-file gain, trimming, timings and loop strategy.
- If an export fails, report the exact error and do not claim successful delivery.

## Outputs

- `NAME_FINAL.mp3` — full-length mixed MP3.
- `NAME_REPORT.json` — exact timeline, source filenames, operations, technical warnings, unexecuted notes, output paths.
- When `export_stems` is enabled: `NAME_VOICE_ONLY.wav` and `NAME_MUSIC_ONLY.wav`, synchronized from time zero. Import the WAVs on separate tracks in Movavi, Audacity, or another audio editor.

## Installation / portability

Install the purpose-built `dist/audio-studio-skill.zip` in products that support Agent Skill ZIP import. Unlike a GitHub Source ZIP, this archive has one correctly named top-level `audio-studio/` folder. The standalone desktop form works independently. Some platforms still require explicit tool permissions or local installation of Python and FFmpeg. See `README.md`, `PORTABILITY.md`, and `docs/COMPATIBILITY.md`.

## Testing

Run `python tests/test_audio.py` (FFmpeg required). Tests synthesize their own audio and verify ordering, specified gaps, absence of music during last voice, outro, export duration, and a no-music project. No actual private recordings are included in this ZIP.
