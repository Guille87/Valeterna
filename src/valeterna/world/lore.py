"""Notas de lore y Diario (GDD §2 "Lore collectibles", v0.13.0-c).

Una `LoreNote` es un texto suelto (carta, página de diario, inscripción) que
se encuentra al visitar por primera vez un sub-lugar sin servicio propio. Se
lee en el momento y queda en el Diario (`Player.mundo["diario"]`, lista de ids
en orden de descubrimiento) para poder releerla desde el menú de Personaje.

Datos + funciones puras, igual que `world/npc.py`: no imprimen ni preguntan.
Cada módulo de `world/data/` declara las suyas en un `LORE` opcional y
`world/map.py` las agrega.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class LoreNote:
    id: str
    zone_id: str
    sub_location: str
    title: str
    text: str


def has_note(player, note: LoreNote) -> bool:
    return note.id in player.mundo["diario"]


def add_note(player, note: LoreNote) -> bool:
    """Guarda la nota en el Diario. `True` si es nueva, `False` si ya estaba
    (así el llamador sabe si es la primera vez que se lee)."""
    if has_note(player, note):
        return False
    player.mundo["diario"].append(note.id)
    return True


def found_notes(player, catalog: dict[str, LoreNote]) -> list[LoreNote]:
    """Las notas ya encontradas, en orden de descubrimiento. Ignora ids que ya
    no existan en el catálogo (una nota renombrada en una versión futura no
    debe romper una partida guardada)."""
    return [catalog[note_id] for note_id in player.mundo["diario"] if note_id in catalog]
