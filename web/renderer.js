/* Browser-only Audio Studio engine. No media bytes leave the browser.
   Audio decoded through Web Audio and encoded to 320 kbps MP3 using vendored lamejs. */
(() => {
  "use strict";
  const RATE = 48000;
  const MAX_SECONDS = 900; // bound memory for an OfflineAudioContext
  const musicDb = {
    "very quiet": [-31, -24],
    quiet: [-25, -17],
    balanced: [-19, -12],
    prominent: [-13, -8]
  };
  const gainFromDb = value => Math.pow(10, value / 20);
  const pause = () => new Promise(resolve => setTimeout(resolve, 0));
  const seconds = number => Number.isFinite(number) && number >= 0 && number <= 120;

  function getVoiceGain(buffer, doNormalize) {
    if (!doNormalize) return 1;
    let peak = 0, squares = 0, n = 0;
    for (let c = 0; c < buffer.numberOfChannels; c++) {
      const data = buffer.getChannelData(c);
      for (let i = 0; i < data.length; i += 64) {
        const v = Math.abs(data[i]);
        if (v > peak) peak = v;
        squares += v * v;
        n++;
      }
    }
    if (n === 0 || peak < 1e-5) return 1;
    const rms = Math.sqrt(squares / n);
    return Math.max(0.3, Math.min(3.5, 0.12 / Math.max(rms, 0.01), 0.89 / peak));
  }

  function arrange(buffers, settings, hasMusic) {
    const timeline = [], musicRegions = [];
    const gap0 = Number(settings.after_intro_seconds);
    const gap = Number(settings.between_seconds);
    const outro = hasMusic ? Number(settings.outro_seconds) : 0;
    if (![gap0, gap, outro].every(seconds)) throw new Error("All timing values must be between 0 and 120 seconds.");
    let cursor = 0;
    buffers.forEach((buffer, i) => {
      if (i > 0) {
        const pause = i === 1 ? gap0 : gap;
        if (pause > 0) musicRegions.push({ start: cursor, end: cursor + pause, type: "gap" });
        cursor += pause;
      }
      const start = cursor, end = cursor + buffer.duration;
      timeline.push({ buffer, start, end });
      musicRegions.push({ start, end, type: "voice", index: i });
      cursor = end;
    });
    if (outro > 0) {
      musicRegions.push({ start: cursor, end: cursor + outro, type: "outro" });
      cursor += outro;
    }
    if (cursor <= 0 || cursor > MAX_SECONDS)
      throw new Error("Browser MP3 rendering supports projects up to 15 minutes. Use the desktop Python/FFmpeg engine for longer projects.");
    return { timeline, musicRegions, total: cursor };
  }

  async function decodeFile(context, file) {
    if (!file) throw new Error("No audio file provided.");
    try { return await context.decodeAudioData(await file.arrayBuffer()); }
    catch { throw new Error("Could not decode " + file.name + ". Convert it to WAV or MP3, then retry."); }
  }

  async function renderProject({ tracks, music, settings, onProgress = () => {} }) {
    if (!Array.isArray(tracks) || !tracks.length) throw new Error("Add at least one recording.");
    if (!window.lamejs || typeof window.lamejs.Mp3Encoder !== "function")
      throw new Error("MP3 encoder was not loaded. Check your internet connection and refresh.");
    if (settings.denoise_voice)
      throw new Error("Noise reduction is not yet available in the browser. Uncheck it or use the desktop FFmpeg version.");
    if (settings.export_stems)
      throw new Error("Separate WAV stems are not yet supported by the browser engine. Uncheck the option or use the desktop editor.");
    const AudioContextType = window.AudioContext || window.webkitAudioContext;
    if (!AudioContextType || !window.OfflineAudioContext) throw new Error("This browser does not support audio rendering.");
    const decoder = new AudioContextType();
    let voice = [], musicBuffer = null;
    try {
      for (let i = 0; i < tracks.length; i++) {
        onProgress("Decoding voice " + (i + 1) + " of " + tracks.length + "...");
        voice.push(await decodeFile(decoder, tracks[i].file));
      }
      if (music) {
        onProgress("Decoding background music...");
        musicBuffer = await decodeFile(decoder, music);
      }
    } finally {
      await decoder.close();
    }
    const { timeline, musicRegions, total } = arrange(voice, settings, !!musicBuffer);
    const offline = new OfflineAudioContext(2, Math.ceil(total * RATE), RATE);
    timeline.forEach(({ buffer, start, end }) => {
      const source = offline.createBufferSource();
      source.buffer = buffer;
      let last = source;
      if (settings.gentle_cleanup) {
        const hp = offline.createBiquadFilter();
        hp.type = "highpass";
        hp.frequency.value = 80;
        last.connect(hp);
        last = hp;
      }
      const gain = offline.createGain();
      last.connect(gain);
      gain.connect(offline.destination);
      const volume = getVoiceGain(buffer, settings.normalize_voice);
      const fade = Math.min(0.025, (end - start) / 4);
      gain.gain.setValueAtTime(0, start);
      gain.gain.linearRampToValueAtTime(volume, start + fade);
      gain.gain.setValueAtTime(volume, end - fade);
      gain.gain.linearRampToValueAtTime(0, end);
      source.start(start);
    });
    if (musicBuffer) {
      const source = offline.createBufferSource();
      source.buffer = musicBuffer;
      source.loop = true;
      const gain = offline.createGain();
      source.connect(gain);
      gain.connect(offline.destination);
      const levels = musicDb[settings.music_level] || musicDb.quiet;
      let previous = 0;
      gain.gain.setValueAtTime(0, 0);
      for (const region of musicRegions) {
        let next;
        if (region.type === "outro" || region.type === "gap") next = gainFromDb(levels[1]);
        else if (region.index === 0 && !settings.music_under_intro) next = 0;
        else if (region.index === timeline.length - 1 && settings.mute_music_during_final_voice) next = 0;
        else next = gainFromDb(levels[0]);
        const fade = Math.min(0.04, (region.end - region.start) / 4);
        gain.gain.setValueAtTime(previous, region.start);
        gain.gain.linearRampToValueAtTime(next, region.start + fade);
        gain.gain.setValueAtTime(next, region.end);
        previous = next;
      }
      const fadeOut = Math.min(0.75, total / 4);
      gain.gain.setValueAtTime(previous, total - fadeOut);
      gain.gain.linearRampToValueAtTime(0, total);
      source.start(0);
      source.stop(total);
    }
    onProgress("Mixing voice and music in the browser...");
    const rendered = await offline.startRendering();
    const encoder = new window.lamejs.Mp3Encoder(2, RATE, 320);
    const left = rendered.getChannelData(0), right = rendered.getChannelData(1);
    const output = [], block = 1152;
    for (let offset = 0; offset < left.length; offset += block) {
      const end = Math.min(offset + block, left.length);
      const l = new Int16Array(end - offset), r = new Int16Array(end - offset);
      for (let j = offset, k = 0; j < end; j++, k++) {
        l[k] = Math.round(Math.max(-1, Math.min(1, left[j])) * 32767);
        r[k] = Math.round(Math.max(-1, Math.min(1, right[j])) * 32767);
      }
      const encoded = encoder.encodeBuffer(l, r);
      if (encoded.length) output.push(new Uint8Array(encoded));
      if (offset % (block * 100) === 0) {
        onProgress("Encoding MP3: " + Math.min(100, Math.round(100 * offset / left.length)) + "%");
        await pause();
      }
    }
    const tail = encoder.flush();
    if (tail.length) output.push(new Uint8Array(tail));
    const blob = new Blob(output, { type: "audio/mpeg" });
    if (blob.size < 512) throw new Error("MP3 encoder returned an unexpectedly small file.");
    onProgress("MP3 ready (" + (blob.size / 1048576).toFixed(2) + " MB).");
    return { blob, duration: total, bitrate_kbps: 320, sample_rate_hz: RATE };
  }
  window.AudioStudioRender = { renderProject, maxProjectSeconds: MAX_SECONDS };
})();
