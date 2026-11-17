"use strict";

async function renderAudio(files, musicFile, settings, progress) {
  const sampleRate = 44100;
  const context = new AudioContext({ sampleRate });
  const decode = async file => {
    try { return await context.decodeAudioData(await file.arrayBuffer()); }
    catch { throw new Error("Could not decode " + file.name + " in this browser."); }
  };
  try {
    progress("Reading recordings…");
    const voices = [];
    for (const file of files) voices.push(await decode(file));
    const music = musicFile ? await decode(musicFile) : null;
    let cursor = 0;
    const schedule = voices.map((buffer, index) => {
      if (index) cursor += index === 1 ? settings.after_intro_seconds : settings.between_seconds;
      const start = cursor;
      cursor += buffer.duration;
      return { buffer, start };
    });
    const frames = Math.ceil((cursor + settings.outro_seconds) * sampleRate);
    const mix = new OfflineAudioContext(2, frames, sampleRate);
    const voiceBus = mix.createGain();
    const musicBus = mix.createGain();
    const compressor = mix.createDynamicsCompressor();
    voiceBus.connect(compressor);
    musicBus.connect(compressor);
    compressor.connect(mix.destination);
    // A sample envelope gently attenuates steady low-level noise when enabled.
    function gate(buffer) {
      for (let channel = 0; channel < buffer.numberOfChannels; channel++) {
        const samples = buffer.getChannelData(channel);
        let envelope = 0, gain = 1;
        for (let i = 0; i < samples.length; i++) {
          envelope = Math.max(Math.abs(samples[i]), envelope * 0.9994);
          const target = envelope < 0.006 ? 0.18 : 1;
          gain += (target - gain) * (target > gain ? 0.08 : 0.001);
          samples[i] *= gain;
        }
      }
    }
    schedule.forEach(({ buffer, start }) => {
      if (settings.denoise_voice) gate(buffer);
      const source = mix.createBufferSource();
      source.buffer = buffer;
      let output = source;
      if (settings.gentle_cleanup) {
        const filter = mix.createBiquadFilter();
        filter.type = "highpass";
        filter.frequency.value = 80;
        source.connect(filter);
        output = filter;
      }
      const volume = mix.createGain();
      if (settings.normalize_voice) {
        let peak = 0;
        for (let channel = 0; channel < buffer.numberOfChannels; channel++) {
          for (const sample of buffer.getChannelData(channel)) peak = Math.max(peak, Math.abs(sample));
        }
        if (peak > 0) volume.gain.value = Math.min(4, 0.65 / peak);
      }
      output.connect(volume);
      volume.connect(voiceBus);
      source.start(start);
    });
    if (music) {
      const source = mix.createBufferSource();
      source.buffer = music;
      source.loop = true;
      source.connect(musicBus);
      const level = { "very quiet": 0.065, quiet: 0.12, balanced: 0.23, prominent: 0.4 }[settings.music_level];
      const start = settings.music_under_intro ? 0 : voices[0].duration;
      const end = frames / sampleRate;
      const finalStart = schedule.at(-1).start;
      const regions = settings.mute_music_during_final_voice
        ? [[start, finalStart], [Math.max(start, cursor), end]]
        : [[start, end]];
      musicBus.gain.value = 0;
      for (const [from, to] of regions) {
        if (to <= from) continue;
        const fade = Math.min(0.25, (to - from) / 2);
        musicBus.gain.setValueAtTime(0, from);
        musicBus.gain.linearRampToValueAtTime(level, from + fade);
        musicBus.gain.setValueAtTime(level, to - fade);
        musicBus.gain.linearRampToValueAtTime(0, to);
      }
      if (start < end) source.start(start);
    }
    progress("Mixing audio…");
    const audio = await mix.startRendering();
    progress("Encoding 320 kbps MP3…");
    const encoder = new lamejs.Mp3Encoder(2, sampleRate, 320);
    const left = audio.getChannelData(0);
    const right = audio.getChannelData(1);
    const chunks = [];
    function pcm(sample) {
      return Math.round(Math.max(-1, Math.min(1, sample)) * 32767);
    }
    for (let offset = 0; offset < frames; offset += 1152) {
      const count = Math.min(1152, frames - offset);
      const l = new Int16Array(count);
      const r = new Int16Array(count);
      for (let i = 0; i < count; i++) {
        l[i] = pcm(left[offset + i]);
        r[i] = pcm(right[offset + i]);
      }
      const bytes = encoder.encodeBuffer(l, r);
      if (bytes.length) chunks.push(bytes);
      if (offset % (1152 * 80) === 0) await new Promise(resolve => setTimeout(resolve, 0));
    }
    chunks.push(encoder.flush());
    return new Blob(chunks, { type: "audio/mpeg" });
  } finally {
    await context.close();
  }
}
