from valeterna.characters.classes import CharClass, starting_stats
from valeterna.characters.enemies.goblin import Goblin
from valeterna.characters.player import Player
from valeterna.characters.skills import CATALOG, MAX_EQUIPPED_ACTIVES, SkillKind, known_skills, pool_for
from valeterna.combat import battle


def _player(char_class=CharClass.VAGABUNDO, level=1):
    p = Player("H", starting_stats(char_class), char_class=char_class)
    p.level = level
    return p


def test_catalog_is_well_formed():
    for sid, skill in CATALOG.items():
        assert skill.id == sid
        assert skill.milestone in range(1, 8)
        if skill.is_active:
            assert skill.cooldown >= 1
        else:
            assert skill.kind is SkillKind.PASSIVE


def test_every_class_has_one_active_and_one_passive_at_m1():
    for cls in CharClass:
        m1 = [s for s in pool_for(cls) if s.milestone == 1]
        assert sum(s.is_active for s in m1) == 1
        assert sum(s.kind is SkillKind.PASSIVE for s in m1) == 1


def test_known_skills_are_gated_by_level():
    assert {s.id for s in known_skills(CharClass.VAGABUNDO, 1)} == {"golpe_firme", "segundo_aliento"}
    assert {s.id for s in known_skills(CharClass.VAGABUNDO, 3)} == {"golpe_firme", "segundo_aliento"}
    # M2 se aprende al nivel 4 (provisional).
    assert {s.id for s in known_skills(CharClass.VAGABUNDO, 4)} == {"golpe_firme", "segundo_aliento", "aguante"}


def test_has_passive_only_true_for_learned_passives():
    p = _player(CharClass.GUERRERO)
    assert p.has_passive("piel_de_piedra") is True
    assert p.has_passive("segundo_aliento") is False  # otra clase
    assert p.has_passive("golpe_firme") is False  # es activa, no pasiva


def test_reflejos_adds_flat_evasion():
    picaro = _player(CharClass.PICARO)
    base = starting_stats(CharClass.PICARO).evasion
    assert picaro.get_total_evasion() == base + 8


def test_piel_de_piedra_reduces_physical_damage_only():
    guerrero = _player(CharClass.GUERRERO)
    guerrero.stats.armor = 0
    guerrero.stats.magic_resist = 0
    phys = guerrero.take_damage(50)
    guerrero.stats.health = guerrero.stats.max_health
    magic = guerrero.take_damage(50, is_magical=True)
    assert phys < magic  # la pasiva solo mitiga el físico


def test_segundo_aliento_heals_on_kill(monkeypatch, weak_enemy):
    monkeypatch.setattr("valeterna.combat.battle.time.sleep", lambda *a, **k: None)
    vaga = _player(CharClass.VAGABUNDO)
    vaga.stats.health = 10
    battle._handle_victory(vaga, weak_enemy, [], ["Goblin"])
    assert vaga.stats.health > 10


def test_autoequip_and_cap():
    p = _player(CharClass.VAGABUNDO)
    p.autoequip_skills()
    assert p.equipped_skills == ["golpe_firme"]
    p.equipped_skills = ["golpe_firme", "no_existe", "golpe_firme", "segundo_aliento"]
    p.sanitize_equipped_skills()
    assert p.equipped_skills == ["golpe_firme"]  # quita repetido, desconocido y la pasiva


def test_sanitize_respects_max_equipped():
    assert MAX_EQUIPPED_ACTIVES == 4


def test_execute_skill_golpe_firme_never_misses_and_hits_harder(monkeypatch):
    monkeypatch.setattr("valeterna.combat.battle.random.choice", lambda seq: "hit")
    monkeypatch.setattr("valeterna.characters.stats.random.random", lambda: 0.99)  # fallaría un ataque normal
    monkeypatch.setattr("valeterna.combat.battle.random.random", lambda: 0.99)  # sin crítico
    monkeypatch.setattr("valeterna.characters.player.random.randint", lambda a, b: 10)

    p = _player(CharClass.VAGABUNDO)
    enemy = Goblin()
    enemy.stats.armor = 0
    enemy.stats.evasion = 99  # un ataque normal fallaría seguro
    hp = enemy.stats.health

    battle._execute_skill(p, enemy, CATALOG["golpe_firme"], [])

    assert enemy.stats.health < hp  # acertó pese a la evasión altísima
    assert hp - enemy.stats.health == 14  # 10 base * 1.4


def test_execute_skill_golpe_bajo_crits_and_bleeds(monkeypatch):
    monkeypatch.setattr("valeterna.combat.battle.random.choice", lambda seq: "hit")
    monkeypatch.setattr("valeterna.characters.stats.random.random", lambda: 0.0)
    monkeypatch.setattr("valeterna.combat.battle.random.random", lambda: 0.99)  # no forzamos crítico por azar
    monkeypatch.setattr("valeterna.characters.player.random.randint", lambda a, b: 10)

    p = _player(CharClass.PICARO)
    enemy = Goblin()
    enemy.stats.armor = 0
    battle._execute_skill(p, enemy, CATALOG["golpe_bajo"], [])

    assert any(e["name"] == "sangrado" for e in enemy.status_effects)


def test_execute_skill_proyectil_arcano_ignores_magic_resist(monkeypatch):
    monkeypatch.setattr("valeterna.combat.battle.random.choice", lambda seq: "hit")
    monkeypatch.setattr("valeterna.combat.battle.random.random", lambda: 0.99)
    monkeypatch.setattr("valeterna.characters.player.random.randint", lambda a, b: 40)

    arc = _player(CharClass.ARCANISTA)
    arc.stats.magic_power = 40
    enemy = Goblin()
    enemy.stats.magic_resist = 100  # enorme; el proyectil la ignora
    hp = enemy.stats.health

    battle._execute_skill(arc, enemy, CATALOG["proyectil_arcano"], [])

    assert hp - enemy.stats.health >= 30  # casi todo el golpe entra


