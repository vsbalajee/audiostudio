# Audio Studio portability

Audio Studio is aligned with the [Agent Skills](https://agentskills.io/specification) open format: a folder named `audio-studio` with `SKILL.md` and optional scripts/resources. The audio engine itself is ordinary Python + FFmpeg, not a proprietary LLM API.

## Choose an artifact

1. **Installable skill archive:** `dist/audio-studio-skill.zip` — use for supported skills-upload workflows; one `audio-studio/` folder in the ZIP.
2. **Full source archive:** GitHub **Code → Download ZIP** — includes tests, CI, documentation and the skill package under `dist/`.
3. **Standalone desktop app:** extract either package and launch `scripts/form.py` from the extracted folder with Python and FFmpeg installed.

## First-read welcome and chat-first startup

If a supported AI assistant reads the archive before a project begins, `SKILL.md` instructs it to show an **eight-line** welcome stored in `forms/welcome-message.md`, with **Start Audio Studio** as the final action. This is a model instruction, **not** a universal upload-event trigger: some chat products require the user to explicitly ask the assistant to read the ZIP first.



The default assistant interaction is “Start Audio Studio” → request missing recordings/music → show measured timeline → confirm → render if tools allow. See [`docs/CHAT_FIRST.md`](docs/CHAT_FIRST.md). The standalone graphical desktop form is optional; no AI platform is required to render it inside chat.

## LLM execution requirements

An AI model can interpret `SKILL.md` if it can access the file. **To process audio**, it also needs a working execution environment, the source audio bytes, Python, FFmpeg and permission to write outputs. A generic chat interface may have none of these. Installing instructions and executing code are distinct capabilities.

Supported paths are described accurately in [`docs/COMPATIBILITY.md`](docs/COMPATIBILITY.md). Claude custom skills and Gemini CLI have explicit Agent Skills support; the ChatGPT product and other web interfaces vary by offering and enabled tools.

## Honest operation rules

- A folder URL is not equal to access to media bytes. Validate and retrieve files first.
- Waveform metrics do not mean the program can emotionally listen to music or narration.
- Freely written additional instructions are not automatically executed by the FFmpeg engine.
- WAV stems contain independent editable tracks; MP3 is one stereo mixed stream.
- Never post private input files or copyrighted backing tracks in a public code repository.

This package does not create a native Movavi project or a hosted audio processing website.
