from valeterna.world.lore import LoreNote
from valeterna.world.npc import NPC, Choice, Condition, Conversation, DialogueNode, end, set_flag
from valeterna.world.zone import Zone

ZONE = Zone(
    id="bosque_de_los_susurros",
    name="Bosque de los Susurros",
    theme="Bosque encantado",
    enemies=("Orco", "Espíritu Vengativo", "Troll"),
    sub_locations=("Claro del altar", "Cabaña quemada"),
    key_npcs=("Mirelle",),
)

_MIRELLE_INTRO = Conversation(
    id="mirelle_intro",
    start="saludo",
    nodes=(
        DialogueNode(
            "saludo",
            "No te acerques al claro con esa luz: los espíritus de este bosque siguen a quien camina con fuego. "
            "Soy Mirelle. Esta cabaña fue mía, y de mi marido. Ahora es un montón de vigas que arden por dentro "
            "sin llama.",
            effects=(set_flag("conocio_a_mirelle"),),
            choices=(
                Choice("¿Qué pasó aquí?", next="incendio"),
                Choice("¿Por qué sigues viviendo aquí?", next="quedarse"),
                end(
                    "Perdona, no quería molestar.",
                    "No molestas. Hace mucho que nadie me habla sin llevar un hacha en la mano.",
                ),
            ),
        ),
        DialogueNode(
            "incendio",
            "Una noche los árboles empezaron a susurrar. Mi marido salió a mirar. Volvió con los ojos vacíos, y "
            "cuando quise detenerlo prendió la cabaña con los dos dentro. Yo salí. Él no.",
            choices=(
                end(
                    "Lo siento mucho.",
                    "No lo sientas. Es lo que hace este bosque: te devuelve a los tuyos, pero rotos.",
                ),
                end(
                    "¿Quién susurraba?",
                    "Algo con voz de muchos. No lo vi, solo lo oí. Y sigo oyéndolo cada noche.",
                ),
                end("¿Sigue vivo tu marido?", "Vivo, no. Camina entre los árboles. Es distinto. Ya no lo miro."),
            ),
        ),
        DialogueNode(
            "quedarse",
            "Porque alguien tiene que vigilar el viejo camino que baja hacia el cañón. La corrupción sigue ese "
            "sendero; si el paso se cierra, no llegará a las tierras de abajo. Ya casi está cerrado. Cuando lo "
            "esté del todo, me marcharé.",
            choices=(
                end(
                    "¿El paso del cañón está sellado?",
                    "Casi. Alguien lo selló desde el otro lado, no sé quién. Y lo hizo bien.",
                ),
                end(
                    "¿Cuánto tiempo llevas vigilando?",
                    "Desde el invierno. Y no cuento las noches, solo las mañanas.",
                ),
                end(
                    "Deberías irte al pueblo.",
                    "Eso me dice Dorn cada vez que le mando un recado. Pero yo tengo aquí mi tarea.",
                ),
            ),
        ),
    ),
)

_MIRELLE_CIENAGA = Conversation(
    id="mirelle_cienaga",
    start="olor",
    trigger=Condition(requires_flags=("conocio_a_oren",)),
    nodes=(
        DialogueNode(
            "olor",
            "Traes olor a ciénaga. Cuando el viento cambia, el bosque huele igual. ¿Has estado allí abajo? "
            "¿Qué has visto?",
            choices=(
                end(
                    "A un barquero llamado Oren.",
                    "Oren. Lo recuerdo: traía mercancía hasta Piedrablanca. Es de los que no se hunden.",
                ),
                end(
                    "Agua negra hasta donde alcanza la vista.",
                    "Ya era negra antes de la Brecha. Mi abuela decía que allí abajo hay algo que duerme.",
                ),
                end("Prefiero no hablar de ello.", "Tampoco yo. Pero alguien tendrá que hacerlo."),
            ),
        ),
    ),
)

NPCS = (
    NPC(
        id="mirelle",
        name="Mirelle",
        zone_id="bosque_de_los_susurros",
        conversations=(_MIRELLE_INTRO, _MIRELLE_CIENAGA),
        idle_lines=(
            "Escucha. ¿Lo oyes? Yo ya no distingo el bosque del silencio.",
            "No cortes ramas. A los árboles no les gusta que les recuerden que son madera.",
            "Cada mañana que despierto sin oír susurros, desconfío.",
        ),
    ),
)

LORE = (
    LoreNote(
        id="inscripcion_altar",
        zone_id="bosque_de_los_susurros",
        sub_location="Claro del altar",
        title="Inscripción del altar",
        text=(
            "Grabada en la piedra, con letra apretada: «Lo que se ata aquí no descansa; lo que lo ata, tampoco. "
            "Quien rompa la cadena, que sepa antes qué paga.» Debajo, mucho más reciente, alguien ha arañado una "
            "sola palabra: «Perdón.»"
        ),
    ),
    LoreNote(
        id="viga_muescas",
        zone_id="bosque_de_los_susurros",
        sub_location="Cabaña quemada",
        title="Muescas en una viga",
        text=(
            "Una viga salvada del fuego, con muescas de trampero: una por cada noche que las voces le hablaron. "
            "Hay cuarenta y siete. La última está grabada tan hondo que el filo llegó a atravesar la madera."
        ),
    ),
)
