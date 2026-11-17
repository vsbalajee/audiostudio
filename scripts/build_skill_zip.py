#!/usr/bin/env python3
"""Create a deterministic, platform-agnostic Agent Skill ZIP (standard library only).

Unlike GitHub's Source ZIP, the skill archive has exactly one top-level folder
named audio-studio containing SKILL.md and its runtime dependencies.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
from io import BytesIO
from pathlib import Path
import sys
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / 'dist' / 'audio-studio-skill.zip'
INCLUDED = (
    'SKILL.md',
    'LICENSE',
    'SECURITY.md',
    'CONTRIBUTING.md',
    'CODE_OF_CONDUCT.md',
    'CHANGELOG.md',
    'README.md',
    'PORTABILITY.md',
    'Start_Audio_Studio_Windows.bat',
    'Start_Audio_Studio_Mac_Linux.sh',
    'scripts/audio_studio.py',
    'scripts/chat_bridge.py',
    'scripts/form.py',
    'forms/chat-form.md',
    'forms/welcome-message.md',
    'docs/CHAT_FIRST.md',
    'examples/chat-session.example.json',
    'forms/form.schema.json',
    'examples/project.example.json',
    'docs/COMPATIBILITY.md',
    'docs/ARCHITECTURE.md',
    'docs/form-preview.png',
)


def build_archive() -> bytes:
    out = BytesIO()
    with ZipFile(out, 'w', compression=ZIP_DEFLATED, compresslevel=9) as archive:
        for rel in INCLUDED:
            src = ROOT / rel
            if not src.is_file():
                raise FileNotFoundError(f'Missing required skill file: {src}')
            entry = ZipInfo(f'audio-studio/{rel}', date_time=(2026, 11, 16, 0, 0, 0))
            entry.create_system = 3
            entry.external_attr = (0o755 if rel.endswith('.sh') else 0o644) << 16
            entry.compress_type = ZIP_DEFLATED
            archive.writestr(entry, src.read_bytes(), compress_type=ZIP_DEFLATED, compresslevel=9)
    return out.getvalue()


def main() -> int:
    parser = argparse.ArgumentParser(description='Build or check Audio Studio skill ZIP')
    parser.add_argument('--check', action='store_true', help='Fail if distribution ZIP is not up to date')
    args = parser.parse_args()
    if args.check:
        if not OUTPUT.is_file():
            print('ERROR: packaged ZIP missing; run python scripts/build_skill_zip.py', file=sys.stderr)
            return 1
        # Compression output can vary between zlib versions and platforms.
        # Validate uncompressed file contents, paths and completeness instead of
        # byte-comparing independently compressed ZIPs.
        expected = {f'audio-studio/{rel}' for rel in INCLUDED}
        with ZipFile(OUTPUT, 'r') as archive:
            found = set(archive.namelist())
            if found != expected:
                print('ERROR: packaged ZIP entries differ from expected source list', file=sys.stderr)
                return 1
            for rel in INCLUDED:
                archived = archive.read(f'audio-studio/{rel}')
                current = (ROOT / rel).read_bytes()
                # Git attributes check out Windows .bat files with CRLF, while
                # the portable skill ZIP may contain LF. Both are equivalent.
                if rel.endswith('.bat'):
                    archived = archived.replace(b'\r\n', b'\n')
                    current = current.replace(b'\r\n', b'\n')
                if archived != current:
                    print(f'ERROR: stale packaged file: {rel}', file=sys.stderr)
                    return 1
        digest = sha256(OUTPUT.read_bytes()).hexdigest()
        print(f'PASS: {OUTPUT.name} contains exactly the current source files; SHA256 {digest}')
    else:
        binary = build_archive()
        digest = sha256(binary).hexdigest()
        OUTPUT.parent.mkdir(exist_ok=True, parents=True)
        OUTPUT.write_bytes(binary)
        print(f'Built {OUTPUT} ({len(binary):,} bytes) SHA256 {digest}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
