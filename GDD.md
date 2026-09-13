# Game Design Document — Valeterna

<p align="center"><a href="GDD.md">English</a> · <a href="docs/GDD_es.md">Español</a></p>

Living design document for the game's evolution from a combat loop into a text
RPG with a world, a story, NPCs, character classes, skills and a large bestiary.
Version history: [CHANGELOG.md](CHANGELOG.md). Delivery plan:
[ROADMAP.md](ROADMAP.md). Balance notes: [TODO.md](TODO.md).

**Status: planning.** Almost nothing here is built yet — this is the target, it
keeps changing, and none of it is final until it ships. There is **no 1.0
target**: the game ships pre-release versions until the maintainer decides it is
launch-ready.

---

## 1. Vision & pillars

Today the game is: pick an enemy from a list → fight → repeat. The goal is to
keep that combat (it works and is tuned) and wrap it in a **world worth moving
through**: named zones on a map, ~10 enemies per zone, NPCs with branching
dialogue, a dark-fantasy questline, classes, skills learned across the whole
progression, seven damage elements with weaknesses / resistances / immunities.

1. **The combat stays the star.** The ATB system, the enemies, the loot and
   crafting are the core. Everything new deepens the loop of *get stronger →
   push deeper*, it does not replace it.
2. **Exploration is choice, not filler.** Every screen offers a real decision:
   push forward, farm, spend, talk, turn in a quest, go back for something.
3. **Serious dark fantasy.** Valeterna is a dying kingdom. No comic relief.
4. **Still a console game.** Numbered `input()` menus, `colorama` colour, no
   window. The world is described, not drawn.
5. **Additive, not a rewrite.** Each phase ships on top of the last without
   breaking saves or the test suite.
6. **Translatable from the start.** All new player-facing text goes through a
   strings layer (`i18n`) so multi-language is cheap later (see §9.1).
7. **Everything connected.** Skills unlock near the enemies they help against;
   set pieces drop where their theme lives; elements matter because zones lean
   into specific damage types. No system added "for the sake of it".

---

## 2. Story — "La Brecha" (The Breach)

**Premise.** Years ago the **Dragón de Ceniza** razed the capital, Valeterna.
Its fire did more than burn — it cracked the veil between the mortal world and
the planes below. Through that **breach**, things that should not walk the world
spill into the kingdom — the restless dead among them, and worse — and
corruption spreads outward from the ruined capital like rot from a wound. *(The
story never names in advance what the player will fight; the reader knows only
"whatever comes through the breach".)*

