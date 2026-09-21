"""NPCs y diálogo ramificado (GDD §8.2, v0.13.0-a).

Todo es datos + funciones puras: el recorrido de una conversación
(`play_conversation`) no imprime ni pregunta nada por sí mismo, recibe tres
callbacks (`show`, `pick`, `notify`) — así la lógica se testea entera y la
capa interactiva (`ui/exploration.py`) solo aporta `print()`/`input()`.

Modelo: un `NPC` tiene `Conversation`s; cada una es un árbol de
`DialogueNode`s (texto del NPC + respuestas `Choice` del jugador). Una
conversación **no repetible** se registra en `mundo["dialogos_vistos"]` al
terminar y no vuelve a salir; el NPC cae entonces a una línea suelta repetible.
"""

import random
from collections.abc import Callable
from dataclasses import dataclass, field

from valeterna.items.factory import item_factory

_NO_MORE_TO_SAY = "No tiene nada más que decirte."


@dataclass(frozen=True)
class Condition:
    """Condición opcional de un disparo de conversación o de una respuesta.
    Vacía = siempre se cumple."""

    requires_flags: tuple[str, ...] = ()
    forbids_flags: tuple[str, ...] = ()
    min_level: int = 0

    def is_met(self, player) -> bool:
        flags = player.mundo["banderas"]
        return (
            all(f in flags for f in self.requires_flags)
            and not any(f in flags for f in self.forbids_flags)
            and player.level >= self.min_level
        )


@dataclass(frozen=True)
class Effect:
    """Efecto mecánico de elegir una respuesta. `kind`: `"set_flag"` (`value` =
    nombre de la bandera), `"give_gold"` (`amount`) o `"give_item"` (`item` =
    dict en el formato de `Item.to_dict()`, `amount` = unidades)."""

    kind: str
    value: str = ""
    amount: int = 0
    item: dict | None = None


def set_flag(name: str) -> Effect:
    return Effect("set_flag", value=name)


def give_gold(amount: int) -> Effect:
    return Effect("give_gold", amount=amount)


def give_item(item: dict, amount: int = 1) -> Effect:
    return Effect("give_item", amount=amount, item=item)


def apply_effects(effects: tuple[Effect, ...], player) -> list[str]:
    """Aplica los efectos al jugador y devuelve los avisos a mostrarle."""
    messages: list[str] = []
    for effect in effects:
        if effect.kind == "set_flag":
            player.mundo["banderas"].add(effect.value)
        elif effect.kind == "give_gold":
            player.inventory.gold += effect.amount
            messages.append(f"Recibes {effect.amount} de oro.")
        elif effect.kind == "give_item":
            item = item_factory(effect.item) if effect.item else None
            if item is not None:
                player.inventory.add_item(item, effect.amount, announce=False)
                messages.append(f"Recibes {item.name}" + (f" x{effect.amount}." if effect.amount > 1 else "."))
        else:
            raise ValueError(f"Efecto de diálogo desconocido: {effect.kind!r}")
    return messages


@dataclass(frozen=True)
class Choice:
    """Una respuesta del jugador. `next` = id del siguiente nodo (`None` =
    fin de la conversación). `reply` = lo que contesta el NPC nada más elegirla
    (imprescindible si la respuesta cierra la conversación: si no, el jugador
    se despide y el NPC se queda callado)."""

    text: str
    next: str | None = None
    condition: Condition = field(default_factory=Condition)
    effects: tuple[Effect, ...] = ()
    reply: str | None = None


@dataclass(frozen=True)
class DialogueNode:
    """Texto del NPC + respuestas. Sin `choices`, el nodo es lineal: tras
    mostrarlo se pasa a `next` (o termina si es `None`). Los `effects` del nodo
    se aplican al mostrarlo, antes de las respuestas — para que el jugador vea
    que recibe algo (p. ej. un regalo) *antes* de contestar."""

    id: str
    text: str
    choices: tuple[Choice, ...] = ()
    next: str | None = None
    effects: tuple[Effect, ...] = ()


@dataclass(frozen=True)
class Conversation:
    id: str
    start: str
    nodes: tuple[DialogueNode, ...]
    trigger: Condition = field(default_factory=Condition)
    repeatable: bool = False

    def get_node(self, node_id: str) -> DialogueNode:
        for node in self.nodes:
            if node.id == node_id:
                return node
        raise KeyError(f"Nodo {node_id!r} no existe en la conversación {self.id!r}")


Show = Callable[[str], None]
Pick = Callable[[list[str]], int]


def play_conversation(conversation: Conversation, player, show: Show, pick: Pick, notify: Show) -> None:
    """Recorre el árbol: muestra cada nodo, ofrece las respuestas cuya
    condición se cumple (`pick` recibe sus textos y devuelve el índice
    elegido), aplica sus efectos (`notify` recibe los avisos) y sigue por su
    `next`. Al terminar, una conversación no repetible queda registrada como
    vista."""
    node_id: str | None = conversation.start
    while node_id is not None:
        node = conversation.get_node(node_id)
        show(node.text)
        for message in apply_effects(node.effects, player):
            notify(message)
        if not node.choices:
            node_id = node.next
            continue
        options = [c for c in node.choices if c.condition.is_met(player)]
        if not options:
            break
        choice = options[pick([c.text for c in options])]
        if choice.reply:
            show(choice.reply)
        for message in apply_effects(choice.effects, player):
            notify(message)
        node_id = choice.next
    if not conversation.repeatable:
        player.mundo["dialogos_vistos"].add(conversation.id)


@dataclass(frozen=True)
class NPC:
    """`conversations` se evalúan en orden: sale la primera cuyo disparo se
    cumple y que no sea una única ya vista. Si no hay ninguna, el NPC suelta
    una de sus `idle_lines`."""

    id: str
    name: str
    zone_id: str
    conversations: tuple[Conversation, ...] = ()
    idle_lines: tuple[str, ...] = ()

    def next_conversation(self, player) -> Conversation | None:
        seen = player.mundo["dialogos_vistos"]
        for conversation in self.conversations:
            if conversation.trigger.is_met(player) and (conversation.repeatable or conversation.id not in seen):
                return conversation
        return None

    def talk(self, player, show: Show, pick: Pick, notify: Show) -> None:
        conversation = self.next_conversation(player)
        if conversation is None:
            show(random.choice(self.idle_lines) if self.idle_lines else _NO_MORE_TO_SAY)
            return
        play_conversation(conversation, player, show, pick, notify)
