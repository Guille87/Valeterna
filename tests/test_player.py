import pytest

from valeterna.characters.player import Player
from valeterna.characters.stats import Stats
from valeterna.items.equipment import Armor, Weapon


# Curva de reducción de daño: dealt = round(amount * 20 / (mitigación + 20)).
def test_take_damage_applies_the_armor_reduction_curve(player):
    player.stats.armor = 20
    dealt = player.take_damage(40)
    assert dealt == 20  # 40 * 20/(20+20) = 20 (armadura 20 reduce el 50%)
    assert player.stats.health == 80


def test_take_damage_magical_uses_magic_resist_instead_of_armor(player):
    player.stats.armor = 100  # no debería influir en absoluto en daño mágico
    player.stats.magic_resist = 20

    dealt = player.take_damage(40, is_magical=True)

    assert dealt == 20  # 40 * 20/(20+20), con res. mágica, ignora la armadura
    assert player.stats.health == 80


def test_take_damage_has_a_minimum_chip_and_never_heals(player):
    # Un golpe que acierta nunca hace 0 solo por armadura: siempre pasa 1.
    player.stats.armor = 999
    dealt = player.take_damage(40)
    assert dealt == 1
    assert player.stats.health == 99


def test_take_damage_of_zero_stays_zero(player):
    player.stats.armor = 999
    assert player.take_damage(0) == 0
    assert player.stats.health == 100


def test_take_damage_armor_penetration_reduces_mitigation(player):
    player.stats.armor = 20
    dealt = player.take_damage(40, armor_penetration=10)
    assert dealt == 27  # mitigación efectiva 10 -> 40 * 20/30


def test_take_damage_armor_penetration_cannot_go_below_zero_mitigation(player):
    player.stats.armor = 20
    dealt = player.take_damage(40, armor_penetration=100)
    assert dealt == 40  # mitigación 0 -> daño íntegro


def test_take_damage_magic_penetration_reduces_magic_resist_mitigation(player):
    player.stats.magic_resist = 30
    dealt = player.take_damage(40, is_magical=True, magic_penetration=10)
    assert dealt == 20  # mitigación efectiva 20 -> 40 * 20/40


def test_get_attack_range_includes_weapon_bonus(player):
    player.equipped_weapon = Weapon("Espada", "desc", 1, damage=3)
    assert player.get_attack_range() == (8, 13)


def test_get_attack_range_halved_when_quemado(player):
    player.equipped_weapon = Weapon("Espada", "desc", 1, damage=3)
    player.apply_status("quemado", duration=2)
    assert player.get_attack_range() == (4, 6)


def test_get_attack_range_includes_ring_damage_bonus(player):
    player.equipped_weapon = Weapon("Espada", "desc", 1, damage=3)
    player.equipped_armor["anillo1"] = Armor("Anillo de Fuerza", "desc", 1, slot="anillo", damage=4)
    assert player.get_attack_range() == (12, 17)  # base(5,10) + arma(3) + anillo(4)


def test_get_total_armor_includes_equipped_armor_bonus(player):
    player.equipped_armor["peto"] = Armor("Escudo", "desc", 1, slot="peto", defense=5)
    assert player.get_total_armor() == 7


def test_get_total_armor_sums_multiple_equipped_slots(player):
    player.equipped_armor["peto"] = Armor("Peto", "desc", 1, slot="peto", defense=5)
    player.equipped_armor["perneras"] = Armor("Perneras", "desc", 1, slot="perneras", defense=3)
    assert player.get_total_armor() == 2 + 5 + 3  # base(2) + peto(5) + perneras(3)


def test_get_total_magic_resist_sums_equipped_slots(player):
    player.stats.magic_resist = 1
    player.equipped_armor["brazales"] = Armor("Brazales", "desc", 1, slot="brazales", magic_resist=3)
    assert player.get_total_magic_resist() == 4


def test_get_total_resist_is_zero_without_matching_armor(player):
    assert player.get_total_resist("sagrado") == 0.0


def test_get_total_resist_sums_matching_equipped_slots(player):
    player.equipped_armor["anillo1"] = Armor("Anillo", "desc", 1, slot="anillo", resist={"sagrado": 0.10})
    player.equipped_armor["amuleto"] = Armor("Amuleto", "desc", 1, slot="amuleto", resist={"sagrado": 0.10})
    assert player.get_total_resist("sagrado") == pytest.approx(0.20)


def test_get_total_resist_ignores_other_elements(player):
    player.equipped_armor["anillo1"] = Armor("Anillo", "desc", 1, slot="anillo", resist={"sagrado": 0.10})
    assert player.get_total_resist("oscuridad") == 0.0


def test_get_total_resist_is_capped_at_75_percent(player):
    player.equipped_armor["anillo1"] = Armor("Anillo", "desc", 1, slot="anillo", resist={"arcano": 0.50})
    player.equipped_armor["amuleto"] = Armor("Amuleto", "desc", 1, slot="amuleto", resist={"arcano": 0.50})
    assert player.get_total_resist("arcano") == 0.75


