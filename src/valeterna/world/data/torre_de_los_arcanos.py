from valeterna.world.npc import NPC, Choice, Condition, Conversation, DialogueNode, end, set_flag
from valeterna.world.zone import Zone

ZONE = Zone(
    id="torre_de_los_arcanos",
    name="Torre de los Arcanos / Necrópolis",
    theme="Torre de magos + cementerio",
    enemies=("Mago", "Nigromante"),
    sub_locations=("Biblioteca", "Cripta"),
    key_npcs=("Sella",),
)

_SELLA_INTRO = Conversation(
    id="sella_intro",
    start="saludo",
    nodes=(
        DialogueNode(
            "saludo",
            "Cierra la puerta, por favor. No por los muertos: por las corrientes. Soy Sella, archivera de la Torre "
            "de los Arcanos; o lo fui, hasta que descubrí en qué se gastaba la biblioteca.",
            effects=(set_flag("conocio_a_sella"),),
            choices=(
                Choice("¿Qué hacían en la torre?", next="torre"),
                Choice("¿Y los muertos de fuera?", next="muertos"),
                end("Me marcho.", "Haz lo que quieras. Pero no toques nada de lo que brilla."),
            ),
        ),
        DialogueNode(
            "torre",
            "Canalizaban la Brecha. Creían que podían domesticarla: extraer su energía y dársela a un reino que se "
            "caía a pedazos. No pudieron. Solo lograron que la Brecha respirase por nosotros.",
            effects=(set_flag("sella_tomo_pista"),),
            choices=(
                end(
                    "¿Quién dio la orden?",
                    "Un consejo de magos. Ninguno queda entero.",
                ),
                end(
                    "¿Y tú? ¿Ayudaste?",
                    "Catalogué los rituales. Es lo mismo que ayudar, aunque me repita que no.",
                ),
                end(
                    "¿Se puede detener?",
                    "Quizá desde la Biblioteca. Hay un tomo prohibido que explica cómo apagar el canal. Aún no lo "
                    "he encontrado.",
                ),
            ),
        ),
        DialogueNode(
            "muertos",
            "Los levanta el mismo canal. La Brecha empuja hacia arriba lo que haya enterrado, y aquí abajo hay "
            "siglos de enterrados. Los nigromantes no los crean: los guían. Es más barato.",
            choices=(
                end(
                    "Barato y horrible.",
                    "Sí. Pero un reino que se cae ya no tiene escrúpulos.",
                ),
                end("¿Se les puede dar descanso?", "Solo cerrando el canal. Todo lo demás es agua en un cesto."),
                end(
                    "¿Y tú por qué no huyes?",
                    "Porque no hay adónde. Y porque soy la única que sabe leer las notas de los que se fueron.",
                ),
            ),
        ),
    ),
)

_SELLA_CIUDADELA = Conversation(
    id="sella_ciudadela",
    start="aldric",
    trigger=Condition(requires_flags=("conocio_a_aldric",)),
    nodes=(
        DialogueNode(
            "aldric",
            "Aldric... ¿has hablado con él? Coincidimos en la misma corte: yo escribía, él juraba. Los dos fracasamos.",
            choices=(
                end(
                    "Dice que la catedral era el último bastión.",
                    "Lo era. Y lo que la ocupa ahora entró por la misma grieta que mis rituales.",
                ),
                end(
                    "Le diré que sigues viva.",
                    "No. Guarda ese dato. Si necesita odiarme, lo prefiero a que me compadezca.",
                ),
                end(
                    "¿Qué os pasó a los dos?",
                    "Un pacto de juventud. Uno de los dos no lo cumplió. Ya no importa cuál.",
                ),
            ),
        ),
    ),
)

NPCS = (
    NPC(
        id="sella",
        name="Sella",
        zone_id="torre_de_los_arcanos",
        conversations=(_SELLA_INTRO, _SELLA_CIUDADELA),
        idle_lines=(
            "Estoy ordenando lo que queda. El orden es lo último que se pierde.",
            "No leas en voz alta nada de esta biblioteca. Algunas frases contestan.",
            "Cada libro que salvo es un canal que no se abre.",
        ),
    ),
)
