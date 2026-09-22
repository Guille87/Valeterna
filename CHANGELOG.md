# Changelog

<p align="center"><a href="CHANGELOG.md">English</a> · <a href="docs/CHANGELOG_es.md">Español</a></p>

All notable changes to this project are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added

- **Real elemental affinities for all 14 enemies** (GDD §5, v0.11.0-a): every
  enemy now declares actual weaknesses, resistances, and immunities instead of
  the old single-element ×2.0 legacy dict (now removed entirely). See
  `CLAUDE.md` for the full table. Follow-up polish from playtesting: reworded
  the "resists" message so it doesn't read as full immunity, dropped a
  redundant "blocked the attack" line when a hit is already elemental-immune,
  Veneno de Contacto now announces immunity instead of staying silent, and
  Espíritu Vengativo can no longer bleed (incorporeal).
- **Elemental resistance on armour + 3 new elemental weapons** (GDD §5/§6.4,
  v0.11.0-b): `Armor` can now carry `resist` (% damage reduction per element,
  summed via `Player.get_total_resist()`, capped at 75%) — granted so far by
  Cinturón de Resistencia (arcano), Amuleto de Resistencia (oscuridad) and
  Anillo de Vitalidad (sagrado). New craftable weapons Espada Consagrada
  (sagrado), Daga Umbría (oscuridad) and Vara Arcana (arcano) — the first
  player-obtainable weapons for those 3 elements. Also fixed a related gap:
  whether a hit is physical or magical is now decided by the weapon's element
  (any class wielding a sagrado/oscuridad/arcano weapon deals magic-resist-
  mitigated damage), not just by being an Arcanista.
- **Elemental reactions** (GDD §5, v0.11.0-c): "Shatter" — a rayo hit against a
  frozen (congelado) target instantly breaks the ice and deals 1.5× bonus
  damage instead of attempting the normal paralysis, on both `Player` and
  `Enemy`. "Combustion" — applying quemado while veneno is already active (or
  vice versa) merges both into a single `combustion` status that deals more
  damage per turn than either alone, halves physical attack like burn does,
  and stays curable by Antídoto (its description now says so too). Follow-up
  fixes from playtesting: the "X has been burned/poisoned" message now always
  prints *before* the "fire and poison merge into combustion" one, not after;
  and once combustion is active, a further attempt to burn or poison the same
  target no longer does anything (no duration refresh, no repeated fusion
  message) — it's already both at once.
- **World package foundations** (GDD §3/§9.2/§9.4, v0.12.0-a): a new `world/`
  package holds zone data — `Zone` (id, name, theme, backbone enemies,
  sub-locations, key NPCs) and one module per zone in `world/data/`, collected
  into `world/map.py`'s `ZONE_ORDER`/`ZONES`. Save schema v2 adds a `mundo`
  block to the save file (`zona_actual`, `zonas_visitadas`, `misiones`,
  `banderas`, `dialogos_vistos`, `diario`, `arena_mejor_oleada`), migrated
  automatically for saves from before this change (the current zone is
  inferred from combat progress). Purely groundwork — nothing in `game_loop`
  uses zones yet; that's the next sub-phase.
