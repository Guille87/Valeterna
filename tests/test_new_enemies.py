from valeterna.characters.enemies.angel_caido import AngelCaido
from valeterna.characters.enemies.bandido import Bandido
from valeterna.characters.enemies.demonio import Demonio
from valeterna.characters.enemies.dragon import Dragon
from valeterna.characters.enemies.espiritu_vengativo import EspirituVengativo
from valeterna.characters.enemies.gargola import Gargola
from valeterna.characters.enemies.golem import GolemDePiedra
from valeterna.characters.enemies.huargo import Huargo
from valeterna.characters.enemies.nigromante import Nigromante
from valeterna.characters.stats import apply_mitigation
from valeterna.combat.battle import ENEMY_PROGRESSION
from valeterna.items.equipment import Weapon


def test_huargo_pack_bite_adds_bonus_damage_when_triggered(player, monkeypatch):
    # random.random() es un único objeto compartido por todo el proceso (stats.py,
    # enemy_base.py y huargo.py "importan" la misma función), así que no se puede
    # dar un valor distinto según el módulo que llame: usamos una secuencia con
    # el orden real de las tiradas dentro de Huargo.perform_turn() ->
    # [acierto del golpe principal, crítico del golpe principal, ¿hay mordisco de manada?, acierto del mordisco].
    rolls = iter([0.0, 0.99, 0.0, 0.0])
    monkeypatch.setattr("valeterna.characters.stats.random.random", lambda: next(rolls))
    monkeypatch.setattr("valeterna.characters.enemies.enemy_base.random.randint", lambda a, b: 10)
    player.stats.armor = 0

    huargo = Huargo()
    before = player.stats.health
    huargo.perform_turn(player)
    dealt = before - player.stats.health

    # Ataque principal sin crítico: 10. Mordisco de manada: 10 // 2 = 5.
    assert dealt == 10 + 5


def test_huargo_pack_bite_never_triggers_when_roll_is_high(player, monkeypatch):
    # Secuencia: [acierto del golpe principal, crítico del golpe principal, ¿mordisco de manada?]
    rolls = iter([0.0, 0.99, 0.99])
    monkeypatch.setattr("valeterna.characters.stats.random.random", lambda: next(rolls))
    monkeypatch.setattr("valeterna.characters.enemies.enemy_base.random.randint", lambda a, b: 10)
    player.stats.armor = 0

    huargo = Huargo()
    before = player.stats.health
    huargo.perform_turn(player)
    dealt = before - player.stats.health

    assert dealt == 10


def test_bandido_disarm_zeroes_weapon_bonus_until_it_expires(player, monkeypatch):
    monkeypatch.setattr("valeterna.characters.enemies.bandido.random.random", lambda: 0.0)  # siempre desarma y acierta
    player.equipped_weapon = Weapon("Espada", "desc", 1, damage=5)

    assert player.get_attack_range() == (10, 15)  # base(5-10) + arma(+5)

    bandido = Bandido()
    bandido.perform_turn(player)

    assert any(e["name"] == "desarmado" for e in player.status_effects)
    assert player.get_attack_range() == (5, 10)  # el bonus del arma no cuenta mientras esté desarmado

    player.on_turn_end()  # duración 2 -> 1
    assert player.get_attack_range() == (5, 10)

    player.on_turn_end()  # duración 1 -> 0, el estado desaparece
    assert not any(e["name"] == "desarmado" for e in player.status_effects)
    assert player.get_attack_range() == (10, 15)


def test_espiritu_vengativo_curse_reduces_armor_until_it_expires(player, monkeypatch):
    monkeypatch.setattr(
        "valeterna.characters.enemies.espiritu_vengativo.random.random", lambda: 0.0
    )  # siempre maldice y acierta
    player.stats.armor = 6

    assert player.get_total_armor() == 6

    espiritu = EspirituVengativo()
    espiritu.perform_turn(player)

    assert any(e["name"] == "maldicion" for e in player.status_effects)
    assert player.get_total_armor() == 2  # 6 - power(4)

    for _ in range(3):  # duración 3 -> 0, el estado desaparece
        player.on_turn_end()

    assert not any(e["name"] == "maldicion" for e in player.status_effects)
    assert player.get_total_armor() == 6


def test_espiritu_vengativo_curse_never_reduces_armor_below_zero(player):
    player.stats.armor = 2
    player.apply_status("maldicion", duration=3, power=100)

    assert player.get_total_armor() == 0


