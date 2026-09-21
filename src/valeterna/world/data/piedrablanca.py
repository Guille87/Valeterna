from valeterna.items.potions.healing_potion import HealingPotion
from valeterna.world.npc import NPC, Choice, Conversation, DialogueNode, give_item, set_flag
from valeterna.world.zone import Zone

ZONE = Zone(
    id="piedrablanca",
    name="Piedrablanca",
    theme="Último pueblo libre",
    enemies=(),
    sub_locations=("Taberna", "Herrería", "Mercado", "Refugio"),
    key_npcs=("Yerma", "Dorn", "Halbrand", "Nia"),
)

_MET_YERMA = set_flag("conocio_a_yerma")
_POTION = give_item(HealingPotion("Poción de Salud", "Restaura 20 HP", 2, 20).to_dict())

# Solo Yerma por ahora (v0.13.0-a, para poder jugar el motor de diálogo de
# punta a punta); el resto de NPCs de Piedrablanca y de las demás regiones
# llegan en v0.13.0-b.
_YERMA_INTRO = Conversation(
    id="yerma_intro",
    start="bienvenida",
    nodes=(
        DialogueNode(
            "bienvenida",
            "Otra cara viva... Pasa, pasa. Soy Yerma, y la Taberna es mía, o lo que queda de ella. "
            "Tienes pinta de haber visto arder Valeterna.",
            choices=(
                Choice("Sí. Fui de los pocos que salieron con vida.", next="superviviente"),
                Choice("Solo busco una cama y algo caliente.", next="cama"),
                Choice("¿Qué está pasando en estas tierras?", next="brecha"),
            ),
        ),
        DialogueNode(
            "superviviente",
            "Entonces ya sabes lo que es perderlo todo. Aquí nadie te pedirá cuentas de lo que hiciste para "
            "salir. Toma, invita la casa; nunca se sabe cuándo hará falta.",
            effects=(_POTION,),
            choices=(
                Choice("Gracias, Yerma.", effects=(_MET_YERMA,), reply="No hay de qué. Ve con cuidado ahí fuera."),
                Choice("No hacía falta.", effects=(_MET_YERMA,), reply="Lo sé. Por eso mismo se hace."),
                Choice(
                    "Lo recordaré.",
                    effects=(_MET_YERMA,),
                    reply="Más te vale. Aquí la memoria es lo único que no se ha quemado.",
                ),
            ),
        ),
        DialogueNode(
            "cama",
            "Descansar cuesta según lo maltrecho que vengas: cuanto más curtido, más hay que remendar. "
            "Baja a la Taberna cuando lo necesites; el fuego siempre está encendido.",
            choices=(
                Choice(
                    "Lo tendré en cuenta.",
                    effects=(_MET_YERMA,),
                    reply="Hazlo. Y come algo antes, que se te ve flaco.",
                ),
                Choice(
                    "Espero que el precio sea justo.",
                    effects=(_MET_YERMA,),
                    reply="Justo para mí y para ti. No le cobraría de más a quien vuelve de ahí fuera.",
                ),
                Choice("Hasta luego.", effects=(_MET_YERMA,), reply="Hasta luego. El fuego seguirá encendido."),
            ),
        ),
        DialogueNode(
            "brecha",
            "Dicen que el Dragón rajó el velo al quemar la capital, y que por esa grieta se cuela todo lo que "
            "no debería andar por el mundo. Yo solo sé que cada noche hay más muertos que no se quedan quietos.",
            choices=(
                Choice(
                    "Voy a averiguar de dónde viene.",
                    effects=(_MET_YERMA,),
                    reply="Entonces vuelve de una pieza para contármelo. Y no te fíes de nada que sonría.",
                ),
                Choice("¿Y tú por qué sigues aquí?", next="porque"),
                Choice(
                    "Prefiero no pensarlo.",
                    effects=(_MET_YERMA,),
                    reply="Nadie te lo reprochará. Aunque no pienses en ella, la grieta sigue ahí.",
                ),
            ),
        ),
        DialogueNode(
            "porque",
            "Porque alguien tiene que mantener el fuego encendido para quien vuelve. Si la gente deja de volver, "
            "Piedrablanca ya habrá caído, aunque sus muros sigan en pie.",
            choices=(
                Choice(
                    "Volveré, te lo prometo.",
                    effects=(_MET_YERMA,),
                    reply="Eso me basta. Anda, ve; la noche no espera.",
                ),
                Choice(
                    "Eres más valiente que yo.",
                    effects=(_MET_YERMA,),
                    reply="No lo soy. Solo soy demasiado terca para irme.",
                ),
                Choice(
                    "Ojalá haya más como tú.",
                    effects=(_MET_YERMA,),
                    reply="Los hay. Casi todos bajo tierra, pero los hay.",
                ),
            ),
        ),
    ),
)

NPCS = (
    NPC(
        id="yerma",
        name="Yerma",
        zone_id="piedrablanca",
        conversations=(_YERMA_INTRO,),
        idle_lines=(
            "Siéntate un rato. El fuego no se apaga solo, pero tampoco pide nada a cambio.",
            "Si te duele algo, la Taberna hace milagros por unas pocas monedas.",
            "Cada mañana que amanece sin humo en el horizonte cuenta como una victoria.",
        ),
    ),
)
