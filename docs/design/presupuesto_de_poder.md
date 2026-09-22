# El "poder" de un personaje o enemigo: cómo funciona y cómo lo hicimos aquí

Documento explicativo, no técnico de referencia rápida (para eso está el docstring
de `characters/power_budget.py`). Es para entender **de verdad** qué es ese
número que ves en juegos como Raid Shadow Legends o Hustle Castle, de dónde
sale, y exactamente cómo se calculó el de Valeterna paso a paso.

---

## 1. ¿Qué es el "Poder" que ves en otros juegos?

Cuando Raid Shadow Legends te dice que un campeón tiene "Poder: 83.609", ese
número **no es una estadística real del juego** — no existe un stat llamado
"poder" en las fórmulas de daño. Es un **resumen inventado por los diseñadores**
que coge todas las estadísticas de verdad (vida, ataque, defensa, velocidad,
probabilidad de crítico, resistencia, precisión...) y las mezcla en un solo
número con una fórmula propia, normalmente secreta, para que el jugador pueda
comparar dos campeones (o el mismo campeón con dos equipos distintos) de un
vistazo sin tener que leer quince estadísticas y hacer la cuenta mentalmente.

Es exactamente lo mismo que hace una ficha de coche cuando resume "aceleración,
frenada, agarre, potencia..." en una sola cifra de "prestaciones", o un producto
que resume especificaciones técnicas en una puntuación de una web de análisis.
**Comprime información real en un número fácil de comparar.**

### ¿De dónde sale el número exactamente?

Cada juego tiene su propia fórmula, no publicada casi nunca, pero todas siguen
el mismo patrón general:

```
poder = (algo de vida) × (algo de ataque) × (algo de defensa) × (algo de velocidad) × ...
```

normalmente con cada "algo" pesado de forma distinta (la vida no vale lo mismo
punto por punto que la velocidad, por ejemplo) y a veces con ajustes por
mecánicas especiales (crítico, resistencias elementales, habilidades). El
equipo (armas, armaduras, objetos) sube el poder porque sube las estadísticas
reales que entran en la fórmula — el "poder" en sí no se guarda en ningún
sitio, **se recalcula cada vez** a partir de las estadísticas actuales del
personaje. Por eso en Raid Shadow Legends el poder de un campeón cambia al
instante si le cambias el equipo: no es que el juego "sepa" tu poder, es que
lo recalcula sobre la marcha.

### ¿Y el "poder recomendado" para avanzar de etapa?

