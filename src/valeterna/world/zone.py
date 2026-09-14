from dataclasses import dataclass, field


@dataclass(frozen=True)
class Zone:
    """Una zona del mapa (GDD §3). Puramente datos, igual que un enemigo en
    `characters/enemies/`: la lógica de viaje/desbloqueo vive en `world/map.py`,
    no aquí.

    `enemies` son los nombres "backbone" ya implementados que habitan la zona
    (coinciden con las claves de `combat.battle.ENEMY_PROGRESSION`); el resto
    del roster de cada zona (hasta ~10, GDD §4) es diseño futuro. Una zona sin
    enemigos (p. ej. Piedrablanca, el pueblo) usa una tupla vacía.
    """

    id: str
    name: str
    theme: str
    enemies: tuple[str, ...] = field(default_factory=tuple)
    sub_locations: tuple[str, ...] = field(default_factory=tuple)
    key_npcs: tuple[str, ...] = field(default_factory=tuple)