The player is one of the few survivors of the razing who can still hold a
weapon. From **Piedrablanca**, the last free village, they set out to **find the
source of the breach and close it** — following the corruption back through
seven increasingly ruined regions. *What waits at the source, and whether
closing it is even possible, is not spelled out up front.* (The Dragón is the
kingdom's historical catastrophe; it is **not** framed as "the boss you are
marching to kill". See §4 for how the final confrontation is handled.)

### Main questline — 7 acts, one per region

The acts thread the regions together with a reason to keep going. **7 acts is
the current shape**; it could grow after 1.0 with a lot more content and
testing, but that is a long-shot, not a plan.

| Act | Region | Beat |
|-----|--------|------|
| I | Los Yermos | Halbrand: break the bandit raids strangling the village. |
| II | Bosque de los Susurros | Cael explains the breach; an altar deep in the forest is feeding it, and something is bound there. |
| III | Ciénaga de los Ahogados | Something older than the breach stirs in the drowned marsh, where the corruption pools. |
| IV | Cañón del Trueno | Mirelle: the corruption flows down the old mountain road, and the pass is sealed. |
| V | Torre de los Arcanos / Necrópolis | Sella: the mage tower is channelling the breach, and the dead are rising across the Necrópolis. |
| VI | Ciudadela en Ruinas | Aldric: the cathedral was the kingdom's last bastion; what holds it now came through the breach, and it is worse than what razed the city. |
| VII | El Corazón de la Brecha | The corruption's true origin lies deeper than the cathedral — and it is not what the survivors expected. |

### Side quests

Optional, never block the path, give meaningful rewards (unique items, recipes,
gold, lore). **Goal: several per region**, so the loop is more than "kill and
advance" — the player has errands, targets and reasons to backtrack. Initial set:

- **La muñeca de Nia** (Los Yermos) — a child's doll lost in the bandit camp.
- **El encargo de Dorn** (Bosque) — Troll hide for a one-off legendary chest.
- **El tomo prohibido de Sella** (Necrópolis) — unlocks a magic-damage recipe.
- More to be designed per region.

### Lore collectibles

Notes (letters, journal pages, inscriptions) found while exploring. Read once,
then stored in a **Diario** re-readable from the character menu. Optional
world-building; adds life to the world without gating anything.

---

## 3. World — zones & map

A graph of **zones** with free backtracking. A zone unlocks when you defeat its
**guardian** (a mini-boss) or complete the story beat that opens it.

```
Piedrablanca (hub, no enemies)
   │
Los Yermos ── Bosque de los Susurros ── Ciénaga de los Ahogados ── Cañón del Trueno ──
   Torre de los Arcanos / Necrópolis ── Ciudadela en Ruinas ── El Corazón de la Brecha
```

**Travel** vs **fast-travel**: you reach a *new* zone by walking from its
neighbour (`Viajar`), only once the gate is open — this is the "frontier".
Once a zone is visited it joins the **fast-travel** list (from the hub or a
signpost): instant, free, for backtracking to shop / craft / turn in quests /
farm. Both are free for now; a road-encounter or a cost could be added later if
backtracking feels frictionless.

| Zone | Theme | Backbone enemies (existing) | Sub-locations | Key NPCs |
|------|-------|-----------------------------|---------------|----------|
| **Piedrablanca** | Last free village | — | Taberna (rest), Herrería, Mercado, Refugio | Yerma, Dorn, Halbrand, Nia |
| **Los Yermos** | Wilds around the village | Goblin, Huargo, Esqueleto, Bandido | Campamento de bandidos, Túmulo | Cael |
| **Bosque de los Susurros** | Haunted forest | Orco, Espíritu Vengativo, Troll | Claro del altar, Cabaña quemada | Mirelle |
| **Ciénaga de los Ahogados** | Drowned marsh | *(all new)* | Templo hundido, Embarcadero podrido | *(new)* |
| **Cañón del Trueno** | Mountain pass, stone | Gárgola, Gólem de Piedra | Mina derrumbada, Puente colgante | Kort |
| **Torre de los Arcanos / Necrópolis** | Mage tower + graveyard | Mago, Nigromante | Biblioteca, Cripta | Sella |
| **Ciudadela en Ruinas** | The razed capital, infernal ground | Ángel Caído, Demonio | Catedral rota, Plaza | Aldric |
| **El Corazón de la Brecha** | The origin — designed last | *(§4)* | — | — |

Shop / forge / rest / save live in Piedrablanca's sub-locations; a "Mercado
errante" and a "Fuego de campamento" (paid rest) appear in later zones.

---

## 4. Enemies — roster design

**Target: ~10 enemies per zone, ~70 total.** The current 14 are the *backbone*
(the mechanically-unique named ones); the rest is new design.

### 4.1 Per-zone structure

Each zone's ~10 enemies:

| Tiers | Role | Notes |
|-------|------|-------|
| 1–4, 6, 8 | **standard** | random encounters weight toward these |
| 5, 7, 9 | **elite** | tougher and rarer, a strong signature ability — above standard, below the guardian |
| 10 | **guardian** | a mini-boss; defeating it once opens the next zone. Stays farmable afterwards |

The **three elites and the guardian each drop one of the zone's four in-zone
set pieces** (§6.3) — so an elite is always worth hunting, and completing a
set's story-mode half means clearing its zone thoroughly.

### 4.2 The final confrontation

The **guardian of El Corazón de la Brecha is the Dragón** — the kingdom's
historical antagonist, returned. It is **designed last**, once the whole roster
exists, so it can sit strictly above everything as the hardest fight in the
game; its stats are unknowable until then and are a deliberate open item. The
story (§2) does not name it as the goal, to keep the ending a reveal and to
leave room for the map to grow past it later.

### 4.3 Enemy template

Every enemy is designed against this template (kept as a living table in
`docs/design/bestiario.md` once phase work starts):

| Field | Meaning |
|-------|---------|
| `nombre` | Spanish, dark-fantasy, no repeats |
| `zona` / `tier` | zone + power rank 1–10 within it |
| `rango` | standard / elite / guardian |
| `arquetipo` | bruiser / skirmisher / caster / support / tank / ambusher |
| `habilidad` | one signature mechanic (§4.5) |
| `elemento` | element its attacks deal (or physical) |
| `debilidades` | 0–2 elements at ×1.5 (minor) or ×2.0 (major) |
| `resistencias` | a budget of 2: two ×0.5 on different elements, or one ×0.25 |
| `inmunidades` | elements taken at ×0 (no damage, no status), plus any standalone status immunity |
| `stats` | from the power budget (§4.4) |
| `drops` | materials + a chance at a unique; commons roll from the zone tier (§7.3) |

### 4.4 Power budget

70 enemies cannot be tuned by eye. Each enemy gets a **power score**; from the
ATB math (`TODO.md`), effective threat scales with `hp × speed × daño_neto`
(net damage = mean damage − effective mitigation). Define a normalised score and
a target curve `objetivo(zona N, tier T) = base · f(N) · g(T)`; design each
enemy within ±10 % of its target, then playtest-verify guardians and a sample
of each tier the way the chain is verified today. The player's expected level at
each zone falls out of this pass too (it is deliberately **not** fixed yet —
see §6.2). Formula and constants live in `TODO.md`.

### 4.5 Signature abilities (menu of mechanics to draw from)

Existing patterns: pre-battle ambush, periodic extra hit, self-heal under a
threshold, unavoidable attack, applied debuff through a hit roll, summon an
ally. New: ranged attack (partly ignores evasion), gold theft, stun (skip a
turn), stacking armour shred, life drain, enrage under a threshold, `consagrar`
(marks the player for bonus damage), curse that blocks healing.

### 4.6 Sample zone — Los Yermos (10)

Demonstrates the template; the other six zones are follow-up design work.

| Tier | Rank | Name | Archetype | Signature | Deals | Weak to | Resists | Immune to |
|------|------|------|-----------|-----------|-------|---------|---------|-----------|
| 1 | standard | Rata Gigante | skirmisher | quick bite, minor poison chance | veneno | fuego | — | — |
| 2 | standard | Goblin | bruiser | ambush after first defeat | físico | — | — | — |
| 3 | standard | Goblin Montaraz | ranged | arrows (partly ignore evasion) | físico | fuego | — | — |
| 4 | standard | Huargo | skirmisher | pack bite (extra hit) | físico | — | — | — |
| 5 | **elite** | Chamán Goblin | support | heals an ally / self, minor curse | oscuridad | sagrado | oscuridad | — |
| 6 | standard | Esqueleto | tank | revives once | físico | sagrado | veneno | veneno, sangrado |
| 7 | **elite** | Bandido | ambusher | disarm | físico | veneno | — | — |
| 8 | standard | Salteador | skirmisher | double quick strike, steals gold | físico | — | — | — |
| 9 | **elite** | Ogro del Yermo | bruiser | crushing blow that stuns | físico | fuego | — | paralizado |
| 10 | **guardian** | El Carnicero | bruiser/tank | enrage below 40 % HP, applies sangrado | físico | sagrado | veneno | — |

---

## 5. Elements & affinities

**Seven elements** + physical (the default, no element). Every element does two
things: it **modifies damage** via the target's affinity, *and* it can apply a
signature **status** on hit.

| Element | Damage type | On-hit status |
|---------|-------------|---------------|
| **fuego** | physical | `quemado` — DoT + **physical** attack output reduced (magic unaffected) |
| **veneno** | physical | `veneno` — DoT vs max HP |
| **rayo** | physical | `paralizado` — chance to skip a turn |
| **hielo** | physical | `congelado` — chance to skip a turn |
| **sagrado** | magical | `consagrado` — takes +25 % damage from all sources, can't self-heal |
| **oscuridad** | magical | `marchito` — healing / regen received −50 % |
| **arcano** | magical | `fractura mágica` — the target's `magic_resist` drops to 0 for the duration (so follow-up magical hits land hard) |

`arcano`'s status replaces the earlier "silence" idea: **`silenciado` is
dropped** — a hard cast-lockout was useless against non-casters and
back-breaking against the Mago. `fractura mágica` is always at least somewhat
useful when you deal magical damage, never a hard shutdown, and thematically
"crack the magic that shields it".

### Affinity model (data layer)

- **Weakness** — base **×1.5**. It becomes **×2.0** only when the damage
  combines *two* elements the enemy is weak to (an elemental reaction, a
  dual-element skill, or hitting a target already carrying a weakness-element
  status with a second weakness element). `Enemy.weaknesses: set[str]`, 0–2
  elements.
- **Resistance** — base **×0.5**; **×0.25** when the damage combines *two*
  elements the enemy resists. Resistance also **halves that element's on-hit
  status chance and duration** (it resists the whole element, not just the
  numbers). `Enemy.resistances: set[str]`, 0–2 elements.
- **Immunity** — the extreme of resistance: that element does **×0 damage** and
  its status **never** applies. Reserved for "it literally cannot be affected"
  (a construct and `veneno`, a wraith and `físico`). `Enemy.immune_elements:
  set[str]`.
- **Standalone status immunity** — takes the element's damage normally but
  can't receive one specific status (something too massive to `paralizar` while
  still taking `rayo` damage). `Enemy.immune_statuses: set[str]`.
