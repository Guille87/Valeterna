"""Motor de diálogo (GDD §8.2, v0.13.0-a): condiciones, efectos, recorrido de
un árbol, conversaciones únicas vs repetibles y validación del contenido real."""

import pytest

from valeterna.items.factory import item_factory
from valeterna.items.potions.healing_potion import HealingPotion
from valeterna.world.map import NPCS, ZONES, npcs_in_zone
from valeterna.world.npc import (
    NPC,
    Choice,
    Condition,
    Conversation,
    DialogueNode,
    Effect,
    apply_effects,
    give_gold,
    give_item,
    play_conversation,
    set_flag,
)


def _scripted(*picks):
    """(show, pick, notify, log): `pick` consume `picks` en orden."""
    log = {"shown": [], "options": [], "notified": []}
    answers = iter(picks)

    def pick(options):
        log["options"].append(list(options))
        return next(answers)

    return log["shown"].append, pick, log["notified"].append, log


def _simple_conversation(**kwargs):
    return Conversation(
        id=kwargs.pop("id", "c1"),
        start="a",
        nodes=(
            DialogueNode(
                "a",
                "Hola.",
                choices=(
                    Choice("Uno", next="b"),
                    Choice("Dos", effects=(set_flag("dijo_dos"),)),
                    Choice("Tres"),
                ),
            ),
            DialogueNode("b", "Segundo nodo.", next="c"),
            DialogueNode("c", "Fin lineal."),
        ),
        **kwargs,
    )


# --- Condition ----------------------------------------------------------------


def test_empty_condition_is_always_met(player):
    assert Condition().is_met(player) is True


def test_condition_requires_and_forbids_flags(player):
    cond = Condition(requires_flags=("a",), forbids_flags=("b",))
    assert cond.is_met(player) is False
    player.mundo["banderas"].add("a")
    assert cond.is_met(player) is True
    player.mundo["banderas"].add("b")
    assert cond.is_met(player) is False


def test_condition_min_level(player):
    cond = Condition(min_level=5)
    assert cond.is_met(player) is False
    player.level = 5
    assert cond.is_met(player) is True


# --- Efectos ------------------------------------------------------------------


def test_effects_set_flag_gold_and_item(player):
    potion = HealingPotion("Poción de Salud", "Restaura 20 HP", 2, 20).to_dict()
    gold_before = player.inventory.gold

    messages = apply_effects((set_flag("x"), give_gold(7), give_item(potion, 2)), player)

    assert "x" in player.mundo["banderas"]
    assert player.inventory.gold == gold_before + 7
    assert player.inventory.quantities["Poción de Salud"] == 2
    assert any("7 de oro" in m for m in messages)
    assert any("Poción de Salud x2" in m for m in messages)


def test_unknown_effect_raises(player):
    with pytest.raises(ValueError):
        apply_effects((Effect("teletransportar"),), player)


# --- Recorrido ----------------------------------------------------------------


def test_play_conversation_follows_choices_and_linear_nodes(player):
    show, pick, notify, log = _scripted(0)  # "Uno" -> b -> c

    play_conversation(_simple_conversation(), player, show, pick, notify)

    assert log["shown"] == ["Hola.", "Segundo nodo.", "Fin lineal."]
    assert log["options"] == [["Uno", "Dos", "Tres"]]


def test_play_conversation_applies_choice_effects_and_notifies(player):
    conv = Conversation(
        id="c",
        start="a",
        nodes=(
            DialogueNode(
                "a", "Toma.", choices=(Choice("Vale", effects=(give_gold(3),)), Choice("No"), Choice("Quizá"))
            ),
        ),
    )
    show, pick, notify, log = _scripted(0)

    play_conversation(conv, player, show, pick, notify)

    assert log["notified"] == ["Recibes 3 de oro."]


def test_choices_with_unmet_conditions_are_hidden(player):
    conv = Conversation(
        id="c",
        start="a",
        nodes=(
            DialogueNode(
                "a",
                "Hola.",
                choices=(
                    Choice("Siempre"),
                    Choice("Solo con bandera", condition=Condition(requires_flags=("f",))),
                    Choice("Otra"),
                ),
            ),
        ),
    )
    show, pick, notify, log = _scripted(0)

    play_conversation(conv, player, show, pick, notify)

    assert log["options"] == [["Siempre", "Otra"]]


def test_node_with_every_choice_hidden_ends_the_conversation(player):
    hidden = Condition(requires_flags=("nunca",))
    conv = Conversation(
        id="c", start="a", nodes=(DialogueNode("a", "Hola.", choices=(Choice("x", condition=hidden),)),)
    )
    show, pick, notify, log = _scripted()

    play_conversation(conv, player, show, pick, notify)

    assert log["shown"] == ["Hola."]
    assert "c" in player.mundo["dialogos_vistos"]


