# Audio Studio — Simple Chat Setup

**Purpose:** A conversational *startup template*, not a promise that a graphical Tkinter application will appear inside an LLM. See [Chat-first workflow](../docs/CHAT_FIRST.md).

## On activation: start here, do not lecture about installation

If the user says **“Start Audio Studio”**, **“Use the Audio Studio skill”**, or submits a configuration, reply immediately with a short welcome and request **only what is missing**.

**If no recordings are attached:**

> **Audio Studio is ready.** Please attach your voice recordings (individual MP3/WAV/MP4 files or one ZIP). You can also attach a background instrumental, or say “no music.” I'll check the files and show you the proposed sequence and pauses before processing.

If the user **already supplied settings**, acknowledge them in one concise line; **do not ask again** for project name, gap, music level, cleanup, normalization or mute choice.

If the user has attached the voice files, **skip the upload request**. Validate file access with the host's actual tools; request music only if the user wants it and it is missing. Do not ask for media that is already available through an authorized connection.

## Optional compact form (only if the host supports native controls)

Show these fields in a small panel, preferably with defaults already filled:

| Field | Default | Control |
| --- | --- | --- |
| Project name | My Audio Project | Short text |
| Voice recordings | Required; supplied through the chat attachment control or authorized storage | Attachment instruction, **not a fake upload button** |
| Background music | None / attach an instrumental | Attachment instruction |
| Gap between all recordings | 3 seconds | Number or dropdown |
| Music level | Quiet | Very quiet / Quiet / Balanced / More prominent |
| Gently reduce low rumble | On | Checkbox |
| Balance voice volume | On | Checkbox |
| No music during final voice | On, unless user explicitly says off | Checkbox |
| Extra instructions | Empty | Optional text area |

**More options** (do not display until asked): different gap after clip 1, musical outro, music under intro, separate WAV tracks, edge trimming, stronger denoise, per-clip rules. A musical outro is **5 seconds by default when background music is supplied**.

When native controls are unavailable, provide the short welcome and ask for attachments rather than rendering a long text form. The chat's file attachment mechanism is the actual upload interface; no skill can conjure a universal file-picker widget.

## When audio is available: preview first

Show the detected filenames, numerical order when appropriate, estimated clip durations, and a readable timeline:

`Voice 0 → 3s gap → Voice 1 → 3s gap → Voice 2 ... → final voice → optional outro`

Do not claim durations have been measured until they actually have. State whether music is **present or muted** beneath the last voice, honoring user-provided `true` **and** `false`. If the user specifies **“3 seconds between clips”**, apply 3 seconds to **every gap**, including the first, unless a distinct intro gap was also requested.

Confirm the timeline with the user before the first render. After approval, translate selected values with `scripts/chat_bridge.py` (or directly populate the supported engine JSON), then run `validate` and `render` if the host actually permits them.

## Quick user prompt

> Start Audio Studio. I will attach voice recordings and optional background music. Guide me through a short setup, reuse settings I already provided, show the timeline, and only process the files if your tools support it.

## Honest capability rules

- The assistant may **display an inline native form** only when supported by that chat product. This document itself is not a native form executable across all LLMs.
- Python, FFmpeg, actual audio bytes and write access are required for processing. Otherwise direct the user to the standalone local GUI with brief setup instructions.
- `additional_instructions` are **not automatically executed** by the engine. Explicitly review them and map only supported instructions into settings, or warn the user.
- Never claim to have listened to audio, removed noise, or exported files unless the corresponding operations were truly performed and verified.
