"""Regression tests: eight-clip projects, user-specified gaps, and hard music mutes."""
from __future__ import annotations

import array
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import wave

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from audio_studio import run_project, validated_config, AudioStudioError


def make_tone(path: Path, duration: float = 1.3) -> None:
    subprocess.run(
        ['ffmpeg', '-nostdin', '-y', '-loglevel', 'error', '-f', 'lavfi', '-i',
         f'sine=frequency=220:duration={duration}', '-c:a', 'pcm_s16le', str(path)],
        check=True,
    )


class EightClipTests(unittest.TestCase):
    def test_eight_clips_music_absent_for_last_voice(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            voices = []
            for i in range(8):
                src = root / f'{i}.wav'
                make_tone(src)
                voices.append(str(src))
            music = root / 'music.wav'
            make_tone(music, 1.5)
            result = run_project(
                {
                    'project_name': '8 voice regression',
                    'voice_files': voices,
                    'music_file': str(music),
                    'output_dir': str(root / 'output'),
                    'export_stems': True,
                    'after_intro_seconds': 5,
                    'between_seconds': 3,
                    'outro_seconds': 5,
                    'normalize_voice': False,
                },
                progress=lambda _: None,
            )
            report = json.loads(Path(result['report']).read_text(encoding='utf8'))
            timeline = report['timeline']
            self.assertEqual([clip['name'] for clip in timeline], [f'{i}.wav' for i in range(8)])
            self.assertAlmostEqual(timeline[1]['start'] - timeline[0]['end'], 5, delta=0.03)
            for i in range(2, 8):
                self.assertAlmostEqual(timeline[i]['start'] - timeline[i - 1]['end'], 3, delta=0.03)
            self.assertAlmostEqual(result['duration_seconds'], 8 * 1.3 + 5 + 6 * 3 + 5, delta=0.25)
            last = timeline[-1]
            with wave.open(result['music_stem'], 'rb') as wav:
                self.assertEqual(wav.getsampwidth(), 2)
                sr = wav.getframerate()
                wav.setpos(round(last['start'] * sr))
                samples = array.array('h')
                samples.frombytes(wav.readframes(round((last['end'] - last['start']) * sr)))
            self.assertTrue(samples)
            self.assertTrue(all(sample == 0 for sample in samples), 'Music must be hard-muted for all of voice 7')

    def test_unknown_setting_rejected(self) -> None:
        with self.assertRaisesRegex(AudioStudioError, 'Unsupported configuration'):
            validated_config({'voice_files': [], 'after_intro_secondz': 3})

    def test_non_object_config_rejected(self) -> None:
        with self.assertRaisesRegex(AudioStudioError, 'JSON object'):
            validated_config(['bad', 'config'])


if __name__ == '__main__':
    unittest.main(verbosity=2)
