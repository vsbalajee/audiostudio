# Technical architecture

```text
User recordings ──┐
                  ├── Config validation → FFprobe → voice preparation → ordered voice timeline ──┐
Music source ─────┘                            ↓                                                 │
                         loop/crossfade + volume envelope + voice-only hard mute                 │
                                              ↓                                                 │
                                       music WAV timeline ───────────────────────────────────────┤
                                                                                                ↓
                                                                                 FFmpeg mix + limiter
                                                                                                ↓
                                                            MP3 (320 kbps) + optional WAV stems + JSON report
```

## Modules

- `scripts/form.py` — local five-section Tkinter GUI; supports individual files, a folder, or a ZIP.
- `scripts/audio_studio.py` — input validation, FFprobe checks, FFmpeg conversion and technical mixing engine.
- `scripts/build_skill_zip.py` — deterministic ZIP packager, ensuring the installable AI skill archive matches the checked-in source.
- `forms/chat-form.md` — intentionally minimal interface schema for assistants that support interactive controls.
- `tests/` — creates synthetic audio to check observable technical behavior.

## Design principles

1. **Non-destructive:** original recordings are read only.
2. **Reproducible:** JSON config + change report enable subsequent adjustments.
3. **Deterministic:** configured seconds and mute windows take priority over heuristic decisions.
4. **Safe defaults:** preserve internal pauses; use light enhancement.
5. **Honest limitations:** numerical measures do not indicate emotional delivery or good taste in background music.
6. **Local by default:** no hosted service, telemetry, credentials or external API dependencies.

## Practical limits

- Processing large or long source files requires enough RAM, storage and CPU time for temporary 48 kHz WAV stems.
- Volume automation is computed with FFmpeg filter expressions; very large multi-clip sessions may require splitting into chapters or further engine optimization, especially on Windows with command-length limits.
- The optional denoise filter can produce artifacts, and the music looping method cannot guarantee a seamless musical phrase at every crossfade.
- Output loudness is gain-limited, not a guarantee of a particular streaming-platform LUFS target. Export results should be auditioned by the user.
- Proprietary DAW/Movavi project import/export is not part of this release. Stems are the portable editable output.

## Threat considerations

Untrusted inputs are passed to FFmpeg decoders. Keep FFmpeg updated and avoid processing unknown sources with elevated system permissions. ZIP extraction is size-limited and writes under a temporary directory, but malicious archives remain a risk.
