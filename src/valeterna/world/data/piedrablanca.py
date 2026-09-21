from valeterna.items.potions.healing_potion import HealingPotion
from valeterna.world.lore import LoreNote
from valeterna.world.npc import (
    NPC,
    Choice,
    Condition,
    Conversation,
    DialogueNode,
    end,
    give_gold,
    give_item,
    set_flag,
)
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

_YERMA_INTRO = Conversation(
    id="yerma_intro",
    start="bienvenida",
    nodes=(
        DialogueNode(
            "bienvenida",
            "Otra cara viva... Pasa, pasa. Soy Yerma, y la Taberna es mía, o lo que queda de ella. "
            "Tienes pinta de haber visto arder Valeterna.",
            choices=(
                Choice(
                    "Sí. Fui de los pocos que salieron con vida.",
                    next="superviviente",
                    condition=Condition(forbids_flags=("recibio_pocion_yerma",)),
                ),
                Choice("Solo busco una cama y algo caliente.", next="cama"),
                Choice("¿Qué está pasando en estas tierras?", next="brecha"),
            ),
        ),
        DialogueNode(
            "superviviente",
            "Entonces ya sabes lo que es perderlo todo. Aquí nadie te pedirá cuentas de lo que hiciste para "
            "salir. Toma, invita la casa; nunca se sabe cuándo hará falta.",
            effects=(_POTION, set_flag("recibio_pocion_yerma")),
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

_HALBRAND_INTRO = Conversation(
    id="halbrand_intro",
    start="saludo",
    nodes=(
        DialogueNode(
            "saludo",
            "Alto ahí... ah, no eres uno de ellos. Soy Halbrand, capitán de lo que queda de la guardia: once "
            "hombres, y tres duermen con fiebre. Los bandidos de los Yermos nos quitan las caravanas y nos cortan "
            "los caminos. Sin comida no habrá pueblo.",
            effects=(set_flag("conocio_a_halbrand"),),
            choices=(
                Choice("¿Qué quieren esos bandidos?", next="bandidos"),
                Choice("¿Por qué no atacáis su campamento?", next="campamento"),
                end(
                    "Yo me encargaré de ellos.",
                    "Cada bandido que caiga es un carro que llega al mercado. No lo olvidaremos.",
                ),
            ),
        ),
        DialogueNode(
            "bandidos",
            "Lo que quieren todos: lo que otros tienen. Antes eran mercenarios del rey; cuando cayó la capital "
            "nadie les pagó y aprendieron que es más fácil quitar que ganar. Ya no distinguen entre soldado y "
            "campesino.",
            choices=(
                end(
                    "¿Eran soldados del reino?",
                    "Algunos. Los reconocerás por cómo se mueven. Eso los hace más peligrosos, no menos.",
                ),
                end(
                    "Entonces no hay quien razone con ellos.",
                    "Lo intenté dos veces. La segunda me devolvieron a un explorador sin botas y sin caballo.",
                ),
                end(
                    "Tendrán un cabecilla.",
                    "Lo tienen. Pero mientras siga en pie el campamento, cortarle la cabeza solo cambiaría el nombre.",
                ),
            ),
        ),
        DialogueNode(
            "campamento",
            "Con once hombres, la mitad enfermos, dejaría los muros vacíos y se colarían por la puerta de atrás. "
            "Necesito a alguien que no tenga que proteger ninguna puerta.",
            choices=(
                end("Un mercenario, en resumen.", "Un aliado. La diferencia es que a ti te doy las gracias."),
                end(
                    "¿Y qué ofreces a cambio?",
                    "Lo que pueda: la gratitud de la guardia y una puerta que se abre sin preguntas.",
                ),
                end("Entendido. Tendrás noticias mías.", "Ojalá sean buenas."),
            ),
        ),
    ),
)

_HALBRAND_INFORME = Conversation(
    id="halbrand_informe",
    start="informe",
    trigger=Condition(requires_flags=("conocio_a_cael",)),
    nodes=(
        DialogueNode(
            "informe",
            "Me dicen que hablaste con el erudito de los Yermos. Cree que los bandidos y la Brecha tienen algo "
            "que ver. Yo solo sé que desde que se abrió los ataques son más rabiosos. ¿Qué te contó?",
            choices=(
                end(
                    "Dice que la Brecha se alimenta de algo.",
                    "Lo que sea, que se alimente de otra cosa que no sea mi gente.",
                ),
                end(
                    "Que no todo enemigo es humano.",
                    "Eso ya lo sé. Los bandidos, al menos, me dejan un cuerpo que enterrar.",
                ),
                end(
                    "No me fío de todo lo que dice.",
                    "Haces bien. Un erudito cree lo que ha leído; un soldado, lo que ha visto. Yo prefiero lo segundo.",
                ),
            ),
        ),
    ),
)

_DORN_INTRO = Conversation(
    id="dorn_intro",
    start="saludo",
    nodes=(
        DialogueNode(
            "saludo",
            "¿Buscas piezas o buscas consejo? Uno se paga con oro, el otro con atención. Soy Dorn. Cazaba en el "
            "Bosque de los Susurros antes de que se llenara de lo que hoy lo llena; ahora vendo lo que otros "
            "traen y guardo lo que nadie quiere.",
            effects=(set_flag("conocio_a_dorn"),),
            choices=(
                Choice("¿Qué se caza en el Bosque de los Susurros?", next="bosque"),
                Choice(
                    "¿Tienes algún trabajo para mí?",
                    next="encargo",
                    condition=Condition(forbids_flags=("dorn_encargo_troll",)),
                ),
                end("Solo estoy mirando.", "Mira lo que quieras. Lo que se ve no se cobra."),
            ),
        ),
        DialogueNode(
            "bosque",
            "Ciervos, jabalíes, algún oso. Y ahora Orcos que arrancan árboles de raíz y Trolls que regeneran lo "
            "que les cortas. Los ciervos se han ido. Lo que queda no se caza: te caza.",
            choices=(
                end("¿Y los espíritus?", "No los cazo. Les dejo el paso. En un bosque se aprende cuándo callar."),
                end(
                    "Los Trolls parecen difíciles.",
                    "Lo son. Pero su piel vale más que la de cualquier animal: se curte y aguanta lo que un cuero "
                    "cualquiera no.",
                ),
                end("Entonces evitaré el Bosque.", "Evitarlo es de sabios. Pero no te veo cara de sabio."),
            ),
        ),
        DialogueNode(
            "encargo",
            "Sí, una cosa. Hay un cofre en mi vieja cabaña que solo se abre con piel de Troll: mi padre lo cerró "
            "así y yo perdí la llave. Tráeme una cuando la tengas. Toma un adelanto para que te equipes, y no "
            "vuelvas a por más.",
            effects=(give_gold(20), set_flag("dorn_encargo_troll")),
            choices=(
                end(
                    "Cuenta conmigo.",
                    "Bien. Y ten cuidado: los Trolls se levantan de heridas que matarían a un hombre.",
                ),
                end(
                    "¿Qué hay en el cofre?",
                    "Lo que mi padre consideraba digno de guardar. No lo sé. Eso es lo bueno.",
                ),
                end(
                    "No prometo nada.",
                    "Nadie lo hace. Quédate el adelanto igualmente; me sería más triste pedírtelo de vuelta.",
                ),
            ),
        ),
    ),
)

_DORN_CABANA = Conversation(
    id="dorn_cabana",
    start="cabana",
    trigger=Condition(requires_flags=("conocio_a_mirelle",)),
    nodes=(
        DialogueNode(
            "cabana",
            "¿Has estado en la cabaña quemada del Bosque? Vive allí una mujer, Mirelle. Poníamos trampas juntos "
            "antes de que ardiera todo. ¿Sigue de una pieza?",
            choices=(
                end("Sigue viva, y terca.", "Terca ya era. Me alegra que siga siéndolo."),
                end(
                    "Está sola entre los espíritus.",
                    "Lo sé. Le he dicho mil veces que bajara al pueblo. Nunca escucha.",
                ),
                end(
                    "No me dijo que te conociera.",
                    "No lo diría. Nos separamos mal. Ya te lo contará, si le da la gana.",
                ),
            ),
        ),
    ),
)

_NIA_INTRO = Conversation(
    id="nia_intro",
    start="saludo",
    nodes=(
        DialogueNode(
            "saludo",
            "¡Eh! Tú llevas espada. ¿Vas a los Yermos? Yo soy Nia. Perdí a Pipa, mi muñeca. Los bandidos me la "
            "quitaron cuando llegamos por el camino, y ahora la tienen en su campamento.",
            effects=(set_flag("conocio_a_nia"),),
            choices=(
                Choice("¿Cómo era tu muñeca?", next="pipa"),
                Choice("¿No es peligroso hablar con desconocidos?", next="peligro"),
                end(
                    "Veré qué puedo hacer.",
                    "¿De verdad? Prométeme que la buscarás. Es de trapo, con un ojo de botón azul y otro negro.",
                ),
            ),
        ),
        DialogueNode(
            "pipa",
            "Es de trapo y tiene un ojo azul y otro negro, porque el otro se perdió. Mi madre la cosió con un "
            "trozo de su vestido de boda. Por eso tengo que recuperarla.",
            choices=(
                end("Suena importante.", "Lo es. Es lo único que me queda de casa."),
                end(
                    "¿Dónde la viste por última vez?",
                    "En el carro. Un bandido la cogió y se rio. Se fueron hacia el campamento.",
                ),
                end("Habrá que rescatarla, entonces.", "¡Sí! No tengo nada que darte, pero te lo agradeceré mucho."),
            ),
        ),
        DialogueNode(
            "peligro",
            "Halbrand dice que no me aleje del pueblo. Pero tú no eres un bandido: los bandidos no preguntan. "
            "Tú preguntas.",
            choices=(
                end("Tiene razón, no te alejes.", "Ya lo sé. Por eso te lo pido a ti."),
                end("Buen ojo para la gente.", "Me lo dice Yerma. Que se me da bien juzgar a las personas."),
                end(
                    "Cuídate mucho, Nia.",
                    "Siempre. Me quedo junto a la fuente. Desde allí se ve la puerta.",
                ),
            ),
        ),
    ),
)

_NIA_ESPERA = Conversation(
    id="nia_espera",
    start="espera",
    trigger=Condition(requires_flags=("conocio_a_halbrand",)),
    nodes=(
        DialogueNode(
            "espera",
            "Halbrand me ha regañado por asomarme al camino. Pero desde la fuente veo quién vuelve. ¿Has visto ya "
            "el campamento?",
            choices=(
                end("Aún no. Pero la buscaré.", "Vale. Yo sigo esperando."),
                end("Halbrand tiene razón: es peligroso.", "Lo sé. Pero los mayores siempre dicen lo mismo."),
                end(
                    "¿Cómo se llama tu madre?",
                    "Ena. No llegó a Piedrablanca. Prefiero no hablar de eso.",
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
    NPC(
        id="halbrand",
        name="Halbrand",
        zone_id="piedrablanca",
        conversations=(_HALBRAND_INTRO, _HALBRAND_INFORME),
        idle_lines=(
            "Doble turno en la puerta. Otra vez.",
            "Si ves humo hacia los Yermos, avísame antes que a nadie.",
            "Un pueblo que duerme tranquilo es un pueblo que alguien ha vigilado.",
        ),
    ),
    NPC(
        id="dorn",
        name="Dorn",
        zone_id="piedrablanca",
        conversations=(_DORN_INTRO, _DORN_CABANA),
        idle_lines=(
            "Todo se vende, salvo la paciencia. Esa se acaba.",
            "Si vuelves con piel de Troll, sabrás dónde encontrarme.",
            "Un buen cazador escucha más de lo que dispara.",
        ),
    ),
    NPC(
        id="nia",
        name="Nia",
        zone_id="piedrablanca",
        conversations=(_NIA_INTRO, _NIA_ESPERA),
        idle_lines=(
            "Estoy contando las piedras de la fuente. Van cuarenta y tres.",
            "Pipa siempre sabía cuándo iba a llover.",
            "Si ves a un bandido, dile que me devuelva mi muñeca. Sin enfadarte.",
        ),
    ),
)

LORE = (
    LoreNote(
        id="tablon_refugio",
        zone_id="piedrablanca",
        sub_location="Refugio",
        title="Tablón del Refugio",
        text=(
            "Entre avisos de raciones y turnos de guardia hay un papel arrugado: «Se busca a Ena, viuda de "
            "Valeterna, que viajaba con una niña de unos ocho años. Quien la haya visto en el camino, que avise "
            "a Halbrand.» Alguien ha tachado la palabra «busca» y no ha escrito nada encima."
        ),
    ),
)
