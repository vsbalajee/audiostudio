# Audio Studio v2.1 preview: Browser MP3 renderer and chat project editing

## What was missing in production v2.0

- The live browser form's Generate MP3 button was disabled. The old web app only generated timeline previews and downloaded JSON settings.
- The production MCP endpoint exposed only `start_audio_studio`, `get_audio_studio_defaults`, `preview_audio_timeline`. No project-edit tools existed.

## What's new in this branch

- Actual browser-only audio mix and MP3 encoding through Web Audio's `OfflineAudioContext` and the **lamejs 1.2.1** browser MP3 encoder. Encoder source is copied from npm to the Worker's static assets by `npm run build:web` (automatically runs before `npm run deploy`).
- Supports ordered voice recordings, independently configurable first/remaining gaps, looped music soundtrack, music volume presets, optional music under first clip, mute music during final voice, music outro, per-voice RMS gain balancing and basic highpass cleanup.
- Exports an actual 320 kbps, 48 kHz stereo MP3 after an explicit timeline preview (downloaded to the user).
- New stateless MCP tools `create_audio_project` and `edit_audio_project`. Chat can manage **filenames and settings**: add/remove/move clips in the plan, select/clear music, update permitted settings. Tools return the updated project JSON plus a browser deep link containing the configuration.

## Limitations (do not claim features that do not exist)

- Audio media stays **on the user's computer**. No audio file is uploaded or processed by Cloudflare; no backend processing charges are introduced.
- Chat cannot read or edit local file contents, trim voice samples, or delete local audio files. Chat only changes the **project plan**; you must select the files again in the browser after opening an updated link. Existing browser tabs don't synchronize automatically.
- No server-side project persistence or authentication. The assistant must pass the full `project` JSON in every subsequent MCP edit. Chat configuration links include **filenames and settings** in the URL; avoid private filenames.
- 15-minute browser rendering cap due to memory limits. Firefox/Chrome audio decoding availability varies by source codec. Use desktop Python/FFmpeg engine for longer or unsupported projects.
- Browser processing is **not feature-equivalent** to the Python engine: voice normalization is approximate RMS gain, low-rumble cleanup is basic highpass, `denoise_voice` and `export_stems` are **not implemented**; selecting them yields an explicit error. There is no transcript-aware editing.
- No user data transfer or remote deletion capabilities are built. Do not expose private files or business data via unauthenticated MCP tools.
- MP3 at 320 kbps is the encoding bitrate, not a claim to enhance quality beyond the original recordings.

## Developer quick start

At the repository root:

```bash
npm install
npm run build:web
npm run typecheck
npm run dev
```

Then open `http://localhost:8787/`. Select voice WAV/MP3 files, optionally music, choose timing, **Preview timeline**, and click **Generate MP3**.

For Cloudflare's current deploy command `npm run deploy`, npm automatically runs `predeploy` to bundle `lame.min.js` before Wrangler deploys the `web/` assets. Do not replace the deploy command with a plain `npx wrangler deploy` unless `npm run build:web` also runs first.

Run the GitHub workflow `Browser MP3 and chat MCP integration tests` before merging. It creates synthetic WAV files, exercises project-chat MCP calls, drives Chromium against a local Cloudflare Worker, generates MP3 outputs and validates them with FFprobe.

## Chat operation examples

- "Create a project titled My Podcast with voice files intro.wav, interview.wav and closing.wav, quiet music and three-second gaps." → `create_audio_project`.
- "Remove interview.wav." → `edit_audio_project` with `action=remove_voice` and previously returned project JSON.
- "Move closing.wav to the first position." → `edit_audio_project` with `action=move_voice`, `from_position` and `position=1`.
- "Set after-intro gap to 5 seconds." → `edit_audio_project` with `action=update_setting`, `setting=after_intro_seconds`, `value=5`.

Once the new MCP tools are live, the user may need to refresh or reconnect the ChatGPT Audio Studio plugin before the updated tools appear.

## Third-party software

Browser MP3 encoding uses `lamejs` version 1.2.1, installed from npm. Preserve its original license and attribution in any distributions. The source code and package license are available from https://www.npmjs.com/package/lamejs.
