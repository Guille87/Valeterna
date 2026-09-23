from dataclasses import dataclass, field


@dataclass(frozen=True)
class Zone:
    """Una zona del mapa (GDD §3). Puramente datos, igual que un enemigo en
    `characters/enemies/`: la lógica de viaje/desbloqueo vive en `world/map.py`,
    no aquí.

    `enemies` son los nombres "backbone" ya implementados que habitan la zona
    (coinciden con las claves de `combat.battle.ENEMY_PROGRESSION`); el resto
    del roster de cada zona (hasta ~10, GDD §4) es diseño futuro. Una tupla
    vacía puede significar dos cosas distintas, diferenciadas por `is_hub`:
    un roster todavía sin diseñar (p. ej. la Ciénaga de los Ahogados, hasta
    que le toque su propia sub-fase) o una zona que, por diseño, nunca tiene
    enemigos — hoy solo Piedrablanca, el pueblo (GDD §3: "hub, no enemies").

    `is_hub` (v0.14.x, feedback del usuario: se podía "explorar" Piedrablanca
    y toparse con cualquier enemigo ya desbloqueado, rompiendo la idea de
    pueblo seguro) distingue ambos casos para `ui/exploration.py`: un roster
    sin diseñar sigue recurriendo a "cualquier enemigo desbloqueado" para no
    bloquear Explorar; un hub nunca tiene combate, tenga lo que tenga
    desbloqueado.
    """

    id: str
    name: str
    theme: str
    enemies: tuple[str, ...] = field(default_factory=tuple)
    sub_locations: tuple[str, ...] = field(default_factory=tuple)
    key_npcs: tuple[str, ...] = field(default_factory=tuple)
    is_hub: bool = False