- So: **resistant** = shrugs it off (less damage, weaker status); **immune** =
  nothing happens at all. The four knobs cover every case; most enemies use one
  or two.
- Damage: `final = base × affinity`, then armour / magic-resist mitigation
  (magical elements mitigated by `magic_resist`).
- Player elemental defence: `Armor` may carry `resist` (a small dict, a %
  reduction per element), summed as `Player.get_total_resist(element)` — a few
  pieces and a set grant it.

### Elemental reactions *(planned — balance carefully)*

- `fuego` already melts `congelado` (kept).
- `rayo` on a `congelado` target: **shatter** — removes freeze, deals bonus
  damage.
- `fuego` + `veneno` on the same target: the two DoTs combine into a stronger
  one for the shared remaining duration.

Watch that reactions don't become the only viable strategy or trivialise
elite/guardian fights.

---

## 6. Combat systems

### 6.1 Classes

Chosen once at character creation; persisted (as `clase="vagabundo"` on disk for
the balanced class — kept for save compatibility); old saves default to it.

| Class | Identity | Effect |
|-------|----------|--------|
| **Aventurero** | balanced (today's character) | current base stats & growth; the safe default; a flexible skill pool |
| **Guerrero** | tank / bruiser | +HP, +armour, +physical damage; tankier growth; no magic |
| **Pícaro** | fast / crit / poison | +speed, +evasion, +crit chance; agile growth; fragile |
| **Arcanista** | magic / elemental | lower HP/armour; **standard attack is magical** (`is_magical`), scaling with a new *poder mágico* stat — finally makes enemy `magic_resist` matter |

Classes touch character creation, `Stats`, the per-level `_*_GROWTH_RATE`
constants, the Arcanista branch in `_execute_turn`, and which skill pool the
player draws from (§6.2).

**Open design questions (later, not v0.10):**

- **Per-class weapon families.** Each class could only equip weapons from its own
  family — but a *family*, not a single type: Guerrero → blunt / swords / axes /
  maces + shield; Pícaro → daggers *and* other light/finesse weapons; Arcanista →
  staves *and* other caster weapons (wands, orbs…); Aventurero → anything (or a
  broad subset). Needs a weapon-category field on `Weapon` and a filter in the
  equip flow. *(Done: the balanced class was renamed "Vagabundo" → "Aventurero"
  — display only, save value unchanged.)*

### 6.2 Skills

No mana bar. Each class has a **pool of ~8 skills** unlocked across the *whole*
progression, chosen so each one helps against what its region throws at you.
Skills unlock two ways: some **by level** (the early ones), some **by defeating
a region's guardian** (the later ones — so power tracks story progress, not just
grinding). **Exact levels / guardians are set in the power-budget phase
(v0.14)**; until then a skill is tied to its milestone. Milestones: **M1** Los
Yermos · **M2** Bosque · **M3** Ciénaga · **M4** Cañón · **M5**
Torre/Necrópolis · **M6** Ciudadela · **M7** El Corazón.

