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

Notes (letters, journal pages, inscriptions) found by visiting a zone's
sub-locations (implemented in v0.13.0-c: one note per sub-location that has no service
of its own, read on the first visit). Then stored in a **Diario** re-readable from the
character menu. Optional
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

**Travel** vs **fast-travel** *(implemented in v0.12.0-b)*: you reach a *new*
zone by walking from its neighbour (`Viajar`), only once the gate is open —
this is the "frontier" (`world.map.is_zone_reachable()`: the zone's first
backbone enemy must already be unlocked, or the zone has no roster yet and so
is always open). Once a zone is visited it joins the **fast-travel** list
(from anywhere, not just the hub or a signpost yet — that restriction is
future polish): instant, free, for backtracking to shop / craft / turn in
quests / farm. Both are free for now; a road-encounter or a cost could be
added later if backtracking feels frictionless. There are no real "gates"
(guardians) yet — reachability is inferred from the same enemy-unlock chain
combat already uses, per `world.map.default_zone_for_progress()`'s save
migration and `is_zone_reachable()`'s live check.

| Zone | Theme | Backbone enemies (existing) | Sub-locations | Key NPCs |
|------|-------|-----------------------------|---------------|----------|
| **Piedrablanca** | Last free village | — | Taberna (rest), Herrería, Mercado, Refugio | Yerma, Dorn, Halbrand, Nia |
| **Los Yermos** | Wilds around the village | *(10, complete — §4.6)* | Campamento de bandidos, Túmulo | Cael |
| **Bosque de los Susurros** | Haunted forest | *(10, complete — §4.7)* | Claro del altar, Cabaña quemada | Mirelle |
| **Ciénaga de los Ahogados** | Drowned marsh | *(10, complete — §4.8)* | Templo hundido, Embarcadero podrido | Oren |
| **Cañón del Trueno** | Mountain pass, stone | *(10, complete — §4.9)* | Mina derrumbada, Puente colgante | Kort |
| **Torre de los Arcanos / Necrópolis** | Mage tower + graveyard | *(10, complete — §4.10)* | Biblioteca, Cripta | Sella |
| **Ciudadela en Ruinas** | The razed capital, infernal ground | Ángel Caído, Demonio | Catedral rota, Plaza | Aldric |
| **El Corazón de la Brecha** | The origin — designed last | *(§4)* | — | — |

Shop / forge / rest *(implemented in v0.12.0-c)* / save live in Piedrablanca's
sub-locations (save stayed in the Personaje menu rather than moving to
Refugio — no reason yet to gate it by location); a "Mercado errante" and a
"Fuego de campamento" (paid rest) appear in later zones *(not yet
implemented)*.

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
ATB math (`TODO.md`), effective threat scales with `hp × speed × net damage`
(net damage = mean damage − effective mitigation). Define a normalised score and
a target curve `target(zone N, tier T) = base · f(N) · g(T)`; design each
enemy within ±10 % of its target, then playtest-verify guardians and a sample
of each tier the way the chain is verified today. The player's expected level at
each zone falls out of this pass too (it is deliberately **not** fixed yet —
see §6.2). *Implemented in v0.14.0-b as `characters/power_budget.py`* — formula, constants and their derivation live in its module docstring; the full report on the current 14 enemies lives in `TODO.md`.

### 4.5 Signature abilities (menu of mechanics to draw from)

Existing patterns: pre-battle ambush, periodic extra hit, self-heal under a
threshold, unavoidable attack, applied debuff through a hit roll, summon an
ally. New: ranged attack (partly ignores evasion), gold theft, stun (skip a
turn), stacking armour shred, life drain, enrage under a threshold, `consagrar`
(marks the player for bonus damage), curse that blocks healing.

### 4.6 Sample zone — Los Yermos (10) *(implemented in v0.14.0-c)*

Demonstrates the template; the other six zones are follow-up design work
(Bosque de los Susurros done next, §4.7 — the other five remain open).

