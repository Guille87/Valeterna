# Documento de Diseño del Juego — Valeterna

<p align="center"><a href="../GDD.md">English</a> · <a href="GDD_es.md">Español</a></p>

Documento vivo del diseño para la evolución del juego: pasar de un bucle de
combate a un RPG de texto con mundo, historia, NPCs, clases, habilidades y un
bestiario grande. Historial de versiones: [CHANGELOG](CHANGELOG_es.md). Plan de
entrega: [ROADMAP](ROADMAP_es.md). Notas de balance: [TODO.md](../TODO.md).

**Estado: planificación.** Casi nada de esto está hecho — es el objetivo, va
cambiando, y nada es definitivo hasta que se implementa. **No hay objetivo de
1.0**: se publican versiones pre-lanzamiento hasta que el mantenedor decida que
está listo para salir.

---

## 1. Visión y pilares

Hoy el juego es: eliges un enemigo de una lista → peleas → repites. La idea es
mantener ese combate (funciona y está calibrado) y envolverlo en un **mundo por
el que merezca la pena moverse**: zonas con nombre en un mapa, ~10 enemigos por
zona, NPCs con diálogo ramificado, una questline de fantasía oscura, clases,
habilidades que se aprenden a lo largo de toda la progresión, siete elementos de
daño con debilidades / resistencias / inmunidades.

1. **El combate sigue siendo el protagonista.** El sistema ATB, los enemigos, el
   botín y la herrería son el núcleo. Todo lo nuevo profundiza el bucle de
   *hacerse fuerte → llegar más lejos*, no lo sustituye.
2. **Explorar es elegir, no relleno.** Cada pantalla ofrece una decisión real:
   avanzar, farmear, gastar, hablar, entregar una misión, volver a por algo.
3. **Fantasía oscura seria.** Valeterna es un reino que se muere. Sin alivio
   cómico.
4. **Sigue siendo un juego de consola.** Menús numerados con `input()`, color
   con `colorama`, sin ventana. El mundo se describe, no se dibuja.
5. **Aditivo, no una reescritura.** Cada fase se monta sobre la anterior sin
   romper partidas ni la suite de tests.
6. **Traducible desde el principio.** Todo el texto nuevo de cara al jugador
   pasa por una capa de strings (`i18n`) para que el multi-idioma futuro sea
   barato (ver §9.1).
7. **Todo conectado.** Las habilidades se desbloquean cerca de los enemigos
   contra los que ayudan; las piezas de conjunto sueltan donde vive su tema; los
   elementos importan porque las zonas se apoyan en tipos de daño concretos.
   Nada se añade "por añadir".

---

## 2. Historia — "La Brecha"

**Premisa.** Hace años, el **Dragón de Ceniza** arrasó la capital, Valeterna. Su
fuego hizo algo más que quemar — agrietó el velo entre el mundo mortal y los
planos de abajo. Por esa **brecha** se cuelan cosas que no deberían caminar por
el mundo — los muertos que no descansan entre ellas, y cosas peores —, y la
corrupción se extiende hacia fuera desde la capital en ruinas como la
podredumbre de una herida. *(La historia nunca nombra de antemano a qué se
enfrentará el jugador; el lector solo sabe "lo que salga por la brecha".)*