def test_gargola_charges_every_third_turn(player, monkeypatch):
    monkeypatch.setattr("valeterna.characters.stats.random.random", lambda: 0.0)  # siempre acierta y critea
    monkeypatch.setattr("valeterna.characters.enemies.enemy_base.random.randint", lambda a, b: 10)
    player.stats.armor = 0
    player.stats.max_health = player.stats.health = (
        10_000  # los críticos con max_atk no deben dejarlo K.O. antes de tiempo
    )

    gargola = Gargola()
    before = player.stats.health
    gargola.perform_turn(player)  # turno 1: ataque normal
    gargola.perform_turn(player)  # turno 2: ataque normal
    normal_damage = before - player.stats.health

    before = player.stats.health
    gargola.perform_turn(player)  # turno 3: embestida
    charge_damage = before - player.stats.health

    # Cada ataque normal critea (v0.14.0-c: max_atk * crit_damage, no la tirada
    # mockeada); la embestida multiplica x1.8 sin crítico propio, así que sí
    # respeta la tirada mockeada (10).
    assert charge_damage == int(10 * 1.8)
    assert normal_damage == 2 * int(gargola.stats.max_atk * gargola.stats.crit_damage)


def test_golem_earthquake_ignores_evasion(player, monkeypatch):
    monkeypatch.setattr("valeterna.characters.enemies.golem.random.random", lambda: 0.0)  # siempre terremoto
    monkeypatch.setattr("valeterna.characters.enemies.enemy_base.random.randint", lambda a, b: 10)
    player.stats.evasion = 1000  # no debería importar: el terremoto no se puede esquivar
    player.stats.armor = 0

    golem = GolemDePiedra()
    before = player.stats.health
    golem.perform_turn(player)
    dealt = before - player.stats.health

    assert dealt == 10


def test_nigromante_dark_bolt_uses_magic_resist_not_armor(player, monkeypatch):
    # Secuencia: [¿invoca esqueleto?, acierto del dardo, crítico del dardo]
    rolls = iter([0.99, 0.0, 0.99])
    monkeypatch.setattr("valeterna.characters.stats.random.random", lambda: next(rolls))
    monkeypatch.setattr("valeterna.characters.enemies.enemy_base.random.randint", lambda a, b: 10)
    player.stats.armor = 100  # no debería influir en absoluto en el dardo (es daño mágico)
    player.stats.magic_resist = 10

    nigromante = Nigromante()
    before = player.stats.health
    nigromante.perform_turn(player)
    dealt = before - player.stats.health

    assert dealt == apply_mitigation(10, 10 - nigromante.stats.magic_penetration)  # ignora los 100 de armadura


def test_nigromante_summon_deals_physical_damage_using_armor(player, monkeypatch):
    # Secuencia: [¿invoca esqueleto?, acierto del esqueleto invocado]
    rolls = iter([0.0, 0.0])
    monkeypatch.setattr("valeterna.characters.stats.random.random", lambda: next(rolls))
    monkeypatch.setattr("valeterna.characters.enemies.enemy_base.random.randint", lambda a, b: 10)
    player.stats.armor = 4
    player.stats.magic_resist = 100  # no debería influir: el esqueleto invocado pega físico

    nigromante = Nigromante()
    before = player.stats.health
    nigromante.perform_turn(player)
    dealt = before - player.stats.health

    assert dealt == apply_mitigation(10, 4 - nigromante.stats.armor_penetration)


def test_angel_caido_self_heals_when_health_is_low(player, monkeypatch):
    monkeypatch.setattr("valeterna.characters.enemies.angel_caido.random.random", lambda: 0.0)
    monkeypatch.setattr("valeterna.characters.enemies.angel_caido.random.randint", lambda a, b: 40)

    angel = AngelCaido()
    angel.stats.health = int(angel.stats.max_health * 0.4)
    before = angel.stats.health
    angel.perform_turn(player)

    assert angel.stats.health == before + 40


def test_angel_caido_does_not_self_heal_above_threshold(player, monkeypatch):
    # random.random()=0.0 provocaría curación si estuviera por debajo del umbral;
    # como está a vida llena, ese chequeo ni se evalúa (cortocircuito del `and`).
    monkeypatch.setattr("valeterna.characters.stats.random.random", lambda: 0.0)
    monkeypatch.setattr("valeterna.characters.enemies.enemy_base.random.randint", lambda a, b: 10)

    angel = AngelCaido()
    angel.stats.health = angel.stats.max_health
    before = angel.stats.health
    angel.perform_turn(player)

    assert angel.stats.health == before


