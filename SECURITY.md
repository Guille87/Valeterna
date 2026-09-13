# Security Policy

<p align="center"><a href="SECURITY.md">English</a> · <a href="docs/SECURITY_es.md">Español</a></p>

## Supported versions

This is a small hobby project. Only the latest release and `main` receive fixes.

## Reporting a vulnerability

Please **do not open a public issue** for security problems.

Email **guillermo_amado@hotmail.es** with:

- a description of the problem and its impact,
- steps to reproduce,
- the version or commit affected.

You can expect an acknowledgement within a few days. Once a fix is ready it will
be released and the report credited, unless you prefer to stay anonymous.

## Scope notes

- The optional Discord crash report (`config/crash_reporting.py`) scrubs the OS
  username and home paths before sending, and is opt-in and off by default.
- The admin/debug panel is a single-player cheat gated by a password hash in the
  git-ignored `config/secrets.py`; it is not a security boundary.

## Auto-update threat model

The Windows build can update itself (`src/valeterna/updater.py`). Applying
an update is always an explicit player action; the startup check is a plain HTTPS
GET to the GitHub API and sends nothing.

- **What is protected:** the update is downloaded over HTTPS from the GitHub
  Release and its SHA-256 is checked against the `SHA256SUMS` file published in
  the same Release before anything is applied. A hash mismatch, a missing
  `SHA256SUMS`, or a version not strictly newer than the installed one all abort
  the update. This defends against a corrupted download or a network attacker.
- **What is not protected:** anyone who can push a Release to the repository (a
  compromised maintainer account) can publish a matching hash for a malicious
  build. The planned mitigation is an Ed25519 detached signature verified in
  `updater.verify()` with a public key baked into the binary.