def test_take_damage_applies_elemental_resist_before_mitigation(player):
    player.stats.armor = 0
    player.equipped_armor["amuleto"] = Armor("Amuleto", "desc", 1, slot="amuleto", resist={"oscuridad": 0.5})
    dealt = player.take_damage(20, element="oscuridad")
    assert dealt == 10  # 20 * (1 - 0.5), sin más mitigación (armadura 0)


def test_take_damage_ignores_resist_for_a_different_element(player):
    player.stats.armor = 0
    player.equipped_armor["amuleto"] = Armor("Amuleto", "desc", 1, slot="amuleto", resist={"oscuridad": 0.5})
    dealt = player.take_damage(20, element="sagrado")
    assert dealt == 20


def test_get_total_crit_chance_and_damage_sum_equipped_slots(player):
    player.equipped_armor["guantes"] = Armor("Guantes", "desc", 1, slot="guantes", crit_chance=0.05, crit_damage=0.15)
    player.equipped_armor["botas"] = Armor("Botas", "desc", 1, slot="botas", crit_damage=0.10)

    assert player.get_total_crit_chance() == 0.05
    assert player.get_total_crit_damage() == 1.5 + 0.15 + 0.10  # base(1.5) + guantes + botas


def test_get_total_speed_returns_base_stat(player):
    assert player.get_total_speed() == player.stats.speed == 10


def test_get_total_speed_sums_equipped_boots(player):
    player.equipped_armor["botas"] = Armor("Botas Ligeras", "desc", 1, slot="botas", speed=3)
    assert player.get_total_speed() == 13


def test_get_total_precision_sums_equipped_shoulders(player):
    player.equipped_armor["hombreras"] = Armor("Hombreras", "desc", 1, slot="hombreras", precision=4)
    assert player.get_total_precision() == player.stats.precision + 4


def test_get_total_evasion_sums_equipped_leggings(player):
    player.equipped_armor["perneras"] = Armor("Perneras", "desc", 1, slot="perneras", evasion=6)
    assert player.get_total_evasion() == player.stats.evasion + 6


def test_get_total_regen_is_zero_without_equipment(player):
    # A diferencia del resto de get_total_*, el stat base nunca sube (solo objetos).
    assert player.stats.regen == 0
    assert player.get_total_regen() == 0


def test_get_total_regen_sums_equipped_slots(player):
    player.equipped_armor["peto"] = Armor("Peto Vital", "desc", 1, slot="peto", regen=8)
    player.equipped_armor["anillo1"] = Armor("Anillo de Vitalidad", "desc", 1, slot="anillo1", regen=2)
    assert player.get_total_regen() == 10


def test_on_turn_start_applies_passive_regen_from_equipment(player):
    player.equipped_armor["peto"] = Armor("Peto Vital", "desc", 1, slot="peto", regen=8)
    player.stats.health = 50

    player.on_turn_start()

    assert player.stats.health == 58


def test_on_turn_start_passive_regen_never_exceeds_max_health(player):
    player.equipped_armor["peto"] = Armor("Peto Vital", "desc", 1, slot="peto", regen=8)
    player.stats.health = player.stats.max_health - 3  # menos que el regen

    player.on_turn_start()

    assert player.stats.health == player.stats.max_health


def test_get_equipped_element_prefers_weapon_over_bracers(player):
    player.equipped_weapon = Weapon("Espada de Hielo", "desc", 1, damage=3, element="hielo")
    player.equipped_armor["brazales"] = Armor("Brazales", "desc", 1, slot="brazales", element="fuego")
    assert player.get_equipped_element() == "hielo"


def test_get_equipped_element_falls_back_to_bracers(player):
    player.equipped_armor["brazales"] = Armor("Brazales", "desc", 1, slot="brazales", element="fuego")
    assert player.get_equipped_element() == "fuego"


def test_equipping_armor_with_health_bonus_increases_max_health(player):
    peto = Armor("Peto", "desc", 1, slot="peto", max_health=20)
    peto.use(player)

    assert player.stats.max_health == 120
    assert player.equipped_armor["peto"] is peto


def test_swapping_armor_in_same_slot_reverses_previous_health_bonus(player):
    peto_viejo = Armor("Peto Viejo", "desc", 1, slot="peto", max_health=20)
    peto_viejo.use(player)
    assert player.stats.max_health == 120

    peto_nuevo = Armor("Peto Nuevo", "desc", 1, slot="peto", max_health=5)
    peto_nuevo.use(player)

    assert player.stats.max_health == 105  # 100 base - 20 (revertido) + 5 (nuevo)
    assert player.equipped_armor["peto"] is peto_nuevo


def test_unequipping_health_bonus_clamps_current_health_down(player):
    peto = Armor("Peto", "desc", 1, slot="peto", max_health=20)
    peto.use(player)
    player.stats.health = 120  # a tope

    peto_debil = Armor("Peto Débil", "desc", 1, slot="peto", max_health=0)
    peto_debil.use(player)

    assert player.stats.max_health == 100
    assert player.stats.health == 100  # se re-clampa al nuevo máximo


