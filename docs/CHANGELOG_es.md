# Changelog

<p align="center"><a href="../CHANGELOG.md">English</a> · <a href="CHANGELOG_es.md">Español</a></p>

Todos los cambios notables de este proyecto se documentan en este archivo.

El formato se basa en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/)
y este proyecto sigue el [Versionado Semántico](https://semver.org/lang/es/).

## [Unreleased]

### Añadido

- **Afinidades elementales reales para los 14 enemigos** (GDD §5, v0.11.0-a):
  cada enemigo declara ya debilidades, resistencias e inmunidades de verdad en
  vez del antiguo dict de un solo elemento a ×2.0 (eliminado por completo).
  Tabla completa en `CLAUDE.md`. Pulido tras las pruebas: reformulado el
  mensaje de "resiste" para que no parezca inmunidad total, quitada una línea
  redundante de "bloqueó el ataque" cuando el golpe ya era inmune, Veneno de
  Contacto ahora avisa de la inmunidad en vez de quedarse en silencio, y el
  Espíritu Vengativo ya no puede sangrar (es incorpóreo).
- **Resistencia elemental en armadura + 3 armas elementales nuevas** (GDD
  §5/§6.4, v0.11.0-b): `Armor` puede llevar ya `resist` (% de reducción de
  daño por elemento, sumado con `Player.get_total_resist()`, tope 75%) — por
  ahora lo dan el Cinturón de Resistencia (arcano), el Amuleto de Resistencia
  (oscuridad) y el Anillo de Vitalidad (sagrado). Armas craftables nuevas
  Espada Consagrada (sagrado), Daga Umbría (oscuridad) y Vara Arcana (arcano)
  — las primeras armas de esos 3 elementos que el jugador puede conseguir.
  De paso se arregló un hueco relacionado: si un golpe es físico o mágico lo
  decide ahora el elemento del arma (cualquier clase con un arma sagrado/
  oscuridad/arcano mitiga con resistencia mágica), no solo ser Arcanista.
- **Reacciones elementales** (GDD §5, v0.11.0-c): "Fusión" — un golpe de rayo
  contra un objetivo congelado rompe el hielo al instante y hace ×1.5 de daño
  extra en vez de intentar el paralizado normal, tanto en `Player` como en
  `Enemy`. "Combustión" — aplicar quemado mientras ya hay veneno activo (o al
  revés) funde ambos en un único estado `combustion` que hace más daño por
  turno que cualquiera de los dos por separado, reduce el ataque físico a la
  mitad igual que la quemadura, y sigue siendo curable con el Antídoto (su
  descripción ahora también lo dice). Arreglos tras las pruebas: el mensaje
  "X ha sido quemado/envenenado" ahora sale siempre ANTES que el de "el fuego
  y el veneno se funden en combustión", no al revés; y una vez la combustión
  está activa, un nuevo intento de quemar o envenenar al mismo objetivo ya no
  hace nada (ni refresca la duración, ni repite el mensaje de fusión) — ya es
  las dos cosas a la vez.
- **Cimientos del paquete de mundo** (GDD §3/§9.2/§9.4, v0.12.0-a): nuevo
  paquete `world/` con los datos de zona — `Zone` (id, nombre, tema, enemigos
  backbone, sub-lugares, NPCs clave) y un módulo por zona en `world/data/`,
  reunidos en `world/map.py` (`ZONE_ORDER`/`ZONES`). El esquema de guardado v2
  añade un bloque `mundo` al archivo (`zona_actual`, `zonas_visitadas`,
  `misiones`, `banderas`, `dialogos_vistos`, `diario`,
  `arena_mejor_oleada`), migrado automáticamente para partidas anteriores a
  este cambio (la zona actual se infiere del progreso de combate). Es solo
  la base — `game_loop` todavía no usa zonas, eso llega en la siguiente
  sub-fase.
- **Bucle de exploración por zona** (GDD §8.1, v0.12.0-b): desaparece el
  antiguo menú plano de `game_loop`, sustituido por un menú por zona
  (`ui/exploration.py`) — **Explorar** (tirada ponderada: combate contra un
  enemigo desbloqueado al azar de la zona actual, un pequeño hallazgo de oro,
  o nada), **Ir a...** (lista los sub-lugares de la zona; de momento un stub,
  sin NPCs hasta v0.13.0), **Viajar** (viaje rápido a cualquier zona
  visitada, más "frontera" a la siguiente zona en cuanto es alcanzable), y
  **Personaje** (todo lo demás que antes era el menú entero: inventario,
  tienda, herrería, estadísticas, habilidades, bestiario, equipar, opciones,
  guardar). Elegir un enemigo concreto por nombre para pelear desaparece — el
  combate ahora solo llega a través de la tirada de Explorar.
- **Servicios de zona: tienda/herrería reubicadas + descanso + variedad en
  los hallazgos** (GDD §7.4/§8.1, v0.12.0-c): Tienda y Herrería salen del menú
  Personaje y se mudan a "Ir a..." de Piedrablanca — Mercado abre la tienda,
  Herrería la herrería. Nueva "Taberna": cura del todo y limpia todos los
  estados alterados a cambio de oro (el coste escala con el nivel, un número
  provisional todavía sin ajustar). El hallazgo de Explorar ahora a veces da
  una poción de salud gratis en vez de siempre oro.

- **Motor de diálogo** (GDD §8.2, v0.13.0-a): nuevo `world/npc.py` con NPCs, conversaciones ramificadas, respuestas del jugador (condiciones sobre banderas de historia/nivel, efectos: activar una bandera, dar oro u objeto), conversaciones únicas vs repetibles (las únicas se recuerdan en el guardado y el NPC pasa a líneas sueltas) y una opción nueva "Hablar con..." en el menú de zona. De momento solo Yerma (Piedrablanca) tiene contenido; el resto del reparto llega a continuación.

### Cambiado

- **Reordenado el menú de combate**: Atacar, Habilidades, Defender, Objetos,
  Huir, Info, Auto-Batalla, Auto-Batalla Turbo (antes era Atacar, Objetos,
  Info, Huir, Defender, Habilidades...) — agrupa las dos opciones de acción
  (atacar/habilidades) y la defensiva (defender) al principio, antes que las
  utilitarias.
- **El proyecto pasa de llamarse "JuegoRolTexto" a Valeterna** (el nombre del
  reino en el GDD) — nadie se había descargado todavía ninguna build, así que ha
  sido un corte limpio sin capa de compatibilidad: el paquete de Python
  (`src/valeterna/`, todos los imports), el nombre de distribución/script
  (`valeterna`), el spec/ejecutable de PyInstaller (`Valeterna.spec` →
  `Valeterna.exe`), el repositorio de GitHub y toda la documentación/CI usan ya
  el nombre nuevo.

### Arreglado

- **El login de admin ya no se queda colgado en consolas sin terminal real**
  (p. ej. el panel "Run" de PyCharm, a diferencia de su pestaña "Terminal"):
  `getpass.getpass()` necesita un terminal real para ocultar la entrada, y en
  algunas consolas de IDE no lanza una excepción cuando no lo tiene — se
  queda colgado sin más, aceptando Intro como si fuera parte de la
  contraseña, sin terminar nunca. `_check_admin_password()` ahora comprueba
  `sys.stdin.isatty()` primero y va directa a la entrada visible cuando no
  hay terminal real, en vez de depender de una excepción que puede no llegar
  nunca.

## [0.10.0] - 2026-09-09

### Añadido

- **Habilidades** (GDD §6.2): cada clase tiene ahora un pool de habilidades. Las
  **pasivas** están siempre activas una vez aprendidas; las **activas**
  reemplazan tu ataque y tienen enfriamiento en turnos — equipas hasta 4 para
  llevar al combate. Nuevo menú "Habilidades" para gestionarlas y una acción
  "Habilidades" en combate para usarlas (la auto-batalla usa una activa lista si
  la hay). Este release trae el hito 1 (1 activa + 1 pasiva por clase, se aprende
  al crear el personaje): Golpe Firme / Segundo Aliento (Aventurero), Embate /
  Piel de Piedra (Guerrero), Golpe Bajo / Reflejos (Pícaro), Proyectil Arcano /
  Sintonía (Arcanista). Nuevos estados `sangrado` y `aturdido`, cada uno con su
  mensaje y color propios. Los números son provisionales.
- **Habilidades del hito 2** (se aprenden al nivel 4, provisional): Aguante
  (Aventurero — por debajo del 30% de vida obtienes +15% de armadura y res.
  mágica), Represalia (Guerrero — 30% de probabilidad de contraatacar un golpe
  físico), Veneno de Contacto (Pícaro — 20% de probabilidad de envenenar al
  golpear), Escudo de Maná (Arcanista — activa a4: absorbe por completo el
  próximo golpe).

- **Cadenas de auto-batalla**: tras activar la Auto-Batalla o el Turbo contra un
  enemigo ya derrotado, el juego pregunta cuántas peleas seguidas hacer (hasta
  20). Cada una se resuelve como siempre (botín, oro, XP, curación) y la
  siguiente empieza sola — sin menú, sin "Presiona Enter" por pelea. La cadena se
  detiene si caes o huyes; pulsar `Q` te devuelve al control manual, y desde el
  menú puedes cambiar de Auto a Turbo (o al revés) a mitad de la cadena. Al
  terminar (ganes o pierdas) muestra un resumen de todo lo conseguido en la
  cadena entera — oro, XP, niveles y cada objeto con su tipo (arma / armadura +
  hueco / poción / material de herrería).

- **Clases de personaje** (GDD §6.1): al crear personaje eliges entre
  **Aventurero** (el personaje equilibrado de siempre), **Guerrero** (tanque),
  **Pícaro** (rápido / crítico / frágil) o **Arcanista** (mágico). Cada una tiene
  sus stats de arranque y su crecimiento por nivel. Las partidas viejas y los
  personajes actuales siguen siendo Aventurero.
- Stat **`poder mágico`**: el ataque estándar del Arcanista es mágico
  (`is_magical`), escala con `poder mágico` en vez de con el arma, usa el
  elemento `arcano` por defecto y lo mitiga la resistencia mágica del enemigo
  —así la `magic_resist` por fin importa contra el jugador—. Solo crece por nivel
  para el Arcanista.
- Los guardados registran ahora `clase` y `habilidades_equipadas` (esta última
  sin uso hasta que llegue el sistema de habilidades).

### Cambiado

- Las fichas de estadísticas (menú "Estadísticas" y los dos paneles de info en
  combate) agrupan en una línea las stats relacionadas: armadura + resistencia
  mágica, precisión + evasión, prob. crítico + daño crítico; la XP va ahora junto
  al nivel. El panel de combate muestra además el daño crítico del jugador y la
  prob. de crítico + daño crítico del enemigo.
- El personaje admin también elige clase, para poder probarlas con stats de cheat.
- El aviso de "versión nueva disponible" aparece ahora cada vez que se dibuja el
  menú principal y de nuevo al entrar en "Nueva Partida" / "Cargar Partida"
  (antes de pedir el nombre), en vez de solo una vez por sesión — si no, es fácil
  pasarlo por alto. Dentro de la partida sigue mostrándose una sola vez, al
  entrar.
- El combate ya no corta la canción que suena contra un enemigo estándar — solo
  el jefe final y los cinco enemigos duros del tramo final cambian a música de
  combate propia. Evita que las peleas cortas (y las cadenas de auto-batalla)
  reinicien la música cada pocos segundos. (Cuando existan élites y guardianes de
  zona serán ellos quienes activen la música de combate — ver `TODO.md`.)
- Las fichas de combate se imprimen ahora antes de una emboscada previa, no
  después, para ver el enfrentamiento primero. Además una línea indica quién
  tiene la iniciativa (más velocidad) y cada acción lleva ahora una cabecera
  `── Turno N · Nombre ──` (con la clase, para el jugador). Una pequeña pausa
  tras el turno del enemigo deja leer el daño antes de que salga el menú.
- La clase equilibrada se llama ahora **Aventurero** (antes "Vagabundo") — solo
  el nombre visible; el valor guardado no cambia.
- La línea de botín al ganar muestra el tipo de cada objeto (arma / armadura +
  hueco / poción / material de herrería) y, para armas y armaduras, las
  estadísticas que otorga. Las pociones ya no repiten lo que hacen (ya estaba en
  la descripción).
- La auto-batalla Turbo mantiene su velocidad (sin pausas ni esperas) pero ya no
  oculta las barras de vida tras el turno del enemigo — se ve cómo va la pelea.
- Un ataque esquivado dice ahora "X lo esquiva" en vez de "falla el golpe" — los
  ataques no fallan por sí solos, solo cuando el objetivo esquiva (evasión vs
  precisión).
- Más estados van coloreados: `sangrado` (rojo claro, distinto de la quemadura),
  `aturdido` (amarillo claro, distinto de la parálisis), `desarmado`, `maldición`,
  `confusión`.

## [0.9.0] - 2026-09-09

### Añadido

- **Modelo de afinidades elementales** (GDD §5): los enemigos ahora pueden ser
  débiles, resistentes o inmunes a cada uno de los 7 elementos. Debilidad ×1.5 de
  daño (×2.0 si dos de los elementos del ataque son débiles), resistencia ×0.5
  (×0.25 si dos), inmunidad ×0 de daño y sin estado. Inmunidad aparte a estados
  concretos.
- **Estados en los enemigos**: quemadura, veneno, parálisis, congelación,
  `fractura mágica` (anula la resistencia mágica) y el resto se procesan ahora en
  el turno del enemigo (daño por turno, turnos perdidos, mensajes de fin) igual
  que ya se hacía con el jugador.
- **Armas que infligen estados**: un arma con elemento (o con `inflicts`
  explícito) tiene una probabilidad de aplicar el estado correspondiente al
  golpear. La probabilidad y la duración se reducen a la mitad contra un enemigo
  que resista el elemento, y se bloquean por completo si es inmune.
- **Capa de strings i18n** (`i18n.t(key, **kwargs)`, GDD §9.1): los textos de
  combate/estados salen de un catálogo por idioma con recurso al español y luego
  a la clave. El idioma se lee de `config.ini` `[IDIOMA]`. De momento solo se han
  migrado los textos nuevos de la v0.9.0.
- Un combatiente congelado / paralizado pierde con seguridad el turno en el que
  se le aplica el estado; las tiradas de escape por turno solo se aplican después.
- Distintivos de estado en las barras de vida de combate con cada efecto activo y
  sus turnos restantes (p. ej. `[quemado 2 · veneno 1]`).
- Tienda: los objetos apilables (pociones, antídotos) se pueden comprar y vender
  de varios en varios, hasta donde llegue el oro — un único mensaje resumen en
  lugar de una línea por unidad. Los textos de tienda, venta y herrería van
  coloreados.
- Panel de admin: "conseguir x20 de cada poción".

### Cambiado

- **La mitigación de daño ahora es multiplicativa** (rendimientos decrecientes
  estilo Raid): `daño × K / (defensa + K)` con `K = 20`, nunca absorbido del todo
  (mínimo 1), en lugar de la resta `daño − armadura` que se rompía a gran escala.
  Es un cambio de balance; la cadena de 14 enemigos se recalibrará más adelante.
- `quemado` ahora es solo físico — ya no se derrite con cualquier golpe mágico,
  solo con uno marcado explícitamente como de fuego.
- El Gólem de Piedra ahora es débil a `hielo` e inmune a `rayo` (antes era débil
  a `rayo`).
- Un jugador paralizado / congelado ahora recibe el menú de turno normal (usar
  objetos, intentar huir con la mitad de probabilidad) en vez de saltarse el
  turno automáticamente; no puede "Defender" mientras está inmovilizado.
- Orden de los mensajes de combate: la nota de golpe crítico y la de estado
  infligido salen ahora después de la línea de daño, no antes.

### Corregido

- El Bandido ya no puede volver a desarmar a un jugador ya desarmado (peleas que
  consistían solo en desarmes repetidos).
- Los lanzadores de hechizos enemigos (Mago) ahora muestran el número de daño de
  cada hechizo.
- Un enemigo paralizado / congelado ya no imprime cabecera de turno ni barras de
  vida duplicadas en un turno en el que no hace nada.
- Los ataques de un jugador desarmado ya no llevan el elemento ni el estado del
  arma (ahora caída).

## [0.8.0] - 2026-09-08

### Corregido

- Auto-actualización: el `.bat` relanzador ahora se arranca con `os.startfile`
  (ShellExecute) en vez de `subprocess.Popen`, que a veces fallaba con
  `0xC0000142` (fallo al inicializar cmd.exe) al lanzarse mientras el juego se
  cerraba. También se añade un pequeño margen antes de que el juego cierre.
- Cerrar stdin (entrada canalizada agotada, consola sin TTY) ahora cierra el
  juego limpiamente en vez de lanzar `EOFError` como cierre inesperado (que
  además disparaba el informe opcional a Discord).

## [0.7.0] - 2026-09-08

### Añadido

- Al empezar un combate se muestran siempre las fichas de jugador y enemigo,
  sin importar quién tenga el turno primero; un enemigo que aún no has derrotado
  aparece como `???`.
- Auto-batalla Turbo: una segunda opción de auto-batalla sin pausas entre
  turnos, sin barra de vida por turno y sin el "Presiona Enter" de victoria —
  para farmear rápido enemigos que ya te resultan fáciles.
- Las fichas de estadísticas (jugador, enemigo, bestiario) van coloreadas por
  estadística.
- Cualquier texto que mencione un estado alterado se colorea igual en todo el
  juego: veneno en verde, quemadura en rojo, parálisis en amarillo, congelación
  en azul.

### Cambiado

- El Goblin no embosca hasta que se le ha derrotado al menos una vez (la
  primera pelea del juego siempre es limpia).

## [0.6.0] - 2026-09-08

### Corregido

- Paso de aplicación de la auto-actualización: el `.bat` relanzador ahora corre
  en su propia consola (así sobrevive al cierre del juego y sus comandos
  funcionan), espera al juego por nombre de proceso, espeja la versión nueva con
  `robocopy /MIR` (borrando ficheros obsoletos — sobre todo el `*.dist-info` de
  la versión anterior, que dejaba al juego ya actualizado informando de la
  versión vieja), protege `config.ini` y la carpeta de partidas, y deja un
  `apply.log`.

## [0.5.0] - 2026-09-08

### Añadido

- Acción de combate "Defender": gastas el turno para reducir a la mitad el daño
  que recibes hasta tu siguiente turno.
- Poción de Antídoto: elimina al instante veneno, quemadura, parálisis y
  congelación. Se vende en la tienda.
- La versión del juego se muestra bajo el título del menú principal y del menú
  de partida.

## [0.4.0] - 2026-09-08

### Añadido

- Entrada de teclado no bloqueante y multiplataforma (`ui/keyboard.py`); el juego
  y la suite de tests ya no necesitan Windows.
- Comprobación estática de tipos con `pyright` (modo `basic`) como check obligatorio del CI.
- Smoke test de arranque (`app.main()` arranca y sale limpio).
- Captura del README generada a partir de un combate real (`tools/capture_screenshot.py`).
- `build-check` en el CI — construye el `.exe` cuando cambian los archivos de empaquetado.
- Auto-actualización (build empaquetada): comprueba los GitHub Releases al
  arrancar y avisa si hay una versión más nueva; toggle y comprobación manual en
  Opciones.
- La auto-actualización ya puede descargar, verificar (SHA-256 contra el
  `SHA256SUMS` del Release) y aplicar una actualización, reiniciando el juego con
  un `.bat` relanzador sin tocar `saved_games/` ni `config.ini`.
- El workflow de release publica un archivo `SHA256SUMS` junto al zip de Windows.

### Cambiado

- El CI ejecuta la matriz de tests en Linux (3.10–3.13) más un job de Windows.
- Protección de la rama `main`: PR + CI en verde obligatorios; el badge de
  cobertura vive en una rama huérfana `badges`.
- El conjunto de reglas de Ruff añade `UP`, `B` y `SIM`.

## [0.3.0] - 2026-09-07

Primera versión etiquetada. Añade el informe de errores, la infraestructura de
proyecto y una gran pasada de cobertura de tests sobre la línea base 0.2.0.

### Añadido

- Registro de errores en disco: `logs/juego.log` (rotativo) y un
  `logs/crash_<timestamp>.txt` por cada cierre inesperado, manteniendo la
  ventana abierta para que quien juega con el `.exe` pueda leer la ruta.
- Informe opcional (opt-in) del cierre inesperado a un webhook de Discord, con
  mención al desarrollador y las rutas del perfil / nombre de usuario
  censurados. Se configura en `config/secrets.py`; se activa/desactiva en *Opciones*.
- `config/secrets.py` (no versionado) para el webhook de Discord, el ID de
  mención y el hash de la contraseña de admin, con la plantilla
  `config/secrets.example.py` versionada y el accesor tolerante `config/secret_store.py`.
- El jugador se reconoce por el nombre con el que registró la partida: la carga
  no distingue mayúsculas/minúsculas y se restaura el nombre canónico; *Nueva
  Partida* rechaza un nombre que ya tiene partida guardada.
- Integración continua (GitHub Actions): Ruff y la suite de tests en Python
  3.10–3.13 (Windows), más un badge de cobertura que se autocommitea.
- Workflow de release: al empujar un tag `vX.Y.Z` se construye el paquete de
  Windows y se adjunta al GitHub Release.
- Archivos de proyecto: `LICENSE` (MIT), `CONTRIBUTING`, `ROADMAP`, este
  `CHANGELOG`, `CODE_OF_CONDUCT`, `SECURITY`, plantillas de issue/PR, Dependabot, `.editorconfig`.
- Ruff como linter y formateador (conjunto de reglas conservador), configurado en `pyproject.toml`.
- Pasada de cobertura de tests: 70% → 91% (238 tests). `ui/menus.py` y `app.py`
  se excluyen de la métrica por ser pegamento interactivo.

### Corregido

- El juego se cerraba al abrir el inventario teniendo un material de crafteo
  (los objetos sin estadísticas no implementaban `get_stats_info()`).
- El error de audio `Audio device hasn't been opened` al salir, provocado por el
  hilo watchdog de música ejecutándose tras cerrarse el mezclador.

### Eliminado

- `tools/settings_admin.py` — código muerto (una ventana de ajustes en Tkinter sin usar).

## [0.2.0] - 2026-09-06

Línea base: el estado del juego cuando se empezó a llevar este changelog. Los
cambios anteriores no se registraron formalmente.

### Añadido

- Sistema de turnos ATB (Active Time Battle), 1 contra 1.
- 14 enemigos con mecánicas propias y una cadena de desbloqueo fija.
- 11 huecos de equipo estilo Diablo con estadística base por hueco y secundarias.
- Herrería (12 recetas), tienda y bestiario.
- Panel de administración/debug protegido con contraseña.
- Música de fondo por «mood» (aventura / combate).
- Guardado/carga en JSON + base64 con copia de seguridad.
- Empaquetado con PyInstaller para Windows.

## [0.1.0] - 2024-05-04

### Añadido

- Versión inicial: combate por turnos básico en consola.

[Unreleased]: https://github.com/Guille87/Valeterna/compare/v0.10.0...HEAD
[0.10.0]: https://github.com/Guille87/Valeterna/compare/v0.9.0...v0.10.0
[0.9.0]: https://github.com/Guille87/Valeterna/compare/v0.8.0...v0.9.0
[0.8.0]: https://github.com/Guille87/Valeterna/compare/v0.7.0...v0.8.0
[0.7.0]: https://github.com/Guille87/Valeterna/compare/v0.6.0...v0.7.0
[0.6.0]: https://github.com/Guille87/Valeterna/compare/v0.5.0...v0.6.0
[0.5.0]: https://github.com/Guille87/Valeterna/compare/v0.4.0...v0.5.0
[0.4.0]: https://github.com/Guille87/Valeterna/compare/v0.3.0...v0.4.0
[0.3.0]: https://github.com/Guille87/Valeterna/releases/tag/v0.3.0