def test_missing_node_raises(player):
    conv = Conversation(id="c", start="a", nodes=(DialogueNode("a", "x", next="zzz"),))
    show, pick, notify, _ = _scripted()

    with pytest.raises(KeyError):
        play_conversation(conv, player, show, pick, notify)


def test_one_time_conversation_is_recorded_when_it_ends(player):
    show, pick, notify, _ = _scripted(2)

    play_conversation(_simple_conversation(), player, show, pick, notify)

    assert "c1" in player.mundo["dialogos_vistos"]


def test_repeatable_conversation_is_never_recorded(player):
    show, pick, notify, _ = _scripted(2)

    play_conversation(_simple_conversation(repeatable=True), player, show, pick, notify)

    assert player.mundo["dialogos_vistos"] == set()


# --- NPC ----------------------------------------------------------------------


def _npc(*conversations, idle=()):
    return NPC(id="n", name="N", zone_id="z", conversations=conversations, idle_lines=idle)


def test_npc_picks_the_first_eligible_conversation(player):
    gated = _simple_conversation(id="gated", trigger=Condition(requires_flags=("f",)))
    open_ = _simple_conversation(id="open")
    npc = _npc(gated, open_)

    assert npc.next_conversation(player) is open_
    player.mundo["banderas"].add("f")
    assert npc.next_conversation(player) is gated


def test_npc_skips_a_one_time_conversation_already_seen(player):
    npc = _npc(_simple_conversation(id="once"))
    player.mundo["dialogos_vistos"].add("once")

    assert npc.next_conversation(player) is None


def test_npc_repeats_a_repeatable_conversation(player):
    rep = _simple_conversation(id="rep", repeatable=True)
    npc = _npc(rep)
    player.mundo["dialogos_vistos"].add("rep")

    assert npc.next_conversation(player) is rep


def test_npc_talk_falls_back_to_an_idle_line(player):
    npc = _npc(_simple_conversation(id="once"), idle=("Buen día.",))
    player.mundo["dialogos_vistos"].add("once")
    show, pick, notify, log = _scripted()

    npc.talk(player, show, pick, notify)

    assert log["shown"] == ["Buen día."]


def test_npc_talk_without_idle_lines_has_a_default(player):
    show, pick, notify, log = _scripted()

    _npc().talk(player, show, pick, notify)

    assert log["shown"] == ["No tiene nada más que decirte."]


def test_npc_talk_plays_the_conversation_then_goes_idle(player):
    npc = _npc(_simple_conversation(id="once"), idle=("Otra vez tú.",))
    show, pick, notify, log = _scripted(2)

    npc.talk(player, show, pick, notify)
    npc.talk(player, show, pick, notify)

    assert log["shown"] == ["Hola.", "Otra vez tú."]


# --- Contenido real -----------------------------------------------------------


def _all_conversations():
    return [(npc, conv) for npc in NPCS.values() for conv in npc.conversations]


def test_npc_ids_are_unique_and_registered_in_their_zone():
    assert len({n.id for n in NPCS.values()}) == len(NPCS)
    for npc in NPCS.values():
        assert npc.zone_id in ZONES
        assert npc.name in ZONES[npc.zone_id].key_npcs
    assert [n.id for n in npcs_in_zone("piedrablanca")] == ["yerma"]
    assert npcs_in_zone("los_yermos") == []


def test_conversation_ids_are_globally_unique():
    ids = [conv.id for _, conv in _all_conversations()]
    assert len(ids) == len(set(ids))


def test_every_real_conversation_is_well_formed():
    for _, conv in _all_conversations():
        node_ids = [n.id for n in conv.nodes]
        assert len(node_ids) == len(set(node_ids))
        assert conv.start in node_ids
        for node in conv.nodes:
            if node.next is not None:
                assert node.next in node_ids
            # GDD §8.2: los nodos con respuestas ofrecen al menos 3.
            assert node.choices == () or len(node.choices) >= 3
            for choice in node.choices:
                if choice.next is not None:
                    assert choice.next in node_ids


def test_every_real_effect_can_be_applied():
    for _, conv in _all_conversations():
        for node in conv.nodes:
            for choice in node.choices:
                for effect in choice.effects:
                    assert effect.kind in {"set_flag", "give_gold", "give_item"}
                    if effect.kind == "give_item":
                        assert item_factory(effect.item) is not None


def test_yermas_intro_can_be_played_through_every_first_branch(player):
    conv = NPCS["yerma"].conversations[0]
    for first in range(3):
        show, pick, notify, _ = _scripted(first, 0, 0)
        play_conversation(conv, player, show, pick, notify)
        assert "conocio_a_yerma" in player.mundo["banderas"]
        player.mundo["dialogos_vistos"].clear()
        player.mundo["banderas"].clear()
