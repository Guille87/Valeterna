from valeterna.world.lore import LoreNote
from valeterna.world.npc import NPC, Choice, Condition, Conversation, DialogueNode, end, give_gold, set_flag
from valeterna.world.zone import Zone

ZONE = Zone(
    id="cienaga_de_los_ahogados",
    name="Ciénaga de los Ahogados",
    theme="Marisma anegada",
    enemies=(),  # roster nuevo por diseñar (GDD §4)
    sub_locations=("Templo hundido", "Embarcadero podrido"),
    key_npcs=("Oren",),
)

_OREN_INTRO = Conversation(
    id="oren_intro",
    start="saludo",
    nodes=(
        DialogueNode(
            "saludo",
            "Sube o baja, pero no te quedes en las tablas: la mitad están podridas. Soy Oren. Llevo el bote por "
            "estas aguas desde antes de que las llamaran de los Ahogados. Cuento a los que me encuentro: hoy sois "
            "uno.",
            effects=(set_flag("conocio_a_oren"),),
            choices=(
                Choice("¿Por qué las llaman de los Ahogados?", next="ahogados"),
                Choice(
                    "¿Puedes llevarme por el pantano?",
                    next="bote",
                    condition=Condition(forbids_flags=("recibio_oro_oren",)),
                ),
                end("Solo estoy de paso.", "Todos están de paso. Y algunos se quedan, boca abajo."),
            ),
        ),
        DialogueNode(
            "ahogados",
            "Porque los que entran sin barquero se quedan. El agua tiene memoria: devuelve a los suyos por la "
            "noche, empapados y con hambre. Y hay algo más abajo, más antiguo que la Brecha. No lo he visto. Lo he "
            "sentido moverse bajo el bote.",
            choices=(
                end(
                    "¿Más antiguo que la Brecha?",
                    "Antes de que hubiera reino ya se contaban cuentos de esta ciénaga. La Brecha solo la ha "
                    "despertado.",
                ),
                end("¿Y por qué sigues navegando?", "Porque conozco cada tabla. Es mi manera de rezar."),
                end("Tendré cuidado.", "No lo tendrás, pero es amable de tu parte decirlo."),
            ),
        ),
        DialogueNode(
            "bote",
            "Puedo. Pero el agua cambia: lo que ayer era camino hoy es fondo. Toma esta bolsa que saqué del agua; "
            "pesa menos de lo que crees, pero te servirá para comprar valor.",
            effects=(give_gold(25), set_flag("recibio_oro_oren")),
            choices=(
                end("Gracias, Oren.", "No me las des. Guarda el oro por si el pantano decide cobrar."),
                end("¿De quién era la bolsa?", "De alguien que ya no la necesita. No preguntes más."),
                end(
                    "¿Qué pides a cambio?",
                    "Nada. Solo que si ves un templo hundido, no entres solo. Aviso de barquero.",
                ),
            ),
        ),
    ),
)

_OREN_PASO = Conversation(
    id="oren_paso",
    start="paso",
    trigger=Condition(requires_flags=("conocio_a_kort",)),
    nodes=(
        DialogueNode(
            "paso",
            "Vienes del Cañón: hueles a piedra mojada. Dicen que sellaron el paso desde arriba. ¿Lo has visto?",
            choices=(
                end(
                    "Kort guarda el paso y no deja pasar a nadie.",
                    "Entonces hace bien. Lo que baja por ese camino no debería mezclarse con esta agua.",
                ),
                end(
                    "Vi el puente colgante.",
                    "Mi abuelo lo cruzaba con mulas. Hoy no lo cruzaría ni un pájaro.",
                ),
                end(
                    "¿Y tú por qué preguntas?",
                    "Porque si el paso se cierra, este pantano se queda sin nadie con quien hablar. Y un barquero "
                    "sin nadie es solo un hombre con un bote.",
                ),
            ),
        ),
    ),
)

NPCS = (
    NPC(
        id="oren",
        name="Oren",
        zone_id="cienaga_de_los_ahogados",
        conversations=(_OREN_INTRO, _OREN_PASO),
        idle_lines=(
            "El agua sube. Siempre sube. Lo raro es cuando baja.",
            "No mires el fondo mucho rato: el fondo también mira.",
            "Cada noche cuento las luces del pantano. Cada noche hay una más.",
        ),
    ),
)

LORE = (
    LoreNote(
        id="relieve_templo",
        zone_id="cienaga_de_los_ahogados",
        sub_location="Templo hundido",
        title="Relieve del templo hundido",
        text=(
            "Bajo el agua turbia, un relieve casi borrado: una figura inmensa hundida en la ciénaga y, a su "
            "alrededor, pequeñas figuras arrodilladas. Ninguna mira a la grande. Todas miran hacia arriba, "
            "hacia quien lee."
        ),
    ),
    LoreNote(
        id="cuaderno_embarcadero",
        zone_id="cienaga_de_los_ahogados",
        sub_location="Embarcadero podrido",
        title="Cuaderno del embarcadero",
        text=(
            "Una lista de fechas y cifras con letra de barquero: «Subieron: 3. Volvieron: 1». «Subieron: 5. "
            "Volvieron: 2». Los últimos renglones dicen solo: «Hoy, al volver, conté uno más de los que llevé.»"
        ),
    ),
)
