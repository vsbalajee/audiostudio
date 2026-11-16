# Security policy

## Supported releases

Once releases are published, the latest release is the version intended for maintenance. Older source packages may not receive fixes.

## Reporting a vulnerability

Please **do not publish exploit details or private recordings in a public GitHub issue**. Contact the repository maintainer privately through GitHub's profile/contact information, or use GitHub's private vulnerability reporting feature when enabled.

We will acknowledge credible reports as capacity permits. We do not promise a fixed response time or commercial SLA.

## Threat model and safe use

- Only open audio files and ZIP archives from sources you trust. FFmpeg and archive decoders may have upstream vulnerabilities; keep them updated.
- The desktop form extracts supported media from ZIP archives to a temporary directory; it uses generated filenames and upper limits on declared uncompressed size. ZIP metadata is not a guarantee against every malicious archive.
- Processing runs **locally**. No built-in account login, network uploads, telemetry, or cloud backend.
- A public GitHub repository is **not** a secure location for personal voices, private project mixes, tokens, passwords, or commercial instrumentals.
- Never execute untrusted code solely because an AI assistant was given a public GitHub link. Review the skill's contents and requested permissions.
- FFmpeg is a separate tool with its own license and security update schedule.

## Privacy

This software has no service-side user accounts or recordings database. It operates on files the user chooses and writes results to the configured directory. Only share outputs with explicit permission.