- **Zone exploration loop** (GDD §8.1, v0.12.0-b): the old flat `game_loop`
  menu is gone, replaced by a new per-zone menu (`ui/exploration.py`) —
  **Explorar** (a weighted roll: combat against a random unlocked enemy from
  the current zone, a small gold discovery, or nothing), **Ir a...** (lists
  the zone's sub-locations; a stub for now, no NPCs until v0.13.0), **Viajar**
  (fast-travel to any visited zone, plus "frontera" to the next zone once
  reachable), and **Personaje** (everything else that used to be the whole
  menu: inventory, shop, forge, stats, skills, bestiary, equip, options,
  save). Picking a specific enemy to fight by name is gone — combat now only
  happens through Explorar's roll.
- **Zone services: shop/forge relocated + rest + discovery variety** (GDD
  §7.4/§8.1, v0.12.0-c): Tienda and Herrería moved out of the Personaje menu
  into Piedrablanca's "Ir a..." — Mercado opens the shop, Herrería the forge.
  New "Taberna" rest: full heal + clears all status effects for gold (cost
  scales with level, a provisional number not yet balance-tuned). Explorar's
  discovery outcome now sometimes gives a free healing potion instead of
  always gold.

- **Dialogue engine** (GDD §8.2, v0.13.0-a): new `world/npc.py` with NPCs, branching conversations, player replies (conditions on story flags/level, effects: set a flag, give gold or an item), conversations you can come back to (replies you have already exhausted get a green check, gifts are only given once, and the NPC falls back to idle lines once the whole tree is done), and a new "Hablar con..." option in the zone menu. Only Yerma (Piedrablanca) had content at first.

- **Power budget tool** (GDD §4.4, v0.14.0-b): a design-time helper (not a game screen) that scores an enemy's intrinsic threat (`max_health × speed × net_damage`) and compares it to a target curve fit to the existing roster — used from here on to sanity-check a new enemy's stats before writing its code, instead of only finding out via hundreds of simulated fights. Daño Crítico now shown as a bonus percentage (e.g. `+60%`) instead of a raw multiplier (`x1.60`) or the total (`160%`) — everywhere it appears: Bestiario, battle info and character stats.

- **Progressive bestiary** (GDD §7.2, v0.14.0-a): an enemy's entry now fills in as you defeat it more often. **1 kill**: lore line, HP, attack, gold and the elements its attacks deal. **3 kills**: the rest of its stats and its signature ability. **5 kills**: weaknesses / resistances / immunities, the statuses it can inflict on you and the ones it is immune to. **10 kills**: its full drop table with probabilities. A hint tells you how many more kills reveal the next tier. All 14 enemies got a lore line and a one-sentence ability description.

- **Lore notes and the Diario** (GDD §2, v0.13.0-c): the sub-locations without a service of their own (Refugio, Campamento de bandidos, Túmulo, Claro del altar, Templo hundido, Biblioteca, Cripta, Catedral rota, Plaza...) now hold a lore note — a letter, an inscription, a journal page — that you read the first time you visit. 13 notes in total. They are kept in a new **Diario** (Personaje menu, with a found/total counter) where you can reread them, grouped by zone.

- **NPC cast** (GDD §3, v0.13.0-b): Halbrand, Dorn and Nia join Yerma in Piedrablanca, and every other region gets its key NPC — Cael (Los Yermos), Mirelle (Bosque de los Susurros), Oren (Ciénaga, a new ferryman), Kort (Cañón del Trueno), Sella (Torre/Necrópolis) and Aldric (Ciudadela). Each has a branching first-meeting conversation, a follow-up that only unlocks once you have met another NPC (so talking around and backtracking pays off), and idle lines. Dorn, Oren and Kort give small one-time gifts. Story-only for now: quests arrive later.

### Changed

- **Combat menu reordered**: Attack, Skills, Defend, Items, Flee, Info,
  Auto-Battle, Auto-Battle Turbo (was Attack, Items, Info, Flee, Defend,
  Skills, ...) — groups the two action choices (attack/skills) and the
  defensive option (defend) up front, before the utility ones.
- **Project renamed from "JuegoRolTexto" to Valeterna** (the kingdom name from
  the GDD) — nobody had downloaded a build yet, so this was a clean cut with no
  compatibility shim: the Python package (`src/valeterna/`, all imports),
  distribution/script name (`valeterna`), the PyInstaller spec/executable
  (`Valeterna.spec` → `Valeterna.exe`), the GitHub repository, and every doc/CI
  reference now use the new name.

### Fixed

- **Admin login no longer hangs on non-terminal consoles** (e.g. PyCharm's
  "Run" panel, as opposed to its "Terminal" tab): `getpass.getpass()` needs a
  real terminal to hide input, and on some IDE consoles it doesn't raise an
  exception when it can't get one — it just hangs, accepting Enter as if it
  were part of the password, never returning. `_check_admin_password()` now
  checks `sys.stdin.isatty()` first and goes straight to the visible fallback
  when there's no real terminal, instead of relying on an exception that might
  never come.

## [0.10.0] - 2026-09-09

### Added

- **Skills** (GDD §6.2): each class now has a skill pool. **Passives** are always
  on once learned; **actives** replace your attack and have a turn cooldown — you
  equip up to 4 to bring into a fight. New "Habilidades" menu to manage them and a
  "Habilidades" combat action to use them (auto-battle uses a ready active if it
  has one). This release ships milestone 1 (one active + one passive per class,
  learned at creation): Golpe Firme / Segundo Aliento (Aventurero), Embate / Piel
  de Piedra (Guerrero), Golpe Bajo / Reflejos (Pícaro), Proyectil Arcano /
  Sintonía (Arcanista). New `sangrado` (bleed) and `aturdido` (stun) statuses,
  each with its own message and colour. Numbers are provisional.
- **Milestone 2 skills** (learned at level 4, provisional): Aguante (Aventurero —
  below 30% HP, +15% armour and magic resist), Represalia (Guerrero — 30% to
  counterattack a physical hit), Veneno de Contacto (Pícaro — 20% to poison on
  hit), Escudo de Maná (Arcanista — active a4: fully absorbs the next hit).

- **Auto-battle chains**: after you turn on Auto-Battle or Turbo against an
  already-defeated enemy, the game asks how many fights to run back-to-back (up
  to 20). Each resolves as normal (loot, gold, XP, post-battle heal) and the next
  starts on its own — no menu, no per-fight "press Enter". The chain stops if you
  fall or flee; pressing `Q` drops you back to manual control, and you can switch
  Auto ↔ Turbo mid-chain from the menu. At the end (win or loss) it prints a
  summary of everything gained across the whole chain — gold, XP, levels, and
  each item with its type (weapon / armour + slot / potion / forge material).

- **Character classes** (GDD §6.1): pick one of **Aventurero** (the classic
  balanced character), **Guerrero** (tank), **Pícaro** (fast / crit / fragile) or
  **Arcanista** (magic) at character creation. Each has its own starting stats
  and per-level growth. Old saves and existing characters stay Aventurero.
- **`poder mágico`** stat: the Arcanista's standard attack is magical
  (`is_magical`), scales with `poder mágico` instead of the weapon, defaults to
  the `arcano` element, and is mitigated by the enemy's magic resist — so
  `magic_resist` finally matters against a player. Grows every level for the
  Arcanista only.
- Save files now record `clase` and `habilidades_equipadas` (the latter unused
  until the skill system lands).

### Changed

- Stat sheets (the "Estadísticas" menu and both in-combat info panels) group
  related stats on one line: armour + magic resist, precision + evasion, crit
  chance + crit damage; XP now sits next to the level. The combat info panel also
  shows the player's crit damage and the enemy's crit chance + crit damage.
- The admin character now picks a class too, so the classes can be tested with
  cheat stats.
- The "new version available" notice now shows every time the main menu is drawn
  and again when you enter "Nueva Partida" / "Cargar Partida" (before the name
  prompt), instead of only once per session — easy to miss otherwise. In-game it
  still shows just once, on entering the session.
- Combat no longer cuts the current track for a standard enemy — only the final
  boss and the five hard late-game enemies switch to dedicated battle music. Keeps
  short (and chained auto-) fights from restarting the music every few seconds.
  (When zone elites/guardians exist they'll be what triggers battle music — see
  `TODO.md`.)
- Combat info sheets now print before a pre-battle ambush, not after, so you see
  the matchup first. A line also states who has the initiative (higher speed),
  and each action is now headed `── Turno N · Name ──` (with the class for the
  player). A short pause after the enemy's turn lets you read the damage before
  the menu redraws.
- The balanced class is now called **Aventurero** (was "Vagabundo") — display
  name only; the save value is unchanged.
- The victory loot line shows each dropped item's type (weapon / armour + slot /
  potion / forge material) and, for weapons and armour, the stats it grants.
  Potions no longer repeat what they do (it was already in the description).
