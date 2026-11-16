"""Skill packaging should be self-contained, deterministic and free of private media."""
import io
from pathlib import Path
import sys
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from build_skill_zip import build_archive


class SkillPackagingTests(unittest.TestCase):
    def test_single_root_and_skill_exists(self):
        blob = build_archive()
        with zipfile.ZipFile(io.BytesIO(blob), 'r') as archive:
            names = archive.namelist()
            self.assertIn('audio-studio/SKILL.md', names)
            self.assertIn('audio-studio/scripts/audio_studio.py', names)
            self.assertIn('audio-studio/scripts/form.py', names)
            self.assertIn('audio-studio/docs/COMPATIBILITY.md', names)
            self.assertTrue(all(name.startswith('audio-studio/') for name in names))
            self.assertTrue(all(not name.endswith(('.mp3', '.mp4', '.wav')) for name in names))

    def test_deterministic(self):
        self.assertEqual(build_archive(), build_archive())


if __name__ == '__main__':
    unittest.main()
