import random

from valeterna.characters.enemies.angel_caido import AngelCaido
from valeterna.characters.enemies.arana_tejesombras import AranaTejesombras
from valeterna.characters.enemies.bandido import Bandido
from valeterna.characters.enemies.chaman_goblin import ChamanGoblin
from valeterna.characters.enemies.demonio import Demonio
from valeterna.characters.enemies.dragon import Dragon
from valeterna.characters.enemies.druida_corrupto import DruidaCorrupto
from valeterna.characters.enemies.el_carnicero import ElCarnicero
from valeterna.characters.enemies.el_enraizado import ElEnraizado
from valeterna.characters.enemies.enjambre_polillas import EnjambrePolillas
from valeterna.characters.enemies.ent_corrompido import EntCorrompido
from valeterna.characters.enemies.espiritu_vengativo import EspirituVengativo
from valeterna.characters.enemies.gargola import Gargola
from valeterna.characters.enemies.goblin import Goblin
from valeterna.characters.enemies.goblin_montaraz import GoblinMontaraz
from valeterna.characters.enemies.golem import GolemDePiedra
from valeterna.characters.enemies.huargo import Huargo
from valeterna.characters.enemies.lobo_umbrio import LoboUmbrio
from valeterna.characters.enemies.mage import Mago
from valeterna.characters.enemies.nigromante import Nigromante
from valeterna.characters.enemies.ogro_del_yermo import OgroDelYermo
from valeterna.characters.enemies.orc import Orc
from valeterna.characters.enemies.oso_espectral import OsoEspectral
from valeterna.characters.enemies.rata_gigante import RataGigante
from valeterna.characters.enemies.salteador import Salteador
from valeterna.characters.enemies.skeleton import Skeleton
from valeterna.characters.enemies.troll import Troll
from valeterna.crafting.forge import Forge
from valeterna.items.equipment import Armor

# Orden real de la cadena (combat/battle.py::ENEMY_PROGRESSION), con la posición
# de cada uno (1-indexado) para poder comprobar la progresión por hueco.
CHAIN = [
    (1, Goblin),
    (2, RataGigante),
    (3, GoblinMontaraz),
    (4, Huargo),
    (5, ChamanGoblin),
    (6, Skeleton),
    (7, Bandido),
    (8, Salteador),
    (9, OgroDelYermo),
    (10, ElCarnicero),
    (11, Orc),
    (12, EspirituVengativo),
    (13, Troll),
    (14, AranaTejesombras),
    (15, DruidaCorrupto),
    (16, OsoEspectral),
    (17, EnjambrePolillas),
    (18, LoboUmbrio),
    (19, EntCorrompido),
    (20, ElEnraizado),
    (21, Gargola),
    (22, GolemDePiedra),
    (23, Mago),
    (24, Nigromante),
    (25, AngelCaido),
    (26, Demonio),
    (27, Dragon),
]

# El stat "base" garantizado en todo objeto de ese hueco (ver la conversación
# de diseño en TODO.md, sección "Reparto de estadísticas por hueco").
BASE_STAT_BY_SLOT = {
    "casco": "max_health",
    "peto": "defense",
    "hombreras": "precision",
    "brazales": "crit_chance",
    "guantes": "crit_damage",
    "cinturon": "defense",
    "perneras": "evasion",
    "botas": "speed",
    "anillo": "crit_damage",
    "amuleto": "magic_resist",
}

STAT_FIELDS = [
    "defense",
    "max_health",
    "magic_resist",
    "crit_chance",
    "crit_damage",
    "damage",
    "regen",
    "speed",
    "precision",
    "evasion",
]

