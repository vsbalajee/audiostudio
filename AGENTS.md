# Instructions for coding agents and AI assistants

This project implements Audio Studio, a local audio-processing engine and portable Agent Skill.

1. Read [`SKILL.md`](SKILL.md) for end-user behavior and capability limits. When invoked, follow **chat-first activation**: ask for missing attachments, reuse supplied settings, and show the timeline before rendering. See [`docs/CHAT_FIRST.md`](docs/CHAT_FIRST.md).
2. **Do not claim to listen, understand emotion, or judge music quality** unless a real audio-listening tool is available and was used. Waveform measurement and FFmpeg filters do not establish emotional understanding.
3. Never pretend linked Drive/Dropbox/local files are accessible before verifying their contents.
4. Preserve original recordings, words, natural pauses, pitch, speaking speed, and licensing. Do not publish private source recordings.
5. Prefer the reproducible `scripts/audio_studio.py` CLI for headless AI agents. The Tkinter form requires a graphical desktop; do not launch it in headless CI.
6. `additional_instructions` are notes only. Convert them into supported JSON settings before rendering, or report unsupported requirements explicitly.
7. After any change to timing, mixing, or export code, run:
   `python -m unittest discover -s tests -p 'test*.py' -v`
8. Keep documentation truthful. `SKILL.md` is portable, but automatic installation and audio execution depend on the AI platform and its tools.
9. Do not add hard-coded secrets, private audio, copyrighted music samples, or unverifiable performance claims.
10. Package the installable skill with `python scripts/build_skill_zip.py`; do not hand-edit the generated ZIP.
