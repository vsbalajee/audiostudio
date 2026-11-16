# Audio Studio — Compact Form for Any AI Assistant

When the chat app supports a native form, these are its recommended fields. If native forms are not available, ask the user conversationally for only missing information. A standalone GUI is provided in `scripts/form.py`.

## Required

**Project name:** [My Audio Project]

**Voice recordings:** [Attach files / ZIP, or provide accessible folder link]

**Background music:** [Attach instrumental file / choose none]

## Timing

**After first recording:** [5] seconds music-only gap (if music selected)

**Between remaining recordings:** [3] seconds

**Music-only ending:** [5] seconds

## Select options

- [x] Keep recordings in numerical order (0, 1, 2...)
- [x] Balance voice volumes gently
- [x] Reduce low-frequency rumble
- [ ] Optional stronger noise reduction (may cause artifacts)
- [ ] Trim silence at the beginnings/ends of recordings
- [x] Keep music beneath the narration at a low volume
- [x] No background music during the final voice recording
- [ ] Add music beneath the introduction
- [ ] Export separate synchronized WAV tracks for editing

**Music strength:** [Quiet — voice first / Very quiet / Balanced / More prominent]

**Additional requirements:** [Optional free text — must be reviewed explicitly by the LLM or user, never silently marked complete]

**Output:** [320 kbps stereo MP3 / MP3 + WAV stems]

## Assistant instructions

1. Resolve attachments/folder contents through tools only if actually accessible; don't assume URLs have been downloaded.
2. Confirm order and any conflicting requests.
3. Convert the choices into `examples/project.example.json` keys.
4. Ask approval if the free-text requirements cannot be represented by supported settings.
5. Run validate, then render. Share only generated files that were verified to exist.
6. Report technical changes, duration, and known limitations. Never claim to have artistically listened unless an actual listening capability was available.
