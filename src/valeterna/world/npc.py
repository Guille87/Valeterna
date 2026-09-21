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


def end(text: str, reply: str, *effects: Effect) -> Choice:
    """Atajo para una respuesta que cierra la conversación: el jugador dice
    `text`, el NPC contesta `reply` y termina."""
    return Choice(text, reply=reply, effects=effects)


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
# `pick(textos, hechas)`: `hechas[i]` indica si la respuesta i ya está agotada
# (para que la UI le ponga un check); devuelve el índice elegido.
Pick = Callable[[list[str], list[bool]], int]


def _choice_key(conversation: Conversation, node: DialogueNode, index: int) -> str:
    return f"{conversation.id}/{node.id}/{index}"


def _visible_indices(node: DialogueNode, player) -> list[int]:
    return [i for i, c in enumerate(node.choices) if c.condition.is_met(player)]


def _resolve(conversation: Conversation, node_id: str | None) -> DialogueNode | None:
    """Sigue los nodos lineales hasta llegar a uno con respuestas; `None` si la
    cadena termina antes."""
    while node_id is not None:
        node = conversation.get_node(node_id)
        if node.choices:
            return node
        node_id = node.next
    return None


def _choice_done(conversation: Conversation, node: DialogueNode, index: int, player, path: frozenset) -> bool:
    """Una respuesta está agotada si es una respuesta final que ya se eligió, o
    si lleva a más respuestas y todas las visibles están agotadas. `path` evita
    recursión infinita en árboles con bucles (volver a un nodo ya recorrido
    cuenta como agotado)."""
    if _choice_key(conversation, node, index) in player.mundo["dialogos_vistos"]:
        return True
    target = _resolve(conversation, node.choices[index].next)
    if target is None:
        return False
    if target.id in path:
        return True
    return _all_done(conversation, target, player, path | {target.id})


def _all_done(conversation: Conversation, node: DialogueNode, player, path: frozenset) -> bool:
    return all(_choice_done(conversation, node, i, player, path) for i in _visible_indices(node, player))


def _apply_once(effects: tuple[Effect, ...], key: str, player, notify: Show) -> None:
    """Aplica los efectos. Los que dan algo (oro/objetos) se entregan una sola
    vez por partida aunque el jugador vuelva a pasar por ahí; los que solo
    activan banderas son idempotentes y no hace falta recordarlos."""
    if not effects:
        return
    once = any(e.kind != "set_flag" for e in effects)
    marker = f"{key}#efectos"
    seen = player.mundo["dialogos_vistos"]
    if once and marker in seen:
        return
    for message in apply_effects(effects, player):
        notify(message)
    if once:
        seen.add(marker)


def play_conversation(conversation: Conversation, player, show: Show, pick: Pick, notify: Show) -> None:
    """Recorre el árbol: muestra cada nodo, ofrece las respuestas cuya
    condición se cumple (`pick` recibe sus textos y cuáles están ya agotadas, y
    devuelve el índice elegido), aplica sus efectos (`notify` recibe los avisos)
    y sigue por su `next`.

    La conversación se puede volver a recorrer: cada respuesta final elegida
    queda registrada en `mundo["dialogos_vistos"]` y las respuestas agotadas se
    marcan. Una conversación no repetible solo se da por vista (y el NPC deja
    de ofrecerla) cuando todo su árbol está agotado."""
    seen = player.mundo["dialogos_vistos"]
    last_key: str | None = None
    node_id: str | None = conversation.start
    while node_id is not None:
        node = conversation.get_node(node_id)
        show(node.text)
        _apply_once(node.effects, f"{conversation.id}/{node.id}", player, notify)
        if not node.choices:
            node_id = node.next
            continue
        visible = _visible_indices(node, player)
        if not visible:
            break
        path = frozenset({node.id})
        done = [_choice_done(conversation, node, i, player, path) for i in visible]
        index = visible[pick([node.choices[i].text for i in visible], done)]
        choice = node.choices[index]
        if choice.reply:
            show(choice.reply)
        last_key = _choice_key(conversation, node, index)
        _apply_once(choice.effects, last_key, player, notify)
        node_id = choice.next
    if last_key:
        seen.add(last_key)
    if not conversation.repeatable:
        start = _resolve(conversation, conversation.start)
        if start is None or _all_done(conversation, start, player, frozenset({start.id})):
            seen.add(conversation.id)


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
