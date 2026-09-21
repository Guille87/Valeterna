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
    log = {"shown": [], "options": [], "done": [], "notified": []}
    answers = iter(picks)

    def pick(options, done):
        log["options"].append(list(options))
        log["done"].append(list(done))
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


def test_choice_reply_is_shown_right_after_picking(player):
    conv = Conversation(
        id="c",
        start="a",
        nodes=(
            DialogueNode(
                "a",
                "Hola.",
                choices=(Choice("Adiós", reply="Hasta luego."), Choice("Otra"), Choice("Otra más")),
            ),
        ),
    )
    show, pick, notify, log = _scripted(0)

    play_conversation(conv, player, show, pick, notify)

    assert log["shown"] == ["Hola.", "Hasta luego."]


def test_node_effects_apply_when_the_node_is_shown_before_the_replies(player):
    order = []
    conv = Conversation(
        id="c",
        start="a",
        nodes=(
            DialogueNode(
                "a",
                "Toma.",
                effects=(give_gold(4),),
                choices=(Choice("Gracias"), Choice("Vale"), Choice("Bien")),
            ),
        ),
    )
    gold_before = player.inventory.gold

    def pick(options, done):
        order.append(("pick", player.inventory.gold - gold_before))
        return 0

    play_conversation(conv, player, lambda t: order.append(("show", t)), pick, lambda m: order.append(("notify", m)))

    assert order == [("show", "Toma."), ("notify", "Recibes 4 de oro."), ("pick", 4)]


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


def test_one_time_conversation_is_recorded_once_every_reply_is_exhausted(player):
    for picks in [(2,), (1,)]:
        show, pick, notify, _ = _scripted(*picks)
        play_conversation(_simple_conversation(), player, show, pick, notify)
        assert "c1" not in player.mundo["dialogos_vistos"]

    show, pick, notify, _ = _scripted(0)  # "Uno" -> nodos lineales
    play_conversation(_simple_conversation(), player, show, pick, notify)

    assert "c1" in player.mundo["dialogos_vistos"]


def test_repeatable_conversation_is_never_recorded(player):
    show, pick, notify, _ = _scripted(2)

    play_conversation(_simple_conversation(repeatable=True), player, show, pick, notify)

    assert "c1" not in player.mundo["dialogos_vistos"]


# --- Volver a hablar: checks y agotamiento ------------------------------------


def _tree():
    """raíz: [A -> nodo n1 con [A1, A2] , B (final), C (final)]"""
    return Conversation(
        id="t",
        start="root",
        nodes=(
            DialogueNode(
                "root",
                "Raíz.",
                choices=(Choice("A", next="n1"), Choice("B", reply="b"), Choice("C", reply="c")),
            ),
            DialogueNode(
                "n1",
                "Rama.",
                choices=(Choice("A1", reply="a1"), Choice("A2", reply="a2"), Choice("A3", reply="a3")),
            ),
        ),
    )


def test_a_picked_final_reply_is_checked_next_time(player):
    show, pick, notify, log = _scripted(1)  # B

    play_conversation(_tree(), player, show, pick, notify)
    show, pick, notify, log = _scripted(2)
    play_conversation(_tree(), player, show, pick, notify)

    assert log["done"][0] == [False, True, False]


def test_a_branch_is_checked_only_when_all_its_replies_are(player):
    def run(*picks):
        show, pick, notify, log = _scripted(*picks)
        play_conversation(_tree(), player, show, pick, notify)
        return log

    first = run(0, 0)  # A -> A1
    assert first["done"][0] == [False, False, False]

    second = run(0, 1)  # A -> A2
    assert second["done"][0][0] is False
    assert second["done"][1] == [True, False, False]

    third = run(0, 2)  # A -> A3
    assert third["done"][0][0] is False  # todavia faltaba A3
    assert third["done"][1] == [True, True, False]

    fourth = run(0, 0)  # ahora la rama A entera esta agotada
    assert fourth["done"][0] == [True, False, False]
    assert fourth["done"][1] == [True, True, True]


def test_conversation_is_offered_again_until_the_whole_tree_is_exhausted(player):
    npc = _npc(_tree())
    show, pick, notify, _ = _scripted(1)

    play_conversation(_tree(), player, show, pick, notify)  # solo B

    assert "t" not in player.mundo["dialogos_vistos"]
    assert npc.next_conversation(player) is not None


def test_conversation_is_retired_once_everything_is_checked(player):
    npc = _npc(_tree(), idle=("Idle.",))
    for picks in [(0, 0), (0, 1), (0, 2), (1,), (2,)]:
        show, pick, notify, _ = _scripted(*picks)
        play_conversation(_tree(), player, show, pick, notify)

    assert "t" in player.mundo["dialogos_vistos"]
    assert npc.next_conversation(player) is None