- Turbo auto-battle keeps its speed (no pauses / sleeps) but no longer hides the
  health bars after the enemy's turn — you can see how the fight is going.
- A dodged attack now reads "X lo esquiva" instead of "falla el golpe" — attacks
  never miss on their own, only when the target dodges (evasion vs precision).
- More status effects are colour-coded: `sangrado` (light red, distinct from
  burn), `aturdido` (light yellow, distinct from paralysis), `desarmado`,
  `maldición`, `confusión`.

## [0.9.0] - 2026-09-09

### Added

- **Elemental affinity model** (GDD §5): enemies can now be weak to, resist or be
  immune to each of the 7 elements. Weakness ×1.5 damage (×2.0 if two of the
  attack's elements are weak), resistance ×0.5 (×0.25 if two), immunity ×0 damage
  and no status. Separate standalone immunity to individual status effects.
- **Status effects on enemies**: burn, poison, paralysis, freeze, `fractura
  mágica` (zeroes magic resist) and the rest are now processed on the enemy's
  turn (damage over time, skipped turns, fade messages) the same way they already
  were on the player.
- **Weapons that inflict status**: a weapon with an element (or an explicit
  `inflicts`) has a chance to apply the matching status on hit. Chance and
  duration are halved against an enemy that resists the element, and blocked
  entirely against one immune to it.
- **i18n string layer** (`i18n.t(key, **kwargs)`, GDD §9.1): combat/status
  strings now come from a locale catalog with fallback to Spanish then to the
  key. Language is read from `config.ini` `[IDIOMA]`. Only the new v0.9.0 strings
  are migrated for now.
- Frozen / paralysed combatants are guaranteed to lose the turn the status is
  applied; only afterwards do the per-turn escape rolls apply.
- Status badges on the combat health bars show each active effect and its
  remaining turns (e.g. `[quemado 2 · veneno 1]`).
- Shop: stackable items (potions, antidotes) can be bought and sold several at a
  time, up to what your gold allows — one summary message instead of one line per
  unit. Shop, sell menu and forge lines are colour-coded.
- Admin panel: "get x20 of every potion".

### Changed

- **Damage mitigation is now multiplicative** (Raid-style diminishing returns):
  `damage × K / (defence + K)` with `K = 20`, never fully absorbed (minimum 1),
  replacing the old `damage − armour` subtraction that broke down at scale. This
  is a balance shift; the 14-enemy chain will be recalibrated in a later pass.
- `quemado` (burn) is now physical-only — it no longer melts on any magical hit,
  only on an explicitly fire-flagged one.
- The Gólem de Piedra is now weak to `hielo` and immune to `rayo` (was weak to
  `rayo`).
- A paralysed / frozen player now gets the normal turn menu (use items, attempt
  to flee at half chance) instead of the turn being skipped automatically; no
  "Defender" while immobilised.
- Combat message order cleaned up: the critical-hit note and any inflicted-status
  note now come after the damage line, not before it.

### Fixed

- The Bandido can no longer re-disarm an already-disarmed player (fights that
  consisted only of repeated disarms).
- Enemy spellcasters (Mago) now print the damage number of each spell.
- A paralysed / frozen enemy no longer prints a turn header and duplicate health
  bars for a turn it does nothing on.
- A disarmed player's attacks no longer carry the (now dropped) weapon's element
  or status.

## [0.8.0] - 2026-09-08

### Fixed

- Auto-update: the relauncher `.bat` is now started with `os.startfile`
  (ShellExecute) instead of `subprocess.Popen`, which intermittently failed with
  `0xC0000142` (cmd.exe init failure) when spawned during the game's shutdown.
  A short grace period was also added before the game exits.
- Closing stdin (piped input running out, no TTY) now exits the game cleanly
  instead of raising `EOFError` as an unexpected crash (which also fired the
  optional Discord report).

## [0.7.0] - 2026-09-08

### Added

- Battle start always shows both combat sheets (player and enemy) regardless of
  turn order; an enemy you haven't defeated yet is shown as `???`.
- Turbo auto-battle: a second auto-battle option with no turn pauses, no
  per-turn health bar and no victory prompt — for fast farming of enemies you
  can already beat easily.
- Stat sheets (player, enemy info, bestiary) are colour-coded per stat.
- Any text mentioning a status effect is colour-coded consistently everywhere:
  poison green, burn red, paralysis yellow, freeze blue.

### Changed

- The Goblin never ambushes until it has been defeated at least once (the very
  first fight of the game is always clean).

## [0.6.0] - 2026-09-08

### Fixed

- Auto-update apply step: the relauncher `.bat` now runs in its own console
  (so it survives the game closing and its commands actually work), waits for
  the game by process name, mirrors the new build with `robocopy /MIR` (removing
  stale files — notably the old version's `*.dist-info`, which left the updated
  game still reporting the previous version), protects `config.ini` and the save
  folder, and writes an `apply.log`.

## [0.5.0] - 2026-09-08

### Added

- "Defender" combat action: spend your turn to halve the damage you take until
  your next turn.
- Antidote potion: instantly clears poison, burn, paralysis and freeze. Sold in
  the shop.
- The game version is shown under the main-menu and in-game menu titles.

## [0.4.0] - 2026-09-08

### Added

- Cross-platform, non-blocking keyboard input (`ui/keyboard.py`); the game and
  test suite no longer require Windows.
- Static type checking with `pyright` (basic mode) as a required CI check.
- Boot smoke test (`app.main()` starts and exits cleanly).
- README screenshot generated from a real battle (`tools/capture_screenshot.py`).
- CI `build-check` — builds the `.exe` when packaging files change.
- Auto-update (frozen build): checks GitHub Releases on startup and shows a
  notice when a newer version is available; toggle and manual check in Options.
- Auto-update can now download, verify (SHA-256 against the Release's
  `SHA256SUMS`) and apply an update, restarting the game via a `.bat` relauncher
  without touching `saved_games/` or `config.ini`.
- Release workflow publishes a `SHA256SUMS` file alongside the Windows zip.

### Changed

- CI runs the test matrix on Linux (3.10–3.13) plus one Windows job.
- Branch protection on `main`: PR + green CI required; the coverage badge lives
  on an orphan `badges` branch.
- Ruff rule set extended with `UP`, `B` and `SIM`.

## [0.3.0] - 2026-09-07

First tagged release. Adds error reporting, project infrastructure and a large
test-coverage pass on top of the 0.2.0 baseline.

### Added

- On-disk error logging: `logs/juego.log` (rotating) and a standalone
  `logs/crash_<timestamp>.txt` per crash, with the window held open so a
  packaged `.exe` player can read the path.
- Optional, opt-in crash report to a Discord webhook, with the developer
  mentioned and OS username / home paths scrubbed. Configured via
  `config/secrets.py`; toggleable under *Options*.
- `config/secrets.py` (git-ignored) for the Discord webhook, mention ID and the
  admin password hash, with a committed `config/secrets.example.py` template and
  a tolerant `config/secret_store.py` accessor.
- The player is now recognised by the name they registered the save with:
  loading is case-insensitive and the canonical name is restored; *New Game*
  refuses a name that already has a save.
- Continuous integration (GitHub Actions): Ruff and the test suite on Python
  3.10–3.13 (Windows), plus a self-committed coverage badge.
- Release workflow: tagging `vX.Y.Z` builds the Windows package and attaches it
  to the GitHub Release.
- Project files: `LICENSE` (MIT), `CONTRIBUTING`, `ROADMAP`, this `CHANGELOG`,
  `CODE_OF_CONDUCT`, `SECURITY`, issue/PR templates, Dependabot, `.editorconfig`.
- Ruff as linter and formatter (conservative rule set), configured in `pyproject.toml`.
- Test-coverage pass: 70% → 91% (238 tests). `ui/menus.py` and `app.py` are
  excluded from the metric as interactive glue.

### Fixed

- The game crashed when opening the inventory while holding a crafting material
  (items with no stats did not implement `get_stats_info()`).
- Audio error `Audio device hasn't been opened` printed on exit, caused by the
  music watchdog thread running after the mixer was closed.

### Removed

- `tools/settings_admin.py` — dead code (an unused Tkinter settings window).

## [0.2.0] - 2026-09-06

Baseline: the state of the game when this changelog started. Earlier changes
were not formally tracked.

### Added

- Active Time Battle turn system, 1-vs-1.
- 14 enemies with unique mechanics and a fixed unlock chain.
- 11 Diablo-style equipment slots with a per-slot base stat and secondary stats.
- Forge (12 recipes), shop and bestiary.
- Password-protected admin/debug panel.
- Mood-based background music (adventure / battle).
- JSON + base64 save/load with backup fallback.
- PyInstaller packaging for Windows.

## [0.1.0] - 2024-05-04

### Added

- Initial version: basic console turn-based combat.

[Unreleased]: https://github.com/Guille87/Valeterna/compare/v0.10.0...HEAD
[0.10.0]: https://github.com/Guille87/Valeterna/compare/v0.9.0...v0.10.0
[0.9.0]: https://github.com/Guille87/Valeterna/compare/v0.8.0...v0.9.0
[0.8.0]: https://github.com/Guille87/Valeterna/compare/v0.7.0...v0.8.0
[0.7.0]: https://github.com/Guille87/Valeterna/compare/v0.6.0...v0.7.0
[0.6.0]: https://github.com/Guille87/Valeterna/compare/v0.5.0...v0.6.0
[0.5.0]: https://github.com/Guille87/Valeterna/compare/v0.4.0...v0.5.0
[0.4.0]: https://github.com/Guille87/Valeterna/compare/v0.3.0...v0.4.0
[0.3.0]: https://github.com/Guille87/Valeterna/releases/tag/v0.3.0
