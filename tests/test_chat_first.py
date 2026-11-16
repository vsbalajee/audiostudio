"""Regression checks for the chat-first setup contract and conversion bridge."""
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from chat_bridge import convert_chat_setup


class ChatFirstTests(unittest.TestCase):
    def test_user_settings_preserved_and_global_gap_applies_everywhere(self):
        config = convert_chat_setup({
            'project_name': 'My Audio Project',
            'voice_files': ['/tmp/0.mp4', '/tmp/1.mp4'],
            'gap_seconds': 3,
            'music_level': 'quiet',
            'gentle_noise_reduction': True,
            'normalize_voice': True,
            'mute_music_during_final_voice': False,
        })
        self.assertEqual(config['after_intro_seconds'], 3)
        self.assertEqual(config['between_seconds'], 3)
        self.assertEqual(config['music_voice_db'], -25.0)
        self.assertFalse(config['mute_music_during_final_voice'])
        self.assertTrue(config['gentle_cleanup'])

    def test_explicit_intro_gap_overrides_general_gap(self):
        config = convert_chat_setup({'voice_files': ['clip.wav'], 'gap_seconds': 3, 'after_intro_seconds': 5})
        self.assertEqual(config['after_intro_seconds'], 5)
        self.assertEqual(config['between_seconds'], 3)

    def test_input_requires_accessible_audio_paths(self):
        with self.assertRaisesRegex(ValueError, 'Voice recordings are missing'):
            convert_chat_setup({'gap_seconds': 3})

    def test_unknown_or_invalid_inputs_are_not_silently_ignored(self):
        for invalid in ({'voice_files': ['a.wav'], 'magic_emotion_detection': True},
                        {'voice_files': ['a.wav'], 'music_level': 'best'},
                        {'voice_files': ['a.wav'], 'mute_music_during_final_voice': 'false'},
                        {'voice_files': ['a.wav'], 'gap_seconds': -2},
                        {'voice_files': ['a.wav'], 'gap_seconds': True}):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                convert_chat_setup(invalid)

    def test_example_is_parseable_and_matches_our_user_request(self):
        example = json.loads((ROOT / 'examples/chat-session.example.json').read_text(encoding='utf-8'))
        project = convert_chat_setup(example)
        self.assertFalse(project['mute_music_during_final_voice'])
        self.assertEqual(project['between_seconds'], 3)
        self.assertEqual(project['after_intro_seconds'], 3)

    def test_skill_includes_startup_requirements(self):
        skill = (ROOT / 'SKILL.md').read_text(encoding='utf-8')
        self.assertIn('Start Audio Studio', skill)
        self.assertIn('Ask only for missing', skill)
        self.assertIn('forms/chat-form.md', skill)
        self.assertIn('docs/CHAT_FIRST.md', skill)
        self.assertIn('Do not launch Tkinter', skill)


if __name__ == '__main__':
    unittest.main()