Es la otra mitad de la misma idea. Si el juego sabe calcular el poder de
*tu* personaje con esa fórmula, puede calcular con la misma fórmula el poder
de **los enemigos** de la siguiente etapa/mazmorra/piso. Si tu poder está muy
por debajo del de los enemigns que te esperan, el juego te avisa ("Poder
recomendado: 50.000") para que no entres a una paliza sin saberlo. Es la
misma cuenta, aplicada a los dos lados de la pelea, con una curva de
dificultad que dice "en la etapa N, el enemigo típico tiene tal poder".

Eso es exactamente lo que hemos montado en Valeterna, solo que aplicado al
lado del **diseño** (para que yo sepa, al escribir un enemigo nuevo, si está
sobre o infra-tuneado) en vez de mostrado en pantalla al jugador — aunque
nada impide, el día que se quiera, sacar ese mismo número en el Bestiario o en
la pantalla de un enemigo antes de un combate, tal como hace Raid Shadow
Legends. Técnicamente ya lo tenemos: solo faltaría imprimirlo.

---

## 2. Cómo lo hemos hecho en Valeterna, paso a paso

### 2.1 La fórmula: `power_score()`

```python
daño_medio = (min_atk + max_atk) / 2
factor_crítico = 1 + crit_chance × (crit_damage − 1)
daño_neto = daño_medio × factor_crítico
poder = vida_máxima × velocidad × daño_neto
```

Tres piezas:

- **`vida_máxima`** — cuánto aguanta el enemigo. Más vida, más turnos vivo, más
  amenaza acumulada.
- **`velocidad`** — con el sistema de turnos ATB de Valeterna (barra que se
  llena según la velocidad, el más rápido actúa más veces), la velocidad no
  es solo "quién va primero": un enemigo el doble de rápido literalmente
  **actúa el doble de veces**. Por eso multiplica, no solo suma.
- **`daño_neto`** — el daño medio de un golpe, ajustado por lo que aporta de
  media el crítico. Si un enemigo tiene 10% de probabilidad de crítico con
  x1.6 de daño, en media cada golpe suyo hace un 6% más de lo que parece
  (`1 + 0.10 × 0.6 = 1.06`), así que ese 6% extra se mete en el daño neto.

Multiplicar los tres (en vez de sumarlos) es deliberado: un enemigo con el
doble de vida **y** el doble de daño no es "el doble de amenaza", es **cuatro
veces** más peligroso (aguanta el doble de intercambios y cada intercambio
te cuesta el doble) — eso solo sale bien con una multiplicación, no con una
suma.

**Lo que decidimos NO meter, y por qué:** el GDD original pedía restar
"la mitigación efectiva" del daño (`daño_neto = daño_medio − mitigación`). Lo
descartamos a propósito: ¿mitigación de quién? No hay un jugador "de
referencia" fijo en Valeterna — un Guerrero de nivel 5 con armadura de hierro
y un Arcanista de nivel 3 con una túnica tienen mitigaciones completamente
distintas. Restar un número inventado habría sido **más** especulativo que no
restar nada. En vez de eso, medimos la amenaza *intrínseca* del enemigo (lo
que puede hacer, sin asumir a quién se lo hace) y dejamos que el playtest
real —combates de verdad contra un jugador de verdad— confirme si encaja.
Es la misma filosofía que ya seguíamos para calibrar los 14 enemigos actuales
antes de que existiera esta herramienta.

**Lo que la fórmula no ve (y por qué eso está bien):** solo mira
`min_atk`/`max_atk`, así que un enemigo cuya amenaza real viene de otro sitio
sale "más bajo" de lo que es en la práctica. Dos ejemplos reales del roster
actual:
- El **Esqueleto** revive una vez a mitad de vida — en la práctica tiene el
  doble de aguante de lo que dice su `max_health`, pero la fórmula no lo sabe.
- El **Mago** se cura y controla con hechizos de estado en vez de pegar
  fuerte — su daño base es bajo a propósito, pero su amenaza real viene de
  otro sitio que la fórmula no mide.

No es un fallo que haya que arreglar: es una limitación conocida y
documentada (en el docstring del módulo y en el informe de `TODO.md`). Ningún
número-resumen de un juego real es perfecto tampoco — el "Poder" de Raid
Shadow Legends también falla estrepitosamente con campeones cuyo valor viene
de una habilidad especial rara, no de sus stats brutas; es un motivo habitual
de queja en esa comunidad, de hecho.

### 2.2 La curva objetivo: `target_score()`

Con `power_score()` puedo puntuar a un enemigo, pero necesito saber **qué
número le "toca"** según dónde vive en el juego (qué zona, qué posición
dentro de esa zona). Para eso está la curva objetivo:

```
objetivo(zona, tier) = BASE × ZONE_GROWTH^zona × TIER_GROWTH^(tier − 1)
```

- **`zona`** — la posición de la zona en el mapa (Piedrablanca=0, Los
  Yermos=1, Bosque=2... hasta El Corazón de la Brecha=7).
- **`tier`** — la posición del enemigo dentro de su zona, del 1 (el más flojo)
  al 10 (el guardián).
- **`ZONE_GROWTH`** y **`TIER_GROWTH`** — cuánto crece el objetivo al subir un
  escalón en cada eje. Son **exponenciales** (se multiplican, no se suman) a
  propósito: así es como crecen de verdad los juegos de rol por turnos — cada
  zona nueva no es "un poco más difícil", es notablemente más difícil, y lo
  mismo dentro de una zona según te acercas al guardián. Es la misma forma que
  tiene, por ejemplo, la curva de experiencia por nivel que ya usa Valeterna
  (`Player._required_xp_for_level`) o la torre de pisos de Hustle Castle que
  mencionas: cada piso no suma una cantidad fija de dificultad, la multiplica.

#### ¿De dónde salieron `1500`, `2.1` y `1.25`?

No me los inventé — los ajusté a los datos reales que ya teníamos, con
**regresión log-lineal** (una técnica estadística estándar para ajustar una
curva exponencial a un conjunto de puntos). La idea en cristiano:

1. Calculé el `power_score()` real de los 14 enemigos actuales.
2. Los agrupé por zona y calculé la media de poder de cada una de las 6 zonas
   ya pobladas (Los Yermos, Bosque, Cañón, Torre, Ciudadela, El Corazón de la
   Brecha con solo el Dragón).
3. Como la curva es exponencial, si tomas el logaritmo de esos números, la
   relación se vuelve **una línea recta** (esa es la gracia del logaritmo:
   convierte "multiplicar por X en cada paso" en "sumar log(X) en cada
   paso", que es lineal). Ajustar una recta a un puñado de puntos es un
   problema resuelto desde el siglo XIX (mínimos cuadrados): buscas la recta
   que minimiza la distancia total a todos los puntos.
4. Esa recta, deshecho el logaritmo, me da `ZONE_GROWTH` (la pendiente) y una
   constante base.
5. Repetí el mismo truco **dentro** de Los Yermos, la única zona con tiers
   que el propio GDD fija explícitamente (Goblin=tier 2, Huargo=tier 4,
   Esqueleto=tier 6, Bandido=tier 7, en la tabla de ejemplo del §4.6) — eso me
   dio `TIER_GROWTH`.
6. Con las dos pendientes ya calculadas, despejé `BASE` para que la curva
   coincidiera con los datos de partida.
7. Los números que salieron de la regresión no eran redondos (algo como
   `2.106...` y `1.239...`) — los redondeé a `2.1` y `1.25` porque son
   números que un humano puede leer y recordar, y la diferencia es
   insignificante frente a la incertidumbre real de la fórmula (recuerda: ya
   sabemos que hay enemigos que se salen un 15-44% del objetivo por
   mecánicas que la fórmula no ve).

En resumen: la curva no es una ley física, es **la mejor recta que pasa cerca
de cómo ya habíamos calibrado el juego a mano**, hecha explícita para poder
usarla hacia delante. Si en el futuro decidimos que la progresión debe ser
más o menos empinada, se cambian esas tres constantes y toda la curva se
recalcula sola — no hay que retocar 70 enemigos uno a uno.

### 2.3 `zone_score_range()` — el rango, no el número exacto

Para una zona cuyos tiers todavía no están diseñados (todas menos Los
Yermos, por ahora), no tiene sentido pedir "el objetivo exacto del tier 6" si
ni siquiera sabemos qué enemigo va a ser el tier 6. En su lugar,
`zone_score_range(zona)` da el **rango completo** válido para esa zona:
`[objetivo(zona, 1), objetivo(zona, 10)]`. Cualquier enemigo de esa zona
debería caer dentro de ese rango, sea cual sea su tier exacto — es una
comprobación más floja, pero útil sin tener que decidir tiers antes de
tiempo.

### 2.4 `deviation()` — cuánto te has desviado

Una sola función: `(actual − objetivo) / objetivo`, en tanto por uno. Si un
enemigo puntúa 4 532 y el objetivo era 3 938, la desviación es
`(4532-3938)/3938 = +0.15`, es decir, +15%. El GDD pide diseñar dentro de
±10% de desviación como primera pasada; fuera de eso no es un error, es una
señal de que toca revisar la mecánica o el playtest antes de darlo por bueno.

---

## 3. Cómo se usa esto en la práctica (lo que hicimos en v0.14.0-c)

1. Antes de escribir el código de un enemigo nuevo, calculo
   `target_score(zona, tier)` para saber qué número "le toca".
2. Elijo unas estadísticas (vida, velocidad, ataque, crítico...) que den un
   `power_score()` cerca de ese objetivo — con lápiz y papel, probando
   combinaciones hasta acercarme.
3. Si el enemigo tiene una mecánica que añade amenaza sin subir esas stats
   (como robar oro, aturdir, sangrar), apunto las estadísticas **por debajo**
   del objetivo a propósito, sabiendo que la mecánica compensa la diferencia
   en la práctica — igual que ya vimos que pasa con el Bandido actual
   (emboscada + desarme, +44% sobre el objetivo real en combate aunque sus
   stats "de papel" estén más bajas).
4. El número final no es la última palabra: como dice el propio GDD, el
   siguiente paso es **playtest real** — combates simulados de verdad, como
   los que ya se han hecho para calibrar toda la cadena existente (ver el
   historial completo en `TODO.md`).

---

## 4. Si algún día quieres mostrarlo en pantalla

Nada te lo impide — es exactamente el mismo cálculo que hace Raid Shadow
Legends al enseñarte "Poder: 83.609" en la ficha de un campeón. Bastaría con
llamar a `power_score(player.stats)` (o a una variante que sume también el
equipo, como ya hacen los `get_total_*()` de `Player`) y mostrarlo en
Estadísticas o en la ficha de un enemigo del Bestiario. Ahora mismo es solo
una herramienta interna de diseño porque para eso se pidió en esta fase, pero
el cálculo ya está listo si algún día se quiere dar el salto a mostrarlo al
jugador, en este juego o en cualquier otro.