def test_cooldown_decrements_each_player_turn(monkeypatch, weak_enemy):
    monkeypatch.setattr("valeterna.combat.battle.time.sleep", lambda *a, **k: None)
    monkeypatch.setattr("valeterna.combat.battle._player_menu", lambda *a, **k: "atacar")
    p = _player(CharClass.VAGABUNDO)
    cooldowns = {"golpe_firme": 3}

    battle._run_player_turn(p, weak_enemy, ["Goblin"], is_auto=False, cooldowns=cooldowns)

    assert cooldowns["golpe_firme"] == 2


def test_sintonia_lets_the_arcanist_pick_the_element(monkeypatch):
    from valeterna.combat.elements import ELEMENTS

    arc = _player(CharClass.ARCANISTA)
    monkeypatch.setattr("valeterna.combat.battle.console.ask", lambda *a, **k: "1")
    battle._prompt_battle_element(arc)
    assert arc.battle_element == sorted(ELEMENTS)[0]


def test_sintonia_only_prompts_for_the_arcanist(monkeypatch):
    vaga = _player(CharClass.VAGABUNDO)
    monkeypatch.setattr(
        "valeterna.combat.battle.console.ask",
        lambda *a, **k: (_ for _ in ()).throw(AssertionError("no debería preguntar")),
    )
    battle._prompt_battle_element(vaga)
    assert vaga.battle_element is None


def test_m2_adds_one_skill_per_class_at_level_4():
    for cls in CharClass:
        lvl1 = {s.id for s in known_skills(cls, 1)}
        lvl4 = {s.id for s in known_skills(cls, 4)}
        assert len(lvl4 - lvl1) == 1


def test_aguante_boosts_defense_below_30_percent(monkeypatch):
    p = _player(CharClass.VAGABUNDO, level=4)
    p.stats.armor = 20
    p.stats.magic_resist = 20
    p.stats.health = p.stats.max_health  # sano: sin bonus
    assert p.get_total_armor() == 20
    p.stats.health = int(p.stats.max_health * 0.2)  # < 30%
    assert p.get_total_armor() == 23  # +15%
    assert p.get_total_magic_resist() == 23


def test_veneno_de_contacto_can_poison_on_hit(monkeypatch):
    monkeypatch.setattr("valeterna.combat.battle.random.choice", lambda seq: "hit")
    monkeypatch.setattr("valeterna.characters.stats.random.random", lambda: 0.0)  # acierta
    monkeypatch.setattr("valeterna.combat.battle.random.random", lambda: 0.0)  # el veneno prende
    monkeypatch.setattr("valeterna.characters.player.random.randint", lambda a, b: 10)

    p = _player(CharClass.PICARO, level=4)
    enemy = Goblin()
    battle._execute_turn(p, enemy, [])
    assert any(e["name"] == "veneno" for e in enemy.status_effects)


def test_escudo_de_mana_absorbs_the_next_hit():
    p = _player(CharClass.ARCANISTA, level=4)
    battle._execute_skill(p, Goblin(), CATALOG["escudo_de_mana"], [])
    assert p.mana_shield is True

    hp = p.stats.health
    dealt = p.take_damage(40)
    assert dealt == 0
    assert p.stats.health == hp
    assert p.mana_shield is False  # se consume
    assert p.take_damage(40) > 0  # el siguiente golpe ya entra


def test_represalia_counterattacks_after_a_physical_hit(monkeypatch):
    monkeypatch.setattr("valeterna.combat.battle.random.choice", lambda seq: "hit")
    monkeypatch.setattr("valeterna.combat.battle.random.random", lambda: 0.0)  # contraataca
    monkeypatch.setattr("valeterna.characters.stats.random.random", lambda: 0.0)
    monkeypatch.setattr("valeterna.characters.player.random.randint", lambda a, b: 10)

    p = _player(CharClass.GUERRERO, level=4)
    p.took_physical_hit = True
    enemy = Goblin()
    enemy.stats.armor = 0
    hp = enemy.stats.health
    battle._try_represalia(p, enemy, [])
    assert enemy.stats.health < hp


def test_represalia_does_nothing_without_a_physical_hit():
    p = _player(CharClass.GUERRERO, level=4)
    p.took_physical_hit = False
    enemy = Goblin()
    hp = enemy.stats.health
    battle._try_represalia(p, enemy, [])
    assert enemy.stats.health == hp


def test_enemy_bleed_damages_over_time():
    enemy = Goblin()
    enemy.apply_status("sangrado", 3)
    hp = enemy.stats.health
    enemy.on_turn_start()
    assert enemy.stats.health < hp


def test_embate_stuns_with_the_aturdido_status_not_paralizado(monkeypatch):
    monkeypatch.setattr("valeterna.combat.battle.random.choice", lambda seq: "hit")
    monkeypatch.setattr("valeterna.characters.stats.random.random", lambda: 0.0)
    monkeypatch.setattr("valeterna.combat.battle.random.random", lambda: 0.0)  # el aturdir prende
    monkeypatch.setattr("valeterna.characters.player.random.randint", lambda a, b: 10)

    p = _player(CharClass.GUERRERO)
    enemy = Goblin()
    battle._execute_skill(p, enemy, CATALOG["embate"], [])

    names = [e["name"] for e in enemy.status_effects]
    assert "aturdido" in names
    assert "paralizado" not in names


def test_aturdido_enemy_loses_its_turn(capsys):
    enemy = Goblin()
    enemy.apply_status("aturdido", 1)
    assert enemy.on_turn_start() is False
    assert "aturdido" in capsys.readouterr().out