def test_gold_and_item_effects_are_given_only_once(player):
    conv = Conversation(
        id="g",
        start="a",
        nodes=(
            DialogueNode(
                "a",
                "Toma.",
                effects=(give_gold(5),),
                choices=(
                    Choice("Uno", effects=(give_gold(2),), reply="r"),
                    Choice("Dos", reply="r"),
                    Choice("Tres", reply="r"),
                ),
            ),
        ),
    )
    gold = player.inventory.gold

    for _ in range(3):
        show, pick, notify, log = _scripted(0)
        play_conversation(conv, player, show, pick, notify)

    assert player.inventory.gold == gold + 5 + 2
    assert len(log["notified"]) == 0  # la tercera vez ya no avisa de nada


def test_flag_only_effects_are_not_recorded(player):
    show, pick, notify, _ = _scripted(1)
    conv = Conversation(
        id="f",
        start="a",
        nodes=(
            DialogueNode(
                "a",
                "Hola.",
                choices=(Choice("x", reply="r"), Choice("y", effects=(set_flag("z"),), reply="r"), Choice("w")),
            ),
        ),
    )

    play_conversation(conv, player, show, pick, notify)

    assert "z" in player.mundo["banderas"]
    assert not any(k.endswith("#efectos") for k in player.mundo["dialogos_vistos"])


def test_hidden_choices_do_not_block_exhaustion(player):
    conv = Conversation(
        id="h",
        start="a",
        nodes=(
            DialogueNode(
                "a",
                "Hola.",
                choices=(
                    Choice("Visible", reply="r"),
                    Choice("Oculta", condition=Condition(requires_flags=("nunca",)), reply="r"),
                    Choice("Otra", reply="r"),
                ),
            ),
        ),
    )
    for pick_index in (0, 1):  # solo hay 2 visibles
        show, pick, notify, _ = _scripted(pick_index)
        play_conversation(conv, player, show, pick, notify)

    assert "h" in player.mundo["dialogos_vistos"]


def test_looping_trees_do_not_recurse_forever(player):
    conv = Conversation(
        id="l",
        start="a",
        nodes=(
            DialogueNode(
                "a",
                "Hola.",
                choices=(Choice("Otra vez", next="a"), Choice("Adiós", reply="r"), Choice("Adiós 2", reply="r")),
            ),
        ),
    )
    show, pick, notify, _ = _scripted(0, 1)  # bucle una vez y luego Adiós

    play_conversation(conv, player, show, pick, notify)

    assert "l/a/1" in player.mundo["dialogos_vistos"]


def test_purely_linear_conversation_is_retired_after_one_play(player):
    conv = Conversation(id="lin", start="a", nodes=(DialogueNode("a", "Hola.", next="b"), DialogueNode("b", "Fin.")))
    show, pick, notify, _ = _scripted()

    play_conversation(conv, player, show, pick, notify)

    assert "lin" in player.mundo["dialogos_vistos"]


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


def test_npc_talk_replays_the_conversation_until_exhausted_then_goes_idle(player):
    npc = _npc(_simple_conversation(id="once"), idle=("Otra vez tú.",))
    show, pick, notify, log = _scripted(2, 1, 0)

    for _ in range(4):
        npc.talk(player, show, pick, notify)

    assert log["shown"] == ["Hola.", "Hola.", "Hola.", "Segundo nodo.", "Fin lineal.", "Otra vez tú."]


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
                else:
                    # una respuesta que cierra la conversación necesita réplica:
                    # si no, el jugador se despide y el NPC se queda callado.
                    assert choice.reply, f"{conv.id}/{node.id}: {choice.text!r} cierra sin réplica del NPC"


def test_every_real_effect_can_be_applied():
    for _, conv in _all_conversations():
        for node in conv.nodes:
            all_effects = list(node.effects) + [e for c in node.choices for e in c.effects]
            for effect in all_effects:
                assert effect.kind in {"set_flag", "give_gold", "give_item"}
                if effect.kind == "give_item":
                    assert item_factory(effect.item) is not None


def test_yermas_tree_can_be_exhausted_and_the_potion_is_given_once(player):
    npc = NPCS["yerma"]

    def first_unchecked(options, done):
        return done.index(False) if False in done else 0

    plays = 0
    while npc.next_conversation(player) is not None:
        npc.talk(player, lambda t: None, first_unchecked, lambda m: None)
        plays += 1
        assert plays < 30, "el árbol de Yerma no se agota"

    assert player.inventory.quantities["Poción de Salud"] == 1
    assert "recibio_pocion_yerma" in player.mundo["banderas"]
    assert "yerma_intro" in player.mundo["dialogos_vistos"]


def test_yermas_intro_can_be_played_through_every_first_branch(player):
    conv = NPCS["yerma"].conversations[0]
    for first in range(3):
        show, pick, notify, _ = _scripted(first, 0, 0)
        play_conversation(conv, player, show, pick, notify)
        assert "conocio_a_yerma" in player.mundo["banderas"]
        player.mundo["dialogos_vistos"].clear()
        player.mundo["banderas"].clear()
