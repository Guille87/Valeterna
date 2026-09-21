from valeterna.world.npc import NPC, Choice, Condition, Conversation, DialogueNode, end, set_flag
from valeterna.world.zone import Zone

ZONE = Zone(
    id="ciudadela_en_ruinas",
    name="Ciudadela en Ruinas",
    theme="La capital arrasada, suelo infernal",
    enemies=("Ángel Caído", "Demonio"),
    sub_locations=("Catedral rota", "Plaza"),
    key_npcs=("Aldric",),
)

_ALDRIC_INTRO = Conversation(
    id="aldric_intro",
    start="saludo",
    nodes=(
        DialogueNode(
            "saludo",
            "Alto, viajero. Nadie llega hasta aquí por casualidad. Soy Aldric, último caballero de la Guardia de la "
            "Catedral. Custodio de algo que ya no existe: un reino.",
            effects=(set_flag("conocio_a_aldric"),),
            choices=(
                Choice("¿Qué queda de la catedral?", next="catedral"),
                Choice("¿Qué ocupa ahora la ciudad?", next="ocupante"),
                end(
                    "Vengo a ayudar.",
                    "Pocos vienen a ayudar. Muchos vienen a mirar. Tú tienes ojos de lo primero, por ahora.",
                ),
            ),
        ),
        DialogueNode(
            "catedral",
            "Fue el último bastión. Cuando el Dragón llegó, el rey nos ordenó cerrar las puertas y rezar. "
            "Murieron todos los que rezaban. Yo estaba de guardia en la puerta, y viví. No sé si eso es gracia o "
            "castigo.",
            choices=(
                end("Es una gracia.", "Dilo cuando hayas visto las paredes por dentro."),
                end("Sobrevivir no es culpa.", "Tú no estuviste allí. Yo sí."),
                end(
                    "¿Por qué sigues aquí, entonces?",
                    "Porque alguien tiene que contar los nombres. Los llevo cosidos en el peto, uno por uno.",
                ),
            ),
        ),
        DialogueNode(
            "ocupante",
            "Algo que llegó con la Brecha y es peor que el Dragón. El Dragón arrasó. Esto se queda. Los ángeles "
            "caídos y los demonios que ves no destruyen la ciudad: la gobiernan.",
            choices=(
                end(
                    "¿Quién gobierna?",
                    "No he visto su rostro. Los ángeles caídos le sirven. Los demonios solo lo temen.",
                ),
                end(
                    "¿Se les puede vencer?",
                    "A cada uno, sí. Al que los manda, no lo sé. Hay algo debajo de la catedral; ahí se acaba mi mapa.",
                ),
                end(
                    "Volveré con refuerzos.",
                    "No hay refuerzos, viajero. Solo tú. Y por eso te estoy hablando.",
                ),
            ),
        ),
    ),
)

_ALDRIC_KORT = Conversation(
    id="aldric_kort",
    start="kort",
    trigger=Condition(requires_flags=("conocio_a_kort",)),
    nodes=(
        DialogueNode(
            "kort",
            "Vienes del Cañón. Kort fue cabo de mi guardia antes de retirarse a la mina. Si sigue firme en el "
            "paso, es que aún queda algo de la vieja guardia en pie.",
            choices=(
                end("Sigue firme. Y terco.", "Terco era. Es buen sello el que pone un terco."),
                end(
                    "Perdió a catorce hombres.",
                    "Lo sé. Yo perdí a mil. No es una competición, pero pesa igual.",
                ),
                end(
                    "No me habló de ti.",
                    "No lo haría. Kort nunca hablaba de nadie que no estuviera delante.",
                ),
            ),
        ),
    ),
)

NPCS = (
    NPC(
        id="aldric",
        name="Aldric",
        zone_id="ciudadela_en_ruinas",
        conversations=(_ALDRIC_INTRO, _ALDRIC_KORT),
        idle_lines=(
            "Guardia hasta el alba. Como siempre.",
            "Aquí abajo cada piedra tiene nombre. Yo me sé casi todos.",
            "No mires arriba, a las vidrieras. Aún miran de vuelta.",
        ),
    ),
)