Two kinds:

- **Passive** — always on once learned, no UI, no slot cost.
- **Active** — an action instead of attacking, with a **cooldown in turns**.
  The player may **equip up to 4 actives at a time** (chosen in the character
  menu) — the strategic choice is which four to bring against a given enemy.
  Cooldown state lives in the battle only, not the save.

Combat gains a **"Habilidades"** menu option (lists the 4 equipped actives and
their ready/cooldown state). In auto/turbo: use a ready equipped active if one
exists, else attack.

Sketch (types: `fís` physical, `mág` magical, `ele` elemental, `util` utility;
`aN` = active, cooldown N turns; `p` = passive; subject to balancing):

| M | Aventurero | Guerrero | Pícaro | Arcanista |
|---|-----------|----------|--------|-----------|
| 1 | Golpe Firme — a3 fís: +40 % dmg, can't miss · Segundo Aliento — p: heal 12 % max HP on kill | Embate — a3 fís: strong hit, 40 % stun · Piel de Piedra — p: −12 % physical dmg taken | Golpe Bajo — a3 fís: guaranteed crit + sangrado · Reflejos — p: +12 % evasion | Proyectil Arcano — a2 arc: pierces magic resist · Sintonía — p: choose your attack element at battle start |
| 2 | Aguante — p: below 30 % HP, +15 % armour & magic resist | Represalia — p: 30 % counter on physical hit | Veneno de Contacto — p: 20 % poison on hit | Escudo de Maná — a4 util: fully absorb next hit |
| 3 | Adaptación — p: +10 % resistance to all elements | Provocación — a4 util: enemy loses precision for 3 turns | Filo Envenenado — a3 ven: hit + stronger guaranteed poison | Descarga Elemental — a4 ele: active element's damage + its status |
| 4 | Adrenalina — a5 util: +25 % speed for 3 turns | Grito de Guerra — a5 util: +25 % damage for 3 turns | Sombra — a4 util: dodge the next enemy attack | Ruptura Arcana — a5 arc: damage + `fractura mágica` (enemy magic resist → 0) for 2 turns |
| 5 | Ruptura — a4 fís: ignores half the enemy's armour | Fortaleza — p: +35 % max HP | Golpe Mortal — p: +50 % crit damage | Doble Conjuro — p: 20 % chance an active costs no cooldown |
| 6 | Botín Afortunado — p: +25 % gold, +10 % drop chance | Golpe Sísmico — a5 fís: high damage, ignores evasion | Marca de Muerte — a5 util: enemy takes +30 % of all damage for 3 turns | Mente Aguda — p: −1 turn to all cooldowns |
| 7 | Voluntad de Hierro — p: survive a lethal hit at 1 HP (once/battle) | Último Bastión — a7 util: 2 turns immune to physical damage | Asalto — a7 fís: 3 quick strikes | Cataclismo — a8 arc: massive magic damage, ignores all mitigation |