El jugador es uno de los pocos supervivientes del arrasamiento que todavía puede
empuñar un arma. Desde **Piedrablanca**, la última aldea libre, parte para
**encontrar el origen de la brecha y cerrarla** — siguiendo la corrupción hacia
atrás por siete regiones cada vez más arruinadas. *Qué espera en el origen, y si
cerrarla es siquiera posible, no se explica de entrada.* (El Dragón es la
catástrofe histórica del reino; **no** se plantea como "el jefe al que vas a
matar". Ver §4 sobre cómo se maneja la confrontación final.)

### Misión principal — 7 actos, uno por región

Los actos hilan las regiones con un motivo para seguir. **7 actos es la forma
actual**; podría crecer después de la 1.0 con mucho más contenido y pruebas,
pero eso es una posibilidad remota, no un plan.

| Acto | Región | Momento |
|------|--------|---------|
| I | Los Yermos | Halbrand: rompe las incursiones de bandidos que asfixian la aldea. |
| II | Bosque de los Susurros | Cael explica la brecha; un altar en lo profundo del bosque la alimenta, y algo está atado allí. |
| III | Ciénaga de los Ahogados | Algo más antiguo que la brecha se agita en el pantano anegado, donde la corrupción se encharca. |
| IV | Cañón del Trueno | Mirelle: la corrupción baja por el viejo camino de montaña, y el paso está sellado. |
| V | Torre de los Arcanos / Necrópolis | Sella: la torre del mago canaliza la brecha, y los muertos se levantan por toda la Necrópolis. |
| VI | Ciudadela en Ruinas | Aldric: la catedral fue el último bastión del reino; lo que la ocupa ahora vino por la brecha, y es peor que lo que arrasó la ciudad. |
| VII | El Corazón de la Brecha | El verdadero origen de la corrupción está más hondo que la catedral — y no es lo que los supervivientes esperaban. |

### Misiones secundarias

Opcionales, nunca bloquean el camino, dan recompensas que importan (objetos
únicos, recetas, oro, lore). **Objetivo: varias por región**, para que el bucle
sea más que "matar y avanzar" — el jugador tiene recados, objetivos y motivos
para retroceder. Conjunto inicial:

- **La muñeca de Nia** (Los Yermos) — una muñeca perdida en el campamento de bandidos.
- **El encargo de Dorn** (Bosque) — piel de Troll para una coraza legendaria única.
- **El tomo prohibido de Sella** (Necrópolis) — desbloquea una receta de daño mágico.
- Más por diseñar por región.

### Coleccionables de lore

Notas (cartas, páginas de diario, inscripciones) que se encuentran explorando.
Se leen una vez y quedan en un **Diario** que se relee desde el menú de
personaje. Trasfondo opcional; da vida al mundo sin bloquear nada.

---

## 3. Mundo — zonas y mapa

Un grafo de **zonas** con vuelta atrás libre. Una zona se desbloquea al
derrotar a su **guardián** (mini-jefe) o completar el momento de historia que la
abre.

```
Piedrablanca (hub, sin enemigos)
   │
Los Yermos ── Bosque de los Susurros ── Ciénaga de los Ahogados ── Cañón del Trueno ──
   Torre de los Arcanos / Necrópolis ── Ciudadela en Ruinas ── El Corazón de la Brecha
```

**Viajar** vs **viaje rápido** *(implementado en v0.12.0-b)*: llegas a una zona
*nueva* andando desde su vecina (`Viajar`), solo cuando la puerta está abierta
— esto es la "frontera" (`world.map.is_zone_reachable()`: el primer enemigo
backbone de la zona ya tiene que estar desbloqueado, o la zona no tiene roster
todavía y por tanto está siempre abierta). Una vez visitada, la zona entra en
la lista de **viaje rápido** (desde cualquier sitio, no solo el hub o un
cartel todavía — esa restricción es pulido futuro): instantáneo, gratis, para
retroceder a comprar / craftear / entregar misiones / farmear. Los dos son
gratis de momento; se podría añadir un encuentro de camino o un coste si el
backtracking se siente sin fricción. Todavía no hay "puertas" de verdad
(guardianes) — la alcanzabilidad se infiere de la misma cadena de
desbloqueo de enemigos que ya usa el combate, según
`world.map.default_zone_for_progress()` (migración de guardado) e
`is_zone_reachable()` (comprobación en vivo).

| Zona | Tema | Enemigos esqueleto (existentes) | Sub-lugares | NPCs clave |
|------|------|--------------------------------|-------------|------------|
| **Piedrablanca** | Última aldea libre | — | Taberna (descanso), Herrería, Mercado, Refugio | Yerma, Dorn, Halbrand, Nia |
| **Los Yermos** | Descampados junto a la aldea | Goblin, Huargo, Esqueleto, Bandido | Campamento de bandidos, Túmulo | Cael |
| **Bosque de los Susurros** | Bosque encantado | Orco, Espíritu Vengativo, Troll | Claro del altar, Cabaña quemada | Mirelle |
| **Ciénaga de los Ahogados** | Pantano anegado | *(todos nuevos)* | Templo hundido, Embarcadero podrido | *(nuevo)* |
| **Cañón del Trueno** | Paso de montaña, piedra | Gárgola, Gólem de Piedra | Mina derrumbada, Puente colgante | Kort |
| **Torre de los Arcanos / Necrópolis** | Torre de mago + cementerio | Mago, Nigromante | Biblioteca, Cripta | Sella |
| **Ciudadela en Ruinas** | La capital arrasada, suelo infernal | Ángel Caído, Demonio | Catedral rota, Plaza | Aldric |
| **El Corazón de la Brecha** | El origen — se diseña el último | *(§4)* | — | — |

Tienda / herrería / descanso *(implementado en v0.12.0-c)* / guardado viven en
sub-lugares de Piedrablanca (guardado se quedó en el menú Personaje en vez de
mudarse a Refugio — todavía no hay motivo para restringirlo por ubicación); un
"Mercado errante" y un "Fuego de campamento" (descanso de pago) aparecen en
zonas posteriores *(todavía no implementado)*.

---

## 4. Enemigos — diseño del roster

**Objetivo: ~10 enemigos por zona, ~70 en total.** Los 14 actuales son el
*esqueleto* (los mecánicamente únicos con nombre); el resto es diseño nuevo.

### 4.1 Estructura por zona

Los ~10 enemigos de cada zona:

| Tiers | Rango | Notas |
|-------|-------|-------|
| 1–4, 6, 8 | **estándar** | los encuentros aleatorios pesan hacia estos |
| 5, 7, 9 | **élite** | más duros y raros, una habilidad distintiva fuerte — por encima del estándar, por debajo del guardián |
| 10 | **guardián** | mini-jefe; derrotarlo una vez abre la siguiente zona. Sigue farmeable después |

Los **tres élites y el guardián sueltan cada uno una de las cuatro piezas de
conjunto de la zona** (§6.3) — así un élite siempre merece la pena cazarlo, y
completar la mitad de "modo historia" de un conjunto significa limpiar bien su
zona.

### 4.2 La confrontación final

El **guardián de El Corazón de la Brecha es el Dragón** — el antagonista
histórico del reino, de vuelta. Se **diseña el último**, cuando exista todo el
roster, para que quede estrictamente por encima de todo como la pelea más
difícil del juego; sus estadísticas no se pueden saber hasta entonces y son un
tema abierto a propósito. La historia (§2) no lo nombra como objetivo, para que
el final sea un descubrimiento y para dejar sitio a que el mapa crezca por
detrás más adelante.

### 4.3 Plantilla de enemigo

Cada enemigo se diseña contra esta plantilla (tabla viva en
`docs/design/bestiario.md` cuando empiecen las fases):

| Campo | Significado |
|-------|-------------|
| `nombre` | español, fantasía oscura, sin repetir |
| `zona` / `tier` | zona + rango de poder 1–10 dentro de ella |
| `rango` | estándar / élite / guardián |
| `arquetipo` | bruto / hostigador / lanzador / apoyo / tanque / emboscador |
| `habilidad` | una mecánica distintiva (§4.5) |
| `elemento` | elemento que infligen sus ataques (o físico) |
| `debilidades` | 0–2 elementos a ×1.5 (menor) o ×2.0 (mayor) |
| `resistencias` | presupuesto de 2: dos ×0.5 en elementos distintos, o un solo ×0.25 |
| `inmunidades` | elementos recibidos a ×0 (sin daño, sin estado), más cualquier inmunidad a un estado suelto |
| `stats` | del presupuesto de poder (§4.4) |
| `drops` | materiales + probabilidad de un único; los comunes se tiran del tier de la zona (§7.3) |

### 4.4 Presupuesto de poder

70 enemigos no se calibran a ojo. Cada enemigo tiene un **score de poder**; por
la matemática del ATB (`TODO.md`), la amenaza efectiva escala con
`vida × velocidad × daño_neto` (daño neto = daño medio − mitigación efectiva).
Se define un score normalizado y una curva objetivo `objetivo(zona N, tier T) =
base · f(N) · g(T)`; se diseña cada enemigo dentro de ±10 % de su objetivo, y se
verifica con playtest los guardianes y una muestra de cada tier, igual que hoy.
El nivel esperado del jugador en cada zona sale también de esta pasada (a
propósito **no** está fijado todavía — ver §6.2). Fórmula y constantes en
`TODO.md`.

### 4.5 Habilidades distintivas (menú de mecánicas del que tirar)

Patrones existentes: emboscada previa, golpe extra periódico, autocuración bajo
umbral, ataque inevitable, debuff aplicado tras tirada de acierto, invocar un
aliado. Nuevas: ataque a distancia (ignora parte de la evasión), robo de oro,
aturdir (pierde un turno), desgaste de armadura acumulable, drenaje de vida,
frenesí bajo umbral, `consagrar` (marca al jugador para daño extra), maldición
que bloquea la curación.

### 4.6 Zona de ejemplo — Los Yermos (10)

Demuestra la plantilla; las otras seis zonas son trabajo de diseño posterior.

| Tier | Rango | Nombre | Arquetipo | Distintivo | Inflige | Débil a | Resiste | Inmune a |
|------|-------|--------|-----------|------------|---------|---------|---------|----------|
| 1 | estándar | Rata Gigante | hostigador | mordisco rápido, prob. veneno leve | veneno | fuego | — | — |
| 2 | estándar | Goblin | bruto | emboscada tras la 1ª derrota | físico | — | — | — |
| 3 | estándar | Goblin Montaraz | a distancia | flechas (ignoran parte de la evasión) | físico | fuego | — | — |
| 4 | estándar | Huargo | hostigador | mordisco de manada (golpe extra) | físico | — | — | — |
| 5 | **élite** | Chamán Goblin | apoyo | cura a un aliado / se cura, maldición leve | oscuridad | sagrado | oscuridad | — |
| 6 | estándar | Esqueleto | tanque | revive una vez | físico | sagrado | veneno | veneno, sangrado |
| 7 | **élite** | Bandido | emboscador | desarme | físico | veneno | — | — |
| 8 | estándar | Salteador | hostigador | golpe rápido doble, roba oro | físico | — | — | — |
| 9 | **élite** | Ogro del Yermo | bruto | golpe demoledor que aturde | físico | fuego | — | paralizado |
| 10 | **guardián** | El Carnicero | bruto/tanque | frenesí bajo 40 % vida, aplica sangrado | físico | sagrado | veneno | — |

---

## 5. Elementos y afinidades

**Siete elementos** + físico (el default, sin elemento). Cada elemento hace dos
cosas: **modifica el daño** según la afinidad del objetivo, *y* puede aplicar un
**estado** distintivo al golpear.

| Elemento | Tipo de daño | Estado al golpear |
|----------|--------------|-------------------|
| **fuego** | físico | `quemado` — daño/turno + baja la salida del ataque **físico** (la magia no se ve afectada) |
| **veneno** | físico | `veneno` — daño/turno vs vida máx |
| **rayo** | físico | `paralizado` — prob. de saltar turno |
| **hielo** | físico | `congelado` — prob. de saltar turno |
| **sagrado** | mágico | `consagrado` — recibe +25 % de daño de todo, no puede autocurarse |
| **oscuridad** | mágico | `marchito` — curación / regen recibida −50 % |
| **arcano** | mágico | `fractura mágica` — la `magic_resist` del objetivo baja a 0 durante la duración (para que los golpes mágicos siguientes peguen fuerte) |

El estado de `arcano` sustituye a la idea de "silencio": **`silenciado` se
descarta** — un bloqueo total de hechizos era inútil contra los no-lanzadores y
destrozaba al Mago. `fractura mágica` siempre sirve algo cuando haces daño
mágico, nunca es un apagón total, y temáticamente "agrieta la magia que lo
escuda".

### Modelo de afinidades (capa de datos)

- **Debilidad** — base **×1.5**. Pasa a **×2.0** solo cuando el daño combina
  *dos* elementos a los que el enemigo es débil (una reacción elemental, una
  habilidad de doble elemento, o golpear a un objetivo que ya lleva un estado de
  un elemento de debilidad con un segundo elemento de debilidad).
  `Enemy.weaknesses: set[str]`, 0–2 elementos.
- **Resistencia** — base **×0.5**; **×0.25** cuando el daño combina *dos*
  elementos que el enemigo resiste. La resistencia también **reduce a la mitad
  la probabilidad y la duración del estado** de ese elemento (resiste el
  elemento entero, no solo los números). `Enemy.resistances: set[str]`, 0–2
  elementos.
- **Inmunidad** — el extremo de la resistencia: ese elemento hace **×0 daño** y
  su estado **nunca** se aplica. Reservado para "literalmente no le afecta" (un
  constructo y el `veneno`, un espectro y el `físico`). `Enemy.immune_elements:
  set[str]`.
- **Inmunidad a un estado suelto** — recibe el daño del elemento con
  normalidad, pero no puede recibir un estado concreto (algo demasiado enorme
  para `paralizar` que aun así recibe daño de `rayo`). `Enemy.immune_statuses:
  set[str]`.
- Así: **resistente** = lo aguanta (menos daño, estado más débil); **inmune** =
  no pasa absolutamente nada. Las cuatro palancas cubren todos los casos; la
  mayoría de enemigos usa una o dos.
- Daño: `final = base × afinidad`, y luego la mitigación por armadura /
  res. mágica (los elementos mágicos se mitigan con `magic_resist`).
- **Implementado en v0.11.0-b.** Defensa elemental del jugador: `Armor` puede
  llevar `resist` (un dict pequeño, un % de reducción por elemento), sumado
  como `Player.get_total_resist(elem)`, con un tope del 75% total, y aplicado
  en `Player.take_damage()` antes de la mitigación por armadura/res. mágica.
  Por ahora lo dan tres piezas craftables (Cinturón de Resistencia → arcano,
  Amuleto de Resistencia → oscuridad, Anillo de Vitalidad → sagrado); repartirlo
  más (más objetos, un conjunto temático) queda para una pasada de balance
  posterior. De paso se arregló un hueco relacionado: si un ataque es físico o
  mágico depende del *elemento* (según esta sección), no de la clase de quien
  ataca — `combat/battle.py::_execute_turn` solo miraba si el Arcanista era
  mágico por naturaleza o si una habilidad lo marcaba como `magical`, así que
  alguien sin ser Arcanista empuñando un arma sagrado/oscuridad/arcano seguía
  mitigándose con armadura en vez de resistencia mágica. Ahora
  `is_magical_element(elemento)` también lo activa.

### Reacciones elementales *(implementado en v0.11.0-c)*

- El `fuego` ya derrite `congelado` (se mantiene, sin daño extra — una
  interacción aparte, más pequeña que la fusión de abajo).
- `rayo` sobre un objetivo `congelado`: **fusión** — quita la congelación al
  instante y hace ×1.5 de daño extra en vez de intentar la parálisis habitual.
  Simétrico en `Player` y `Enemy`; hoy los 4 elementos físicos tienen arma
  craftable/soltada (Garra de Tormenta = rayo, Cetro de Escarcha = hielo, más
  fuego/veneno), así que ambos lados de la reacción son alcanzables jugando
  normal, no solo desde hechizos enemigos.
- `quemado` + `veneno` sobre el mismo objetivo (en cualquier orden):
  **combustión** — se funden en un único estado `combustion` en vez de
  coexistir, con más daño por turno que cualquiera de los dos por separado
  (sigue reduciendo el ataque físico a la mitad como la quemadura, sigue
  siendo curable con el Antídoto), con duración = el máximo de los dos
  efectos fusionados.

Nota de balance: como la fusión consume la propia tirada de parálisis del
golpe de rayo y la combustión sustituye dos DoT separados por uno solo (no
suma sus daños sin más), las reacciones cambian el apilamiento bruto por un
único efecto más fuerte en vez de acumular — deliberadamente moderado para que
se lean como un buen extra, no la única estrategia viable en las futuras
peleas de élite/guardián.

---

## 6. Sistemas de combate

### 6.1 Clases

Se elige una vez al crear el personaje; se guarda (la clase equilibrada como
`clase="vagabundo"` en disco, por compatibilidad); las partidas viejas usan esa.

| Clase | Identidad | Efecto |
|-------|-----------|--------|
| **Aventurero** | equilibrado (el personaje de hoy) | estadísticas base y curvas actuales; el default seguro; un pool de habilidades flexible |
| **Guerrero** | tanque / bruto | +Vida, +armadura, +daño físico; crecimiento más tanque; sin magia |
| **Pícaro** | rápido / crítico / veneno | +velocidad, +evasión, +prob. crítico; crecimiento ágil; frágil |
| **Arcanista** | mágico / elemental | menos vida/armadura; **su ataque estándar es mágico** (`is_magical`), escala con un stat nuevo de *poder mágico* — por fin hace que importe la `magic_resist` de los enemigos |

Las clases tocan la creación del personaje, `Stats`, las constantes
`_*_GROWTH_RATE`, la rama del Arcanista en `_execute_turn`, y de qué pool de
habilidades tira el jugador (§6.2).

**Pendientes de diseño (para más adelante, no v0.10):**

- **Familias de arma por clase.** Cada clase solo equiparía armas de su familia
  —pero una *familia*, no un solo tipo—: Guerrero → contundentes/espadas/hachas/
  mazas + escudo; Pícaro → dagas *y* otras armas ligeras/de precisión; Arcanista
  → bastones *y* otras armas de lanzador (varitas, orbes…); Aventurero →
  cualquiera (o un subconjunto amplio). Requiere una categoría de arma en
  `Weapon` y un filtro al equipar. *(Hecho: la clase equilibrada pasó de
  "Vagabundo" a "Aventurero" — solo el nombre visible, el valor guardado no
  cambia.)*

### 6.2 Habilidades

Sin barra de maná. Cada clase tiene un **pool de ~8 habilidades** que se
desbloquean a lo largo de *toda* la progresión, elegidas para ayudar contra lo
que su región te echa encima. Se desbloquean de dos formas: unas **por nivel**
(las tempranas), otras **al derrotar al guardián de una región** (las tardías —
así el poder sigue el avance de la historia, no solo el farmeo). **Los niveles /
guardianes exactos se fijan en la fase de presupuesto de poder (v0.14)**; hasta
entonces una habilidad va atada a su hito. Hitos: **M1** Los Yermos · **M2**
Bosque · **M3** Ciénaga · **M4** Cañón · **M5** Torre/Necrópolis · **M6**
Ciudadela · **M7** El Corazón.

Dos tipos:

- **Pasiva** — siempre activa una vez aprendida, sin UI, sin coste de hueco.
- **Activa** — una acción en vez de atacar, con **enfriamiento en turnos**. El
  jugador puede **equipar hasta 4 activas a la vez** (se eligen en el menú de
  personaje) — la decisión estratégica es qué cuatro llevar contra un enemigo
  dado. El estado del enfriamiento vive solo en el combate, no en el guardado.

El combate gana una opción **"Habilidades"** (lista las 4 activas equipadas y su
estado listo/enfriamiento). En auto/turbo: usa una activa equipada lista si la
hay, si no ataca.

Esbozo (tipos: `fís` físico, `mág` mágico, `ele` elemental, `util` utilidad;
`aN` = activa, enfriamiento N turnos; `p` = pasiva; sujeto a balanceo):

| M | Aventurero | Guerrero | Pícaro | Arcanista |
|---|-----------|----------|--------|-----------|
| 1 | Golpe Firme — a3 fís: +40 % daño, no falla · Segundo Aliento — p: cura 12 % vida máx. al matar | Embate — a3 fís: golpe fuerte, 40 % aturdir · Piel de Piedra — p: −12 % daño físico recibido | Golpe Bajo — a3 fís: crítico garantizado + sangrado · Reflejos — p: +12 % evasión | Proyectil Arcano — a2 arc: perfora res. mágica · Sintonía — p: eliges el elemento de tu ataque al empezar el combate |
| 2 | Aguante — p: bajo 30 % vida, +15 % armadura y res. mágica | Represalia — p: 30 % de contraatacar al recibir un golpe físico | Veneno de Contacto — p: 20 % de aplicar veneno al golpear | Escudo de Maná — a4 util: absorbe por completo el próximo golpe |
| 3 | Adaptación — p: +10 % resistencia a todos los elementos | Provocación — a4 util: el enemigo pierde precisión 3 turnos | Filo Envenenado — a3 ven: golpe + veneno garantizado más potente | Descarga Elemental — a4 ele: daño del elemento activo + su estado |
| 4 | Adrenalina — a5 util: +25 % velocidad 3 turnos | Grito de Guerra — a5 util: +25 % daño 3 turnos | Sombra — a4 util: esquivas el próximo ataque enemigo | Ruptura Arcana — a5 arc: daño + `fractura mágica` (res. mágica del enemigo → 0) 2 turnos |
| 5 | Ruptura — a4 fís: ignora la mitad de la armadura del enemigo | Fortaleza — p: +35 % vida máxima | Golpe Mortal — p: +50 % daño crítico | Doble Conjuro — p: 20 % de que una activa no consuma enfriamiento |
| 6 | Botín Afortunado — p: +25 % oro, +10 % prob. de drop | Golpe Sísmico — a5 fís: daño alto, ignora la evasión | Marca de Muerte — a5 util: el enemigo recibe +30 % de todo el daño 3 turnos | Mente Aguda — p: −1 turno a todos los enfriamientos |
| 7 | Voluntad de Hierro — p: sobrevives a un golpe letal con 1 de vida (1 vez/combate) | Último Bastión — a7 util: 2 turnos inmune a daño físico | Asalto — a7 fís: 3 golpes rápidos | Cataclismo — a8 arc: daño mágico masivo, ignora toda mitigación |

#### 6.2.1 Decisiones fijadas para v0.10.0

Revisadas y cerradas con el mantenedor; los números son provisionales y se
revisarán en la fase de presupuesto de poder de v0.14 (anotado en `TODO.md`).

1. **Deltas de stats / crecimiento por clase (provisionales).** Se aplican sobre
   la base actual del Aventurero al crear; los ajustes de crecimiento van sobre
   los `_*_GROWTH_RATE` actuales:
   - **Aventurero** — sin cambios (el personaje de hoy exactamente).
   - **Guerrero** — +15 % vida máx., +2 armadura base, +1 ataque mín./máx.;
     crecimiento de armadura ×1.3; sin ninguna interacción con magia.
   - **Pícaro** — +3 velocidad, +5 % evasión, +5 % prob. crítico, −10 % vida
     máx.; crecimiento de velocidad ×1.3.
   - **Arcanista** — −15 % vida máx., −2 armadura base; gana el stat
     `poder_mágico` (ver abajo) que crece cada nivel.
2. **`poder_mágico` y el ataque del Arcanista.** Campo nuevo de `Stats`, `0` para
   el resto de clases. El ataque estándar del Arcanista en `_execute_turn` usa
   `poder_mágico` como fuente de daño **en vez del** rango de ataque del arma, y
   se marca `is_magical=True`. Las armas le siguen aportando sus stats
   secundarios y su `element`, pero no daño base.
3. **Elemento del ataque básico del Arcanista.** Por defecto `arcano` (encaja con
   Proyectil Arcano y alimenta `fractura mágica`). La pasiva **Sintonía** (M1)
   deja al jugador cambiar el elemento al empezar el combate.
4. **Niveles de desbloqueo provisionales.** Las habilidades M1 se conceden al
   **crear el personaje (nivel 1)**; las M2 al **nivel 4**. Los valores exactos
   pasan a v0.14; hasta entonces cada habilidad va atada a su hito.
5. **Esquema de guardado.** v0.10.0 añade solo dos claves, no el bloque `mundo`
   completo: `clase` (back-fill a `"vagabundo"`) y `habilidades_equipadas`
   (back-fill a `[]`). El bloque `mundo` entero (§9.4) sigue en v0.12.0.
6. **Modelo de datos de `Skill`.** Una dataclass — `id`, `nombre`, `clase`,
   `tipo` (`pasiva` / `activa`), `hito`, `enfriamiento` — más un hook de efecto
   por habilidad. Las pasivas se consultan con `player.has_passive(id)` en los
   sitios relevantes (`take_damage`, `_execute_turn`, `_handle_victory`,
   procesado de estados); las activas se resuelven con un dispatch en el bucle de
   combate. Vive en `characters/skills.py` (§9.3).

### 6.3 Bonus de conjunto de armadura *(diseño en revisión por el mantenedor — aplazado a v0.12.0+)*

Confirmado con el mantenedor al planificar v0.11.0: este diseño depende de
zonas, enemigos élite y guardianes (tiers 5/7/9/10 de cada zona) y de la Arena
(§6.5), y nada de eso existe todavía — el juego actual sigue siendo la cadena
plana de 14 enemigos. En vez de diseñar una versión provisional de "4
conjuntos sobre la cadena actual" para tener que rehacerla cuando lleguen las
zonas, los bonus de conjunto se quedan sin implementar hasta v0.12.0+, cuando
se puedan construir ya sobre la estructura real de zonas/élites/guardianes.
v0.11.0 cubre en su lugar el resto de "Equipo y afinidades reales":
debilidades/resistencias/inmunidades reales por enemigo (hecho, ver
`TODO.md`), resistencia elemental en armadura, armas elementales nuevas y
reacciones elementales.

`Armor` gana un `set_name` opcional. `Player` cuenta las piezas equipadas por
conjunto y aplica bonus a **2, 4 y 6 piezas** — **los tramos se acumulan** (con
6 piezas tienes a la vez los bonus de 2, 4 y 6). Objetivo de diseño, inspirado
en los conjuntos de Diablo 3 pero adaptado al texto por turnos: **un conjunto
por zona (7 conjuntos)**, cada uno de 6 piezas repartidas en 6 de los 11 huecos
(cuáles 6 varía por conjunto), dejando 5 huecos para combinar libremente. Las
piezas **1–4 sueltan en la zona** — una de cada uno de los tres élites (tiers
5, 7, 9) y del guardián (tier 10); las piezas **5–6 se consiguen en la Arena**
(§6.5). El modo historia te da el bonus de 4, la Arena completa el conjunto.

- **2 piezas** — un stat modesto y siempre útil.
- **4 piezas** — un efecto situacional fuerte.
- **6 piezas** — un efecto que define la build: el motivo para comprometerse.

Borrador (nombres y efectos aún en movimiento):

| Conjunto | Zona | 2 | 4 | 6 |
|----------|------|---|---|---|
| Atavío del Proscrito | Los Yermos | +evasión | el primer golpe de cada combate es crítico garantizado | tras un crítico, tu siguiente ataque también es crítico |
| Manto del Bosque | Bosque | +regeneración | 25 % de envenenar al golpear | los enemigos envenenados reciben +25 % de daño de todo |
| Cieno Viviente | Ciénaga | +res. oscuridad | tu `marchito` también baja el daño del enemigo 15 % | cuando un enemigo muere con `marchito`, curas 20 % vida máx. |
| Placas del Guardián | Cañón del Trueno | +armadura | −10 % daño físico recibido | la primera vez que bajarías del 25 % vida cada combate, bloqueas todo el daño 1 turno |
| Sudario del Nigromante | Torre/Necrópolis | +res. mágica | 20 % de reflejar daño mágico | tras recibir daño mágico, tu siguiente ataque hace daño arcano extra |
| Égida del Caído | Ciudadela | +res. sagrado | curas el 15 % del daño que infliges | por encima del 80 % de vida, +30 % de daño |
| Escamas de Ceniza | El Corazón | +res. fuego y +vida máx. | inmune a `quemado`, +25 % de daño de fuego | al empezar el combate, escudo del 20 % de tu vida máx. |

Ninguna pieza de conjunto es estrictamente mejor que las otras opciones de su
hueco. La lista completa, qué 6 huecos usa cada conjunto y los números siguen
por decidir.

### 6.4 Armas que infligen estados

`Weapon` gana `inflicts` = `{estado, probabilidad, duración, poder}`. En un
golpe del jugador, se tira `probabilidad` y `enemy.apply_status(...)` (respetando
las inmunidades). Exige que **`Enemy` procese estados en su turno** — un espejo
de `Player.on_turn_start` / `on_turn_end`. Mapa de infección de las armas
elementales: veneno→`veneno`, fuego→`quemado`, hielo→`congelado`,
rayo→`paralizado`, oscuridad→`marchito`, sagrado→`consagrado`,
arcano→`fractura mágica`.

### 6.5 Modo Arena

Un lugar de Piedrablanca que se desbloquea tras el Acto III. Eliges un nivel de
dificultad → **N oleadas crecientes**, enemigos de las zonas superadas. La
curación entre oleadas se paga con oro. Está diseñado como **dificultad
elevada**, pero es la **única vía a la 5ª y 6ª pieza de cualquier conjunto**
(§6.3) — el modo historia te deja en el bonus de 4 piezas, la Arena lo completa.
Las recompensas escalan con la oleada: oro, **títulos** cosméticos en la
pantalla de estadísticas, las piezas 5–6 de conjunto, y al menos un único
difícil de obtener. El guardado registra `arena_mejor_oleada`. Combina con la
auto-batalla turbo. Tabla de recompensa-por-oleada por decidir.

---

## 7. Progresión y economía

### 7.1 Subida de nivel

Curva por decidir en la fase de presupuesto de poder (§4.4). Los niveles también
desbloquean habilidades (§6.2). `poder mágico` es un campo nuevo de `Stats`, 0
para no-Arcanistas, creciente para el Arcanista.

### 7.2 Bestiario — revelado progresivo

Según `enemy_kill_counts`, cada umbral añade cosas a la ficha:

- **1** → nombre, vida, rango de ataque, oro, **una frase de lore / descripción
  breve** y —cuando los enemigos tengan ataques elementales (v0.11+)— **el
  elemento de sus ataques**.
- **3** → armadura, res. mágica, velocidad, crítico, más **la habilidad
  distintiva del enemigo** (su truco de `perform_turn`: mordisco en manada,
  desarme, autocuración, terremoto…).
- **5** → debilidades, resistencias e inmunidades elementales, **los estados que
  te puede infligir** y **sus inmunidades a estados sueltos** (con qué no se le
  puede congelar/envenenar/…).
- **10** → tabla de drops completa (primera vez que se muestra).

Con 0 kills: no aparece (como hoy). La implementación llega en v0.14.0.

### 7.3 Escalado del botín y drop-scaling

- **Únicos** — hechos a mano, baja tasa de drop, enemigos concretos (como hoy).
  Las piezas de conjunto y la herrería siguen a mano.
- **Comunes** — `items/loot.py` tira una pieza para un hueco de los **rangos del
  tier de la zona**: magnitud del stat base + 0–3 secundarias (mismas reglas que
  verifica `tests/test_armor_progression.py`).
- **Drop-scaling entre zonas** — cuando un material que suelta un enemigo
  temprano al `p %` lo suelta *también* un enemigo de una zona posterior, el
  posterior lo suelta con **más probabilidad y/o cantidad**. Volver a farmear la
  fuente temprana sigue siendo válido pero más lento, nunca óptimo. (Curva
  exacta por decidir.)

### 7.4 Descanso y muerte

- **Descanso** *(implementado en v0.12.0-c)* — solo en un pueblo, en una
  posada, pagando oro: vida completa + todos los estados alterados limpiados
  (`ui/exploration.py::_rest_flow`, se llega desde la Taberna de Piedrablanca).
  **El coste escala con el nivel**: `_REST_COST_PER_LEVEL × player.level`, con
  `_REST_COST_PER_LEVEL = 10` — explícitamente un número provisional, todavía
  sin ajustar contra los ingresos reales de oro (la pregunta abierta "curva de
  coste del descanso" pasa de abierta a "provisional, revisar en pasadas de
  balance" en vez de quedar del todo resuelta). Un jugador sin oro siempre
  puede farmear unos combates fáciles; descansar es un no-op (con mensaje, no
  con confirmación) si ya está a vida completa y sin estados.
- **Muerte** *(todavía no implementado — hoy solo cura del todo, sin
  reaparecer en un pueblo)* — pierdes una fracción de tu oro (hoy 1/3) y se va
  **para siempre** (sin "saco" recuperable). Reapareces en la última ciudad
  visitada con la vida al máximo y los estados limpiados, perdiendo tu
  posición en la zona actual. Hoy `_handle_defeat()` en `combat/battle.py` ya
  hace la penalización de oro + curación completa; mover `zona_actual` de
  vuelta al último pueblo visitado al morir se dejó fuera de v0.12.0-c a
  propósito (cambia la gestión de la derrota del propio combate, no solo
  código de mundo/exploración) para una pasada posterior.

---

## 8. Sistemas de mundo

### 8.1 Bucle de exploración *(implementado en v0.12.0-b/c)*

Sustituye al antiguo menú plano de `game_loop` por
`ui/exploration.py::zone_loop()`. Dentro de una zona: **Explorar** (tirada
ponderada — combate / un hallazgo / nada; el propio hallazgo es ahora otra
mini-tirada, oro o una poción de salud gratis; el "mini-evento raro" del GDD
sigue siendo solo texto de ambiente vía **Ir a `<sub-lugar>`**, no una tirada
aparte todavía), **Ir a `<sub-lugar>`** (lista los sub-lugares de la zona;
tres de los de Piedrablanca están conectados a servicios de verdad — Mercado
→ Tienda, Herrería → Herrería, Taberna → descanso — el resto, incluido el
Refugio de Piedrablanca, sigue siendo un stub de ambiente; NPC/entrega de
misión por sub-lugar más allá de estos tres espera a v0.13.0), **Viajar**
(frontera a la siguiente zona inmediata en cuanto es alcanzable, o viaje
rápido a cualquier zona ya visitada), **Personaje** (el menú de personaje
siempre disponible: inventario, estadísticas, equipar, habilidades,
bestiario, guardar — extraído del antiguo `game_loop`; diario/misiones se
sumarán cuando existan esos sistemas). Tienda/Herrería salieron de Personaje
y se mudaron a los sub-lugares de Piedrablanca en v0.12.0-c, según el plan de
esta sección.

### 8.2 Diálogo — ramificado, con respuestas del jugador *(motor implementado en v0.13.0-a; contenido en -b)*

El motor (`world/npc.py`) soporta todo lo de abajo salvo efectos de misión (aún no hay sistema de misiones): hoy los efectos disponibles son activar una bandera, dar oro y dar un objeto. Las condiciones dependen de banderas de historia y del nivel del jugador. La regla de "≥3 respuestas" la vigila un test sobre el contenido real. De momento solo Yerma tiene conversaciones.

Un NPC tiene un conjunto de **conversaciones**. Cada conversación tiene: un id,
una condición de disparo (estado de misión / bandera de historia / primer
encuentro), una bandera **`repetible`**, y un **árbol de nodos**.

- Un **nodo** = texto del NPC + una lista opcional de **respuestas del jugador**.
- Una **respuesta** = la frase del jugador + una condición opcional + un enlace
  al siguiente nodo (o un fin) + un **efecto** opcional (poner una bandera, dar
  un objeto, iniciar/avanzar una misión, abrir un servicio).
- Una conversación **no repetible**, una vez recorrida, queda registrada en
  `mundo.dialogos_vistos` y no vuelve a dispararse; el NPC pasa a una frase de
  relleno repetible y corta.

En la primera pasada, las respuestas solo cambian el **texto** que recibes —
sin efecto mecánico — pero el sistema lleva los efectos para más adelante
(easter eggs, sorpresas, contenido detrás de elecciones). Algunas conversaciones
son de una vez (no se pueden repetir), lo que hace que esas elecciones se
sientan permanentes aunque sean cosméticas. **Los nodos de elección ofrecen al
menos 3 respuestas.** Escribir las conversaciones de los NPC queda a cargo de
quien lo implemente (el mantenedor ha dicho que no es su fuerte); el objetivo de
diseño es una mezcla de conversaciones únicas de misión/historia y frases de
relleno/lore repetibles por NPC.

### 8.3 Misiones

`Quest`: id, título, descripción, **objetivo** (matar N de X, llegar a la zona
Y, hablar con Z, conseguir W, o una bandera manual), **recompensa** (oro /
objeto / receta / bandera), **estado** (`no_iniciada` / `activa` / `completada`
/ `entregada`). El progreso se comprueba desde hooks que ya saltan
(`_handle_victory`, llegar a una zona, `Inventory.add_item`). Una entrada
**Misiones** en el menú de personaje las lista.

---

## 9. Técnica

### 9.1 Capa de strings (i18n) — se monta primero

Todo el texto de cara al jugador pasa por `t(clave, **kwargs)`: un paquete
`i18n/` con `catalog_es.py` (luego `catalog_en.py`) — diccionarios planos con
clave por id de string — y un resolver que lee el idioma activo de `config.ini`
`[IDIOMA]` (por defecto `es`). Los helpers de `ui/console.py` no cambian
(reciben strings ya resueltos). **El contenido nuevo se escribe con `t()` desde
el principio;** el español hardcodeado se migra módulo a módulo, empezando por
combate y menús.

### 9.2 Paquete `world/`

Guiado por datos como `characters/enemies/` (un archivo por zona):
`world/zone.py` (`Zone`), `world/npc.py` (`NPC`, `Conversation`, `DialogueNode`,
`Choice`), `world/quest.py` (`Quest`), `world/map.py` (grafo, viaje, puertas),
`world/data/*.py` (un módulo por zona). **`Zone`, `world/data/*.py`, el
registro `ZONE_ORDER`/`ZONES`, y el viaje/puertas (`next_zone()`,
`is_zone_reachable()`) de `world/map.py` ya están implementados
(v0.12.0-a/b)** — `world/npc.py` existe desde v0.13.0-a (motor + Yerma);
`world/quest.py` todavía no.

### 9.3 Otros módulos nuevos

- `characters/skills.py` — definiciones de habilidades; `Player` deriva su pool
  de la clase, y las `conocidas` del nivel; `habilidades_equipadas` (los ≤4 ids
  de activas) se guarda.
- `items/loot.py` — las tablas de tirada de drops comunes por tier de zona.
- `ui/exploration.py` — el bucle de zona (`omit`ido de la cobertura como
  `ui/menus.py`).

### 9.4 Esquema de guardado v2 *(implementado en v0.12.0-a)*

Añade un bloque `mundo`: `zona_actual`, `zonas_visitadas`, `misiones`,
`banderas`, `dialogos_vistos`, `diario`, `arena_mejor_oleada`. Migración v1 →
v2 (`persistence/save_load.py`, mismo patrón que los back-fills anteriores):
sin bloque `mundo` → `zona_actual` se infiere del progreso de
`defeated_enemies` (`world.map.default_zone_for_progress()`),
`zonas_visitadas` se rellena con todas las zonas hasta ahí, todo lo demás
vacío. `unlocked_enemies` / `defeated_enemies` siguen siendo la fuente de
verdad para las puertas. (`clase` y `habilidades_equipadas` ya existían como
claves de nivel superior en el guardado desde v0.10.0, antes de escribirse
esta sección del GDD — no se movieron dentro de `mundo` para no forzar una
migración innecesaria de algo que ya funcionaba.)

### 9.5 Tests

Toda la lógica no interactiva va con tests unitarios: matemática de afinidades
(débil / resiste / inmune / defensa elemental del jugador), inmunidad a estados,
efectos y enfriamientos de habilidades y el límite de 4 huecos, diferencias de
stats/crecimiento por clase, conteo de bonus de conjunto, rangos de tirada de
loot, drop-scaling, progreso de misiones, recorrido y condiciones del árbol de
diálogo y consumo de las de una sola vez, viaje y puertas del mapa, resolución y
fallback de i18n, migración de guardado. El bucle de exploración y los menús
siguen `omit`idos de la métrica de cobertura.

---

## 10. Fases de desarrollo (pre-lanzamiento, abiertas)

Cada fase es una release; **las releases se etiquetan solo con la luz verde del
mantenedor** — las funcionalidades se acumulan en `main` por PRs. El orden puede
cambiar; el GDD es un documento vivo y cualquier cosa de aquí puede cambiar.

| Fase | Tema | Contenido |
|------|------|-----------|
| **v0.9.0** | Fundaciones | capa de strings i18n + migrar el núcleo de combate/menús · modelo de afinidades completo (×1.5/×2 débil, ×0.5/×0.25 resiste, ×0 inmune = sin daño, sin estado) + los 3 elementos nuevos como datos · el jugador y `Enemy` procesan estados (armas que infligen estados) · `quemado` solo penaliza el ataque físico |
| **v0.10.0** | Clases y primeras habilidades | 4 clases al crear · stat `poder mágico` · sistema de habilidades (pasivas siempre / activas con enfriamiento) · menú "Habilidades" + elegir 4 activas equipadas · las primeras ~2-3 habilidades por clase |
| **v0.11.0** | Equipo y afinidades reales | 4 conjuntos de armadura · resistencia elemental en armadura · debilidades / resistencias / inmunidades reales en los 14 enemigos actuales · armas elementales nuevas (sagrado / oscuridad / arcano) · reacciones elementales |
| **v0.12.0** | El mundo, parte 1 | zonas + mapa + bucle de exploración · posada / descanso (coste por nivel) · viaje frontera + viaje rápido · migración de guardado v2 · tienda / herrería reubicadas · encuentros aleatorios + hallazgos |
| **v0.13.0** | Diálogo y NPCs | diálogo ramificado con respuestas del jugador · conversaciones únicas vs repetibles · NPCs de Piedrablanca + las 6 regiones actuales · notas de lore + Diario |
| **v0.14.0** | Bestiario y enemigos I | bestiario progresivo · herramienta de presupuesto de poder (fija la curva de nivel) · Los Yermos + Bosque rellenados a ~10 (élites 5/7/9 + guardián 10) · habilidades de clase de nivel medio atadas a esos enemigos |
| **v0.15.0** | Enemigos II | Ciénaga (nueva) + Cañón + Torre/Necrópolis a ~10 · escalado del botín (únicos + comunes tirados) · drop-scaling entre zonas · más habilidades de clase |
| **v0.16.0** | Enemigos III | Ciudadela a ~10 · habilidades de clase de hito alto · misiones secundarias de esas regiones |
| **v0.17.0** | Historia principal | sistema de misiones · questline "La Brecha" (7 actos) enganchada a los NPCs / guardianes existentes · progresión por historia en vez de elegir enemigo |
| **v0.18.0** | La Arena | modo de oleadas crecientes · recompensas de Arena (títulos + algunas piezas de conjunto + un único difícil) |
| **más adelante** | Endgame y pulido | roster completo → **ajuste final del Dragón** + El Corazón de la Brecha · rebalanceo completo de la cadena · firma Ed25519 del updater · GIF de gameplay · MVC más limpia · *(ampliación)* combate multi-enemigo · *(muy a largo plazo)* posibles actos nuevos |
| **1.0** | — | la declara el mantenedor cuando el juego esté listo para salir |

---

## 11. Preguntas abiertas

- **Bonus de conjunto** (§6.3) — 7 conjuntos (uno por zona), tramos 2/4/6,
  piezas 1–4 de los élites + guardián, 5–6 de la Arena: la dirección está
  fijada, los nombres / qué 6 huecos / los números no. Minar el catálogo de
  conjuntos de Diablo 3 en busca de ideas.
- **Desbloqueo de habilidades** — repartido entre "por nivel" (tempranas) y "al
  derrotar al guardián" (tardías); el reparto exacto sale de la fase de
  presupuesto de poder.
- **Inmunidades a estados sueltos** — se deciden por enemigo mientras se
  construye el roster.
- **Arena** — la tabla de oleada-a-recompensa, y qué único(s) exactamente da.
- **Curva de drop-scaling** — "un poco más de probabilidad, un poco más de
  cantidad", números del testeo.
- **Curva de coste del descanso** — `_REST_COST_PER_LEVEL × nivel` (v0.12.0-c)
  es un valor provisional; la fórmula real todavía necesita ajustarse contra
  el ingreso de oro.