| Tier | Rank | Name | Archetype | Signature | Deals | Weak to | Resists | Immune to |
|------|------|------|-----------|-----------|-------|---------|---------|-----------|
| 1 | standard | Rata Gigante | skirmisher | quick bite, minor poison chance | — | fuego | — | — |
| 2 | standard | Goblin | bruiser | ambush after first defeat | físico | — | — | — |
| 3 | standard | Goblin Montaraz | ranged | ranged shot, minor bleed chance | físico | fuego | — | — |
| 4 | standard | Huargo | skirmisher | pack bite (extra hit) | físico | — | — | — |
| 5 | **elite** | Chamán Goblin | support | self-heal, minor curse | oscuridad | sagrado | oscuridad | — |
| 6 | standard | Esqueleto | tank | revives once | físico | sagrado | veneno | veneno, sangrado |
| 7 | **elite** | Bandido | ambusher | disarm | físico | veneno | — | — |
| 8 | standard | Salteador | skirmisher | double quick strike, steals gold | físico | — | — | — |
| 9 | **elite** | Ogro del Yermo | bruiser | crushing blow that stuns | físico | fuego | — | paralizado |
| 10 | **guardian** | El Carnicero | bruiser/tank | enrage below 40 % HP, applies sangrado | físico | sagrado | veneno | — |

Two changes from the original design pass, both from user feedback: **Goblin
Montaraz** no longer partially ignores evasion — dodging a projectile is, if
anything, *easier* than dodging a melee hit, so giving ranged attacks a
mechanical edge over evasion was backwards; it now rolls the same
`resolve_hit()` as every other attack and its signature moved to a bleed
chance instead. **Steal gold (Salteador)** is deliberately capped and
infrequent (a ~25%-of-turns alternate action, not an add-on to every hit, and
never takes more than the player is carrying) so it reads as a nuisance, not
a punishment — see `characters/power_budget.py`'s neighbour module
`characters/enemies/salteador.py` for the exact numbers. **Unlock order**:
Goblin stays the game's literal first encounter (the whole early XP curve is
calibrated around it) even though its design tier (2) is now below Rata
Gigante's (1) — Rata Gigante unlocks second instead. See
`docs/design/presupuesto_de_poder.md` for how each enemy's stats were sized
against the power-budget curve (§4.4) before writing its code.

### 4.7 Bosque de los Susurros (10) *(implemented in v0.14.0-e)*

Orco, Espíritu Vengativo and Troll (tiers 1-3) predate this template; the 7
new enemies (tiers 4-10) follow it.

| Tier | Rank | Name | Archetype | Signature | Deals | Weak to | Resists | Immune to |
|------|------|------|-----------|-----------|-------|---------|---------|-----------|
| 1 | standard | Orco | bruiser | cyclical fury: 3 turns calm, 3 turns double damage | físico | — | veneno | — |
| 2 | standard | Espíritu Vengativo | ambusher | curse reduces armour | físico | sagrado | — | veneno, sangrado |
| 3 | standard | Troll | tank | regenerates HP every turn | físico | fuego | — | — |
| 4 | standard | Araña Tejesombras | skirmisher | poison bite | físico | fuego | — | — |
| 5 | **elite** | Druida Corrupto | support | self-heal, minor curse | oscuridad | sagrado | oscuridad | — |
| 6 | standard | Oso Espectral | bruiser | life drain: heals for a share of the damage it deals, every hit | físico | sagrado | — | veneno |
| 7 | **elite** | Enjambre de Polillas Pálidas | skirmisher/swarm | periodic second bite, minor poison chance | físico | fuego | — | sangrado |
| 8 | standard | Lobo Umbrío | ambusher | ambushes after first defeat | físico | — | — | — |
| 9 | **elite** | Ent Corrompido | tank | unavoidable root strike | físico | fuego | — | paralizado |
| 10 | **guardian** | El Enraizado | bruiser/support | self-heal below 40 % HP, curses on hit | oscuridad | sagrado | oscuridad, veneno | — |

