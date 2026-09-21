from valeterna.world.npc import NPC, Choice, Condition, Conversation, DialogueNode, end, set_flag
from valeterna.world.zone import Zone

ZONE = Zone(
    id="los_yermos",
    name="Los Yermos",
    theme="Tierras salvajes en torno al pueblo",
    enemies=("Goblin", "Huargo", "Esqueleto", "Bandido"),
    sub_locations=("Campamento de bandidos", "Túmulo"),
    key_npcs=("Cael",),
)

_CAEL_INTRO = Conversation(
    id="cael_intro",
    start="saludo",
    nodes=(
        DialogueNode(
            "saludo",
            "No te acerques al foso, la tierra cede... ¡Ah! Una persona viva. Perdona. Soy Cael. Estudiaba los "
            "archivos reales cuando la capital ardió; ahora estudio lo que ardió con ella. ¿Sabes qué hay bajo "
            "estos túmulos?",
            effects=(set_flag("conocio_a_cael"),),
            choices=(
                Choice("¿Qué es la Brecha?", next="brecha"),
                Choice("¿Por qué vives aquí, entre tumbas?", next="tumbas"),
                end("No, y prefiero no saberlo.", "Sabia decisión. Yo no fui capaz de tomarla."),
            ),
        ),
        DialogueNode(
            "brecha",
            "Una herida en el velo entre lo que es y lo que no debería ser. El Dragón la abrió al arrasar la "
            "capital, pero no habría podido si algo no hubiera estado ya empujando desde el otro lado. Y hay un "
            "altar en el Bosque de los Susurros que la mantiene abierta, alimentándola.",
            effects=(set_flag("sabe_del_altar"),),
            choices=(
                end(
                    "¿Se puede cerrar?",
                    "Quizá. Destruyendo el altar y lo que hay atado a él. Pero no sé qué es lo que hay atado.",
                ),
                end(
                    "¿Quién construyó el altar?",
                    "Gente que creyó estar haciendo algo bueno. Es lo peor de todo.",
                ),
                end(
                    "Suena a superstición.",
                    "Ojalá lo fuera. Pero he visto cómo se comportan los muertos de estos Yermos por la noche.",
                ),
            ),
        ),
        DialogueNode(
            "tumbas",
            "Porque los muertos de aquí fueron los primeros en sentir la Brecha. Ver cómo reaccionan me dice "
            "hacia dónde apunta. Y porque nadie más viene, lo cual me deja trabajar.",
            choices=(
                end(
                    "¿Los muertos hablan?",
                    "No con palabras. Pero caminan siempre en la misma dirección: hacia el Bosque.",
                ),
                end(
                    "¿No tienes miedo?",
                    "Constantemente. Pero es un miedo que trabaja. El que paraliza es otro.",
                ),
                end("Estás loco.", "Es posible. Los cuerdos huyeron y aquí sigo yo."),
            ),
        ),
    ),
)

_CAEL_BOSQUE = Conversation(
    id="cael_bosque",
    start="bosque",
    trigger=Condition(requires_flags=("conocio_a_mirelle",)),
    nodes=(
        DialogueNode(
            "bosque",
            "Has hablado con Mirelle, entonces. Llevaba años sin saber de ella. ¿Ha visto el altar?",
            choices=(
                end(
                    "Vive cerca. Sabe más de lo que cuenta.",
                    "Los que sobreviven en el Bosque siempre saben más de lo que cuentan. Es su forma de seguir vivos.",
                ),
                end(
                    "Dice que hay algo atado al altar.",
                    "Entonces mi teoría se sostiene. Y eso me asusta más que si la hubiese refutado.",
                ),
                end(
                    "No mencionó ningún altar.",
                    "Mejor. Hay cosas que solo se cuentan cuando ya no se puede callarlas.",
                ),
            ),
        ),
    ),
)

NPCS = (
    NPC(
        id="cael",
        name="Cael",
        zone_id="los_yermos",
        conversations=(_CAEL_INTRO, _CAEL_BOSQUE),
        idle_lines=(
            "Perdona, estoy contando huesos. Nunca coinciden con los registros.",
            "Los muertos de estos túmulos no descansan. Solo esperan.",
            "Todo lo que sé cabe en una libreta. Todo lo que temo, en tres.",
        ),
    ),
)