#### 6.2.1 Locked decisions for v0.10.0

These were reviewed and fixed with the maintainer; the numbers are provisional
and will be revisited in the v0.14 power-budget phase (tracked in `TODO.md`).

1. **Per-class stat / growth deltas (provisional).** Applied on top of the
   current Aventurero baseline at creation; growth-rate tweaks on top of the
   current `_*_GROWTH_RATE`:
   - **Aventurero** — unchanged (today's character exactly).
   - **Guerrero** — +15 % max HP, +2 base armour, +1 min/max attack; armour
     growth ×1.3; no other magic interaction.
   - **Pícaro** — +3 speed, +5 % evasion, +5 % crit chance, −10 % max HP;
     speed growth ×1.3.
   - **Arcanista** — −15 % max HP, −2 base armour; gains a `poder_mágico` stat
     (see below) that grows every level.
2. **`poder_mágico` and the Arcanista attack.** New `Stats` field, `0` for every
   other class. The Arcanista's standard attack in `_execute_turn` uses
   `poder_mágico` as its damage source **instead of** the weapon's attack range,
   and is flagged `is_magical=True`. Weapons still contribute their secondary
   stats and `element`, just not base damage, for an Arcanista.
3. **Arcanista basic-attack element.** Defaults to `arcano` (matches Proyectil
   Arcano and feeds `fractura mágica`). The **Sintonía** passive (M1) lets the
   player override the element at battle start.
4. **Provisional unlock levels.** M1 skills are granted at **character creation
   (level 1)**; M2 skills at **level 4**. Exact values move to v0.14; a skill
   stays tied to its milestone until then.
5. **Save schema.** v0.10.0 adds only two keys, not the full `mundo` block:
   `clase` (back-fills to `"vagabundo"`) and `habilidades_equipadas` (back-fills
   to `[]`). The complete `mundo` block (§9.4) still lands in v0.12.0.
6. **`Skill` data model.** A dataclass — `id`, `name`, `class`, `kind`
   (`passive` / `active`), `milestone`, `cooldown` — plus a per-skill effect
   hook. Passives are read via `player.has_passive(id)` at the relevant call
   sites (`take_damage`, `_execute_turn`, `_handle_victory`, status processing);
   actives resolve through a dispatch in the battle loop. Lives in
   `characters/skills.py` (§9.3).

### 6.3 Equipment set bonuses *(design under review by the maintainer — deferred to v0.12.0+)*

Confirmed with the maintainer during v0.11.0 planning: this design depends on
zones, elite enemies and guardians (tiers 5/7/9/10 per zone) and the Arena
(§6.5), none of which exist yet — the current game is still the flat 14-enemy
chain. Rather than draft a throwaway "4 sets on the current chain" version now
and redo it once zones land, set bonuses stay unimplemented until v0.12.0+,
when they can be built once against the real zone/elite/guardian structure.
v0.11.0 instead covers the rest of "Gear & real affinities": real per-enemy
weaknesses/resistances/immunities (done, see `TODO.md`), elemental resistance
on armour, new elemental weapons, and elemental reactions.

`Armor` gains optional `set_name`. `Player` counts equipped pieces per set and
applies bonuses at **2, 4 and 6 pieces** — **tiers stack** (with 6 pieces you
have the 2-, 4- and 6-piece bonuses at once). Design goal, Diablo-3-inspired but
adapted to turn-based text: **one set per zone (7 sets)**, each 6 pieces across
6 of the 11 slots (which 6 varies by set), leaving 5 slots for mix-and-match.
Pieces **1–4 drop in the zone** — one each from the three elite enemies (tiers
5, 7, 9) and the guardian (tier 10); pieces **5–6 come from the Arena** (§6.5).
So story mode gets you the 4-piece bonus, the Arena completes the set.

- **2-piece** — a modest, always-useful stat.
- **4-piece** — a strong situational effect.
- **6-piece** — a build-defining effect: the reason to commit.

Draft (names and effects still moving):

| Set | Zone | 2 | 4 | 6 |
|-----|------|---|---|---|
| Atavío del Proscrito | Los Yermos | +evasion | first hit of each battle is a guaranteed crit | after a crit, your next attack also crits |
| Manto del Bosque | Bosque | +regen | 25 % to poison on hit | poisoned enemies take +25 % damage from all sources |
| Cieno Viviente | Ciénaga | +oscuridad resist | your `marchito` also cuts enemy damage 15 % | when an enemy dies while `marchito`, heal 20 % max HP |
| Placas del Guardián | Cañón del Trueno | +armour | −10 % physical damage taken | first time you'd drop below 25 % HP each battle, block all damage for 1 turn |
| Sudario del Nigromante | Torre/Necrópolis | +magic resist | 20 % reflect magic damage | after taking magic damage, your next attack deals bonus arcano damage |
| Égida del Caído | Ciudadela | +sagrado resist | heal 15 % of damage dealt | while above 80 % HP, +30 % damage |
| Escamas de Ceniza | El Corazón | +fuego resist & +max HP | immune to `quemado`, +25 % fuego damage dealt | at battle start, gain a shield worth 20 % max HP |

No set piece is strictly better than its slot's other options. The full list,
which 6 slots each set uses, and the numbers are still being decided.

### 6.4 Status-inflicting weapons

`Weapon` gains `inflicts` = `{status, chance, duration, power}`. On a player
hit, roll `chance` and `enemy.apply_status(...)` (respecting immunities).
Requires **`Enemy` to process status effects on its turn** — a mirror of
`Player.on_turn_start` / `on_turn_end`. Elemental weapon infliction map:
veneno→`veneno`, fuego→`quemado`, hielo→`congelado`, rayo→`paralizado`,
oscuridad→`marchito`, sagrado→`consagrado`, arcano→`fractura mágica`.

### 6.5 Arena mode

A Piedrablanca location unlocked after Act III. Pick a difficulty tier → **N
escalating waves**, enemies from cleared zones. Healing between waves is paid in
gold. It is designed as **high difficulty**, but it is the **only route to the
5th and 6th piece of any set** (§6.3) — story mode caps you at a 4-piece bonus,
the Arena completes it. Rewards scale with the wave reached: gold, cosmetic
**títulos** on the stats screen, set pieces 5–6, and at least one hard-to-get
unique. Save tracks `arena_mejor_oleada`. Pairs with turbo auto-battle. Exact
reward-per-wave table TBD.

---

## 7. Progression & economy

### 7.1 Leveling

Curve TBD in the power-budget phase (§4.4). Levels also gate skills (§6.2).
`poder mágico` is a new `Stats` field, 0 for non-Arcanista, growing for it.

### 7.2 Bestiary — progressive reveal

Keyed on `enemy_kill_counts`, each threshold adding to the sheet:

- **1** → name, HP, attack range, gold, **a lore line / short description**, and —
  once enemies have elemental attacks (v0.11+) — **the element their attacks deal**.
- **3** → armour, magic resist, speed, crit, plus **the enemy's signature ability**
  (its `perform_turn` gimmick: pack bite, disarm, self-heal, earthquake…).
- **5** → elemental weaknesses, resistances and immunities, **the statuses it can
  inflict on you**, and **its standalone status immunities** (what it can't be
  frozen/poisoned/… with).
- **10** → full drop table (first time it is ever shown).

Below 1 kill: not listed (as today). Implementation lands in v0.14.0.

### 7.3 Loot scaling & drop-scaling

- **Uniques** — hand-designed, low drop rate, specific enemies (as today). Set
  pieces and the forge stay hand-designed.
- **Commons** — `items/loot.py` rolls a piece for a slot from the **zone tier's
  ranges**: base stat magnitude + 0–3 secondaries (same rules
  `tests/test_armor_progression.py` enforces).
- **Drop-scaling across zones** — when a material dropped by an early enemy at
  `p %` is *also* dropped by a later-zone enemy, the later enemy drops it at a
  **higher chance and/or quantity**. Backtracking to farm the early source stays
  valid but slower, never optimal. (Exact curve TBD.)

### 7.4 Rest & death

- **Rest** — only in a town, at an inn, paying gold: full HP + all status
  effects cleared. **Cost scales with level**: higher-level enemies pay out more
  gold, so the inn costs more to keep it a real sink — a rough equilibrium. A
  broke player can always farm a few easy fights for gold.
- **Death** — you lose a fraction of your gold (currently 1/3) and it is **gone
  for good** (no recoverable "saco"). You respawn at the last visited town at
  full HP with statuses cleared, losing your position in the current zone.

---

## 8. World systems

### 8.1 Exploration loop

Replaces the flat `game_loop` menu. Inside a zone: **Explorar** (weighted roll:
encounter / discovery / rare mini-event), **Ir a `<sub-lugar>`** (NPC / service
/ quest turn-in), **Viajar** (frontier or fast-travel), **Personaje** (the
always-available character menu: inventory, stats, equip, skills, bestiary,
diary, quests, save — extracted from today's `game_loop`).

### 8.2 Dialogue — branching, with player choices

An NPC owns a set of **conversations**. Each conversation has: an id, a trigger
condition (quest state / story flag / first meeting), a **`repetible`** flag,
and a **tree of nodes**.

- A **node** = NPC text + an optional list of **player choices**.
- A **choice** = the player's line + an optional condition + a link to the next
  node (or an end) + an optional **effect** (set a flag, give an item,
  start/advance a quest, open a service).
- A **non-repeatable** conversation, once played through, is recorded in
  `mundo.dialogos_vistos` and won't trigger again; the NPC falls back to a
  short repeatable idle line.

For the first pass, choices only change the **text** you get — no mechanical
effect — but the framework carries effects for later (easter eggs, surprises,
choice-gated content). Some conversations are one-time (you can't redo them),
which makes those choices feel permanent even while they're cosmetic. **Choice
nodes offer at least 3 responses.** Writing the NPC conversations is left to the
implementer (the maintainer has said this is not their strength); the design
target is a mix of one-time quest/story conversations and repeatable idle/lore
lines per NPC.

### 8.3 Quests

`Quest`: id, title, description, **objective** (kill N of X, reach zone Y, talk
to Z, collect W, or a manual flag), **reward** (gold / item / recipe / flag),
**state** (`no_iniciada` / `activa` / `completada` / `entregada`). Progress is
checked from hooks that already fire (`_handle_victory`, arriving in a zone,
`Inventory.add_item`). A **Misiones** entry in the character menu lists them.

---

## 9. Technical

### 9.1 Strings layer (i18n) — set up first

All player-facing text goes through `t(key, **kwargs)`: an `i18n/` package with
`catalog_es.py` (later `catalog_en.py`) — plain dicts keyed by string id — and a
resolver reading the active locale from `config.ini` `[IDIOMA]` (default `es`).
`ui/console.py` helpers are unchanged (they take resolved strings). **New
content is authored through `t()` from the start;** existing hardcoded Spanish
migrates module by module, starting with combat and menus.

### 9.2 `world/` package

Data-driven like `characters/enemies/` (one file per zone): `world/zone.py`
(`Zone`), `world/npc.py` (`NPC`, `Conversation`, `DialogueNode`, `Choice`),
`world/quest.py` (`Quest`), `world/map.py` (graph, travel, gating),
`world/data/*.py` (one module per zone).

### 9.3 Other new modules

- `characters/skills.py` — skill definitions; `Player` derives its skill pool
  from class, and `known` from level; `habilidades_equipadas` (the ≤4 active
  ids) is stored.
- `items/loot.py` — common-drop roll tables per zone tier.
- `ui/exploration.py` — the zone loop (`omit`ted from coverage like `ui/menus.py`).

### 9.4 Save schema v2

Adds a `mundo` block: `clase`, `zona_actual`, `zonas_visitadas`,
`habilidades_equipadas`, `misiones`, `banderas`, `dialogos_vistos`, `diario`,
`arena_mejor_oleada`. Migration v1 → v2 (`persistence/save_load.py`, same
pattern as prior back-fills): no `mundo` block → placed in the zone matching
`defeated_enemies` progress, class `vagabundo`, everything else empty.
`unlocked_enemies` / `defeated_enemies` stay the source of truth for gating.

### 9.5 Testing

All non-interactive logic is unit-tested: affinity maths (weak / resist /
immune / player elemental defence), status immunity, skill effects & cooldowns
& the 4-slot limit, class stat/growth differences, set-bonus counting, loot
roll ranges, drop-scaling, quest progress, dialogue tree traversal &
conditions & one-time consumption, map travel & gating, i18n resolution &
fallback, save migration. The exploration loop and menus stay `omit`ted from
the coverage metric.

---

## 10. Development phases (pre-release, open-ended)

Each phase is one release; **releases are tagged only on the maintainer's
go-ahead** — features accumulate on `main` via PRs. Order may shuffle; the GDD
is a living document and any of this can change.

| Phase | Theme | Contents |
|-------|-------|----------|
| **v0.9.0** | Foundations | i18n strings layer + migrate combat/menu core · full affinity model (×1.5/×2 weak, ×0.5/×0.25 resist, ×0 immune = no damage, no status) + the 3 new elements as data · player & `Enemy` status processing (status-inflicting weapons) · `quemado` penalises physical attack only |
| **v0.10.0** | Classes & first skills | 4 classes at creation · `poder mágico` stat · skill system (passives always on / cooldown actives) · "Habilidades" menu + choose 4 equipped actives · the first ~2–3 skills per class |
| **v0.11.0** | Gear & real affinities | 4 armour sets · elemental resistance on armour · real weaknesses / resistances / immunities on the current 14 enemies · new elemental weapons (sagrado / oscuridad / arcano) · elemental reactions |
| **v0.12.0** | The world, part 1 | zones + map + exploration loop · inn / rest (cost scales with level) · frontier travel + fast-travel · save migration v2 · shop / forge relocated · random encounters + discoveries |
| **v0.13.0** | Dialogue & NPCs | branching dialogue with player choices · one-time vs repeatable conversations · NPCs for Piedrablanca + the 6 existing regions · lore notes + Diario |
| **v0.14.0** | Bestiary & enemies I | progressive bestiary · power-budget tool (sets the level curve) · Los Yermos + Bosque fleshed to ~10 (elites 5/7/9 + guardian 10) · mid-progression class skills tied to those enemies |
| **v0.15.0** | Enemies II | Ciénaga (new) + Cañón + Torre/Necrópolis to ~10 · loot scaling (uniques + rolled commons) · cross-zone drop-scaling · more class skills |
| **v0.16.0** | Enemies III | Ciudadela to ~10 · high-milestone class skills · side quests for those regions |
| **v0.17.0** | Main story | quest system · "La Brecha" questline (7 acts) wired to the existing NPCs / guardians · progression by story instead of picking an enemy |
| **v0.18.0** | The Arena | escalating-wave mode · Arena rewards (titles + some set pieces + a hard-to-get unique) |
| **later** | Endgame & polish | full roster → **Dragón final tuning** + El Corazón de la Brecha · full chain rebalance · Ed25519 updater signature · gameplay GIF · cleaner MVC · *(stretch)* multi-enemy combat · *(very long term)* possible extra acts |
| **1.0** | — | called by the maintainer when the game is launch-ready |

---

## 11. Open questions

- **Set bonuses** (§6.3) — 7 sets (one per zone), 2/4/6 tiers, pieces 1–4 from
  the elites + guardian, 5–6 from the Arena: the direction is set, the names /
  which-6-slots / exact numbers are not. Mine Diablo 3's set catalogue for
  adaptable ideas.
- **Elemental reactions** (§5) — final rules and, above all, that they don't
  break elite/guardian fights.
- **Skill unlocks** — split between "by level" (early) and "by guardian defeat"
  (later); the exact split comes out of the power-budget phase.
- **Standalone status immunities** — decided per enemy as the roster is built.
- **Arena** — the wave-to-reward table, and exactly which unique(s) it grants.
- **Drop-scaling curve** — "slightly higher chance, slightly higher quantity",
  numbers from playtesting.
- **Rest cost curve** — the gold-per-level formula, tuned against gold income.