def test_angel_caido_divine_judgment_deals_more_damage_than_normal_strike(player, monkeypatch):
    monkeypatch.setattr("valeterna.characters.enemies.enemy_base.random.randint", lambda a, b: 10)
    player.stats.magic_resist = 0

    angel = AngelCaido()
    angel.stats.health = angel.stats.max_health  # vida llena, evita la autocuración

    # Secuencia: [¿juicio divino? sí, acierto del juicio]
    rolls = iter([0.0, 0.0])
    monkeypatch.setattr("valeterna.characters.stats.random.random", lambda: next(rolls))

    before = player.stats.health
    angel.perform_turn(player)
    judgment_damage = before - player.stats.health

    assert judgment_damage == int(10 * 1.6)  # x1.6, sin mitigación (magic_resist 0)


def test_demonio_confusion_reduces_evasion_until_it_expires(player, monkeypatch):
    # 0.25 cae en el tramo de "confusión" (0.2 <= x < 0.4) y también sirve como acierto.
    monkeypatch.setattr("valeterna.characters.enemies.demonio.random.random", lambda: 0.25)
    player.stats.evasion = 8

    assert player.get_total_evasion() == 8

    demonio = Demonio()
    demonio.perform_turn(player)

    assert any(e["name"] == "confusion" for e in player.status_effects)
    assert player.get_total_evasion() == 3  # 8 - power(5)

    for _ in range(3):  # duración 3 -> 0, el estado desaparece
        player.on_turn_end()

    assert not any(e["name"] == "confusion" for e in player.status_effects)
    assert player.get_total_evasion() == 8


def test_demonio_summon_deals_magical_damage_using_magic_resist(player, monkeypatch):
    # Secuencia: [¿invoca demonio menor? sí, acierto del demonio menor]
    rolls = iter([0.0, 0.0])
    monkeypatch.setattr("valeterna.characters.stats.random.random", lambda: next(rolls))
    monkeypatch.setattr("valeterna.characters.enemies.enemy_base.random.randint", lambda a, b: 10)
    player.stats.armor = 100  # no debería influir: el demonio menor pega mágico
    player.stats.magic_resist = 4

    demonio = Demonio()
    before = player.stats.health
    demonio.perform_turn(player)
    dealt = before - player.stats.health

    assert dealt == 10 - max(0, 4 - demonio.stats.magic_penetration)


def test_dragon_fire_breath_applies_burn_status(player, monkeypatch):
    # Secuencia: [¿aliento de fuego? sí, acierto, ¿quema? sí]
    rolls = iter([0.0, 0.0, 0.0])
    monkeypatch.setattr("valeterna.characters.stats.random.random", lambda: next(rolls))
    monkeypatch.setattr("valeterna.characters.enemies.enemy_base.random.randint", lambda a, b: 10)

    dragon = Dragon()
    dragon.perform_turn(player)

    assert any(e["name"] == "quemado" for e in player.status_effects)


def test_dragon_fire_breath_does_not_always_apply_burn(player, monkeypatch):
    # Secuencia: [¿aliento de fuego? sí, acierto, ¿quema? no]
    rolls = iter([0.0, 0.0, 0.99])
    monkeypatch.setattr("valeterna.characters.stats.random.random", lambda: next(rolls))
    monkeypatch.setattr("valeterna.characters.enemies.enemy_base.random.randint", lambda a, b: 10)

    dragon = Dragon()
    dragon.perform_turn(player)

    assert not any(e["name"] == "quemado" for e in player.status_effects)


