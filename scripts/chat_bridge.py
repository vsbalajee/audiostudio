#!/usr/bin/env python3
"""Convert a compact Audio Studio chat setup into a validated engine configuration.

This module translates explicit form selections; it does not interpret creative
free text or claim to listen to audio. All actual file/audio validation happens
in audio_studio.py. No third-party packages are required.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import sys

from audio_studio import DEFAULTS

MUSIC_LEVELS = {
    'very-quiet': (-32.0, -21.0),
    'quiet': (-25.0, -17.0),
    'balanced': (-20.0, -14.0),
    'more-prominent': (-16.0, -11.0),
}

FIELDS = {
    'project_name', 'voice_files', 'voice_folder', 'music_file', 'output_dir',
    'gap_seconds', 'after_intro_seconds', 'between_seconds', 'outro_seconds',
    'music_level', 'gentle_noise_reduction', 'normalize_voice',
    'mute_music_during_final_voice', 'music_under_intro', 'export_stems',
    'denoise_voice', 'trim_edge_silence', 'additional_instructions',
}

BOOLEAN_FIELDS = {
    'gentle_noise_reduction', 'normalize_voice',
    'mute_music_during_final_voice', 'music_under_intro', 'export_stems',
    'denoise_voice', 'trim_edge_silence',
}


def nonnegative_seconds(key: str, value: object) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f'{key} must be a number of seconds')
    result = float(value)
    if not math.isfinite(result) or result < 0 or result > 300:
        raise ValueError(f'{key} must be between 0 and 300 seconds')
    return result


def convert_chat_setup(raw: dict) -> dict:
    """Map a compact chat form onto audio_studio.py's complete config keys.

    If the user specifies a single gap_seconds value, apply it to EVERY gap,
    including the first pair. More specific per-gap choices override it.
    Never silently flip an explicit False back to the engine's True default.
    """
    if not isinstance(raw, dict):
        raise ValueError('Chat setup must be a JSON object')
    unknown = set(raw) - FIELDS
    if unknown:
        raise ValueError('Unsupported chat setting(s): ' + ', '.join(sorted(unknown)))
    for key in BOOLEAN_FIELDS & raw.keys():
        if not isinstance(raw[key], bool):
            raise ValueError(f'{key} must be true or false')
    for key in ('project_name', 'music_file', 'output_dir', 'voice_folder', 'additional_instructions'):
        if key in raw and not isinstance(raw[key], str):
            raise ValueError(f'{key} must be text')
    if 'voice_files' in raw:
        if not isinstance(raw['voice_files'], list) or not all(isinstance(item, str) for item in raw['voice_files']):
            raise ValueError('voice_files must be a list of file paths')
    if not raw.get('voice_files') and not raw.get('voice_folder'):
        raise ValueError('Voice recordings are missing. Ask the user to attach files or provide an accessible folder before processing.')
    if raw.get('voice_files') and raw.get('voice_folder'):
        raise ValueError('Specify voice_files or voice_folder, not both')

    config = dict(DEFAULTS)
    for key in ('project_name', 'voice_files', 'music_file', 'output_dir',
                'normalize_voice', 'mute_music_during_final_voice',
                'music_under_intro', 'export_stems', 'denoise_voice',
                'trim_edge_silence', 'additional_instructions'):
        if key in raw:
            config[key] = raw[key]
    if 'voice_folder' in raw:
        config['voice_folder'] = raw['voice_folder']
    if 'gentle_noise_reduction' in raw:
        # This uses the engine's 70 Hz high-pass rumble removal, not AI denoising.
        config['gentle_cleanup'] = raw['gentle_noise_reduction']
    if 'gap_seconds' in raw:
        gap = nonnegative_seconds('gap_seconds', raw['gap_seconds'])
        config['after_intro_seconds'] = gap
        config['between_seconds'] = gap
    for key in ('after_intro_seconds', 'between_seconds', 'outro_seconds'):
        if key in raw:
            config[key] = nonnegative_seconds(key, raw[key])
    level = raw.get('music_level', 'quiet')
    if not isinstance(level, str) or level not in MUSIC_LEVELS:
        raise ValueError('music_level must be one of: ' + ', '.join(MUSIC_LEVELS))
    config['music_voice_db'], config['music_gap_db'] = MUSIC_LEVELS[level]
    return config


def main() -> int:
    parser = argparse.ArgumentParser(description='Convert a compact Audio Studio chat setup into project JSON')
    parser.add_argument('--config', required=True, help='Path to a JSON chat setup')
    parser.add_argument('--output', required=True, help='Path for the generated audio engine project JSON')
    args = parser.parse_args()
    try:
        raw = json.loads(Path(args.config).read_text(encoding='utf-8'))
        project = convert_chat_setup(raw)
        dest = Path(args.output)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(json.dumps(project, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    except (ValueError, OSError, json.JSONDecodeError) as exc:
        print(f'ERROR: {exc}', file=sys.stderr)
        return 1
    print(f'Prepared {dest}. Review the timeline and validate the actual files before rendering.')
    if project['additional_instructions'].strip():
        print('WARNING: additional_instructions are notes only; do NOT claim those edits were performed.', file=sys.stderr)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