def test_gain_experience_levels_up_and_boosts_stats(player):
    old_max_health, old_min_atk, old_max_atk, old_armor, old_speed = (
        player.stats.max_health,
        player.stats.min_atk,
        player.stats.max_atk,
        player.stats.armor,
        player.stats.speed,
    )
    player.gain_experience(8)  # required_xp() en nivel 1 es 8 (deliberadamente barato)

    assert player.level == 2
    # Nivel 1 -> 2: ganancia determinista según _growth_gain (ver Player._level_up).
    assert player.stats.max_health == old_max_health + 20
    assert player.stats.health == player.stats.max_health
    assert player.stats.min_atk == old_min_atk + 2
    assert player.stats.max_atk == old_max_atk + 3
    assert player.stats.armor == old_armor + 1
    assert player.stats.speed == old_speed + 2
    assert player.stats.magic_resist == 1  # nivel 2 es par -> gana resistencia mágica


def test_level_up_growth_is_deterministic_and_varies_between_levels(player):
    """La progresión no es aleatoria (misma partida siempre igual), pero tampoco
    es una cantidad fija cada nivel: unos niveles dan más ataque/armadura/velocidad
    que otros, siguiendo la curva continua de _growth_gain (estilo Pokémon)."""
    armor_gains = []
    speed_gains = []
    for _ in range(5):
        before_armor, before_speed = player.stats.armor, player.stats.speed
        player._level_up()
        armor_gains.append(player.stats.armor - before_armor)
        speed_gains.append(player.stats.speed - before_speed)

    # Con tasa 1.4/nivel, la armadura sigue el patrón determinista 1,2,1,2,1 (niveles 2-6)
    assert armor_gains == [1, 2, 1, 2, 1]
    # Con tasa 1.6/nivel, la velocidad sigue el patrón determinista 2,1,2,2,1 (niveles 2-6)
    assert speed_gains == [2, 1, 2, 2, 1]
    # No es una cantidad fija: hay al menos un nivel donde la ganancia varía
    assert len(set(armor_gains)) > 1
    assert len(set(speed_gains)) > 1


def test_gain_experience_can_trigger_multiple_level_ups():
    player = Player("Heroe", Stats(health=100, max_health=100, min_atk=5, max_atk=10, armor=2))
    player.gain_experience(1000)
    assert player.level > 2


def test_level_up_grants_magic_resist_only_on_even_levels(player):
    assert player.stats.magic_resist == 0

    player._level_up()  # nivel 1 -> 2 (par)
    assert player.stats.magic_resist == 1

    player._level_up()  # nivel 2 -> 3 (impar)
    assert player.stats.magic_resist == 1

    player._level_up()  # nivel 3 -> 4 (par)
    assert player.stats.magic_resist == 2


def test_apply_status_refreshes_duration_instead_of_duplicating(player):
    player.apply_status("veneno", duration=2)
    player.apply_status("veneno", duration=5)
    assert len(player.status_effects) == 1
    assert player.status_effects[0]["duration"] == 5


def test_on_turn_start_applies_poison_damage(player):
    player.apply_status("veneno", duration=3)
    can_act = player.on_turn_start()
    assert can_act is True
    assert player.stats.health == 100 - max(1, 100 // 8)


def test_on_turn_start_paralysis_can_block_action(player, monkeypatch):
    player.apply_status("paralizado", duration=2)
    monkeypatch.setattr("valeterna.characters.player.random.random", lambda: 0.1)
    can_act = player.on_turn_start()
    assert can_act is False


def test_on_turn_start_frozen_blocks_action_and_can_thaw(player, monkeypatch):
    player.apply_status("congelado", duration=2)
    monkeypatch.setattr("valeterna.characters.player.random.random", lambda: 0.9)
    assert player.on_turn_start() is False

    player.apply_status("congelado", duration=2)
    monkeypatch.setattr("valeterna.characters.player.random.random", lambda: 0.01)
    assert player.on_turn_start() is True
    assert not any(e["name"] == "congelado" for e in player.status_effects)


def test_on_turn_end_expires_status_effects(player):
    player.apply_status("veneno", duration=1)
    player.on_turn_end()
    assert player.status_effects == []


def test_on_turn_end_removes_expired_stat_buffs(player):
    class FakeBuff:
        def __init__(self):
            self.duration = 1
            self.removed_for = None

        def remove(self, target):
            self.removed_for = target

    buff = FakeBuff()
    player.active_effects.append(buff)
    player.on_turn_end()
    assert buff.removed_for is player
    assert player.active_effects == []


def test_show_stats_prints_crit_damage_as_a_percentage(player, capsys):
    """El daño crítico es un multiplicador (x1.6 = +60% de daño respecto al
    golpe normal), así que se muestra como bonus (+60%), no como total (160%)."""
    player.stats.crit_damage = 1.6
    player.show_stats()
    out = capsys.readouterr().out
    assert "Daño Crítico: +60%" in out
    assert "x1." not in out
    assert "160%" not in out
