from valeterna.items.potions.healing_potion import HealingPotion
from valeterna.world.lore import LoreNote
from valeterna.world.npc import NPC, Choice, Condition, Conversation, DialogueNode, end, give_item, set_flag
from valeterna.world.zone import Zone

ZONE = Zone(
    id="canon_del_trueno",
    name="Cañón del Trueno",
    theme="Paso de montaña, piedra",
    enemies=(
        "Gárgola",
        "Gólem de Piedra",
        "Minero Poseído",
        "Murciélago de Tormenta",
        "Chispa del Puntal",
        "Aparición de la Cuadrilla",
        "Verdugo de la Mina",
        "Cabra Montés Corrupta",
        "Heraldo de la Tormenta",
        "El Decimoquinto",
    ),  # v0.15.0-a: roster completo (GDD §4)
    sub_locations=("Mina derrumbada", "Puente colgante"),
    key_npcs=("Kort",),
)

_POTION = give_item(HealingPotion("Poción de Salud", "Restaura 20 HP", 2, 20).to_dict())

_KORT_INTRO = Conversation(
    id="kort_intro",
    start="saludo",
    nodes=(
        DialogueNode(
            "saludo",
            "Alto. No se pasa. El paso está sellado por orden mía y no admito discusión. Me llamo Kort, capataz "
            "de la mina derrumbada. Lo que la mina se tragó, no vuelve.",
            effects=(set_flag("conocio_a_kort"),),
            choices=(
                Choice("¿Quién selló el paso?", next="sello"),
                Choice(
                    "¿Qué había en la mina?",
                    next="mina",
                    condition=Condition(forbids_flags=("recibio_pocion_kort",)),
                ),
                end("No busco pelea.", "Mejor. Los últimos que la buscaron no volvieron a subir."),
            ),
        ),
        DialogueNode(
            "sello",
            "Yo, con lo que quedaba de mi cuadrilla. Cargamos roca sobre el camino viejo para que la corrupción "
            "no bajara. No es un muro: es una promesa. Y las promesas también se agrietan.",
            choices=(
                end(
                    "¿Se está agrietando ya?",
                    "Con cada tormenta. Por eso las Gárgolas vigilan: alguien las ha puesto ahí.",
                ),
                end("¿Y si necesito pasar?", "Ya se pensará. Pero no ahora, y no sin un buen motivo."),
                end(
                    "Habéis hecho lo correcto.",
                    "No lo sé. Lo hice sin dudar, que a veces es peor.",
                ),
            ),
        ),
        DialogueNode(
            "mina",
            "Buscábamos mineral de tormenta, piedra que guarda relámpagos. Excavamos demasiado y algo respondió "
            "desde abajo. La galería se vino abajo con catorce de los míos dentro. Desde entonces los Gólems "
            "caminan por donde antes cavábamos. Toma esta poción: era de uno de los catorce y ya no la necesita.",
            effects=(_POTION, set_flag("recibio_pocion_kort")),
            choices=(
                end("Lo lamento, Kort.", "No lo lamentes. Aprende de ellos: no caves donde algo escucha."),
                end(
                    "¿Los Gólems eran vuestros?",
                    "Los hizo la mina, no nosotros. Solo los sacamos de la roca sin querer.",
                ),
                end(
                    "¿Crees que queda alguien vivo?",
                    "No. Pero se mueven, y eso a veces es tan cruel como la esperanza.",
                ),
            ),
        ),
    ),
)

_KORT_TORRE = Conversation(
    id="kort_torre",
    start="torre",
    trigger=Condition(requires_flags=("conocio_a_sella",)),
    nodes=(
        DialogueNode(
            "torre",
            "Vienes de la torre del norte. Antes les vendíamos mineral a sus magos: pagaban bien la piedra de "
            "tormenta. Y ahora empiezo a pensar que parte de esto es culpa nuestra.",
            choices=(
                end(
                    "¿Vendíais mineral a la torre?",
                    "Todo el que sacábamos. Ahora sé para qué lo usaban: para canalizar la Brecha.",
                ),
                end("No es culpa vuestra.", "Es amable. Pero yo firmé los albaranes."),
                end("¿Qué sabes de Sella?", "Que era honesta. Y que sus superiores no."),
            ),
        ),
    ),
)

NPCS = (
    NPC(
        id="kort",
        name="Kort",
        zone_id="canon_del_trueno",
        conversations=(_KORT_INTRO, _KORT_TORRE),
        idle_lines=(
            "Las tormentas de aquí no avisan. Las promesas de piedra, tampoco.",
            "Si oyes crujir la roca, corre. No pienses.",
            "Catorce nombres. Los recito cada noche para no olvidar ninguno.",
        ),
    ),
)

LORE = (
    LoreNote(
        id="nombres_puntal",
        zone_id="canon_del_trueno",
        sub_location="Mina derrumbada",
        title="Nombres en un puntal",
        text=(
            "Catorce nombres rascados en un puntal de la mina, en columna, cada uno con letra distinta. Al final "
            "hay un decimoquinto a medio grabar: solo la primera letra, una K, y el surco de un cuchillo que se "
            "detuvo a tiempo."
        ),
    ),
    LoreNote(
        id="cartel_puente",
        zone_id="canon_del_trueno",
        sub_location="Puente colgante",
        title="Cartel del puente",
        text=(
            "Clavado en el primer poste: «PASO CERRADO POR ORDEN DE LA CUADRILLA. Quien cruce lo hace por su "
            "cuenta, y no vuelve por la misma orilla.» Debajo, con carbón: «Ya nadie cruza. Ya nadie llega.»"
        ),
    ),
)
