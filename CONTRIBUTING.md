# Contributing

<p align="center"><a href="CONTRIBUTING.md">English</a> · <a href="docs/CONTRIBUTING_es.md">Español</a></p>

Thanks for your interest. The project is small; these are the conventions.

## Before you start

- **Python 3.10 or newer** (CI runs 3.10–3.13). `pip install -e ".[dev]"` brings
  `pytest`, `pytest-cov` and `ruff`; nothing else is needed.
- **Windows only** for now (`msvcrt` is used in `combat/battle.py` so auto-battle
  can be cancelled with `q`).
- Everyday commands are in the [README](README.md); the architecture is in
  [CLAUDE.md](CLAUDE.md); the detailed balance-tuning history is in [TODO.md](TODO.md).

## Workflow

1. Branch from `main`.
2. One commit per logical unit of change.
3. Run `ruff format .`, then `ruff check .`, then `pyright`, then `pytest`: everything must pass.
4. Open a pull request. CI runs Ruff and the tests on Python 3.10–3.13 (Windows)
   and refreshes the coverage badge; it must be green.

## Conventions

- **Code and comments in Spanish**, consistent with the rest of the project.
  There is no i18n layer: the game's text is printed directly.
- **All terminal colour goes through `ui/console.py`** (`success` / `error` /
  `warning` / `info` / `colorize`), never `colorama` directly.
- **Commit messages**: prefix with `feat:`, `fix:`, `docs:`, `refactor:`,
  `test:`, `ci:`, `build:`, `style:` or `chore:`, and the rest in the imperative.
- No `Co-Authored-By` line from AI tools in commits.
- **Save compatibility**: when adding a field to `Stats` or the save payload,
  read it back with `.get(key, default)` in `persistence/save_load.py` so saves
  from older versions keep loading. There are tests that load minimal/legacy saves.

## Adding an enemy or an item

The full pattern is in [CLAUDE.md](CLAUDE.md):

- **Enemy**: one file in `characters/enemies/` with a class that subclasses
  `Enemy` and overrides `perform_turn()` / `drop_item()`; register the
  Spanish name in `ui/menus.py::_get_enemy_instance()` and slot it into
  `combat/battle.py::ENEMY_PROGRESSION`.
- **Item**: register the class in `items/factory.py::_ITEM_CLASSES` and implement
  `to_dict()` / `from_dict()`, or save/load will silently drop it.

Any logic change comes with its test.

## Regenerating the README screenshot

`docs/screenshot.svg` is produced by `tools/capture_screenshot.py` (a real,
seeded battle rendered as a terminal SVG). To refresh it:

```bash
pip install ansitoimg
python tools/capture_screenshot.py
```

## Releasing a version

- Bump `version` in `pyproject.toml`, then re-run `pip install -e .` so
  `valeterna.__version__` picks up the new value locally (CI and the
  release build always install fresh, so they are always correct).
- Move the relevant entries from *Unreleased* to the new version in
  [`CHANGELOG.md`](CHANGELOG.md) and [`docs/CHANGELOG_es.md`](docs/CHANGELOG_es.md).
- Tag and push:

  ```bash
  git tag vX.Y.Z && git push origin vX.Y.Z
  ```

The release workflow builds the Windows package and attaches it to the GitHub
Release, together with a `SHA256SUMS` file. Both are required — the packaged
game's auto-updater refuses to apply a release that has no matching
`-windows.zip` and `SHA256SUMS` pair.
