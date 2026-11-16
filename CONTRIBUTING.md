# Contributing to Audio Studio

Thank you for helping improve an accessible, privacy-conscious audio tool.

## Before submitting a change

- Open an issue for substantial new features or behavior changes.
- Fork the project and create a focused branch.
- Keep changes narrowly scoped and update the user documentation when behavior changes.
- Run `python -m unittest discover -s tests -p 'test*.py' -v` with FFmpeg available.
- Add regression tests for bug fixes, especially fades, gap durations, voice-only regions and file validation.
- Use synthetic audio in tests. **Never post another person's voice recordings or unlicensed music.**
- Rebuild the skill ZIP using `python scripts/build_skill_zip.py` when bundled files change.

## Pull-request checklist

Describe the problem, solution, safety implications, relevant test output, and any new limitations. Tests must not depend on paid APIs or undisclosed downloads.

## Code style

Python 3.10+ standard-library compatibility, clear functions, explicit errors, safe subprocess arguments (no `shell=True`), and helpful exception messages. Maintain the five-section form wherever possible.

See [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) and [SECURITY.md](SECURITY.md).