# Excepciones deliberadas, acordadas explícitamente con el usuario, donde el
# stat base de un hueco NO sube respecto al enemigo anterior de ese mismo
# hueco: el peto del Mago (una túnica no debe superar en armadura a una coraza
# de piedra, se compensa con resistencia mágica), las botas del Gólem
# (mantienen su identidad de "lentas pero muy resistentes" con una velocidad
# mínima en vez de ninguna) y el casco del Oso Espectral (un cráneo "hueco por
# dentro" da menos max_health que el casco de hueso del Ogro del Yermo, encaja
# con su naturaleza fantasmal/menos sólida).
# El guante del Enjambre de Polillas Pálidas da menos crit_damage que el del
# Salteador: es una pieza de utilidad ligada al polvo venenoso del enjambre
# (tema, no precisión de asesino), no pensada para competir en ese stat.
# El cinturón del Gólem da menos defense que el de El Enraizado: compensa con
# un bonus de max_health que El Enraizado no lleva, en línea con la identidad
# de "tanque" del Gólem antes que con armadura pura en ese hueco.
# Las hombreras del Gólem dan menos precision que las de El Enraizado: de
# nuevo la identidad de "tanque lento" del Gólem, compensada con un bonus de
# defense que El Enraizado no lleva en ese hueco.
KNOWN_EXCEPTIONS = {
    ("Mago", "peto"),
    ("Gólem de Piedra", "botas"),
    ("Oso Espectral", "casco"),
    ("Enjambre de Polillas Pálidas", "guantes"),
    ("Gólem de Piedra", "cinturon"),
    ("Gólem de Piedra", "hombreras"),
}


def _all_armor_drops():
    """(posición, instancia de enemigo, Armor) para cada armadura que puede soltar cada enemigo."""
    random.seed(0)
    original_random = random.random
    random.random = lambda: 0.0  # fuerza a que caigan todos los drops posibles
    try:
        for position, cls in CHAIN:
            enemy = cls()
            for item in enemy.drop_item():
                if isinstance(item, Armor):
                    yield position, enemy, item
    finally:
        random.random = original_random


def test_every_armor_drop_grants_its_slot_base_stat():
    for _position, enemy, item in _all_armor_drops():
        base_field = BASE_STAT_BY_SLOT[item.slot]
        assert getattr(item, base_field), (
            f"{item.name} ({enemy.name}, hueco {item.slot}) no da su stat base ({base_field})"
        )


def test_every_armor_drop_has_between_one_and_four_stats():
    for _position, enemy, item in _all_armor_drops():
        stat_count = sum(1 for field in STAT_FIELDS if getattr(item, field))
        assert 1 <= stat_count <= 4, f"{item.name} ({enemy.name}) tiene {stat_count} stats, fuera de [1,4]"


def test_base_stat_does_not_decrease_within_the_same_slot_along_the_chain():
    """El stat base de cada hueco no baja respecto al enemigo anterior de ese
    mismo hueco, salvo las excepciones deliberadas ya documentadas."""
    last_value_by_slot = {}
    for _position, enemy, item in sorted(_all_armor_drops(), key=lambda t: t[0]):
        base_field = BASE_STAT_BY_SLOT[item.slot]
        value = getattr(item, base_field)
        previous = last_value_by_slot.get(item.slot)
        if previous is not None and (enemy.name, item.slot) not in KNOWN_EXCEPTIONS:
            assert value >= previous, (
                f"{item.name} ({enemy.name}, hueco {item.slot}) da {base_field}={value}, "
                f"menos que un objeto anterior de ese hueco ({previous})"
            )
        last_value_by_slot[item.slot] = value


def _all_forge_armor_templates():
    for recipe in Forge().recipes:
        if isinstance(recipe.result_template, Armor):
            yield recipe.name, recipe.result_template


def test_every_forge_armor_recipe_grants_its_slot_base_stat():
    for recipe_name, item in _all_forge_armor_templates():
        base_field = BASE_STAT_BY_SLOT[item.slot]
        assert getattr(item, base_field), f"{recipe_name} (hueco {item.slot}) no da su stat base ({base_field})"


def test_every_forge_armor_recipe_has_between_one_and_four_stats():
    for recipe_name, item in _all_forge_armor_templates():
        stat_count = sum(1 for field in STAT_FIELDS if getattr(item, field))
        assert 1 <= stat_count <= 4, f"{recipe_name} tiene {stat_count} stats, fuera de [1,4]"
