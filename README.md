# Valeterna

<p align="center"><a href="README.md">English</a> · <a href="docs/README_es.md">Español</a></p>

[![CI](https://github.com/Guille87/Valeterna/actions/workflows/ci.yml/badge.svg)](https://github.com/Guille87/Valeterna/actions/workflows/ci.yml)
[![Coverage](https://raw.githubusercontent.com/Guille87/Valeterna/badges/coverage.svg)](https://github.com/Guille87/Valeterna/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Contributors](https://img.shields.io/github/contributors/Guille87/Valeterna)](https://github.com/Guille87/Valeterna/graphs/contributors)
[![Issues](https://img.shields.io/github/issues/Guille87/Valeterna)](https://github.com/Guille87/Valeterna/issues)
[![Pull requests](https://img.shields.io/github/issues-pr/Guille87/Valeterna)](https://github.com/Guille87/Valeterna/pulls)

**Valeterna** is a Spanish-language, terminal-based turn-based RPG written in Python.
Fight your way through a chain of 14 enemies, manage gear and potions, craft
equipment and grow your character. It is played entirely in the console — there
is no graphical window; `colorama` adds colour and `pygame` (mixer only) plays
background music.

<p align="center"><img src="docs/screenshot.svg" alt="A Goblin battle: attack, ATB turns, victory and level-up" width="640"></p>

## Features

- **Active Time Battle** combat: the faster combatant acts more often, not just
  strict alternation.
- **14 enemies** with unique mechanics and a fixed unlock chain, ending with the Dragon.
- **11 Diablo-style equipment slots** with a guaranteed base stat per slot plus random secondaries.
- **Forge** (12 recipes), **shop** and a **bestiary** that fills in as you win.
- Physical vs. magical damage, penetration, elemental weaknesses, status effects.
- JSON save/load with automatic backup; optional on-disk error log and Discord crash report.

## Requirements

- Python **3.10 or newer** (CI runs 3.10–3.13).
- **Windows only** for now: the auto-battle mode uses `msvcrt` to cancel with `q`.

## Install

```powershell
git clone https://github.com/Guille87/Valeterna.git
cd Valeterna
python -m venv env
.\env\Scripts\activate
pip install -e ".[dev]"
```

The `[dev]` extra adds `pytest`, `pytest-cov` and `ruff`. For playing only, `pip install -e .` is enough.

## Run

```bash
python main.py
# or: python -m valeterna
# or, after install: valeterna
```

## Tests

```bash
pytest                              # run the suite
pytest --cov=valeterna        # with coverage
ruff check . && ruff format --check .
```

## Build a standalone executable

```powershell
pip install pyinstaller
pyinstaller Valeterna.spec
```

The result is in `dist\Valeterna\` — copy the **whole folder** (it needs the
bundled assets and DLLs). `config.ini`, `saved_games\` and `logs\` are created
next to the `.exe`. Use `--onedir` (the spec already does), never `--onefile`.

The packaged game **updates itself**: on startup it checks the GitHub Releases
for a newer version and, if you accept, downloads it, verifies its SHA-256 and
restarts — `saved_games\` and `config.ini` are kept. Turn the check off under
*Opciones*.

Optional error reporting to Discord lives in `src/valeterna/config/secrets.py`
(git-ignored). Copy `config/secrets.example.py` to `config/secrets.py` and fill it
in before building; without it the game runs fine, just without crash reports.

## Documentation

- [Contributing](CONTRIBUTING.md) — workflow and conventions.
- [GDD](GDD.md) — game design document (world, story, RPG direction).
- [Roadmap](ROADMAP.md) — what is done and what is planned.
- [Changelog](CHANGELOG.md) — version history.
- [CLAUDE.md](CLAUDE.md) — detailed architecture notes.
- [TODO.md](TODO.md) — detailed balance-tuning history.

## License

[MIT](LICENSE) © 2026 Guillermo Amado.