def test_enemy_progression_includes_new_enemies_in_expected_order():
    assert ENEMY_PROGRESSION["Goblin"] == "Rata Gigante"
    assert ENEMY_PROGRESSION["Rata Gigante"] == "Goblin Montaraz"
    assert ENEMY_PROGRESSION["Goblin Montaraz"] == "Huargo"
    assert ENEMY_PROGRESSION["Huargo"] == "Chamán Goblin"
    assert ENEMY_PROGRESSION["Chamán Goblin"] == "Esqueleto"
    assert ENEMY_PROGRESSION["Esqueleto"] == "Bandido"
    assert ENEMY_PROGRESSION["Bandido"] == "Salteador"
    assert ENEMY_PROGRESSION["Salteador"] == "Ogro del Yermo"
    assert ENEMY_PROGRESSION["Ogro del Yermo"] == "El Carnicero"
    assert ENEMY_PROGRESSION["El Carnicero"] == "Orco"
    assert ENEMY_PROGRESSION["Orco"] == "Espíritu Vengativo"
    assert ENEMY_PROGRESSION["Espíritu Vengativo"] == "Troll"
    assert ENEMY_PROGRESSION["Troll"] == "Araña Tejesombras"
    assert ENEMY_PROGRESSION["Araña Tejesombras"] == "Druida Corrupto"
    assert ENEMY_PROGRESSION["Druida Corrupto"] == "Oso Espectral"
    assert ENEMY_PROGRESSION["Oso Espectral"] == "Enjambre de Polillas Pálidas"
    assert ENEMY_PROGRESSION["Enjambre de Polillas Pálidas"] == "Lobo Umbrío"
    assert ENEMY_PROGRESSION["Lobo Umbrío"] == "Ent Corrompido"
    assert ENEMY_PROGRESSION["Ent Corrompido"] == "El Enraizado"
    assert ENEMY_PROGRESSION["El Enraizado"] == "Sanguijuela Colosal"
    assert ENEMY_PROGRESSION["Sanguijuela Colosal"] == "Espantajo Anegado"
    assert ENEMY_PROGRESSION["Espantajo Anegado"] == "Ahogado Errante"
    assert ENEMY_PROGRESSION["Ahogado Errante"] == "Chamán del Cieno"
    assert ENEMY_PROGRESSION["Chamán del Cieno"] == "Cangrejo Acorazado"
    assert ENEMY_PROGRESSION["Cangrejo Acorazado"] == "Serpiente de Fango"
    assert ENEMY_PROGRESSION["Serpiente de Fango"] == "Sacerdote Ahogado"
    assert ENEMY_PROGRESSION["Sacerdote Ahogado"] == "Horror de Profundidad"
    assert ENEMY_PROGRESSION["Horror de Profundidad"] == "Guardián del Templo Hundido"
    assert ENEMY_PROGRESSION["Guardián del Templo Hundido"] == "El Anegado"
    assert ENEMY_PROGRESSION["El Anegado"] == "Gárgola"
    assert ENEMY_PROGRESSION["Gárgola"] == "Gólem de Piedra"
    assert ENEMY_PROGRESSION["Gólem de Piedra"] == "Minero Poseído"
    assert ENEMY_PROGRESSION["Minero Poseído"] == "Murciélago de Tormenta"
    assert ENEMY_PROGRESSION["Murciélago de Tormenta"] == "Chispa del Puntal"
    assert ENEMY_PROGRESSION["Chispa del Puntal"] == "Aparición de la Cuadrilla"
    assert ENEMY_PROGRESSION["Aparición de la Cuadrilla"] == "Verdugo de la Mina"
    assert ENEMY_PROGRESSION["Verdugo de la Mina"] == "Cabra Montés Corrupta"
    assert ENEMY_PROGRESSION["Cabra Montés Corrupta"] == "Heraldo de la Tormenta"
    assert ENEMY_PROGRESSION["Heraldo de la Tormenta"] == "El Decimoquinto"
    assert ENEMY_PROGRESSION["El Decimoquinto"] == "Mago"
    assert ENEMY_PROGRESSION["Mago"] == "Nigromante"
    assert ENEMY_PROGRESSION["Nigromante"] == "Tomo Viviente"
    assert ENEMY_PROGRESSION["Tomo Viviente"] == "Guardián Osario"
    assert ENEMY_PROGRESSION["Guardián Osario"] == "Custodio Arcano"
    assert ENEMY_PROGRESSION["Custodio Arcano"] == "Espectro de la Guardia"
    assert ENEMY_PROGRESSION["Espectro de la Guardia"] == "Bibliotecario Errante"
    assert ENEMY_PROGRESSION["Bibliotecario Errante"] == "Carroñero de Cripta"
    assert ENEMY_PROGRESSION["Carroñero de Cripta"] == "Guardián del Tomo Prohibido"
    assert ENEMY_PROGRESSION["Guardián del Tomo Prohibido"] == "El Archivista"
    assert ENEMY_PROGRESSION["El Archivista"] == "Ángel Caído"
    assert ENEMY_PROGRESSION["Ángel Caído"] == "Demonio"
    assert ENEMY_PROGRESSION["Demonio"] == "Ciudadano Hueco"
    assert ENEMY_PROGRESSION["Ciudadano Hueco"] == "Guardia Caída"
    assert ENEMY_PROGRESSION["Guardia Caída"] == "Serafín Corrupto"
    assert ENEMY_PROGRESSION["Serafín Corrupto"] == "Eco de la Guardia"
    assert ENEMY_PROGRESSION["Eco de la Guardia"] == "Custodio de Vidrieras"
    assert ENEMY_PROGRESSION["Custodio de Vidrieras"] == "Verdugo Infernal"
    assert ENEMY_PROGRESSION["Verdugo Infernal"] == "Heraldo del Amo"
    assert ENEMY_PROGRESSION["Heraldo del Amo"] == "El Sin Rostro"
    assert ENEMY_PROGRESSION["El Sin Rostro"] == "Dragón"
    assert ENEMY_PROGRESSION["Dragón"] is None