**Life drain** (Oso Espectral) is new to the signature-ability menu (§4.5):
heals the attacker for a fixed share of the damage it just dealt on every
successful hit, rather than only below a health threshold like the
self-heal pattern used elsewhere. **Stats deliberately diverge from
`target_score()`** (feedback from the user: "reaching the Bosque means
you've already cleared Los Yermos, so it has to be harder, and so on for
every zone after it" — difficulty must stay progressive, zone over zone).
The formal target curve resets low at the start of every zone, but Troll's
*real* power score (already implemented, pre-power-budget-tool) sits far
above its own zone-relative target — designing tiers 4-10 against the
formal curve instead of against Troll's actual power would have made the
Bosque's early tiers weaker than the enemy the player just fought. Instead,
each new tier was sized to exceed the real power of the one before it, and
El Enraizado's real power was kept below Gárgola's (the Cañón del Trueno's
first enemy) so the zone transition stays progressive too — see
`characters/enemies/oso_espectral.py` and the neighbouring files for the
exact numbers, and `tests/test_power_budget.py`'s `_KNOWN_OUT_OF_RANGE` for
why this zone's own tool-reported deviations are expected, not bugs.

### 4.8 Ciénaga de los Ahogados (10) *(implemented in v0.14.0-f)*

This zone had no roster at all before this sub-phase — all 10 enemies are
new, themed around the drowned marsh, Oren's stories of the water "returning
its own" at night, and the sunken temple relief that shows something ancient
kneeling figures once looked up to.

| Tier | Rank | Name | Archetype | Signature | Deals | Weak to | Resists | Immune to |
|------|------|------|-----------|-----------|-------|---------|---------|-----------|
| 1 | standard | Sanguijuela Colosal | bruiser | life drain: heals for a share of the damage it deals, every hit | físico | fuego | — | veneno |
| 2 | standard | Espantajo Anegado | skirmisher | on-hit bleed chance | físico | — | — | — |
| 3 | standard | Ahogado Errante | ambusher | ambushes after first defeat | físico | sagrado | — | — |
| 4 | **elite** | Chamán del Cieno | support | self-heal, minor curse | oscuridad | sagrado | oscuridad | — |
| 5 | standard | Cangrejo Acorazado | tank | unavoidable pincer crush | físico | — | — | — |
| 6 | standard | Serpiente de Fango | skirmisher | periodic second bite, poison chance | físico | fuego | — | — |
| 7 | **elite** | Sacerdote Ahogado | support/control | confusion special attack, dark bolt | oscuridad | sagrado | oscuridad | — |
| 8 | standard | Horror de Profundidad | bruiser | stun-chance special attack | físico | — | — | — |
| 9 | **elite** | Guardián del Templo Hundido | tank | unavoidable stone strike | físico | sagrado | — | paralizado |
| 10 | **guardian** | El Anegado | bruiser/support | self-heal below 40 % HP, curses on hit | oscuridad | sagrado | oscuridad | veneno |

**Same progressive-difficulty requirement as the Bosque, but with no
headroom to absorb it**: on the map (§3) the Ciénaga sits between the
Bosque and the Cañón del Trueno, but El Enraizado's real power (~112k) and
Gárgola's *original* real power (~120k) were only ~7 % apart — nowhere near
enough room for 10 progressive tiers. Resolved, agreed with the user before
implementing, by reinforcing **Gárgola** itself (stats only — HP, attack
range and gold; its charge mechanic and affinities are untouched — real
power ~120k → ~214k) rather than compressing the new zone's own tiers into
an unrealistically flat, barely-progressive band; Gólem de Piedra needed no
change, already comfortably above the new ceiling. The Ciénaga's 10 tiers
then climb from just above El Enraizado up to just below the reinforced
Gárgola (~118.8k → ~205.7k) — see `characters/enemies/sanguijuela_colosal.py`
and the neighbouring files for the exact numbers, and
`tests/test_power_budget.py`'s `_KNOWN_OUT_OF_RANGE` for why this zone's own
tool-reported deviations are expected, same reasoning as the Bosque's.

### 4.9 Cañón del Trueno (10) *(implemented in v0.15.0-a)*

Gárgola and Gólem de Piedra (tiers 1-2, pre-existing, Gárgola reinforced in
§4.8) predate this template; the 8 new enemies (tiers 3-10) follow it, tied
directly into Kort's pre-existing dialogue and lore notes about the mine
collapse: the 14 named miners, the mineral de tormenta the Torre used to
channel the Breach, and a 15th name half-carved on a support beam.

| Tier | Rank | Name | Archetype | Signature | Deals | Weak to | Resists | Immune to |
|------|------|------|-----------|-----------|-------|---------|---------|-----------|
| 1 | standard | Gárgola | tank | charge attack every 3 turns | físico | arcano | — | veneno |
| 2 | standard | Gólem de Piedra | tank | unavoidable earthquake | físico | hielo | — | rayo, paralizado |
| 3 | standard | Minero Poseído | bruiser | on-hit bleed chance (pickaxe) | físico | sagrado | — | — |
| 4 | standard | Murciélago de Tormenta | skirmisher | periodic second swoop | físico | — | — | — |
| 5 | **elite** | Chispa del Puntal | control | lightning bolt, on-hit paralysis chance | rayo | hielo | — | rayo, paralizado |
| 6 | standard | Aparición de la Cuadrilla | ambusher | ambushes after first defeat | físico | — | — | — |
| 7 | **elite** | Verdugo de la Mina | tank | unavoidable cave-in strike | físico | sagrado | — | paralizado |
| 8 | standard | Cabra Montés Corrupta | bruiser | stun-chance headbutt | físico | — | — | — |
| 9 | **elite** | Heraldo de la Tormenta | support | self-heal, minor curse, lightning bolt | rayo | sagrado | rayo | — |
| 10 | **guardian** | El Decimoquinto | bruiser/support | self-heal below 40 % HP, on-hit paralysis via lightning | rayo | sagrado | rayo | — |

**Same progressive-difficulty approach as the previous two zones, but the
next real link (Mago) is a known blind spot the tool can't fix**: Gólem de
Piedra's real power already linked directly to Mago's before this sub-phase
started — Mago is one of only two documented cases (§4.4) where
`power_score()` structurally can't see an enemy's real threat (heal +
control, deliberately low base attack), so that specific transition was
already broken. Rebalancing Mago's stats to compensate would fight its
intended fragile-caster identity and is exactly the kind of systemic
rebalance already deferred elsewhere (see `TODO.md`) — so the 8 new tiers
were sized the same way as the Bosque's and the Ciénaga's, climbing
progressively from Gólem de Piedra's real power, without trying to land
below Mago. That one transition stays a documented, pre-existing exception
rather than something this sub-phase tried to paper over — see
`characters/enemies/minero_poseido.py` and the neighbouring files for the
exact numbers, and `tests/test_power_budget.py`'s `_KNOWN_OUT_OF_RANGE` for
the full reasoning.

### 4.10 Torre de los Arcanos / Necrópolis (10) *(implemented in v0.15.0-b)*

Mago and Nigromante (tiers 1-2, pre-existing) predate this template; the 8
new enemies (tiers 3-10) follow it, tied directly into Sella's pre-existing
dialogue and lore notes: the arcane council that tried to channel the
Breach, a forbidden tome ("Rituales de Cierre y Apertura") missing from the
Biblioteca before she started cataloging, and the dead in the Cripta who
"rise in shifts, one fewer on the list every night."

| Tier | Rank | Name | Archetype | Signature | Deals | Weak to | Resists | Immune to |
|------|------|------|-----------|-----------|-------|---------|---------|-----------|
| 1 | standard | Mago | control/support | 4 elemental spells, self-heal | fuego/rayo/hielo/arcano | — | arcano | — |
| 2 | standard | Nigromante | control | summons a lesser undead ally | oscuridad | sagrado | — | oscuridad |
| 3 | standard | Tomo Viviente | skirmisher | on-hit bleed chance (page cuts) | físico | fuego | — | — |
| 4 | standard | Guardián Osario | bruiser | periodic second bone strike | físico | sagrado | — | — |
| 5 | **elite** | Custodio Arcano | control | self-heal, arcane bolt | arcano | hielo | — | veneno |
| 6 | standard | Espectro de la Guardia | ambusher | ambushes after first defeat | físico | sagrado | — | — |
| 7 | **elite** | Bibliotecario Errante | control | confusion special attack, arcane bolt | arcano | sagrado | arcano | — |
| 8 | standard | Carroñero de Cripta | bruiser | life drain: heals for a share of the damage it deals, every hit | físico | sagrado | veneno | — |
| 9 | **elite** | Guardián del Tomo Prohibido | tank | unavoidable seal-wave strike | físico | sagrado | — | paralizado |
| 10 | **guardian** | El Archivista | bruiser/support | self-heal below 40 % HP, curses on hit via an arcane bolt | arcano | sagrado | arcano | — |

**Same progressive-difficulty approach, and no reinforcement needed this
time — but the same kind of pre-existing broken transition recurs one link
further on**: Nigromante's real power already had a huge gap above Mago's
(the same documented blind-spot case as §4.9), so the 8 new tiers had ample
room to climb from Nigromante's real power upward without touching any
existing enemy. However, Nigromante's real power already linked directly to
Ángel Caído's (the Ciudadela's first enemy, itself lower — another
pre-existing inversion among the original 14, not touched here either), so
the new tiers climb progressively from Nigromante without trying to land
below Ángel Caído, same reasoning as the Mago/Gólem case. All 8 are
therefore expected exceptions in `tests/test_power_budget.py`'s
`_KNOWN_OUT_OF_RANGE`, alongside the Cañón's. One design note: `fractura
mágica` (the `arcano` element's status) was considered for a couple of
these enemies but dropped — it only has an effect on the `Enemy` side today
(halves an enemy's own self-heal) and does nothing to the `Player`, so
inflicting it on the player would be flavor-only; already-functional
statuses (`sangrado`, `maldicion`) were used instead.

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
- **Implemented in v0.11.0-b.** Player elemental defence: `Armor` may carry
  `resist` (a small dict, a % reduction per element), summed as
  `Player.get_total_resist(element)`, capped at 75% total, and applied in
  `Player.take_damage()` before armour/magic-resist mitigation. So far granted
  by three crafted pieces (Cinturón de Resistencia → arcano, Amuleto de
  Resistencia → oscuridad, Anillo de Vitalidad → sagrado); broader
  distribution (more items, a themed set) is left for a later balance pass.
  Also fixed a related gap: whether an attack is physical or magical is a
  property of its *element* (per this section), not of the attacker's class —
  `combat/battle.py::_execute_turn` only checked the Arcanista's innate
  magic/a skill's `magical` flag, so a non-Arcanista wielding a
  sagrado/oscuridad/arcano weapon was still mitigated by armour instead of
  magic resist. Now `is_magical_element(element)` also triggers it.

### Elemental reactions *(implemented in v0.11.0-c)*

- `fuego` already melts `congelado` (kept, no bonus damage — a separate,
  smaller interaction than shatter below).
- `rayo` on a `congelado` target: **shatter** — removes the freeze instantly
  and deals ×1.5 bonus damage instead of attempting the usual paralysis roll.
  Symmetric on `Player` and `Enemy`; four crafted/dropped weapons cover each
  physical element today (Garra de Tormenta = rayo, Cetro de Escarcha =
  hielo, plus fuego/veneno), so both sides of the reaction are reachable
  through normal play, not just enemy spells.
- `quemado` + `veneno` on the same target (in either order): **combustion** —
  the two merge into a single `combustion` status instead of coexisting,
  dealing more damage per turn than either alone (still halves physical
  attack like burn, still curable by Antídoto), with duration = max of the
  two merged effects.

Balance note: since shatter consumes the rayo hit's own paralysis roll and
combustion replaces two separate DoTs with one (not simply adding their
damage), reactions trade raw stacking for a single stronger effect rather than
compounding — kept deliberately modest so they read as a nice bonus, not the
only viable strategy against elite/guardian fights later.

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

Below 1 kill: not listed (as today). *Implemented in v0.14.0-a* (weapon-independent stats such as precision, evasion, penetration and regen ride with the 3-kill tier; the drop table is derived from each enemy's real `drop_item()` rather than declared twice).

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

- **Rest** *(implemented in v0.12.0-c)* — only in a town, at an inn, paying
  gold: full HP + all status effects cleared (`ui/exploration.py::_rest_flow`,
  reached via Piedrablanca's Taberna). **Cost scales with level**:
  `_REST_COST_PER_LEVEL × player.level`, with `_REST_COST_PER_LEVEL = 10` —
  explicitly a provisional number, not yet tuned against real gold income (see
  the "Rest cost curve" open item, now closed as "provisional, revisit during
  balance passes" rather than fully resolved). A broke player can always farm
  a few easy fights for gold; resting is a no-op (with a message, not a
  prompt) when already at full HP with no status effects.
- **Death** *(not yet implemented — still a plain full-heal, no
  respawn-at-town)* — you lose a fraction of your gold (currently 1/3) and it
  is **gone for good** (no recoverable "saco"). You respawn at the last
  visited town at full HP with statuses cleared, losing your position in the
  current zone. Today's `_handle_defeat()` in `combat/battle.py` already does
  the gold penalty + full heal; moving `zona_actual` back to the last visited
  town on defeat is deliberately out of scope for v0.12.0-c (it changes
  combat's own defeat handling, not just world/exploration code) and is left
  for a later pass.

---

## 8. World systems

### 8.1 Exploration loop *(implemented in v0.12.0-b/c)*

Replaces the old flat `game_loop` menu with `ui/exploration.py::zone_loop()`.
Inside a zone: **Explorar** (weighted roll — combat / a discovery / nothing;
the discovery itself is now a mini-roll, gold or a free healing potion, GDD's
"rare mini-event" tier is still just flavour text via **Ir a `<sub-lugar>`**,
not a distinct roll outcome yet), **Ir a `<sub-lugar>`** (lists the zone's
sub-locations; three of Piedrablanca's are wired to real services — Mercado →
Tienda, Herrería → Forge, Taberna → rest — everything else, including
Piedrablanca's Refugio, is still a flavour-text stub; NPC/quest turn-in per
location beyond these three waits on v0.13.0), **Viajar** (frontier to the
immediate next zone once reachable, or fast-travel to anywhere already
visited), **Personaje** (the always-available character menu: inventory,
stats, equip, skills, bestiary, diary, save — extracted from the old `game_loop`;
quests join once that system exists). Tienda/Herrería moved out of
Personaje and into Piedrablanca's sub-locations in v0.12.0-c, per this
section's plan below.

### 8.2 Dialogue — branching, with player choices *(engine implemented in v0.13.0-a; content in -b)*

The engine (`world/npc.py`) supports everything below except quest-related effects (no quest system yet): effects available today are set a flag, give gold, give an item. Conditions gate on story flags and player level. The "≥3 choices" rule is enforced by a test over the real content. All nine NPCs of the §3 table exist since v0.13.0-b (plus Oren, a ferryman invented for the Ciénaga); their conversations are story-only until quests exist.

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
`world/data/*.py` (one module per zone). **`Zone`, `world/data/*.py`, the
`ZONE_ORDER`/`ZONES` registry, and travel/gating (`next_zone()`,
`is_zone_reachable()`) in `world/map.py` are implemented (v0.12.0-a/b)** —
`world/npc.py` exists since v0.13.0-a (engine + the nine NPCs); `world/quest.py`
doesn't exist yet.

### 9.3 Other new modules

- `characters/skills.py` — skill definitions; `Player` derives its skill pool
  from class, and `known` from level; `habilidades_equipadas` (the ≤4 active
  ids) is stored.
- `items/loot.py` — common-drop roll tables per zone tier.
- `ui/exploration.py` — the zone loop (`omit`ted from coverage like `ui/menus.py`).

### 9.4 Save schema v2 *(implemented in v0.12.0-a)*

Adds a `mundo` block: `zona_actual`, `zonas_visitadas`, `misiones`,
`banderas`, `dialogos_vistos`, `diario`, `arena_mejor_oleada`. Migration v1 →
v2 (`persistence/save_load.py`, same pattern as prior back-fills): no `mundo`
block → `zona_actual` inferred from `defeated_enemies` progress
(`world.map.default_zone_for_progress()`), `zonas_visitadas` backfilled to
every zone up to it, everything else empty. `unlocked_enemies` /
`defeated_enemies` stay the source of truth for gating. (`clase` and
`habilidades_equipadas` already existed as top-level save keys since v0.10.0,
before this GDD section was written — they weren't moved under `mundo`, to
avoid an unrelated migration for fields that already work.)

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
| **v0.14.0** | Bestiary & enemies I | progressive bestiary · power-budget tool (sets the level curve) · Los Yermos + Bosque + Ciénaga fleshed to ~10 each (elites 4-9-ish + guardian 10) · mid-progression class skills tied to those enemies |
| **v0.15.0** | Enemies II | Cañón (done, §4.9) + Torre/Necrópolis (done, §4.10) to ~10 · loot scaling (uniques + rolled commons) · cross-zone drop-scaling · more class skills |
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
- **Skill unlocks** — split between "by level" (early) and "by guardian defeat"
  (later); the exact split comes out of the power-budget phase.
- **Standalone status immunities** — decided per enemy as the roster is built.
- **Arena** — the wave-to-reward table, and exactly which unique(s) it grants.
- **Drop-scaling curve** — "slightly higher chance, slightly higher quantity",
  numbers from playtesting.
- **Rest cost curve** — `_REST_COST_PER_LEVEL × level` (v0.12.0-c) is a
  placeholder; the actual formula still needs tuning against gold income.
