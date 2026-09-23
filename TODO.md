# Próximas Implementaciones 🚀

## Panel de Admin
- [x] **Control total para el personaje "admin"** (a petición del usuario, que recordaba una ventana de Tkinter asociada al admin — resultó ser `tools/settings_admin.py`, código muerto que no se llamaba desde ningún sitio del juego y que además usaba nombres de atributos que no coincidían con los reales de `Player`/`Stats`; se borró más tarde en la pasada de organización del proyecto). En su lugar, nueva opción "Panel de Admin" en `game_loop()`, con control real dentro del propio juego (consola, no Tkinter, para ser consistente con el resto):
  - Poner el oro que se quiera.
  - Poner el nivel que se quiera (subir reutiliza `Player._level_up()` real, así que las estadísticas suben con la curva normal del juego en vez de un número arbitrario; bajar el nivel no baja las estadísticas solo, hay que tocarlas a mano si hace falta).
  - Editar cualquier estadística de `Stats` una a una (vida, ataque, armadura, resistencia mágica, velocidad, precisión, evasión, penetraciones, regeneración, crítico).
  - Curación completa instantánea.
  - Desbloquear y marcar como derrotados los 14 enemigos de golpe (incluido el Dragón, y con Bestiario ya accesible para todos).
  - Combate directo contra cualquier enemigo de la cadena, sin depender de `unlocked_enemies`.
  - Conseguir 50 unidades de cada uno de los 14 materiales del juego, lo que de paso descubre las 12 recetas de la herrería (`Inventory.add_item()` ya marca un material como descubierto la primera vez que se consigue, así que no hacía falta lógica aparte).
  - Conseguir una copia de cada arma y armadura que puede soltar algún enemigo (42 objetos en total). Ambas opciones fuerzan `random.random()` a 0 mientras leen `drop_item()` de los 14 enemigos, para que caigan todos los objetos posibles de golpe; los "Obtenido: X" de `Inventory.add_item()` se silencian durante la entrega masiva (si no, imprime cientos de líneas seguidas).
  - De paso, el personaje "admin" al crear partida ahora también empieza con el Dragón marcado como derrotado (antes se quedaba fuera de `defeated_enemies` porque no tiene "siguiente" enemigo que desbloquear), para tener acceso completo al Bestiario desde el principio.
- [x] **Protegido con contraseña** (a petición del usuario: escribir "admin" como nombre ya no basta por sí solo). `_check_admin_password()` pide la contraseña con `getpass.getpass()` (no se ve en pantalla mientras se escribe; si la consola no lo soporta, cae a una entrada visible en vez de bloquear el acceso) y compara su **hash SHA-256** contra una constante — la contraseña real nunca se guarda en texto plano en ningún archivo del repo ni del juego instalado, así que no se puede encontrar buscando entre los archivos.
- [x] **"admin" es un nombre reservado de verdad, no solo un cheat silencioso** (a petición del usuario, ajustando el comportamiento anterior): si se escribe "admin" y la contraseña falla, tanto `start_new_game()` como `load_saved_game()` **rechazan el nombre por completo** — no se puede jugar ni cargar con ese nombre, hay que volver a elegir uno (o reintentar "admin" con la contraseña correcta). Antes, un fallo de contraseña dejaba seguir jugando igualmente con el nombre "admin", solo sin los privilegios; ahora el nombre en sí está bloqueado sin la contraseña correcta. La comprobación se hace en el propio bucle de pedir el nombre (antes de crear al `Player`), y se aplica igual tanto si es partida nueva como si se carga una partida guardada con ese nombre.
- [x] **Arreglado un cuelgue al pedir la contraseña de admin en consolas sin terminal real** (encontrado por el usuario probando desde el panel "Run" de PyCharm, tras el rename de proyecto/carpeta: escribía "admin", le daba a Enter y se quedaba cargando sin ningún error, aceptando más Enters como si fueran parte de la contraseña). Causa: `getpass.getpass()` necesita un terminal real para leer la entrada en modo "crudo" y ocultarla; el `try/except` que ya existía solo cubre el caso en que `getpass` **lanza una excepción** al no tener terminal (documentado como el caso típico), pero en la consola "Run" de PyCharm (distinta de su pestaña "Terminal") no lanza nada — simplemente se cuelga sin devolver el control jamás, así que el except nunca se disparaba. Arreglado comprobando `sys.stdin.isatty()` **antes** de intentar `getpass`: si no hay terminal real, va directa a la entrada visible (`console.ask`) en vez de arriesgarse al cuelgue; el `try/except` se mantiene como red para otros fallos de `getpass` en consolas que sí pasan la comprobación. Cubierto con tests nuevos en `test_menus.py` (sin cobertura previa de `_check_admin_password`, ya que `ui/menus.py` está excluido de la métrica de cobertura).

## UX y correcciones varias
- [x] **El inventario ahora muestra la vida actual/máxima del jugador** (a petición del usuario, para saber de un vistazo si conviene usar una poción de salud), en `Inventory.show_inventory()`.
- [x] **La curación al huir ya no cura daño de peleas anteriores** (a petición del usuario: "si huyo no debería recuperar vida de antes de esta pelea"). Antes, huir pasaba por la misma `_restore_player()` que una victoria, que cura el 50% de *toda* la vida que le falte al jugador, viniera de donde viniera. Ahora `initiate_battle()` guarda la vida al empezar el combate y, si el jugador huye, `_restore_player(..., max_recovery=...)` limita la curación a como mucho la vida perdida **en ese combate concreto** — si entras ya herido de antes y huyes sin recibir ni un golpe, no se cura nada. Cubierto con un test nuevo.
- [x] **Reescrito el sistema de música** (a petición del usuario, tras varios síntomas raros: la música no cambiaba al volver a pelear contra el mismo enemigo, sonaba de golpe un tema de combate de otro enemigo un instante, y a veces una canción terminaba y no sonaba ninguna otra). Causa raíz encontrada: `ResourceManager` reproducía la música como `pygame.mixer.Sound` normal y comprobaba si había que cambiar de pista con `pygame.mixer.get_busy()` — pero esa función devuelve `True` si **cualquier** canal está ocupado, incluidos los efectos de sonido (golpes, hechizos, etc.), no solo la música. Un SFX sonando a mitad de combate podía hacer que el sistema pensara que la música seguía sonando cuando en realidad ya había terminado, bloqueando el cambio de tema. Solución: la música ahora usa el canal dedicado `pygame.mixer.music` (independiente de los canales de efectos), así que `get_busy()` ya solo refleja la música de verdad. Además:
  - Entrar en combate ahora fuerza el cambio de música de inmediato para **cualquier** enemigo (antes solo Orco/Mago tenían ese forzado; el resto dependía de que `update()` detectara el hueco, lo cual fallaba si algo más marcaba el mixer como ocupado — esto es lo que explicaba "la música no cambia al volver a pelear contra el mismo enemigo").
  - `game_loop()` (el menú de la ciudad) nunca llamaba a `resource_manager.update()` — ni una sola vez —, así que en ese menú la música no se refrescaba jamás por sí sola. Añadida la llamada.
  - Como el juego es una consola síncrona que pasa la mayoría del tiempo bloqueada en `input()` esperando al jugador, aunque se llame a `update()` en los sitios correctos, si el jugador no hace nada la música se queda en silencio hasta la siguiente pulsación. Añadido un hilo en segundo plano (`app.py::_music_watchdog`) que llama a `update()` cada 2 segundos, así la música avanza sola aunque el jugador esté simplemente leyendo o ausente.
  - Eliminada `ui/menus.py::smart_input()`, una función que ya intentaba paliar el problema anterior llamando a `update()` antes de cada `input()` pero que no se usaba en ningún sitio del código (código muerto) — superada por el hilo en segundo plano, que cubre el mismo caso de forma más completa.
- [x] **Reasignada la música de combate por dificultad real** (a petición del usuario: antes "Scaring Crows" sonaba en todas las peleas excepto Mago, que tenía "Siege of the Black Gate" en solitario). Ahora: "Siege of the Black Gate" (tema épico) solo para el Dragón, jefe final; "Scaring Crows" (tema inquietante) solo para los 5 enemigos genuinamente duros del tramo final — Gólem de Piedra, Mago, Nigromante, Ángel Caído, Demonio, todos calibrados en su día al 73-78% de victorias del jugador (el rango más bajo/difícil de toda la cadena aparte del propio Dragón, ver el historial de playtest de la sección "Nuevos Enemigos"); el resto de enemigos (Goblin a Gárgola, los primeros 8) comparten el mismo grupo de 3 canciones que ya suena en el menú/aventura, en vez de tener música de combate dedicada. `ResourceManager.play_battle_music()` centraliza esta lógica con las constantes `HARD_BATTLE_ENEMIES`/`FINAL_BOSS`.
- [x] **La música ya no se corta contra enemigos estándar** (a petición del usuario: con auto-batalla y sus cadenas las peleas son tan cortas que la canción cambiaba constantemente al entrar/salir de combate). Ahora `ResourceManager.enter_battle()` solo cambia la música si el enemigo tiene tema propio (`has_dedicated_battle_music()` = jefe final + los 5 duros); contra el resto se deja sonar lo que hubiera (el `mood` sigue en `"adventure"`, así que `update()` rota pistas de aventura con naturalidad al terminar una, sin cortes bruscos a mitad de pelea). `exit_battle()` solo fuerza pista nueva si veníamos de música de combate dedicada. Combate en cadena: `enter_battle`/`exit_battle` se llaman una sola vez, no por pelea.
- [ ] **Pendiente (v0.11+): música por élite/guardián, no por dificultad.** Cuando existan los tiers de zona (§ GDD 7.4: estándar / élite 5-7-9 / guardián 10), la música de combate la activarán los élites y guardianes, no la dificultad calibrada a mano. Los enemigos estándar de zona nunca cortarán la pista. `has_dedicated_battle_music()` es el punto único a cambiar; hoy devuelve `enemy in HARD_BATTLE_ENEMIES or enemy == FINAL_BOSS` como aproximación.

## Reparto de estadísticas por hueco de armadura
- [x] **Cada hueco de armadura tiene ahora un "stat base" garantizado**, a petición del usuario, para que la elección de equipo tenga una lógica reconocible en vez de ser aleatoria pieza a pieza. Reparto acordado: casco→Vida, peto→Armadura, hombreras→Precisión, brazales→Probabilidad de Crítico, guantes→Daño de Crítico, cinturón→Armadura (mismo campo `defense` que el peto — confirmado explícitamente con el usuario que "Resistencia física" no es un stat nuevo, solo el nombre que le dio de pasada), perneras→Evasión, botas→Velocidad, anillo→Daño de Crítico, amuleto→Resistencia Mágica. Cada objeto lleva el stat base **siempre** más entre 0 y 3 estadísticas secundarias (1-4 en total, nunca más de 4, nunca 0).
- [x] **Dos stats nuevos en `Armor`**: `precision` y `evasion` (hombreras y perneras respectivamente no tenían ningún campo que pudiera representarlos hasta ahora). `Player.get_total_precision()`/`get_total_evasion()` pasan de devolver solo el stat base a sumar también el bonus de todo el equipo (mismo patrón que `get_total_armor()`/`get_total_speed()`), cerrando el hueco que `CLAUDE.md` llevaba documentando desde hacía varias sesiones ("existen por simetría de API pero ningún objeto las otorga todavía").
- [x] **La cantidad de estadísticas por objeto sigue la posición en la cadena**: los primeros enemigos sueltan objetos con pocas stats (1-2), los últimos pueden llegar a 3-4, dando sensación de progreso real. Revisados los 14 enemigos uno a uno para que cada objeto tenga su stat base y (cuando hacía falta) se le recortara o ampliara la cantidad de secundarias según su posición.
- [x] **El stat base de cada hueco no baja a lo largo de la cadena** (mismo criterio que la curva de daño de armas de más abajo), con dos excepciones deliberadas acordadas explícitamente: el peto del Mago (una túnica arcana no debe superar en armadura a la coraza de piedra del Gólem —enemigo anterior—, así que se queda con `defense=9` y en su lugar gana `magic_resist=6` como compensación) y las botas del Gólem (mantienen su identidad de "lentas pero muy resistentes" frente a las del Huargo con `speed=1` en vez de `speed=0`, ya que ahora toda bota tiene que dar algo de velocidad). Verificado con un test nuevo (`tests/test_armor_progression.py`) que comprueba automáticamente las tres reglas (stat base presente, entre 1 y 4 stats, base no decreciente por hueco) sobre los 14 enemigos a la vez, para que no se rompa sin darse cuenta en el futuro.
- [x] **Extendido a las 11 recetas de armadura de la herrería** (a petición del usuario). 6 de las 11 ya tenían su stat base por casualidad (Armadura Regenerativa, Guantes de Combate, Botas Ligeras, Anillo de Precisión, Amuleto de Resistencia); las otras 5 no lo tenían y se les añadió: Brazales Arcanos (+crit_chance), Hombreras Reforzadas (+precision), Cinturón de Resistencia (+defense — con cuidado de no volver a duplicar exactamente el drop del Gólem, se le dio solo `defense=3` frente al `defense=4` del Gólem, dejando la resistencia mágica como su verdadero diferenciador), Perneras de Placa (+evasion), Anillo de Fuerza y Anillo de Vitalidad (+crit_damage, este último con un valor alto —0.16— ya que pide Escama de Dragón, el material más raro y tardío del juego). Verificado con dos tests nuevos en `tests/test_armor_progression.py` (stat base presente + entre 1 y 4 stats en total) sobre las 11 recetas.

## Progresión de daño de armas por enemigo
- [x] **Curva de daño de armas rehecha para que sea siempre creciente a lo largo de la cadena** (a petición del usuario, tras notar que el Bandido —4º enemigo— soltaba un arma más floja que las del Huargo —2º— pese a ser más difícil, y que el patrón se repetía varias veces más adelante). Auditados los 14 enemigos: además del caso Huargo/Bandido había violaciones en Orco→Espíritu Vengativo, Gárgola→Gólem (antes con el mismo daño exacto que Troll) y Gólem→Mago→Nigromante. En vez de solo subir cada violación (eso habría inflado el Dragón por encima de 40), se rediseñó la curva completa 1-14 para que sea suave y estrictamente creciente, bajando la Maza de Piedra del Troll (20→17, ya no hacía falta que fuera "la mejor arma hasta ahora" con enemigos posteriores mucho más duros) para dejar hueco a la segunda mitad de la cadena en vez de que todo se acumulara al final. Secuencia final de daño máximo por enemigo: Goblin 4, Huargo 7, Bandido 9, Orco 12, Espíritu Vengativo 14, Troll 17, Gárgola 19, Gólem 21, Mago 23, Nigromante 25, Ángel Caído 27, Demonio 29, Dragón 32 (Goblin/Huargo/Orco sin cambios, el resto ajustado). Las armas elementales de cada pareja (Huargo, Orco, Gárgola, Nigromante) se mantienen por debajo de su versión normal, como ya se había corregido en la pasada anterior.

## Balance de armas elementales
- [x] **Corregida la dominancia estricta de 3 armas elementales** (a petición del usuario, al preguntar por qué el Colmillo Venenoso del Huargo tenía la misma probabilidad que las Garras de Huargo pese a hacer más daño y encima tener elemento). Al añadir las armas de Rayo/Veneno/Hielo se les había dado más daño en crudo que su versión "normal" del mismo enemigo, a la misma tasa de drop — una mejora estricta sin ninguna contrapartida, distinto del patrón ya bien calibrado del Orco (Hacha de Batalla 12 dmg/10% vs Espada Flamígera 10 dmg+fuego/8%, donde la elemental sacrifica daño y rareza a cambio del elemento). Ajustadas las 3 a ese mismo patrón: Huargo (Colmillo Venenoso 8→6 dmg, 10%→8%), Gárgola (Garra de Tormenta 18→13 dmg, 8%→6%), Nigromante (Cetro de Escarcha 20→15 dmg, 8%→6%) — ahora todas pegan menos en crudo y son más raras que su contraparte sin elemento, dando una elección real (daño fiable vs. bonus situacional x2 contra el enemigo débil a ese elemento).

## Progresión de nivel
- [x] **Nivel 1→2 mucho más barato** (a petición del usuario, para dar sensación de progreso rápido justo al empezar y luego ralentizarse como en otros juegos): `Player.required_xp()` para el nivel 1 baja de 40 a **8 XP** — el mínimo que da incluso la primera victoria contra el Goblin (`gold_min=4 * 2` = 8 XP), así que la primerísima pelea del juego siempre sube de nivel, sin depender de la suerte del oro. Confirmado con 30 combates simulados: nivel 2 el 100% de las veces tras 1 sola victoria.
- [x] **Suavizado el resto de la curva temprana** (a petición del usuario, tras notar que aunque el nivel 1→2 costaba solo 8 XP, el 2→3 ya pedía 375 — un frenazo demasiado brusco justo después del subidón inicial). En vez de tocar solo el nivel 1 y dejar el resto de la fórmula intacta, se añadió un "descuento" (`damping`) sobre la fórmula normal que empieza al principio (nivel 2) y se va cerrando de forma lineal hasta llegar al 100% (la curva de siempre, sin cambios) en el nivel 10 en adelante — así no hay ningún salto brusco entre niveles, y el ritmo de nivel alto (que ya estaba calibrado en el playtest del tramo final de la cadena de enemigos) no se toca.
- [x] **Nivel 1→2 vuelve a 8 XP, nivel 2→3 calculado a ~50 XP** (el usuario pidió primero subirlo a 15, luego probó otra idea: volver el 1→2 a 8 pero que el 2→3 quedara en un punto intermedio "calculado", entre los 14 XP que daba el descuento anterior y los 98 XP de la curva original sin suavizar). Calculado exactamente: `98.68 (coste base sin descontar en nivel 2) * 0.5 ≈ 49` — así que el descuento del nivel 2 pasa a arrancar en 50% (antes 18%) en vez de un número improvisado. El resto de niveles (3-9) siguen la misma rampa lineal hasta el 100% en el nivel 10, solo cambia el punto de partida.
  - **Bug real encontrado y corregido durante el primer intento (nivel 1→2 = 15)**: `Player.gain_experience()` nunca resetea `self.experience` — es un umbral acumulado que se compara contra `required_xp()`, no un coste que se descuenta al subir de nivel. Eso significa que `required_xp()` **tiene** que ser no decreciente con el nivel, o una sola pelea pequeña podría subir dos niveles de golpe por accidente. Arreglado con `Player._required_xp_for_level()` (la fórmula + descuento, extraída a un método aparte) y un `max()` contra el umbral del nivel anterior en `required_xp()`, para que la curva completa quede garantizada como no decreciente pase lo que pase con los parámetros del descuento — se mantiene con los valores actuales aunque ya no hiciera falta forzarlo (8 y 49 ya son crecientes por sí solos), como red de seguridad ante futuros ajustes.
  - Curva final: 8, 49, 211, 561, 1184, 2162, 3576, 5496, 7983 XP para los niveles 1→2 hasta 9→10, convergiendo con la fórmula original en el tramo 10-14 (~11000-24000 XP/nivel).

## Interfaz de combate
- [x] **Pausa tras ganar un combate** (a petición del usuario, le pasó que se le coló un objeto conseguido porque el menú reescribía la pantalla encima del resumen de victoria). `_handle_defeat()` ya tenía su propio `console.ask("Presiona Enter para volver...")`, pero `_handle_victory()` no — tras imprimir ¡VICTORIA!, el enemigo desbloqueado, el oro, la XP, el botín y la curación post-combate, `initiate_battle()` volvía directo al menú sin pausa. Añadido un `console.ask("Presiona Enter para continuar...")` al final de `initiate_battle()`, solo en la rama de victoria (huir y derrota no lo necesitan: huir apenas imprime nada, y derrota ya pausaba).
- [x] **Color del número de daño del jugador** (a petición del usuario): el número de daño en `combat/battle.py::_execute_turn` (el ataque estándar del jugador) ahora es **cian** en un golpe normal, y se reserva el **amarillo en negrita** solo para el crítico (mismo estilo que el mensaje "¡Golpe crítico!" que ya se mostraba encima). Antes todos los golpes, críticos o no, usaban el mismo amarillo sin negrita. Los ataques de los enemigos no se han tocado (ese texto vive en cada `enemies/*.py` por separado, siguen en rojo).

## Sistema de acierto
- [x] **`BASE_HIT_CHANCE` cambiado de 90 a 100** (a petición del usuario, tras preguntar por qué esquivaba ataques del Goblin con evasión 0 — la respuesta es que la base del 90% dejaba un margen de fallo incluso sin evasión, cosa que al usuario no le convencía como diseño). Ahora, con evasión 0, el atacante acierta siempre; la evasión del defensor es la única fuente real de esquivar. `MIN_HIT_CHANCE` (suelo del 5%) se mantiene igual. Actualizado el test `test_enemy_default_perform_turn_deals_no_damage_on_a_miss` (forzaba un fallo con `random()=0.99`, que ya no basta por sí solo contra evasión 0 — ahora también sube la evasión del jugador a 50 en ese test).
- [x] **Recalibrado el Goblin tras el cambio de acierto** (playtest de 1500 combates, jugador recién creado a vida completa vs. Goblin recién desbloqueado): el cambio de acierto por sí solo ya sube la tasa de victorias del jugador de ~82% a **~93-95%**, sin tocar ninguna stat del Goblin — de hecho el cambio ayuda más al jugador que al enemigo, porque la precisión base del jugador (0) estaba más lejos del 100% que la del Goblin (precisión 5), así que el jugador gana más puntos de acierto proporcionalmente. No hizo falta ningún ajuste adicional de stats para llegar a "casi siempre gana el jugador".
- ⚠️ **Pendiente de decidir**: este cambio es global (afecta a los 14 enemigos, no solo al Goblin), y toda la cadena estaba calibrada asumiendo la base del 90% (ver el historial de playtest más abajo, "Nuevos Enemigos"). No se ha vuelto a calibrar el resto de la cadena todavía — habría que repetir el mismo tipo de playtest instrumentado para cada enemigo si se quiere mantener el rango de dificultad 73-98% documentado originalmente.

## Tienda
- [x] **La tienda no mostraba las estadísticas de armas/armadura/Poción de Fuerza al comprar** (a petición del usuario, jugando una partida). Cada tipo de objeto ya implementaba `get_stats_info()` (usado en el inventario y en la herrería), pero `ShopItem.__str__` en `shop/shop.py` solo imprimía `template.description` sin llamarlo — por eso la Poción de Salud/Regeneración "funcionaban" (su descripción de texto ya incluye los números a mano, "Restaura 20 HP"), pero la Espada de Hierro, la Armadura de Cuero y la Poción de Fuerza (descripciones puramente de sabor, sin números) no mostraban nada. Arreglado añadiendo `[{template.get_stats_info()}]` al listado de compra, mismo patrón que ya usa `CraftingRecipe.__str__` en la herrería.

## Empaquetado (.exe)
- [x] **Generar un ejecutable con PyInstaller** (a petición del usuario, para probar el juego fuera de PyCharm). Comando: `pyinstaller --onedir --name Valeterna --add-data "assets;assets" main.py` (ver README.md). Probarlo reveló dos bugs reales, no solo del empaquetado — ya afectaban a `python main.py` ejecutado fuera de una consola UTF-8 como la de PyCharm:
  - **`config/paths.py` no funcionaba empaquetado**: `BASE_DIR` se calculaba con `Path(__file__).resolve().parents[3]`, que asume la estructura `src/valeterna/...` del repo — dentro de un bundle de PyInstaller eso apunta a un sitio sin sentido. Ahora detecta `sys.frozen` y usa la carpeta del `.exe` para `BASE_DIR` (así `config.ini`/`saved_games/` persisten junto a él) y `sys._MEIPASS` para `ASSETS_DIR`. Confirmado con el build real: crea `config.ini` y `saved_games/PruebaExe.sav` junto al `.exe`, no en una carpeta temporal.
  - **`UnicodeEncodeError` con los emojis del menú** (p. ej. "⚔️ MENÚ PRINCIPAL ⚔️") en cualquier consola de Windows con code page heredada (el `.exe` fuera de un IDE, o `cmd.exe` normal) — PyCharm usa UTF-8 por defecto, por eso no se veía antes. Arreglado forzando `sys.stdout`/`sys.stderr` a UTF-8 al principio de `app.py::main()`, antes de que `colorama.init()` envuelva los streams.
  - **`NameError: name 'exit' is not defined`** al pulsar "Salir": el código usaba el `exit()`/`quit()` que solo existe como conveniencia del intérprete interactivo (los añade el módulo `site`), y no está disponible en un build congelado de PyInstaller. Cambiado a `sys.exit()` en las dos opciones de menú que salen del juego (`ui/menus.py`).
  - Hay que usar `--onedir`, no `--onefile`: con `--onefile` el juego se descomprime en una carpeta temporal distinta cada vez que arranca, así que las partidas guardadas y el volumen no persistirían entre ejecuciones (aunque el fix de `BASE_DIR`/`sys.executable` esté aplicado).
  - `*.spec` añadido a `.gitignore` (se regenera con el mismo comando, igual que `dist/`/`build/`, que ya estaban ignorados).

## Bestiario
- [x] **Contador de veces derrotado por enemigo** (a petición del usuario). Nuevo `Player.enemy_kill_counts: dict[str, int]`, incrementado en `combat/battle.py::_handle_victory()` en **cada** victoria (a diferencia de `defeated_enemies`, que solo marca la primera vez). Mostrado como "Veces derrotado: N" al principio de la ficha en `print_bestiary_entry()`. Persistido en el guardado; las partidas guardadas antes de este cambio rellenan como mínimo 1 por cada enemigo que ya estuviera en `defeated_enemies` (no se puede saber el número real, pero es mejor que mostrar 0 para un enemigo ya derrotado). El personaje "admin" de pruebas también arranca con 1 por cada enemigo pre-derrotado, por coherencia.
- [x] **Nueva opción de menú "Bestiario"** (a petición del usuario), solo lectura, listada en `game_loop` junto a Tienda/Herrería/Estadísticas. Muestra únicamente los enemigos que ya están en `defeated_enemies` — un enemigo desbloqueado pero no derrotado todavía no aparece en absoluto en la lista, ni siquiera como "???" (así lo pidió el usuario: "solo cuando se han derrotado"). Implementado como `_bestiary_flow()` en `ui/menus.py` (mismo patrón interactivo que `_equip_armor_flow`) + `print_bestiary_entry()` en `ui/formatting.py`, que reutiliza `_get_enemy_instance()` para construir una instancia "limpia" del enemigo (sin arrastrar HP actual de un combate). La ficha muestra stats de combate completos (vida máxima, ataque, armadura/resistencia mágica, velocidad, precisión/evasión, crítico, penetración, regeneración si tiene), la debilidad elemental (`ELEMENTAL_WEAKNESSES`) si la tiene, y el rango de oro que suelta. Deliberadamente **no** incluye la tabla de drops de objetos/materiales (`drop_item()` no expone sus probabilidades de forma estática sin duplicar esa información y arriesgarse a que se desincronice del código real).

## Sistema de Economía (Tienda)
- [x] Crear clase `Shop` con inventario propio.
- [x] Implementar comando `vender` en el menú de la ciudad.
- [x] Lógica para que los ítems tengan un precio de compra y otro de venta.

## Sistema de Forja (Crafting)
- [x] Crear `CraftingRecipe` que pida (Material + Oro).
- [x] **RECETA ESPECIAL:** 1x Piel de Troll + 200 Oro = *Armadura Regenerativa*.
- [x] Añadir submenú "Herrería" en la ciudad.
- [x] Añadir más recetas (una por hueco de armadura nuevo, reutilizando los materiales comunes).
- [x] Dar a la Armadura Regenerativa su efecto de regeneración real por turno: ahora usa el bonus `regen` de `Armor` (+8 HP/turno) sumado en `Player.get_total_regen()` y aplicado en `Player.on_turn_start()` — ver el nuevo stat "Regeneración de Salud" más abajo.
- [ ] **Pendiente: revisar la coherencia de nombres de objetos (materiales / armas / armaduras).** Varios materiales suenan a objeto equipable y su receta no pega con el nombre: p. ej. "Capa de Sombras" es un `Material` (suena a Peto) y con él se craftea una Daga Envenenada + unas Perneras de Placa. Ahora que el resumen de botín de la cadena (`_print_chain_loot`) y el bestiario etiquetan el tipo, se nota más. Pasada de renombrado + revisión de recetas cuando toque el pase de contenido/mundo (v0.12+). Los nombres actuales son provisionales.

## Mejoras de Combate
- [x] Implementar daño elemental (Fuego vs. Troll).
- [x] Añadido Rayo, Veneno y Hielo reutilizando `Enemy.ELEMENTAL_WEAKNESSES` (mismo patrón que Fuego/Troll, sin tocar `combat/battle.py` ni `take_damage()`, ya estaban preparados para cualquier string de elemento). Nuevas debilidades: `Bandido` → Veneno (x2.0, "es de carne y hueso"), `Gólem de Piedra` → Rayo (x2.0, "la piedra empapada de minerales conduce mejor que la carne"), `Dragón` → Hielo (x2.0, el clásico dragón de fuego débil al hielo). Cada elemento tiene ya al menos un arma que lo inflige, sin depender del enemigo débil a él (igual que el fuego, que ya soltaban Orco/Dragón/Demonio sin relación con el Troll): `Huargo` suelta "Colmillo Venenoso" (veneno), `Gárgola` suelta "Garra de Tormenta" (rayo), `Nigromante` suelta "Cetro de Escarcha" (hielo) — las tres al 8-10%, en línea con el resto de armas raras de esos enemigos.

## Slots de Equipamiento (estilo Diablo 3)
- [x] 8 huecos de armadura (casco, hombreras, peto, brazales, guantes, cinturón, perneras, botas) además del arma.
- [x] Cada hueco puede dar un tipo de bonus distinto (armadura, vida, resistencia mágica, crítico, elemento).
- [x] Sistema de golpe crítico (probabilidad + multiplicador).
- [x] Recetas de crafteo para llenar los huecos que no tenían ningún objeto todavía.
- [x] 2 huecos de anillo (comparten "tipo" pero son huecos independientes) + amuleto.
- [x] Bonus de daño plano en equipo (no solo en el arma), para los anillos.
- [x] Objetos que sueltan los enemigos por combate para los huecos que solo tenían receta de crafteo: cada uno de los 11 huecos tiene ahora al menos un enemigo que lo suelta — Huargo→botas, Troll→hombreras, Espíritu Vengativo→brazales, Bandido→guantes, Gólem de Piedra→cinturón, Demonio→perneras, Mago→anillo, Ángel Caído→anillo (más los que ya soltaban casco/peto/amuleto: Esqueleto, Orco/Gárgola/Gólem/Demonio, Nigromante).
- [x] **Revisado el reparto de bonus de hombreras/cinturón/perneras/amuleto** a petición del usuario. Tras la pasada de variedad de drops (ver más abajo), los cuatro huecos ya tenían 3 opciones cada uno con arquetipos bien diferenciados (hombreras: regeneración vs. armadura pura vs. híbrido; perneras: armadura+resistencia mágica vs. velocidad vs. armadura ligera; amuleto: resistencia mágica+crítico vs. armadura+daño físico vs. híbrido) — no hacía falta tocarlos. La única inconsistencia real encontrada fue en **cinturón**: la receta crafteable "Cinturón de Resistencia" daba `max_health=20`, exactamente el mismo valor que el drop del Gólem ("Cinturón de Roca", `defense=4, max_health=20`) — el drop dominaba estrictamente al objeto crafteado (mismos 20 HP + 4 de armadura gratis), sin ningún motivo para craftearlo nunca. Corregido dándole un rol propio: ahora da `max_health=15, magic_resist=4` (resistencia mágica en vez de armadura física), así el jugador elige entre tanque físico (Gólem), velocidad (Huargo) o resistencia mágica (crafteo) según a qué enemigo se enfrente. De paso se reforzó ligeramente "Perneras de Placa" (craft, antes solo `defense=3`) a `defense=3, max_health=12` para que no se quedara tan atrás de sus dos alternativas de drop.
- [x] **Pasada de variedad/tasas de drop de equipamiento** (a petición del usuario, tras auditar los 14 `drop_item()`): todos los enemigos ya soltaban oro siempre (`Enemy.get_gold_drop()` se llama incondicionalmente en `combat/battle.py`, fuera de `drop_item()`) y casi todos ya soltaban al menos un material de crafteo, así que el trabajo real fue (1) bajar **todas** las probabilidades de `Weapon`/`Armor` a ≤10% — varias estaban en 12-20% (Hacha de Batalla del Orco 20%, Casco de Hueso 18%, varios petos/armas a 15%) — y (2) añadir variedad real donde solo había 1-2 objetos por hueco. Los huecos que antes solo tenían la opción de crafteo + un único drop (hombreras, brazales, guantes, cinturón, perneras, botas, amuleto) tienen ahora **2 fuentes de drop distintas cada uno** (3+ opciones contando la receta), con estadísticas contrastadas a propósito para que la elección dependa de la situación, no solo de "el mejor número": p. ej. botas — Huargo da velocidad pura, Gólem da resistencia con velocidad 0 (`Botas de Gólem`); cinturón — Gólem da vida/armadura, Huargo da velocidad (`Cinturón de Manada`); perneras — Demonio da armadura pesada, Bandido da velocidad (`Perneras de Bandido`); brazales — Espíritu Vengativo da resistencia mágica, Orco da daño plano sin elemento (`Brazales de Guerra`, contraste con los Brazales Arcanos con fuego de la herrería); amuleto — Nigromante da resistencia mágica, Dragón da armadura+daño físico (`Amuleto de Escama de Dragón`); guantes — Bandido da crítico, Esqueleto da resistencia mixta (`Guantes Óseos`); hombreras — Troll da regeneración, Gólem da armadura pura (`Hombreras de Gólem`); casco pasó de 2 a 3 opciones con `Capucha de Ladrón` del Bandido (crítico + velocidad, contraste ágil frente al tanque del Esqueleto y el híbrido mágico del Ángel Caído). El peto y los anillos ya tenían bastante variedad (6-7 y 5 opciones respectivamente) y no se tocaron más allá de bajar sus tasas de drop.
- [x] Ahora hay 5 anillos distintos (Fuerza/Precisión/Vitalidad craftables + Anillo Arcano del Mago/Anillo de Juicio del Ángel Caído como drop) — sigue sin poder llevarse dos copias del mismo anillo (`Inventory.add_item()` auto-vende el duplicado), pero ya hay más variedad real para combinar en los dos huecos.
- [x] **Bonus de velocidad en el slot "botas"**: `Armor` gana un campo `speed` (sumado en `Player.get_total_speed()`, mismo patrón que `get_total_armor()`/`get_total_regen()`). La receta "Botas Ligeras" ahora da `speed=3` además de su bonus de crítico existente, y el drop nuevo de Huargo ("Botas de Huargo") da `speed=2` — confirmado con una prueba de extremo a extremo (craftear + equipar sube la velocidad de 10 a 13).
- [x] **Recetas ocultas hasta descubrir sus materiales, cobertura de materiales y cantidades de farmeo real** (a petición del usuario, tras jugar una partida nueva y ver la herrería). Tres cambios:
  - **Descubrimiento de recetas**: `Inventory` gana un `discovered_materials: set[str]`, que se actualiza en `add_item()` cada vez que el jugador consigue un `Material` por primera vez (permanece descubierto aunque luego se gaste craftando — no depende del stock actual). `CraftingRecipe.is_discovered(player)` comprueba que **todos** los materiales de la receta estén en ese set; `Forge.open()` ahora solo lista las recetas descubiertas (y muestra cuántas quedan por descubrir), en vez de enseñar las 11 de golpe desde el principio. Persistido en el guardado (`discovered_materials` en `persistence/save_load.py`), con compatibilidad hacia atrás: las partidas guardadas antes de este cambio recuperan como "descubiertos" los materiales que tengan en el inventario en ese momento.
  - **Cobertura de materiales**: de los 14 materiales (uno por enemigo, ya existían todos — el problema real no era que faltaran drops, sino que solo 5 se usaban en alguna receta: Colmillo de Goblin/Orco, Fragmento de Hueso, Esencia Arcana, Piel de Troll). Revisadas las 11 recetas para que las 9 que sobraban (Colmillo de Huargo, Capa de Sombras, Esencia Espectral, Fragmento de Gárgola, Núcleo de Gólem, Polvo de Hueso Negro, Pluma Corrupta, Ceniza Infernal, Escama de Dragón) entren como material adicional en alguna receta existente, con una asociación temática cuando ha sido posible (p. ej. Colmillo de Huargo en "Botas Ligeras", ya que el Huargo es el enemigo "rápido"; Escama de Dragón en "Anillo de Vitalidad").
  - **Cantidades de farmeo**: las cantidades pasan de x1/x2 a cifras que fuerzan farmear al enemigo correspondiente, escaladas según lo raro que sea el drop y lo difícil que sea la pelea (no un número plano para todos): materiales "comunes" de enemigos tempranos/de tasa de drop 20-35% → x25; materiales de enemigos de tramo medio-alto (Gárgola, Gólem, Nigromante, Ángel Caído, Demonio) → x15 (mismo rango de drop, pero peleas bastante más duras, así que se pide menos cantidad); Esencia Arcana (Mago, 10% de drop) → x8; Piel de Troll (5% de drop, la más rara del juego) → x2; Escama de Dragón (35% de drop pero del jefe final, la pelea más difícil) → x5.
- [x] **Añadida un arma craftable** (a petición del usuario, tras darse cuenta de que las 11 recetas de la herrería eran todas de armadura, ninguna de arma): "Daga Envenenada" (`Colmillo de Huargo` x25 + `Capa de Sombras` x25, 45 oro), un `Weapon` con `element="veneno"` — segunda vía para conseguir un arma de veneno además del drop del Huargo ("Colmillo Venenoso"), mismo patrón que "Brazales Arcanos" ya daba una vía craftable alternativa al fuego. 12 recetas en total ahora.

- [ ] **Conjuntos de equipamiento (sets)**: bonus adicional por llevar puestas varias piezas del mismo set temático (2 piezas → bonus pequeño, 4 piezas → bonus mayor, 6 piezas → el máximo). Comentado con el usuario pero todavía sin diseñar: no existe hoy ningún concepto de `set` en `Armor`, cada pieza de equipo es completamente independiente. No es prioritario por delante de tener buena variedad de objetos individuales (ver la pasada de drops más abajo), pero queda anotado para abordarlo cuando toque. Pendiente de decidir: qué piezas forman cada set (¿por enemigo? ¿por tema, ej. "set de Dragón" repartido entre varios drops del Dragón?), cómo se detecta "N piezas equipadas del mismo set" en `Player`, y qué tipo de bonus dan los tramos 2/4/6 (¿stats planos, como los bonus actuales, o algo nuevo como un efecto pasivo?).

## Nuevos Enemigos (ideas del usuario)
- **Cadena de progresión completa** (los 9 enemigos nuevos ya insertados, no solo añadidos al final): Goblin → **Huargo** → Esqueleto → **Bandido** → Orco → **Espíritu Vengativo** → Troll → **Gárgola** → **Gólem de Piedra** → Mago → **Nigromante** → **Ángel Caído** → **Demonio** → **Dragón**. 14 enemigos en total, todos jugables, todos calibrados con el playtest instrumentado (rango 73-98% de victorias del jugador nada más desbloquear cada uno, con el Dragón —jefe final— en el extremo duro de esa franja, 73%, a propósito).
- **Fórmula usada para calibrar enemigos "lentos/tanque"** (Gárgola, Gólem): como el ATB reparte turnos por velocidad relativa, la condición de equilibrio 50/50 es `hp_enemigo * speed_enemigo * daño_neto_enemigo ≈ hp_jugador * speed_jugador * daño_neto_jugador` (daño_neto = daño medio − mitigación efectiva). Subir la vida del enemigo NO cambia este ratio (alarga la pelea para los dos por igual); solo `speed_enemigo` y `daño_neto_enemigo` mueven la aguja. Apuntar a un daño_neto ~10-15% por debajo del umbral de 50/50 da un ~75-90% de victorias del jugador, la franja donde ha caído el resto de la cadena ya calibrada.
- [x] **Huargo** (`characters/enemies/huargo.py`): rápido y evasivo pero frágil (poca vida/armadura). A veces un segundo lobo se suma con un "mordisco de manada" (20% de probabilidad, medio daño, con su propia tirada de acierto). Reequilibrado tras playtest: primera versión (speed=16, evasion=10) daba solo 7% de victorias al jugador nada más desbloquearlo (demasiado duro justo después del Goblin); bajado a speed=13, evasion=4, crit_chance=0.05 → 81% en la misma prueba.
- [x] **Bandido** (`characters/enemies/bandido.py`): emboscada igual que el Goblin (35%) + intento de "Desarme" (25% de las veces en vez de atacar): aplica el nuevo status `"desarmado"` (2 turnos) que anula el bonus de daño del arma equipada (`Player.get_attack_range()`), reutilizando el sistema genérico de duración/expiración de estados que ya existía. Reequilibrado tras playtest: primera versión (HP65, ATK10-16, ARM3) ganaba el jugador el 100% de las veces nada más desbloquearlo; subido a HP85, ATK13-19, ARM5, crit_chance=0.10 → 94% en la misma prueba.
- [x] **Espíritu Vengativo** (`characters/enemies/espiritu_vengativo.py`): incorpóreo, poca armadura propia pero `armor_penetration=8` (sus "proyectiles espectrales que atraviesan la armadura"). 25% de las veces, en vez de atacar, lanza una **maldición** (nuevo status `"maldicion"`, 3 turnos, resta 4 a `Player.get_total_armor()` mientras dure, con suelo en 0 — mismo patrón que "desarmado" del Bandido). HP210, ATK18-26, crit_chance=0.08.
- [x] **Gárgola** (`characters/enemies/gargola.py`): resistente (armadura 14) pero lenta; cada 3 turnos, en vez de un zarpazo normal, hace una **Embestida** (x1.8 de daño, con su propia tirada de acierto). HP380, ATK29-39, armor_penetration=8.
- [x] **Gólem de Piedra** (`characters/enemies/golem.py`): la armadura más alta de todos los enemigos (20). Un turno de cada cinco, en vez de golpear, provoca un **Terremoto** que salta la tirada de acierto por completo (no se puede esquivar, "sacude el suelo"). HP450, ATK42-54, armor_penetration=12. Calibrado con el playtest habitual, ecuación de referencia incluida abajo: **73%** de victorias del jugador nada más desbloquearlo.
- [x] **Nigromante** (`characters/enemies/nigromante.py`): su ataque habitual (`_dark_bolt`) es **mágico** (`is_magical=True`), no físico — el primer enemigo aparte del Mago que usa `magic_resist`/`magic_penetration` de verdad. 20% de las veces invoca un esqueleto que ataca físico de inmediato (aprovechando el mismo patrón de "golpe extra" que ya usan Huargo/Gárgola, ya que el sistema de combate no soporta varios enemigos a la vez). Ahora sí calibrado con el playtest automático real (el Mago ya es superable, ver más abajo): HP320, ATK48-64, speed=23, magic_penetration=8 → **78%** de victorias del jugador nada más desbloquearlo.
- [x] **Reequilibrado el Mago** (por fin — era el enemigo roto desde hacía varias sesiones, 0% de victorias del jugador). La causa real no era el daño de los hechizos en sí, sino la posición en la cadena: antes iba justo después del Troll (el jugador llegaba pronto, con poca velocidad, así que el Mago sacaba mucha ventaja); ahora, con Gárgola y Gólem por delante, el jugador llega mucho más tarde (nivel ~11) y mucho más rápido — con la velocidad original del Mago (12) eso lo dejaba casi sin turnos y lo volvía **demasiado fácil (92%)**. Subir la velocidad de golpe a 20 (para cerrar ese hueco) lo volvió otra vez casi imposible (27%): la autocuración (40-60 HP si baja del 50%, 40% de probabilidad) hace que más turnos para el Mago no sea un efecto lineal, sino que se retroalimenta (más turnos → más curaciones → la pelea dura más → más turnos todavía). Ajuste final, con margen para esa no-linealidad: speed=15, magic_penetration=4 (daño de los hechizos sin tocar) → **73%**.
- La lección del Mago se confirmó con el Ángel Caído (ver más abajo): un enemigo que se autocura no se calibra igual que uno que no, porque cada punto de velocidad de más vale más de lo que parece por la retroalimentación (más turnos → más curaciones → pelea más larga → más turnos todavía). Hay que subir la velocidad en pasos pequeños y remedir cada vez, no ir a lo grande.
- [x] **Ángel Caído** (`characters/enemies/angel_caido.py`): ataque habitual mágico + autocuración (30% con vida ≤40%, más conservadora que el 40%/≤50% del Mago) + **Juicio Divino** ocasional (15%, x1.6 de daño). Confirmó la lección del Mago: con speed=22 salió 31% (demasiado duro, la autocuración se retroalimenta con la velocidad), con speed=17 salió 98% (demasiado fácil) — el punto correcto fue un valor intermedio, speed=19 con ATK44-60 → **77%**.
- [x] **Demonio** (`characters/enemies/demonio.py`): además de un zarpazo normal, 20% de las veces invoca un demonio menor (golpe mágico extra, mismo patrón que Nigromante/Huargo/Gárgola) y 20% de las veces lanza **Confusión** (nuevo status `"confusion"`, 3 turnos, resta 5 a `Player.get_total_evasion()` — mismo patrón que "maldicion"/"desarmado"). HP420, ATK58-76, armor_penetration=20 (el más perforante con diferencia, "garras infernales"), speed=27 → **77%**.
- [x] **Dragón** (`characters/enemies/dragon.py`, jefe final de la cadena): vida masiva (700, la más alta con diferencia) y evasión "de vuelo". 25% de las veces, en vez de zarpazo/mordisco, exhala un **Aliento de Fuego** (`is_fire=True`, 60% de probabilidad de aplicar quemadura de 3 turnos — daño a lo largo del tiempo, reutilizando el status "quemado" que ya existía). Primer intento con evasion=16 (la más alta de todos los enemigos, pensada para el "esquiva volando") resultó desastroso: **6%** de victorias del jugador — con la precisión del jugador siendo baja a esas alturas, una evasión tan alta le hacía fallar muchísimos golpes, y eso combinado con el resto de sus stats lo volvía casi invencible. Bajado a evasion=6, ATK45-62, armor_penetration=6 → **73%**, apropiadamente en el extremo duro de la franja por ser el jefe final.
- Nota de metodología: medir "dificultad justo al desbloquear" con una sola partida congelada da resultados muy inestables según la suerte de drops (una misma prueba dio 69% y luego 3% de victorias entre dos ejecuciones). Los números de arriba salen de promediar 5 partidas independientes x 30 combates cada una — mucho más fiable.
- **Hallazgo importante para los enemigos que faltan** (Gólem, Nigromante, Ángel Caído, Demonio, Dragón): la velocidad del jugador sube con cada nivel (~+1.5/nivel; nivel 6 ≈ 18, nivel 8 ≈ 21), pero como el sistema ATB reparte turnos según velocidad *relativa* (no solo el orden), un enemigo con una velocidad "de principio de partida" (5-10) se queda casi sin turnos frente a un jugador de nivel alto, por mucha vida o daño que tenga. Primer intento de Espíritu Vengativo/Gárgola con velocidades bajas (11 y 4) dio 100% de victorias del jugador pese a subirles mucho la vida — subir la vida de un enemigo lento **no ayuda a su tasa de victorias** (solo alarga la pelea para los dos por igual); lo que de verdad importa es acercar su velocidad a la del jugador esperado en ese punto y/o subirle el daño por golpe. Subida la velocidad de Espíritu Vengativo a 17 y la de Gárgola a 9 (con más daño y `armor_penetration`) para que puedan competir de verdad. De paso se subió también la velocidad del Troll (5→10, seguía sin apenas actuar por el mismo motivo) aunque su reequilibrio completo sigue pendiente.

## Estadísticas Extendidas (jugador y enemigos)
- [x] **Reequilibrado el Goblin** tras un playtest instrumentado (40+ combates simulados con `time.sleep` acelerado): con los valores originales de esta sesión (speed=14, evasion=8, crit_chance=0.10) el Goblin —pensado como el enemigo tutorial más fácil— ganaba ~60-70% de los combates contra un jugador de nivel 1-2, más que el Esqueleto (el siguiente enemigo, en teoría más difícil). Bajado a speed=11, evasion=3, crit_chance=0.05 (precision=5 y armor_penetration=1 sin cambios); repitiendo el mismo playtest el ratio de victorias del jugador pasa a ~65-85% y la progresión de nivel es notablemente más rápida.
- [x] Velocidad + sistema de turnos ATB (barra de "gauge" estilo Final Fantasy X, no una simple alternancia 1 a 1): `Stats.speed`, `Player.get_total_speed()`, y `combat/battle.py` acumula un gauge por combatiente (`ATB_THRESHOLD`) que se llena a un ritmo proporcional a la velocidad, permitiendo que el más rápido actúe varias veces antes de que el más lento tenga su primer turno. Iniciativa se fusionó con Velocidad (no tiene sentido como stat separada en un combate 1 vs 1; revisar si hace falta separarla el día que haya combates con varios enemigos).
- [x] Huir ahora depende de la velocidad relativa (`_attempt_flee`, fórmula `min(1.0, player_speed / enemy_speed)`: 100% si el jugador iguala o supera la velocidad del enemigo, si no baja pero nunca llega a 0%) y siempre se resuelve antes que cualquier otra acción del enemigo en el mismo tick, sea el jugador más rápido o más lento.
- [x] Al subir de nivel, `Player._level_up()` ahora también sube `speed` — junto con vida/ataque/armadura, con una curva de crecimiento **determinista pero no uniforme** (`Player._growth_gain`, inspirada en cómo Pokémon calcula stats por nivel: `floor(tasa * nivel) - floor(tasa * (nivel-1))` con una tasa fraccionaria por stat, p.ej. armadura a 1.4/nivel da la secuencia fija 1,2,1,2,1...). Así la progresión varía de nivel en nivel (unos dan más ataque, otros más armadura/velocidad) pero es exactamente igual en todas las partidas, no aleatoria. La resistencia mágica sigue siendo fija (+1, solo niveles pares) porque es un ajuste de balance deliberado contra el Mago, no "crecimiento genérico". Crítico (probabilidad y daño), regeneración de salud y penetración de defensa quedan fuera de la progresión por nivel a propósito: solo se conseguirán vía objetos/equipo.
- [x] Precisión y Evasión: tirada de acierto compartida (`characters/stats.py::resolve_hit`, importada tanto por `combat/battle.py::_execute_turn` como por `characters/enemies/enemy_base.py::Enemy.perform_turn` — vive en `stats.py`, un módulo hoja, para que ambos la usen sin crear un ciclo de imports). Parte de un 90% de acierto base (`BASE_HIT_CHANCE`), cada punto de diferencia precisión-evasión suma/resta 1%, con suelo del 5% y techo del 100% (`MIN_HIT_CHANCE`/`MAX_HIT_CHANCE`). Un fallo no llega a tocar armadura/elemento/crítico, se resuelve el primero. `Player.get_total_precision()`/`get_total_evasion()` ya existen (solo stat base, igual que velocidad).
- [x] Crit Chance y Crit Damage para enemigos: `Stats.crit_chance`/`crit_damage` ya no son exclusivos del jugador — cada enemigo tiene sus propios valores (Goblin 10%/x1.6, Esqueleto 5%/x1.5, Orco 8%/x1.75, Troll 3%/x1.5, Mago 12%/x1.6) y tanto `combat/battle.py::_execute_turn` (bifurca jugador con equipo vía `get_total_crit_*()` / enemigo con su stat base) como `Enemy.perform_turn()` (el ataque por defecto) ruedan el crítico y aplican el multiplicador.
- [x] Resistencia Mágica para enemigos: `Enemy.take_damage()` (y el override de `Skeleton`) ganan un parámetro `is_magical` que elige `magic_resist` en vez de `armor` para mitigar, igual que ya hacía `Player.take_damage()`. Valores por enemigo: Goblin 0, Esqueleto 2, Orco 1, Troll 1, Mago 15 (el más resistente, tiene sentido temático). **Importante — este stat todavía no tiene ningún efecto real en partida:** ningún ataque del jugador pasa `is_magical=True` hoy (no hay armas ni hechizos mágicos para el jugador, solo el Mago inflige daño mágico, y siempre contra el jugador, nunca al revés). Queda como infraestructura lista para cuando exista algo como un arma/hechizo mágico jugable — de momento verificado solo con tests directos a `Enemy.take_damage(is_magical=True)`.
- [x] **Cerrado el hueco de Orco en furia / hechizos del Mago**: eran los únicos ataques del juego que no pasaban por `resolve_hit` (siempre acertaban) ni por la tirada de crítico. El golpe devastador del Orco enfurecido (`orc.py`) ahora tira acierto contra la evasión del jugador y puede critear (el doblado de daño se sigue calculando sobre `player.get_total_armor()` con `armor_penetration`, en vez del `player.stats.armor` sin bonus de equipo que usaba antes — bug de paso). Los 4 hechizos del Mago (`mage.py`: Bola de Fuego, Rayo, Dardo de Veneno, Ventisca) ganan la misma tirada de acierto (si falla, no aplica daño ni estado) y la misma tirada de crítico con su `crit_damage`; la penetración mágica (`magic_penetration=4`) no cambia. La invocación de esqueleto del Nigromante y el demonio menor del Demonio ya pasaban por este sistema y no se han tocado.
- [x] Regeneración de Salud: nuevo `Stats.regen` (curación pasiva por turno, distinta del status temporal "regeneración" de las pociones — ambas pueden coexistir y se suman). El jugador tiene el stat base siempre a 0 y no sube al subir de nivel (a petición del usuario): solo se consigue vía objetos. `Armor` gana un campo `regen` sumado en `Player.get_total_regen()` y aplicado cada turno en `Player.on_turn_start()`. Dos fuentes ya craftables: Armadura Regenerativa (peto, +8, ver arriba) y el nuevo Anillo de Vitalidad (+2, receta con 2x Fragmento de Hueso). Para enemigos, `Enemy.on_turn_end()` aplica `self.stats.regen` de forma genérica (0 por defecto = sin efecto) para que futuros enemigos "aptos" lo hereden gratis sin código a medida; el Troll (el único "apto" hoy) mantiene su curación aleatoria pero ahora anclada al stat (`regen=10`, cura entre `regen-5` y `regen+5`, el mismo rango 5-15 que ya tenía) y sigue sobrescribiendo el mensaje para conservar su sabor propio.
- [x] Penetración de Armadura y Penetración Mágica (separadas a petición del usuario, en vez de una única "Penetración de Defensa"): `Stats.armor_penetration`/`magic_penetration`, `Player.get_total_armor_penetration()`/`get_total_magic_penetration()` (solo stat base por ahora). `Player.take_damage()` y `Enemy.take_damage()` (+ el override de `Skeleton`) reducen la mitigación del defensor con la penetración del atacante (`max(0, armadura_o_res.mágica - penetración)`) antes de restar el daño — nunca la vuelven negativa. Conectada en los dos sitios que ya reparten daño: `combat/battle.py::_execute_turn` (ataque físico del jugador) y `Enemy.perform_turn()` (ataque físico del enemigo) pasan `armor_penetration`; los 4 hechizos del Mago (`mage.py`) pasan `magic_penetration`. Valores: Goblin armor_pen=1 (esquiva defensas), Orco armor_pen=3 (el más perforante), Esqueleto/Troll=0, Mago magic_pen=3 (el único con efecto inmediato en partida real hoy, ya que es el único que inflige daño mágico). El Orco en furia sigue fuera (mismo hueco que precisión/evasión/crítico).
- [x] La velocidad ya suma bonus de equipo, no solo el stat base — ver "Bonus de velocidad en el slot botas" en la sección de Slots de Equipamiento, arriba.
## Clases y habilidades (v0.10.0) — números provisionales

Decisiones de diseño cerradas con el usuario en la revisión de §6.1/§6.2 del GDD
(ver §6.2.1 del GDD para el detalle completo). **Todos los números de aquí son
provisionales** y se recalibran en la fase de presupuesto de poder (v0.14), junto
con el rebalanceo completo de la cadena de 14 enemigos que ya quedó pendiente por
el cambio a mitigación multiplicativa.

- [ ] **Deltas de stats por clase** (sobre la base actual del Vagabundo, que no
  cambia):
  - Guerrero: +15% vida máx., +2 armadura base, +1 ataque mín./máx.; crecimiento
    de armadura x1.3.
  - Pícaro: +3 velocidad, +5% evasión, +5% prob. crítico, -10% vida máx.;
    crecimiento de velocidad x1.3.
  - Arcanista: -15% vida máx., -2 armadura base; stat nuevo `poder_magico` que
    crece cada nivel (tasa por definir; empezar ~2.0/nivel y medir).
- [ ] **`poder_magico`**: campo nuevo de `Stats`, 0 para el resto de clases. El
  ataque estándar del Arcanista en `_execute_turn` usa `poder_magico` como fuente
  de daño en vez del rango del arma y va con `is_magical=True`. Las armas le
  aportan stats secundarios y `element`, no daño base. Elemento por defecto:
  `arcano` (la pasiva Sintonía lo cambia al empezar el combate).
- [ ] **Niveles de desbloqueo provisionales**: habilidades M1 al crear (nivel 1),
  M2 al nivel 4. Exactos a v0.14.
- [x] **Motor de habilidades + hito M1** (v0.10.0-b): `characters/skills.py`
  (`Skill` dataclass + `CATALOG`, efectos guiados por `params`), menú
  "Habilidades" (`_skills_flow`), acción "Habilidades" en combate
  (`_choose_skill` / `_execute_skill`), enfriamiento por combate en un dict,
  auto-batalla usa una activa lista si la hay. M1 = 1 activa + 1 pasiva por clase
  (se aprende al crear). Nuevo estado `sangrado` (DoT físico, `max_health//12`).
  **Números provisionales sin verificar** (balanceo en v0.14):
  - Golpe Firme: a3, no falla, x1.4 daño. · Segundo Aliento: cura 12% vida máx. al matar.
  - Embate: a3, x1.5 daño, 40% aturdir 1 turno (reutiliza `paralizado`). · Piel de Piedra: -12% daño físico recibido.
  - Golpe Bajo: a3, crítico garantizado + `sangrado` 3 turnos. · Reflejos: +8 evasión plana (GDD decía "+12%", pendiente de cuadrar cómo se interpreta).
  - Proyectil Arcano: a2, mágico, `magic_penetration += 9999` (ignora la res. mágica). · Sintonía: elige elemento al empezar el combate (`Player.battle_element`, se limpia al terminar).
- [ ] **Balance: el ataque mágico del Arcanista salta la armadura.** Los ataques
  físicos pierden ~30-50% contra la armadura (fórmula multiplicativa), pero el
  ataque mágico se mitiga con `magic_resist`, que casi todos los enemigos tienen
  a 0-2. Con poder mágico y ataque físico comparables, el Arcanista pega bastante
  más en la práctica contra la mayoría de la cadena. Es en parte la fantasía de
  clase (el GDD quiere que la `magic_resist` importe), pero hay que darle a los
  enemigos algo de `magic_resist` o revisar el poder mágico en la pasada de
  presupuesto de poder (v0.14). De momento el admin arranca con `magic_power=25`
  (antes 40) para que el desajuste no sea tan bestia al probar.
- [x] **Hito M2** (v0.10.0-c): fila M2 de la tabla §6.2 (se aprende al nivel 4,
  provisional). Aguante (Aventurero: <30% vida → +15% armadura y res. mágica, en
  `_low_hp_defense_mult`), Represalia (Guerrero: 30% contraataque tras golpe
  físico, `_try_represalia` + `Player.took_physical_hit`), Veneno de Contacto
  (Pícaro: 20% envenenar al golpear, en `_execute_turn`), Escudo de Maná
  (Arcanista: activa a4 de utilidad, `Player.mana_shield` absorbe el próximo
  golpe). **Números sin verificar** — balanceo en v0.14.
- [ ] **Repensar "Veneno de Contacto"** (pasiva M2 del Pícaro). Envenenar
  *cuando te golpean* no encaja con un pícaro (eso es de un monstruo espinoso);
  envenenar *al atacar* ya lo cubriría una activa. Buscar otra pasiva para el
  hueco M2 del Pícaro. De momento se queda implementada y funcional.
- [ ] **Hitos M3-M7** (más adelante): filas M3-M7 de la tabla §6.2, atadas a
  guardianes de zona en la fase de mundo/presupuesto de poder.
- [ ] **Guardado**: v0.10.0 solo añade `clase` (back-fill "vagabundo") y
  `habilidades_equipadas` (back-fill []). El bloque `mundo` completo va en v0.12.0.
- [x] **v0.11.0-a: afinidades elementales reales para los 14 enemigos**
  (GDD §5). Antes solo el Gólem usaba el modelo nuevo (`WEAKNESSES`/
  `RESISTANCES`/`IMMUNE_ELEMENTS`/`IMMUNE_STATUSES`); Bandido, Troll y Dragón
  usaban el `ELEMENTAL_WEAKNESSES` antiguo (un único elemento a ×2.0, sin
  resistencias ni inmunidades); el resto no tenía ninguna afinidad. Migrados
  los 14 y **eliminado el modelo antiguo por completo** (ya no queda ningún
  `ELEMENTAL_WEAKNESSES` en el código). Tabla acordada con el usuario:
  Goblin/Huargo neutrales; Esqueleto débil sagrado, resiste veneno, inmune
  (estado) veneno/sangrado; Bandido débil veneno; Orco resiste veneno; Espíritu
  Vengativo débil sagrado, inmune (elemento+estado) veneno; Troll débil fuego;
  Gárgola débil arcano, inmune (elemento+estado) veneno; Gólem débil hielo,
  inmune (elemento+estado) rayo/paralizado; Mago resiste arcano, sin debilidad
  (su fragilidad ya está en su armadura, la más baja de su tramo — comprobado:
  6, frente a Gárgola 14 y Gólem 20 justo antes en la cadena); Nigromante débil
  sagrado, inmune (elemento+estado) oscuridad/marchito; Ángel Caído débil
  oscuridad, resiste sagrado; Demonio débil sagrado, resiste (no inmune, para
  diferenciarlo del Nigromante) oscuridad; Dragón débil hielo, inmune
  (elemento+estado) fuego/quemado (el "Dragón de Ceniza" del GDD es de fuego).
  **Regla de diseño fijada por el usuario:** inmune a un elemento implica
  inmune también al estado de ese elemento (`IMMUNE_STATUSES`), pero inmune a
  un estado NO implica inmune al elemento (el Esqueleto solo *resiste* el
  elemento veneno pero es inmune al *estado* veneno). Esto no es solo
  conceptual: la pasiva Veneno de Contacto del Pícaro llama a
  `enemy.apply_status("veneno", ...)` directamente en `_execute_turn` sin
  comprobar `affinity_for()` antes, así que sin el flag de estado explícito un
  enemigo "inmune al elemento" podría ser envenenado igualmente por esa vía.
  Como cambio de balance esperado: al pasar del ×2.0 fijo del modelo antiguo al
  ×1.5 estándar de una sola debilidad, Bandido/Troll/Dragón ahora reciben menos
  bonus por arma elemental que antes (subiría a ×2.0 solo si el golpe combinase
  dos elementos de debilidad a la vez, que hoy ninguno tiene). Sets de
  armadura (§6.3) y las nuevas armas elementales sagrado/oscuridad/arcano se
  aplazan a v0.11.0-b/v0.12.0 (los sets dependen de zonas/élites que no
  existen todavía).
- [x] **Ronda de feedback de v0.11.0-a** (probando veneno vs. Bandido/Esqueleto/
  Gárgola/Espíritu Vengativo, Veneno de Contacto y el Bestiario):
  - Reformulado el mensaje de resistencia: "{enemigo} resiste el {elemento}."
    → "{enemigo} es resistente al {elemento}." (a petición del usuario: el
    original daba a entender que no se le podía aplicar el elemento en
    absoluto, en vez de simplemente hacer menos daño — confusión especial con
    el Esqueleto, que sí resiste el elemento veneno pero además es inmune al
    *estado* veneno, el único caso hoy donde coinciden ambas cosas).
  - Quitado el mensaje redundante "{enemigo} ha bloqueado el ataque." cuando
    el golpe ya salió como inmune ("es inmune al {elemento}: el ataque no le
    hace nada.") — antes salían los dos seguidos y no quedaba claro a qué se
    refería cada uno. El mensaje de "bloqueado" se queda como red genérica
    para cualquier otra causa futura de daño 0 que no sea inmunidad elemental.
  - La pasiva Veneno de Contacto del Pícaro ahora avisa explícitamente
    ("{enemigo} es inmune al veneno.") cuando la tirada de probabilidad
    acierta pero el enemigo es inmune — antes se quedaba en silencio total,
    y el jugador no tenía forma de saber si la pasiva había fallado la tirada
    o si el enemigo era inmune.
  - Espíritu Vengativo, además de inmune al veneno, ahora también es inmune
    al estado `sangrado` (a petición del usuario: es incorpóreo, sin cuerpo
    físico que sangre, aunque el sangrado no está ligado a ningún elemento).
  - Quitada una línea en blanco de sobra en `_player_menu()` que aparecía
    entre la cabecera de turno (o el aviso "Eres más rápido") y las opciones
    numeradas — el turno del jugador quedaba con más aire que el del enemigo
    (que nunca tuvo ese hueco); ahora las opciones quedan pegadas igual en
    ambos casos.
  - Confirmado con el usuario que el modelo sí soporta que un enemigo tenga
    **tres** elementos distintos repartidos entre débil/resiste/inmune a la
    vez (p. ej. débil a rayo, resiste veneno e inmune a oscuridad) — los tres
    conjuntos son independientes; simplemente ningún enemigo actual usa esa
    combinación todavía. Posible ajuste para la pasada de 70 enemigos.
- [x] **v0.11.0-b: resistencia elemental en armadura + armas elementales
  nuevas** (GDD §5 y §6.4).
  - **Arreglado un hueco de raíz antes de poder añadir armas mágicas nuevas**:
    `combat/battle.py::_execute_turn` decidía si un golpe era mágico o físico
    mirando solo la clase del atacante (Arcanista) o si una habilidad lo
    marcaba (`magical`), nunca el elemento del arma en sí — así que alguien
    sin ser Arcanista con un arma sagrado/oscuridad/arcano seguía mitigándose
    con armadura, no con resistencia mágica, aunque el GDD dice que lo
    físico/mágico es propiedad del elemento. Usado `is_magical_element()`
    (ya existía en `combat/elements.py` pero no se llamaba desde ningún
    sitio) para que cualquier clase con un arma de esos 3 elementos golpee
    mágico, la lleve quien la lleve.
  - **Resistencia elemental en armadura, sistema nuevo, no un hueco a
    rellenar**: antes `Player.take_damage()` solo distinguía `is_fire`/
    `is_magical` (booleanos), sin ningún `element` genérico — el jugador no
    tenía ningún modelo de afinidad propio. Añadido `element` a
    `take_damage()`, `Armor.resist` (dict elemento→%, tope 75% sumado en
    `Player.get_total_resist()`), y etiquetado con su elemento cada ataque de
    enemigo que ya era claramente elemental: los 4 hechizos del Mago (bola de
    fuego, rayo, veneno, ventisca → fuego/rayo/veneno/hielo), el dardo oscuro
    del Nigromante (oscuridad), el golpe sagrado y el Juicio Divino del Ángel
    Caído (sagrado), el zarpazo y el demonio menor del Demonio (fuego, según
    su propio texto de sabor "daño ígneo"), y el aliento de fuego del Dragón
    (fuego). El resto de enemigos no tiene ataques elementales propios, así
    que no hacía falta tocarlos.
  - Repartida la resistencia nueva en 3 recetas de herrería ya existentes,
    eligiendo el hueco más afín temáticamente en vez de inventar objetos
    nuevos: Cinturón de Resistencia → arcano (su descripción ya decía "tanto
    físico como arcano"), Amuleto de Resistencia → oscuridad (lleva Pluma
    Corrupta), Anillo de Vitalidad → sagrado (un anillo de sanación defiende
    bien contra el elemento cuyo estado bloquea la autocuración). 10% cada
    una, provisional.
  - **3 armas elementales nuevas**, como recetas craftables en vez de drops
    nuevos (para no tocar el balance de botín ya calibrado): Espada Consagrada
    (sagrado, Fragmento de Hueso + Esencia Espectral — materiales de dos
    enemigos ahora débiles a sagrado), Daga Umbría (oscuridad, Capa de
    Sombras + Pluma Corrupta), Vara Arcana (arcano, Esencia Arcana + Núcleo de
    Gólem — el Gólem ahora también débil a arcano). Daño 14-18, por debajo de
    las armas "normales" de tramo similar, siguiendo el patrón ya establecido
    de que lo elemental cambia daño por utilidad. Números provisionales.
  - Reacciones elementales (rayo+congelado, fuego+veneno) quedan para
    v0.11.0-c.
  - **Arreglada la concordancia de género al nombrar el elemento** en los
    mensajes de afinidad (a petición del usuario, tras ver "El oscuridad
    causa estragos..." al atacar con un arma de oscuridad — debía ser "La
    oscuridad"). Los 7 elementos son masculinos salvo "oscuridad"; nuevo
    `combat/elements.py::element_phrase()`/`element_al()` construyen la frase
    con el artículo correcto ("el fuego"/"la oscuridad", "al veneno"/"a la
    oscuridad"), usados en `combat.super_effective`/`immune_hit`/
    `resisted_hit`. Si se añaden elementos nuevos que sean femeninos, hay que
    sumarlos a `_FEMININE_ELEMENTS`.
- [x] **v0.11.0-c: reacciones elementales** (GDD §5, la pareja que quedó
  pendiente de v0.11.0-b).
  - **Fusión (rayo + congelado)**: un golpe de rayo contra un objetivo ya
    congelado le rompe el hielo al instante y hace ×1.5 de daño extra, en vez
    del intento normal de paralizar. Nueva `is_shatter_hit()` en
    `combat/elements.py`, comprobada dentro de `Player.take_damage()` y
    `Enemy.take_damage()` (simétrico en los dos lados). El problema fue que
    "no paralizar esta vez" no lo decide `take_damage()`, sino una llamada
    *aparte* justo después (`_try_inflict_weapon_status()` para un arma de
    rayo del jugador, `Mago._cast_thunder()` para el rayo del enemigo) — así
    que hizo falta un flag de instancia (`just_shattered`, se resetea en cada
    `take_damage()`) que esa llamada aparte consulta antes de tirar el
    paralizado, el mismo patrón que ya usaba `took_physical_hit` para la
    Represalia del Guerrero. Los 4 elementos físicos ya tenían arma jugable
    (Garra de Tormenta = rayo de la Gárgola, Cetro de Escarcha = hielo del
    Nigromante, más las de fuego/veneno), así que la reacción es alcanzable
    en ambas direcciones jugando normal, no solo desde los hechizos del Mago.
  - **Combustión (fuego + veneno)**: aplicar quemado mientras ya hay veneno
    activo (o al revés, o cualquiera de los dos si ya hay combustión) los
    funde en un único estado `combustion` en vez de dejarlos coexistir, con
    más daño por turno que cualquiera de los dos por separado (`max_health //
    6`, frente a `// 16` de quemado y `// 8` de veneno) y duración = el
    máximo de los dos fusionados. Nueva `resolve_status_reaction()` en
    `combat/elements.py`, metida dentro de `apply_status()` en `Player` y
    `Enemy` — al estar centralizada ahí, cada sitio que ya aplicaba quemado o
    veneno (armas con elemento, los hechizos de fuego/veneno del Mago,
    Veneno de Contacto del Pícaro, los ataques de fuego de Dragón/Orco/
    Demonio) se beneficia de la fusión sin tocar ni una línea de esos sitios.
    `combustion` también reduce el ataque físico a la mitad igual que
    quemado (`get_attack_damage()`/`get_attack_range()` ahora comprueban los
    dos nombres) y sigue en `AntidotePotion.CURABLE` — se detectó con un test
    que fallaba (`test_antidote_removes_debuffs_and_leaves_the_rest`) al
    fusionar quemado+veneno en un nombre que el antídoto no reconocía. Un
    enemigo inmune al *estado* veneno (Esqueleto, Gárgola, Espíritu
    Vengativo) nunca llega a tener las dos mitades a la vez, así que la
    fusión queda bloqueada de forma natural sin necesitar una inmunidad a
    `combustion` aparte en ningún enemigo de los 14 actuales.
  - Mensajes nuevos en `i18n/catalog_es.py` (`combat.enemy_combustion`,
    `status.combustion`) y color propio (`Fore.LIGHTGREEN_EX`) en
    `ui/console.py::_STATUS_PATTERNS` para que "combustión" se resalte igual
    que el resto de estados en cualquier línea que la mencione.
- [x] **Ronda de feedback jugando con v0.11.0-c** (probando la combustión
  contra el Gólem de Piedra con daga de veneno + espada de fuego, y la
  pasiva Veneno de Contacto encima).
  - **Orden de mensajes al fusionar**: salía primero "🔥☣️ ¡El fuego y el
    veneno se funden en combustión!" y DESPUÉS "¡Gólem de Piedra ha sido
    quemado!" — al revés de lo esperado (primero se ve qué le pasó, luego la
    reacción). Causa: `apply_status()` imprimía el aviso de fusión ella misma,
    antes de devolver el control a quien llamó (que imprime su propio "ha
    sido quemado/envenenado" DESPUÉS). Arreglado quitando el `print()` de
    dentro de `apply_status()`: ahora solo deja `self.last_status_reaction`
    listo, y el nuevo `pop_status_reaction_message()` (`Player`/`Enemy`) lo
    devuelve y limpia — cada sitio que aplica quemado/veneno llama a este
    método justo DESPUÉS de imprimir su propio mensaje, así que el orden en
    pantalla queda garantizado.
  - **Reaplicar quemado/veneno estando ya en combustión no debería hacer
    nada**: en la misma prueba, tras sangrar con Golpe Bajo y envenenar de
    nuevo con Veneno de Contacto (el Gólem YA tenía combustión, no quemado),
    volvía a salir el aviso de fusión — y aunque no se vio en el log, la
    duración también se estaba refrescando, lo cual tampoco tenía sentido
    (ya es las dos cosas a la vez, un enemigo no puede "quemarse más" estando
    ya en combustión). Nueva `is_status_blocked_by_combustion()` en
    `combat/elements.py`, comprobada al principio de `apply_status()` en
    ambas clases: si el objetivo ya tiene combustión, un intento de aplicar
    quemado o veneno no hace absolutamente nada (`return False`/no-op), ni
    siquiera refresca duración.
  - **Antídoto**: su texto (`get_stats_info()`, la descripción del ítem en la
    tienda, y el docstring de la clase) ahora menciona explícitamente que
    también cura la combustión, aunque el `CURABLE` ya la incluía desde el
    principio — el usuario avisó de que en algún momento futuro puede que
    cada objeto cure un subconjunto distinto de estados en vez de que el
    Antídoto lo cure todo, pero por ahora, al no estar planificado, se deja
    así.
  - Tests nuevos en `tests/test_elemental_reactions.py`:
    `pop_status_reaction_message` (sin reacción / con reacción y se
    consume), bloqueo de reaplicación en `Player`/`Enemy` (sin refrescar
    duración), y un test de integración que verifica con `capsys`/parcheando
    `print` que el mensaje "ha sido quemado" sale antes que el de fusión.
- [x] **Reordenado el menú de combate** (a petición del usuario, sin relación
  con las reacciones elementales): de "Atacar, Objetos, Info, Huir, Defender,
  Habilidades, Auto-Batalla, Auto-Batalla Turbo" a "Atacar, Habilidades,
  Defender, Objetos, Huir, Info, Auto-Batalla, Auto-Batalla Turbo" — las dos
  opciones de acción (atacar/habilidades) y la defensiva (defender) van
  primero, las utilitarias después. `_player_menu()` ya construía la lista de
  opciones dinámicamente como `(etiqueta, token)` y las numeraba por
  enumeración, así que reordenar fue solo reordenar esa construcción; no hay
  ningún sitio que dependa de un índice fijo. Un test en `test_battle.py`
  hardcodeaba la posición antigua de "Defender" ("5") y se quedó colgado en
  bucle infinito al pasar a probar contra la nueva numeración (pedía "Info"
  una y otra vez con la misma respuesta fija) — corregido a "2", y añadido un
  test nuevo (`test_player_menu_options_are_in_the_requested_order`) que fija
  el orden completo, con y sin habilidades equipadas, para que un futuro
  reordenamiento accidental no pase desapercibido.
- [x] **v0.12.0-a: cimientos del paquete de mundo** (GDD §3/§9.2/§9.4 — primera
  sub-fase de v0.12.0, "El mundo, parte 1"). Deliberadamente solo datos +
  migración de guardado, sin tocar todavía `game_loop` ni ningún menú: nada de
  esto cambia cómo se juega hoy.
  - `world/zone.py::Zone` (dataclass congelado: `id`, `name`, `theme`,
    `enemies`, `sub_locations`, `key_npcs`) + un módulo por zona en
    `world/data/` (8 en total: Piedrablanca — el pueblo, sin enemigos — y las
    7 regiones de la tabla del GDD §3), reunidos en `world/map.py` como
    `ZONE_ORDER` (la cadena lineal) y `ZONES` (dict por id).
  - Los 14 enemigos actuales repartidos en sus zonas según la tabla del GDD
    (Los Yermos: Goblin/Huargo/Esqueleto/Bandido; Bosque de los Susurros:
    Orco/Espíritu Vengativo/Troll; Cañón del Trueno: Gárgola/Gólem de Piedra;
    Torre de los Arcanos: Mago/Nigromante; Ciudadela en Ruinas: Ángel
    Caído/Demonio; El Corazón de la Brecha: Dragón). Ciénaga de los Ahogados
    se queda sin roster (todo nuevo, GDD §4) — zona con `enemies=()` a
    propósito, no un descuido.
  - `world/map.py::default_zone_for_progress(defeated_enemies)`: infiere la
    zona "actual" recorriendo `ZONE_ORDER` y viendo hasta dónde hay algún
    enemigo backbone ya derrotado, saltándose sin cortar el avance las zonas
    que todavía no tienen roster (si no, Ciénaga bloquearía para siempre que
    la zona inferida avanzase hasta Cañón del Trueno). Es una aproximación
    deliberada: todavía no hay guardianes que abran zonas de verdad, así que
    se infiere del progreso de combate existente.
  - **Guardado v2**: `Player.mundo` (dict con `zona_actual`,
    `zonas_visitadas`, `misiones`, `banderas`, `dialogos_vistos`, `diario`,
    `arena_mejor_oleada`) se inicializa en `Player.__init__` (Piedrablanca por
    defecto) y se persiste en `persistence/save_load.py`. `banderas`/
    `dialogos_vistos` viven como `set` en memoria (más natural para
    comprobar pertenencia) pero JSON no tiene sets, así que se guardan como
    listas ordenadas y se reconstruyen como `set` al cargar. Migración v1 →
    v2: una partida sin bloque `"mundo"` infiere `zona_actual` con
    `default_zone_for_progress()` y rellena `zonas_visitadas` con toda la
    cadena hasta ahí; el resto empieza vacío. No se tocó nada del guardado ya
    existente (`clase`, `habilidades_equipadas` siguen donde estaban, no se
    movieron dentro de `mundo` pese a que el GDD los mencione ahí — mover
    algo que ya funciona solo para encajar con el documento habría sido una
    migración innecesaria).
  - Tests nuevos: `tests/test_world.py` (consistencia `ZONE_ORDER`/`ZONES`,
    cada uno de los 14 enemigos backbone en exactamente una zona,
    `zone_for_enemy`, varios casos de `default_zone_for_progress` incluyendo
    el salto de una zona vacía) y en `tests/test_save_load.py` (ida y vuelta
    de un `mundo` no vacío con sets, y migración de una partida vieja sin
    bloque `mundo`).
- [x] **v0.12.0-b: bucle de exploración por zona** (GDD §8.1 — segunda
  sub-fase de v0.12.0). Sustituye el antiguo `game_loop()` plano por
  `ui/exploration.py::zone_loop()`, un menú por zona con 4 opciones.
  - **Explorar** (`_explore`): tirada ponderada, `_EXPLORE_ENCOUNTER_CHANCE`
    (0.65) combate / `_EXPLORE_DISCOVERY_CHANCE` (0.15) oro / el resto (0.20)
    nada. El combate elige al azar entre los enemigos desbloqueados que
    pertenecen a la zona actual (`Zone.enemies ∩ unlocked_enemies`); si
    ninguno encaja (zona sin roster todavía, como Piedrablanca o la Ciénaga)
    cae a cualquier enemigo desbloqueado, para que explorar nunca se quede
    bloqueado. Reutiliza el mismo `initiate_battle(..., enemy_factory=...)`
    de siempre, así que las cadenas de auto-batalla siguen funcionando
    igual. Elegir un enemigo concreto por nombre desaparece — antes era
    "Luchar" con una lista numerada, ahora es aleatorio de verdad, como pide
    el GDD.
  - **Ir a `<sub-lugar>`** (`_sublocation_flow`): lista `Zone.sub_locations`
    y al elegir uno solo imprime una línea genérica de "todavía no hay nada
    que hacer aquí" — stub a propósito, los NPCs/servicios llegan en
    v0.13.0.
  - **Viajar** (`_travel_flow`): viaje rápido a cualquier zona ya en
    `player.mundo["zonas_visitadas"]`, más "`<zona>` (frontera)" para
    `world.map.next_zone(zona_actual)` en cuanto `is_zone_reachable()` lo
    permite y todavía no está visitada. Solo ofrece el salto inmediato
    siguiente, nunca varias zonas de golpe. Actualiza `zona_actual` y añade a
    `zonas_visitadas` (sin duplicar).
  - **Personaje** (`_character_menu`): todo lo que antes colgaba directo de
    `game_loop` salvo "Luchar" — Inventario, Tienda, Herrería, Estadísticas,
    Habilidades, Bestiario, Equipar Arma/Armadura, Opciones, Guardar Partida,
    Volver a la zona, Volver al Menú Principal, Salir del Juego, y Panel de
    Admin si `is_admin`. Tienda/Herrería se quedan aquí por ahora a
    propósito — reubicarlas a los sub-lugares de Piedrablanca es v0.12.0-c,
    no esta sub-fase. Devuelve el string `"volver_menu"` (no `None`) cuando
    el jugador elige volver al Menú Principal, para que `zone_loop()` sepa
    cuándo romper su propio bucle — mismo patrón de "señal por valor de
    retorno" que ya usaba `_run_player_turn` en combate (`"huir"` / `"ok"`).
  - **Evitado un ciclo de imports**: `menus.py` llama a `zone_loop()` desde
    `start_new_game()`/`load_saved_game()`, pero `zone_loop()` necesita
    varios helpers que siguen viviendo en `menus.py`
    (`_skills_flow`/`_equip_armor_flow`/`_bestiary_flow`/`_admin_panel_flow`/
    `open_options`/`_get_enemy_instance`). Solución: `exploration.py` importa
    de `menus` solo dentro de las funciones que los usan (nunca a nivel de
    módulo), mismo patrón que ya usaban `combat/battle.py` y
    `characters/player.py` para evitar ciclos parecidos.
  - `game_loop()` se borró por completo (su lógica se repartió entre
    `zone_loop()` y `_character_menu()`); no tenía tests directos porque
    `ui/menus.py` ya estaba fuera de la métrica de cobertura —
    `ui/exploration.py` se añadió al mismo `omit` en `pyproject.toml`, pero
    aun así se testeó con el mismo criterio que `test_menus.py` (parchear
    `console.ask`): `tests/test_exploration.py` cubre las 4 ramas de
    Explorar, viaje rápido/frontera/cancelar, el stub de sub-lugares, y las
    dos señales de salida de `_character_menu`. `world/map.py` ganó
    `next_zone()`/`is_zone_reachable()`, estas sí dentro de la métrica de
    cobertura (100%, `tests/test_world.py`).
  - Probado a mano de extremo a extremo con `main.py` real (creación de
    personaje, varias exploraciones incluyendo un combate completo contra un
    Goblin con subida de nivel, viaje a la frontera de Los Yermos, entrar a
    "Ir a..." y ver el stub, y recorrer el menú de Personaje incluyendo
    guardar partida) — captura completa sin tracebacks.
- [x] **v0.12.0-c: servicios de zona** (GDD §7.4/§8.1 — tercera y última
  sub-fase de v0.12.0, "El mundo, parte 1"). Cierra el hueco que dejó
  v0.12.0-b: Tienda/Herrería seguían en Personaje, "Ir a..." era puro stub, y
  Explorar solo daba oro.
  - **Tienda/Herrería reubicadas**: fuera de `_character_menu`, ahora
    conectadas a los sub-lugares de Piedrablanca vía un dict nuevo
    `_ZONE_SERVICES: dict[(zone_id, sub_location_name), Callable[[Player],
    None]]` que `_sublocation_flow()` consulta antes de caer al stub
    genérico — `("piedrablanca", "Mercado")` → `_open_shop`,
    `("piedrablanca", "Herrería")` → `_open_forge`. El resto de las demás
    zonas (y "Refugio" en Piedrablanca) se queda sin servicio, como stub.
  - **Posada/Descanso** (`_rest_flow`, en `("piedrablanca", "Taberna")`):
    cura del todo y limpia `status_effects` a cambio de oro, con confirmación
    s/n. Coste `_REST_COST_PER_LEVEL (10) × player.level` — número
    deliberadamente provisional, el GDD ya lo marcaba como pregunta abierta
    ("curva de coste del descanso") y sigue sin ajustar contra ingresos
    reales. Si ya se está a vida completa y sin estados, ni siquiera se
    muestra el coste — se avisa directamente de que no hace falta descansar.
    Si no hay oro suficiente tras confirmar, se avisa sin cobrar nada.
  - **Variedad en los hallazgos de Explorar** (`_discovery`): la rama de
    hallazgo ahora es ella misma una mini-tirada — 40%
    (`_DISCOVERY_POTION_CHANCE`) una Poción de Salud gratis vía
    `Inventory.add_item()` (que ya imprime su propio "Obtenido: X"), 60% el
    oro de siempre (3-10).
  - **Trampa al testear el dict de servicios**: `_ZONE_SERVICES` se
    construye una vez al cargar el módulo con referencias directas a
    `_open_shop`/`_open_forge`/`_rest_flow`, así que parchear
    `exploration._open_shop` con `monkeypatch.setattr` no lo intercepta (el
    dict ya guarda el objeto función original, no lo busca por nombre en
    cada llamada) — los tests tuvieron que usar
    `monkeypatch.setitem(exploration._ZONE_SERVICES, (...), ...)` en su
    lugar. Se dejó anotado en el docstring de `_sublocation_flow` para que
    no se repita el mismo despiste más adelante.
  - `_sublocation_flow()` pasó a necesitar `player` además de `zone` (antes
    solo listaba texto); actualizado su único call site en `zone_loop()` y
    los tests existentes de v0.12.0-b que la llamaban directamente.
  - Los índices numéricos de `_character_menu` cambiaron al quitar Tienda y
    Herrería (2 opciones menos) — actualizados los tests que dependían de
    "Volver a la zona"/"Volver al Menú Principal" por posición fija
    (11→9, 12→10, 13→11 con Panel de Admin), mismo tipo de despiste que ya
    había pasado con el reorden del menú de combate en v0.11.0-c.
  - Explícitamente fuera de alcance: reaparecer en el último pueblo visitado
    al morir (GDD §7.4 "Muerte") — cambia la gestión de derrota de
    `combat/battle.py`, no solo código de mundo/exploración, así que se deja
    para una pasada aparte.
  - Probado a mano con `main.py` real: Tienda/Herrería abren correctamente
    desde "Ir a..." en Piedrablanca, la Taberna informa de "ya estás a plena
    forma" a vida completa, y el menú Personaje quedó con 11 opciones (antes
    13) sin Tienda/Herrería.

- [x] **v0.13.0-a: motor de diálogo** (GDD §8.2 — primera sub-fase de v0.13.0,
  "Diálogo y NPCs"). Motor + un NPC de muestra; el reparto completo es -b.
  - `world/npc.py`: dataclasses congeladas (`NPC`, `Conversation`,
    `DialogueNode`, `Choice`, `Condition`, `Effect`) y funciones puras.
    `play_conversation()` no imprime ni pregunta: recibe tres callbacks
    (`show`, `pick`, `notify`), así toda la lógica queda testeada al 100% y
    `ui/exploration.py` solo aporta `print`/`input`.
  - Decisiones: un nodo sin `choices` es lineal (sigue por `next`); si todas
    las respuestas de un nodo quedan ocultas por sus condiciones, la
    conversación termina en vez de colgarse; una conversación única se
    registra en `mundo["dialogos_vistos"]` **al terminar** (GDD: "una vez
    jugada entera"), no al empezar; el NPC elige la primera conversación en
    orden declarado cuyo disparo se cumple y que no sea una única ya vista, y
    si no hay ninguna suelta una línea de `idle_lines`. Efectos disponibles:
    activar bandera, dar oro, dar objeto (dict de `Item.to_dict()`, reusando
    `item_factory`); los de misión esperan a que exista el sistema de misiones.
  - La regla "≥3 respuestas por nodo de elección" no la impone el dataclass
    (los tests del motor usan árboles pequeños) sino un test sobre el contenido
    real (`test_every_real_conversation_is_well_formed`), que además comprueba
    ids únicos, que todo `next` apunte a un nodo existente y que los ítems de
    los efectos se puedan reconstruir.
  - Los NPC se declaran en el módulo de su zona (`NPCS = (...)`) y
    `world/map.py` los agrega en `NPCS`/`npcs_in_zone()`; un test comprueba que
    el nombre de cada NPC figure en `Zone.key_npcs`.
  - Nueva opción "Hablar con..." en el menú de zona (los índices del menú
    pasan a 5 opciones; actualizado el test de `zone_loop`). Contenido: solo
    Yerma (tabernera de Piedrablanca; papel inventado, el GDD solo da el
    nombre): conversación de primer encuentro de 5 nodos que pone la bandera
    `conocio_a_yerma` (una rama regala una Poción de Salud) y 3 líneas sueltas.
  - **Ronda de feedback (probando a Yerma)**: (1) la poción llegaba *después* de
    elegir respuesta, así que el jugador contestaba "gracias / no hacía falta" sin
    saber que había recibido algo — nuevo `DialogueNode.effects`, que se aplican
    al mostrar el nodo (el aviso "Recibes X" sale justo bajo el texto del NPC,
    antes de las respuestas); (2) al despedirse o elegir una respuesta final el
    NPC se quedaba callado — nuevo `Choice.reply` (lo que contesta el NPC al
    momento) y todas las respuestas finales de Yerma tienen ya réplica. Para que
    no se repita con el contenido de -b, un test exige `reply` en toda respuesta
    que cierra la conversación (`next=None`).
  - **Segunda ronda de feedback: poder volver a hablar y ver qué queda**. Antes,
    al terminar el primer camino toda la conversación desaparecía y Yerma solo
    soltaba líneas sueltas. Ahora se puede volver a recorrer el árbol: al final
    de cada camino se guarda la última respuesta elegida
    (`"<conv>/<nodo>/<índice>"` en `dialogos_vistos`) y `pick` recibe una marca
    "agotada" por respuesta, que la UI dibuja como ✔ verde a la derecha. Una
    respuesta está agotada si es final y ya elegida, o si lleva a más respuestas
    y todas las visibles están agotadas (recursivo, con guarda contra bucles; las
    respuestas ocultas por condición no cuentan). La conversación solo se da
    por vista cuando todo el árbol está agotado; entonces vuelven las líneas
    sueltas. Lo que da algo (oro/objetos) se entrega una sola vez por partida
    (`_apply_once`, marcador `#efectos`) y la rama de la poción se oculta con
    `Condition(forbids_flags=("recibio_pocion_yerma",))` en vez de dejarla
    repetible (si no, el texto "toma, invita la casa" saldría sin regalo).
    Consecuencia asumida: al volver a hablar Yerma repite el saludo inicial.
  - Tropiezo: al insertar `_talk_flow` con un script de Python, los `
` de
    los literales se escribieron como saltos de línea reales y rompieron el
    fichero; detectado por ruff/pytest antes de commitear.

- [x] **v0.13.0-b: reparto de NPCs** (GDD §3/§8.2). Solo contenido, sin cambios
  de motor salvo el atajo `end(text, reply, *effects)` para respuestas finales.
  - 9 NPCs según la tabla de zonas del GDD: Piedrablanca (Yerma, Halbrand,
    Dorn, Nia), Los Yermos (Cael), Bosque (Mirelle), Ciénaga (Oren, barquero
    inventado: el GDD deja la zona sin NPC), Cañón (Kort), Torre/Necrópolis
    (Sella), Ciudadela (Aldric). Yerma sigue la primera del menú.
  - Cada uno: conversación de primer encuentro (raíz con 3 respuestas, dos
    ramas de 3 respuestas finales, cada una con réplica del NPC; la bandera
    `conocio_a_<npc>` se pone con un efecto del nodo raíz) + una segunda
    conversación cuyo `trigger` exige haber conocido a *otro* NPC + 3 líneas
    sueltas. Los cruces (Halbrand←Cael, Dorn←Mirelle, Nia←Halbrand,
    Cael←Mirelle, Mirelle←Oren, Oren←Kort, Kort←Sella, Sella←Aldric,
    Aldric←Kort) premian hablar con todos y volver atrás por el mapa.
  - Regalos de una sola vez, con la rama oculta después (`forbids_flags`, como
    la poción de Yerma): Dorn 20 de oro (y planta `dorn_encargo_troll`, semilla
    de "El encargo de Dorn"), Oren 25 de oro, Kort una Poción de Salud. Sella
    activa `sella_tomo_pista` (semilla de "El tomo prohibido"), Cael
    `sabe_del_altar`.
  - El GDD se contradice en dos sitios: Mirelle (Acto IV dice Cañón, la tabla
    dice Bosque) y Dorn (su encargo figura en el Bosque pero vive en
    Piedrablanca). Se siguió la tabla; el encargo se reubicará con el sistema
    de misiones.
  - Tests nuevos: cada `key_npcs` tiene su NPC (y viceversa), toda bandera
    exigida la activa alguna conversación, cada NPC se puede agotar con todas
    las banderas puestas (sin bucles, regalos una vez) y las ramas de regalo
    desaparecen al cogerlas. Los tests de `test_exploration` que asumían que
    Yerma era la única NPC / que Los Yermos no tenía a nadie se ajustaron (la
    zona sin NPC es ahora El Corazón de la Brecha).

- [x] **v0.13.0-c: notas de lore y Diario** (GDD §2 "Lore collectibles").
  Última sub-fase de v0.13.0.
  - Decisión: las notas salen **solo de sub-lugares** (visita por primera vez →
    se lee y queda guardada), no de Explorar: es determinista, da sentido a
    "Ir a..." (que hasta ahora era un stub de una línea) y evita notas que se
    pierdan o se repitan por azar. Los sub-lugares con servicio (Mercado,
    Herrería, Taberna) no tienen nota.
  - `world/lore.py`: `LoreNote` congelada + funciones puras (`add_note`,
    `has_note`, `found_notes`). El Diario es `mundo["diario"]` (lista de ids en
    orden de descubrimiento, ya existía en el guardado desde v0.12.0-a: cero
    migración). `found_notes` ignora ids desconocidos para que renombrar una
    nota en el futuro no rompa partidas antiguas.
  - Cada zona declara sus notas en un `LORE` opcional de su módulo
    (`world/data/*.py`), agregadas en `world/map.py` (`LORE_NOTES`,
    `note_for_sub_location`). 13 notas: Refugio + 2 por zona de Los Yermos a la
    Ciudadela; El Corazón de la Brecha no tiene (se diseña al final). Escritas
    para enlazar con los NPC sin repetirlos (la muñeca de Nia en el campamento,
    la K a medio grabar de Kort, la ficha del tomo prohibido de Sella...).
  - UI: "Diario (n/total)" en Personaje, justo tras Bestiario, con las notas
    agrupadas por zona en el orden del mapa; releer una nota espera un Enter. Los
    índices de Personaje se desplazan (Volver a la zona 9→10, etc.) y se
    ajustaron los tests.
  - Tests nuevos: `tests/test_lore.py` (idempotencia, orden, ids desconocidos,
    ida y vuelta por guardado, ids únicos, cada nota apunta a un sub-lugar real,
    cada sub-lugar sin servicio tiene exactamente una nota) + los de flujo en
    `test_exploration` (primera visita / repetida / sin nota, Diario vacío,
    agrupación, opción inválida). El test antiguo "Refugio sigue siendo un stub"
    ya no procedía y se sustituyó.
  - **Feedback probando**: faltaba una pausa "Presiona Enter para continuar..." tras leer una nota
    al visitar un sub-lugar (el Diario ya la tenía) y tras la última frase de un NPC, como en otros
    sitios del juego. Añadidas en `_sublocation_flow` (solo la primera visita, cuando sale la nota) y
    en `_talk_flow` (tras cada conversación, también tras una línea suelta). Tests nuevos para ambas.
  - **Feedback probando (2)**: palabras como "quemado/quemada" salían en rojo en textos de lore (el
    título "Bando quemado" y la línea "Recorres Cabaña quemada de nuevo") porque `colorize()` y
    `console.say()` tiñen los estados alterados automáticamente. Se eligió que las notas **no** se
    tiñan (en vez de colorearlas a mano): `colorize(..., tint=False)` para el título y `print()` en
    las líneas de "Recorres...". El cuerpo de las notas y los diálogos ya se imprimían sin teñir.
  - Tropiezo: al parchear `exploration.py` con un script de Python vía heredoc,
    los `\n` de los f-strings volvieron a convertirse en saltos de línea reales
    (mismo error que en v0.13.0-a); arreglado con Edit. Y un test con índice de
    menú antiguo no falla: se **cuelga** pidiendo entrada, así que conviene
    lanzar pytest con `timeout`.

- [x] **v0.14.0-a: bestiario progresivo** (GDD §7.2). Primera sub-fase de v0.14.0
  ("Bestiario y enemigos I"; el resto: -b herramienta de presupuesto de poder,
  -c Los Yermos a 10 enemigos + guardián que abre zona, -d Bosque a 10, -e
  habilidades de clase de nivel medio).
  - Escalones por `enemy_kill_counts`: 1 = básicos + descripción + elementos que
    inflige; 3 = resto de stats + habilidad; 5 = afinidades + estados que
    inflige / inmunidades a estados; 10 = tabla de botín. Precisión / evasión /
    penetración / regeneración no tenían escalón en el GDD: van con el de 3.
  - Datos por enemigo como atributos de clase de `Enemy` (`DESCRIPTION`,
    `SIGNATURE`, `ELEMENTS_DEALT`, `INFLICTS`), rellenados en los 14. Las
    descripciones enlazan con el lore ya escrito (el Bandido como mercenario sin
    paga, la Gárgola "puesta ahí por alguien", el Nigromante que "guía" a los
    muertos...). Se añadieron al catálogo i18n los nombres de estado `desarmado`,
    `confusion` y `maldicion`.
  - **Decisión: la tabla de botín se deduce, no se duplica.** El plan hablaba de
    un `DROPS` declarado más un test que lo vigilara; pero los 14 `drop_item()`
    siguen exactamente el patrón `if random.random() <= p: items.append(...)`, así
    que `Enemy.drop_table()` ejecuta el `drop_item()` real con un
    `random.random()` sustituido por un `float` cuyo `<=` siempre acierta y anota
    el umbral, y empareja objetos y umbrales con `zip(strict=True)`. No hay
    segunda copia que se desincronice; si un enemigo futuro rompe el patrón, el
    `strict` revienta y `test_drop_table_stays_consistent_with_drop_item_for_the_whole_roster`
    lo delata. Coste: depende de ese patrón (documentado en el docstring).
  - Cambio de comportamiento: antes una sola derrota enseñaba la ficha entera;
    ahora enseña solo el primer escalón y el resto va apareciendo.
  - Tests: `tests/test_bestiary.py` (cada escalón, la línea de lore sin teñir,
    `drop_table()` exacta para el Goblin, `random.random` restaurado, coherencia
    con `drop_item()` de los 14, ficha completa y renderizable para cada enemigo).
    Ajustado el test antiguo de debilidades (ahora exige 5 derrotas).
  - **Ronda de feedback**: (1) el Daño Crítico se mostraba como multiplicador
    (`x1.60`) en vez de porcentaje como la Prob. Crítico — primer intento:
    `crit_damage * 100` → `160%`. El usuario señaló que eso confunde: `crit_damage`
    es un multiplicador total (daño × 1.6 al criticar), así que "160%" se lee
    como "160% más de daño" (sería x2.6), cuando en realidad es +60% (como en
    Raid Shadow Legends, donde el % mostrado es el bonus sobre el golpe normal,
    no el total) — coincide además con cómo `items/equipment.py` ya mostraba el
    bonus de crítico de una armadura (`+{crit_damage * 100:.0f}%`, ahí sí un
    delta, no un total). Corregido a `+{(crit_damage - 1) * 100:.0f}%` en las
    tres pantallas (Bestiario, información de batalla del jugador y del
    enemigo, `Player.show_stats()`; `Stats.__str__()`, que no se imprime en
    pantalla, se dejó igual); (2) la descripción del Goblin
    mencionaba una condición interna ("si ya lo has derrotado antes") que el
    jugador no puede comprobar y no aporta nada — se quitó, la habilidad ya
    dice que emboscada; (3) "Habilidad: Emboscada: ..." quedaba con dos dos
    puntos seguidos — la línea ahora es "Habilidad {SIGNATURE}" sin los dos
    puntos propios, ya que cada `SIGNATURE` empieza por su propio nombre y
    los dos puntos. El Goblin y el Huargo sin debilidades/resistencias/
    inmunidades a las 5 derrotas es correcto (ninguno tiene ninguna todavía).

- [x] **v0.14.0-b: herramienta de presupuesto de poder** (GDD §4.4). Segunda
  sub-fase de v0.14.0. No es una pantalla del juego: es una herramienta de
  diseño para cuando se escriba el roster de una zona (-c en adelante), para
  saber a ojo si un enemigo nuevo está bien tuneado antes de escribir su
  código, en vez de descubrirlo solo tras cientos de combates simulados.
  - **Fórmula** (`characters/power_budget.py::power_score`): `vida_máxima ×
    velocidad × daño_neto`, con `daño_neto = daño_medio × (1 + crit_chance ×
    (crit_damage - 1))`. Decisión (confirmada con el usuario): **no** resta la
    mitigación de un jugador de referencia — no hay un jugador "típico" fijo
    (varía por clase/nivel/equipo), así que restar algo aquí sería más
    especulativo que no restar nada; que encaje de verdad contra un jugador
    real lo confirma el playtest posterior, tal como pide el GDD.
  - **Limitación conocida y documentada**: la fórmula solo ve
    `min_atk`/`max_atk` — no ve mecánicas que dan amenaza sin subir esas stats
    (autocuración, reanimación, control). El Esqueleto (revive una vez a mitad
    de vida) y el Mago (cura + controla, con ataque base deliberadamente bajo)
    son los dos casos conocidos del roster actual.
  - **Curva objetivo**: `objetivo(zona, tier) = BASE · ZONE_GROWTH^zona ·
    TIER_GROWTH^(tier-1)` (zona = índice en `ZONE_ORDER`, tier 1-10 dentro de la
    zona) — geométrica en ambos ejes. Constantes ajustadas por regresión
    log-lineal contra datos reales, luego redondeadas: `ZONE_GROWTH=2.1`
    (contra el poder medio de las 6 zonas ya pobladas: cada zona ronda el doble
    de poder que la anterior) y `TIER_GROWTH=1.25` (contra la única zona con
    tiers ya fijados por el GDD, Los Yermos §4.6: Goblin=2, Huargo=4,
    Esqueleto=6, Bandido=7 — cada tier sube ~25% sobre el anterior). Las demás
    zonas no tienen tiers de diseño todavía, así que no se les inventa ninguno
    aquí — eso lo decide la sub-fase que rellene esa zona (-c para Los Yermos,
    ya resuelto; -d para el Bosque). `zone_score_range(zona)` da el rango
    `[objetivo(zona,1), objetivo(zona,10)]`, útil para comprobar cualquier
    enemigo de una zona sin necesidad de saber su tier exacto.
  - **No es retroactivo**: los 14 enemigos actuales se calibraron por playtest
    antes de que existiera esta herramienta y no se retocan para encajar en
    ella ahora (sería un rebalanceo aparte, ya anotado como pendiente).
    Informe completo (`tests/test_power_budget.py` fija qué casos están fuera
    y documenta por qué):

    ```
    Enemigo              Zona                     N    Poder  Rango zona [T1,T10]  Tier  Objetivo   Desv.
    Goblin               Los Yermos               1    4 532  [   3 150,  23 469]    2      3 938    +15%
    Huargo               Los Yermos               1    6 156  [   3 150,  23 469]    4      6 152     +0%
    Esqueleto            Los Yermos               1    6 150  [   3 150,  23 469]    6      9 613    -36%
    Bandido              Los Yermos               1   17 299  [   3 150,  23 469]    7     12 016    +44%
    Orco                 Bosque de los Susurros   2   25 042  [   6 615,  49 286]     ?          —  en rango
    Espíritu Vengativo   Bosque de los Susurros   2   82 938  [   6 615,  49 286]     ?          —    FUERA
    Troll                Bosque de los Susurros   2   38 062  [   6 615,  49 286]     ?          —  en rango
    Gárgola              Cañón del Trueno         4  120 350  [  29 172, 217 349]     ?          —  en rango
    Gólem de Piedra      Cañón del Trueno         4  266 976  [  29 172, 217 349]     ?          —    FUERA
    Mago                 Torre de los Arcanos     5   80 400  [  61 262, 456 434]     ?          —  en rango
    Nigromante           Torre de los Arcanos     5  431 944  [  61 262, 456 434]     ?          —  en rango
    Ángel Caído           Ciudadela en Ruinas      6  393 461  [ 128 649, 958 511]     ?          —  en rango
    Demonio               Ciudadela en Ruinas      6  812 965  [ 128 649, 958 511]     ?          —  en rango
    Dragón                El Corazón de la Brecha  7 1051 596  [ 270 163,2012 873]     ?          —  en rango
    ```
    Solo Huargo cae dentro del ±10% de su objetivo exacto. Goblin (+15%) y
    Bandido (+44%, éste también emboscada + desarme) se quedan algo altos;
    Esqueleto (-36%) queda bajo por la reanimación, como se esperaba. De las
    otras zonas, dos enemigos caen fuera del rango [tier1, tier10] de su zona —
    hallazgos honestos, no errores del formato: **Espíritu Vengativo** es más
    rápido y letal de lo que "toca" para estar entre los primeros enemigos de
    su zona (velocidad 17, el más rápido de los 14 salvo el tramo final), y
    **Gólem de Piedra** es, con diferencia, el más resistente de todo el roster
    hasta ahora (armadura 20, la más alta). Ninguno se retoca en esta sub-fase.
  - Tests: `tests/test_power_budget.py` (la fórmula, que la curva crece dentro
    de una zona y entre zonas del mismo tier, `zone_score_range`, `deviation`,
    y el informe completo de los 14 con los casos fuera de rango/tolerancia
    fijados explícitamente para que un cambio futuro en la fórmula o en un
    enemigo obligue a revisar este test, no a que falle en silencio).

- [x] **v0.14.0-c: Los Yermos a 10 enemigos** (GDD §4.6). Tercera sub-fase de
  v0.14.0 (el resto: -d Bosque a 10, -e habilidades de clase de nivel medio).
  - Nuevo documento explicativo `docs/design/presupuesto_de_poder.md`: qué es
    el "Poder" que enseñan juegos como Raid Shadow Legends o Hustle Castle, de
    dónde sale, y cómo se calculó exactamente el de Valeterna paso a paso
    (regresión log-lineal contra los 14 enemigos existentes) — a petición
    expresa del usuario, que quería entenderlo a fondo y tenerlo siempre a
    mano, no solo en el docstring técnico de `power_budget.py`.
  - **6 enemigos nuevos**, cada uno dimensionado antes de escribir su código
    contra `target_score(zona=Los Yermos, tier)`: Rata Gigante (tier 1,
    objetivo 3 150, real 3 214, +2%), Goblin Montaraz (tier 3, objetivo 4 922,
    real 5 166, +5%), Chamán Goblin (tier 5 élite, objetivo 7 690, real 6 990,
    -9%), Salteador (tier 8, objetivo 15 020, real 14 832, -1%), Ogro del
    Yermo (tier 9 élite, objetivo 18 775, real 18 266, -3%), El Carnicero
    (tier 10 guardián, objetivo 23 469, real 23 452, -0%) — todos dentro del
    ±10% que pide el GDD, mucho más ajustados que la cadena original (que se
    calibró antes de que existiera la herramienta).
  - **Orden de desbloqueo**: el Goblin sigue siendo el primer enemigo del
    juego (la curva de XP del nivel 1→2 está calibrada específicamente
    alrededor de su primera victoria) aunque su tier de diseño (2) quede por
    debajo del de la Rata Gigante (1) — se desbloquea justo detrás de él en
    vez de delante. Cadena completa: Goblin → Rata Gigante → Goblin Montaraz →
    Huargo → Chamán Goblin → Esqueleto → Bandido → Salteador → Ogro del
    Yermo → El Carnicero (guardián, abre el Bosque) → Orco (sin cambios desde
    aquí).
  - **Ronda de feedback sobre el diseño (antes de escribir código)**:
    - *Goblin Montaraz*: el diseño original ("las flechas ignoran parte de la
      evasión") lo señaló el usuario como poco realista — esquivar un
      proyectil a distancia es, si acaso, más fácil que esquivar un golpe
      cuerpo a cuerpo, no más difícil. Se descartó y se sustituyó por una
      probabilidad de sangrado al acertar, con la misma tirada de acierto que
      cualquier otro ataque del juego (nada de trato especial a la evasión).
    - *Salteador*: el robo de oro se diseñó desde el principio con topes
      pedidos por el usuario — nunca dejar al jugador a cero, y que no sea
      "todo el rato". Es una acción alternativa (~25% de sus turnos, no un
      añadido a cada golpe) y el importe robado está acotado
      (`min(oro_del_jugador, random(3, 8))`), con mensaje distinto si no lleva
      nada encima.
  - **Mecánicas nuevas, todas reutilizando patrones ya existentes salvo el
    robo de oro**: veneno/sangrado al acertar (Rata Gigante, Goblin Montaraz —
    mismo patrón que el Dardo de Veneno del Mago), autocuración + maldición
    (Chamán Goblin — mezcla de la cura del Ángel Caído y la maldición del
    Espíritu Vengativo), golpe extra (Salteador — mismo patrón que el
    mordisco de manada del Huargo) + robo de oro (nuevo), golpe aplastante
    con aturdimiento (Ogro del Yermo — variante del terremoto del Gólem con
    tirada de acierto), furia de un solo sentido + sangrado (El Carnicero —
    variante de la furia cíclica del Orco, pero permanente una vez activada
    en vez de alternar).
  - **Botín**: cada uno suelta poción + material propio; Rata Gigante, Goblin
    Montaraz, Chamán Goblin y Salteador también arma (daño 5/6/8/10,
    manteniendo la progresión ya documentada — Goblin 4, Huargo 7... — sin
    romperla); Ogro del Yermo y El Carnicero no sueltan arma, solo armadura
    (tanques, no ofensivos). Piezas de armadura nuevas en huecos ya usados por
    Los Yermos (botas, hombreras, amuleto, cinturon, casco, guantes, perneras,
    peto), con valores que respetan la progresión no decreciente por hueco de
    `test_armor_progression.py` a lo largo de toda la cadena de 20 (verificado
    a mano contra los valores reales de los 14 antes de escribir el código, y
    confirmado después con el test). **No se añaden recetas de forja nuevas**
    en esta sub-fase para no ampliar más el alcance — los 6 materiales quedan
    listos para cuando toque.
  - Wiring: `combat/battle.py::ENEMY_PROGRESSION` (cadena), `ui/menus.py`
    (`ALL_ENEMY_NAMES`, `_get_enemy_instance`, imports), `characters/enemies/
    __init__.py`, `world/data/los_yermos.py::ZONE.enemies` (10 nombres).
  - Tests: `tests/test_los_yermos_10.py` (nueva, 17 tests — una mecánica por
    enemigo, llamando a los métodos internos directamente en vez de encadenar
    tiradas de `perform_turn()` completo, como ya hace `test_new_enemies.py`),
    afinidades de los 6 en `test_enemy_affinities.py`, `test_armor_progression.py`
    y `test_new_enemies.py` actualizados con la cadena de 20. Un combate
    simulado completo contra El Carnicero de principio a fin (victoria,
    desbloqueo del Orco, furia activada al cruzar el 40%) para comprobarlo en
    el juego real, no solo con tests.

- [x] **Playtest tras v0.14.0-c: iniciativa engañosa y varianza de daño entre
  ataque normal / habilidad / crítico** (a petición del usuario, jugando una
  partida nueva contra el Goblin). Dos arreglos, sin tocar el roster de
  enemigos.
  - **Mensaje de iniciativa incorrecto con velocidades parecidas**: el
    mensaje "⚡ X tiene la iniciativa" solo comparaba velocidad en crudo
    (`pv >= ev`), pero el turno real lo decide una carrera de barras ATB por
    ticks, y con velocidades parecidas (el caso real del usuario: jugador 10,
    Goblin 11) los dos cruzan el umbral en el **mismo tick** — y ahí el turno
    del jugador se resuelve siempre primero por regla ya existente (para que
    un enemigo más rápido nunca interrumpa una huida). El mensaje no tenía en
    cuenta esa regla, así que podía anunciar al enemigo y aun así empezar el
    jugador. Arreglado calculando `ticks = ceil(100 / velocidad)` para cada
    lado y anunciando al jugador siempre que `ticks_jugador <= ticks_enemigo`
    — la misma condición que decide el turno real, no una aproximación.
  - **Una habilidad o un crítico podían pegar menos que un ataque normal con
    suerte.** Causa real (comprobada leyendo el código, no a ojo): tanto el
    multiplicador de una habilidad (`damage_mult`, p. ej. 1.4 de Golpe Firme)
    como el del crítico (`crit_damage`) se aplicaban sobre la **misma** tirada
    aleatoria `random(min_atk, max_atk)` de un ataque normal — con un rango
    proporcionalmente ancho (el máximo casi dobla al mínimo a nivel bajo), una
    tirada alta sin ningún bonus podía superar a una tirada baja con el +40%
    o el crítico encima.
  - **Solución elegida, de las 4 que se plantearon**: ni estrechar el rango de
    daño de todo el juego (recalibraría los 20 enemigos), ni sumar dos dados
    más pequeños (cambio de motor demasiado amplio para esto), ni dejarlo
    como estaba. La opción 2 — que una habilidad de daño no multiplique la
    tirada, sino una base fija — se quedó, pero **afinada por el propio
    usuario**: en vez del "+6 fijo" que propuse yo (que se descuadraría según
    suben `min_atk`/`max_atk` con nivel/equipo, al ser un número inventado sin
    relación con esas stats), la base pasa a ser **siempre el extremo alto del
    rango de ataque** (`get_attack_range()[1]` / `get_magic_attack_range()[1]`
    para el Arcanista) tanto para una habilidad de daño como para un crítico —
    con el multiplicador propio de cada uno (`damage_mult`, `crit_damage`)
    aplicado encima igual que antes. Al ser un porcentaje de las stats reales
    del jugador (no un número absoluto), escala solo por sí mismo según sube
    el ataque máximo, sin descuadrarse.
  - El usuario propuso una segunda idea a modo de alternativa por si "siempre
    el máximo" resultaba demasiado fuerte: promediar dos veces (`(min+max)/2`,
    y luego el promedio de eso con `max`) — que él mismo describió como "un
    75% de poder". Comprobado algebraicamente: `((min+max)/2 + max)/2 =
    min·0.25 + max·0.75`, exactamente el percentil 75 del rango, aunque
    llegó a ese número por partida doble en vez de calcularlo directo. Se
    descartó a favor de "siempre el máximo" por ser más simple de explicar y
    de implementar (sin una constante de percentil que justificar) y porque
    encaja mejor con el objetivo declarado ("que una habilidad se sienta
    fuerte de verdad, garantizado") — la idea del 75% queda anotada aquí por
    si el máximo resulta demasiado fuerte tras más playtest y hay que
    suavizarlo.
  - **Deliberadamente solo para el jugador**: los enemigos siguen tirando su
    dado normal en sus propios críticos, decisión revisada poco después (ver
    la siguiente entrada).
  - Tests: `tests/test_battle.py` — el mensaje de iniciativa en el caso de
    empate real (10 vs 11), y tres tests de daño con un `randint` mockeado
    deliberadamente bajo para demostrar que una habilidad y un crítico lo
    ignoran (usan el máximo) mientras un ataque normal lo sigue respetando.

- [x] **Segunda ronda: crítico de enemigos igual que el del jugador, y quitar
  las velocidades del mensaje de iniciativa.** El usuario confirmó que sí
  quiere pagar el coste de descuadrar el tuneado de la curva de poder con tal
  de que el crítico se sienta igual de fiable jugando o siendo golpeado.
  - `Enemy.get_max_attack_damage()` (`enemy_base.py`): mismo patrón que
    `get_attack_damage()` (incluida la mitad de daño por `quemado`/
    `combustión`), pero con `self.stats.max_atk` fijo en vez de tirar el
    dado. Es la base compartida que usan todos los golpes críticos del
    roster.
  - Cambiado el orden de cálculo en **10 sitios**: el `Enemy.perform_turn()`
    por defecto (usado por la mayoría del roster salvo cuando entra en juego
    un ataque especial propio), la furia del Orco, y los ataques propios de
    Ángel Caído, Chamán Goblin, Demonio, Dragón, El Carnicero, Goblin
    Montaraz, Nigromante, Rata Gigante y los 4 hechizos del Mago (ahí el
    máximo solo sustituye la tirada base `atk_base`; el bonus propio del
    hechizo, p. ej. `random.randint(15, 25)` de la Bola de Fuego, se deja
    aleatorio). Ahora todos calculan `is_crit` **antes** de decidir la base de
    daño (`get_max_attack_damage()` si critea, `get_attack_damage()` si no),
    en vez de tirar el dado y multiplicar después.
  - **No se ha tocado nada que hoy no criteaba**: la embestida de la Gárgola,
    el terremoto del Gólem, el golpe aplastante del Ogro del Yermo y el
    segundo golpe del Salteador son "golpes especiales" con un multiplicador
    fijo propio y sin tirada de crítico separada — se han dejado exactamente
    igual, no se les ha añadido una posibilidad de critear que no tenían.
  - **No se ha recalibrado ningún enemigo.** El daño medio de un enemigo sube
    algo (sus críticos ahora pegan más fuerte de forma consistente en vez de
    a veces flojo/a veces fuerte), lo cual descuadra ligeramente el informe de
    `tests/test_power_budget.py` respecto a cuando se calculó — asumido a
    propósito, no se ha vuelto a ajustar ninguna stat. Si en un futuro
    playtest algún enemigo se siente demasiado fuerte, revisar primero si es
    por esto antes de tocar otra cosa.
  - **Mensaje de iniciativa sin números**: "⚡ {nombre} tiene la iniciativa."
    a secas, sin "(velocidad X vs Y)". Motivo doble: simplicidad pedida por
    el usuario, y que antes de derrotar a un enemigo por primera vez su
    velocidad es un dato que el Bestiario todavía redacta como `???` — el
    mensaje anterior lo enseñaba igualmente antes de tiempo.
  - Tests: `tests/test_battle.py::test_enemy_default_perform_turn_applies_crit_multiplier`
    reescrito con la misma técnica (`randint` mockeado bajo) para demostrar
    que el crítico por defecto usa el máximo. Ajustados tres tests que
    dejaban de tener sentido con el nuevo daño de crítico (`test_battle.py`,
    `test_enemy_attacks.py`, `test_new_enemies.py`): dos morían antes de
    tiempo porque el crítico, ahora más fuerte, dejaba al jugador de prueba a
    0 HP a mitad del test (se les subió la vida o se les resetea entre
    pasos), y uno ajustaba el valor esperado del crítico del Goblin al nuevo
    cálculo basado en `max_atk` en vez del `randint` mockeado.

- [x] **"Cazar..." para elegir enemigo, y Explorar pesado hacia el progreso**
  (GDD §8.1, feedback del usuario tras la v0.14.0-c). Motivo: con Los Yermos
  ya a 10 enemigos, un jugador que había llegado hasta el tier 9 podía, en
  la siguiente tirada de Explorar, volver a caer contra el Goblin del tier 1
  — de las tres opciones que se plantearon (A: solo pesar Explorar, B: solo
  añadir "Cazar", C: las dos), el usuario eligió la C.
  - `_zone_candidates(zone, unlocked_enemies)`: extraído de `_explore` (antes
    hacía el filtro inline), ahora compartido con `_hunt_flow`. Devuelve los
    enemigos desbloqueados de la zona en el orden de `Zone.enemies` (de tier
    1 a 10, el mismo orden que ya asume el ajuste de `power_budget.py`); si
    la zona no tiene roster propio (Piedrablanca, Ciénaga), cae al orden de
    `unlocked_enemies`.
  - `_weighted_enemy_choice(candidates)`: `random.choices(candidates,
    weights=range(1, len(candidates)+1))` — el enemigo más avanzado de la
    zona tiene N veces más probabilidad que el primero (N = nº de
    candidatos), sin llegar a excluir del todo a los primeros. Sustituye al
    `random.choice()` uniforme de antes en `_explore`.
  - **"Cazar..."** (`_hunt_flow`), nueva opción 2 del menú de zona (el menú
    pasa de 5 a 6 opciones: Explorar, Cazar..., Ir a..., Hablar con...,
    Viajar, Personaje — todo lo que iba después se desplaza un índice, igual
    que pasó con el Diario en v0.13.0-c). Lista los mismos
    `_zone_candidates`, con un ✔ verde en los ya derrotados (que en la
    práctica son todos menos el más nuevo, el "frontera" que todavía no has
    vencido — un enemigo solo se desbloquea al derrotar al anterior de la
    cadena). Elegir uno va directo a `initiate_battle(...)`, sin la tirada
    de oro/poción de Explorar (ese incentivo se queda solo en Explorar, a
    propósito, para no volver "Cazar" estrictamente mejor en todos los
    casos) — pensado para farmear un enemigo concreto (botín, oro, nivel) o
    para no depender del azar cuando lo que quieres es ir a por el guardián.
  - Tests: `tests/test_exploration.py` — `_zone_candidates` (orden de tier y
    su fallback), `_weighted_enemy_choice` (pesos crecientes, sin comprobar
    el azar real para no hacer un test inestable), listado de `_hunt_flow`
    con checks, elegir un enemigo concreto, volver sin pelear, sin
    candidatos, y que `zone_loop` despacha bien la opción 2. Los dos tests
    viejos de `_explore` que mockeaban `random.choice` (ya sin uso real, la
    tirada pasó a `random.choices`) se actualizaron para mockear la función
    que de verdad se llama ahora.

- [x] **"Cazar..." no debe listar al enemigo "frontera" todavía sin
  derrotar, y aviso simétrico de turno repetido del enemigo** (feedback del
  usuario tras probar la v0.14.0-hunt en partida real, antes incluso de
  fusionar el PR anterior).
  - **Bug de Cazar**: la primera versión de `_hunt_flow` reutilizaba
    `_zone_candidates` tal cual, que devuelve todo lo *desbloqueado*, no solo
    lo *derrotado* — así que al empezar la partida (con el Goblin
    desbloqueado pero sin pelear ni una vez) Cazar ya lo mostraba, y tras
    vencerlo, Cazar mostraba también a la Rata Gigante (el nuevo "frontera")
    igual de sin derrotar. `_hunt_flow` ahora filtra
    `_zone_candidates(...)` contra `defeated_enemies`, así que solo aparecen
    enemigos ya vencidos al menos una vez; con la lista vacía (nada
    derrotado todavía en la zona) muestra un aviso en vez de una lista
    vacía o el enemigo sin conocer. El primer encuentro con cualquier
    enemigo sigue siendo cosa de Explorar, nunca de Cazar — de paso ya no
    hace falta el ✔ de "derrotado" en la lista, porque ahora todo lo listado
    lo está.
  - **Aviso de turno repetido, lado enemigo**: en un combate real el usuario
    vio dos turnos seguidos del Goblin (más rápido que su personaje) sin
    ningún indicio de por qué — la barra ATB estaba funcionando como
    debía (rebasa el umbral más de una vez antes de que el jugador lo cruce
    ni una), pero solo el lado del jugador avisaba de esto ("⏩ Eres más
    rápido: actúas de nuevo antes que {enemigo}."). `_run_one_battle` ahora
    también rastrea si el jugador ha actuado desde el último turno del
    enemigo (`player_acted`, espejo de la `enemy_acted` que ya existía) y se
    lo pasa a `_run_enemy_turn(..., repeated=...)`, que imprime su propia
    línea ("⏩ {enemigo} es más rápido: actúa de nuevo antes que tú.") justo
    bajo la cabecera de turno cuando toca.
  - Tests: `tests/test_exploration.py` reescribe los tests de `_hunt_flow`
    para el nuevo filtrado (frontera nunca listada, solo derrotados,
    "Volver" con un único candidato) y ajusta los mensajes esperados.
    `tests/test_battle.py` añade un test unitario de `_run_enemy_turn` con
    `repeated=True`/`False` y un test de extremo a extremo con un enemigo
    mucho más rápido en una batalla real, comprobando que el aviso aparece.

- [x] **Encuentros con sabor de rol al empezar el combate** (GDD §8.1
  follow-up, feedback del usuario tras probar la v0.14.0-hunt: "estilo
  Pokémon", un aviso sencillo al toparte con un enemigo, no un motor de
  diálogo como `world/npc.py`). Resumen del pedido: enemigos normales, una
  frase sencilla de "algo se te pone delante"; élite, algo más tenebroso que
  deje claro que no va a ser fácil; guardián, lo mismo pero aún más
  tenebroso; y para élite/guardián, si el jugador ya ha perdido contra ese
  enemigo, desde el siguiente encuentro que provoque/vacile en vez de repetir
  la intro.
  - Tres atributos de clase nuevos en `Enemy` (`enemy_base.py`):
    `ENCOUNTER_KIND` (`"normal"` por defecto / `"elite"` / `"guardian"`),
    `ENCOUNTER_LINE` (la frase de la 1ª vez) y `TAUNT_LINES` (tupla de
    provocaciones, solo élite/guardián, una al azar cada vez).
  - Clasificación: en vez de inventar un criterio nuevo, élite = los 5
    enemigos que ya tenían música de combate propia
    (`HARD_BATTLE_ENEMIES`: Gólem de Piedra, Mago, Nigromante, Ángel Caído,
    Demonio); guardián = El Carnicero y el Dragón (el usuario confirmó
    incluir también al Dragón, el jefe final, con el mismo sistema). El
    resto (13 enemigos) se quedan en "normal".
  - `combat/battle.py::_announce_encounter(player, enemy)`: 1ª vez que ves a
    ese enemigo (cualquier tipo) → siempre imprime `ENCOUNTER_LINE`. Desde la
    2ª, solo élite/guardián dicen algo más, y solo si ya perdiste contra él
    (`_defeat_flag`, puesto por `_handle_defeat(player, enemy, ...)`, ahora
    con el enemigo como parámetro opcional). Se llama desde `_run_one_battle`
    justo antes de "¡Ha comenzado la batalla...!", con el mismo criterio que
    el resto del sabor de esa pantalla (se omite en Turbo). Sale tanto desde
    Explorar como desde Cazar — la frase describe enfrentarte al enemigo, no
    cómo lo encontraste.
  - Persistencia sin tocar el esquema de guardado: reaprovecha
    `player.mundo["banderas"]` con dos flags por enemigo (`vio_a_<nombre>`,
    `perdio_contra_<nombre>`), el mismo patrón que ya usan los flags de
    diálogo.
  - Las 20 frases de encuentro y las provocaciones de El Carnicero/Dragón las
    escribió Claude siguiendo el tono ya establecido en cada `DESCRIPTION`;
    **revisadas y aprobadas por el usuario** tras probarlas en partida (si
    hace falta retocar o añadir más adelante, se hará entonces).
  - Tests: `tests/test_battle.py` — 1ª vez vs. repetición en un enemigo
    normal, la provocación de un élite solo se desbloquea tras perder,
    `_handle_defeat` solo marca la derrota en enemigos no-normales, se oculta
    en Turbo, y aparece en una batalla real de extremo a extremo.

- [x] **Pausa en la frase de encuentro, pantalla de victoria más informativa,
  y estadísticas del equipo a la vista** (feedback del usuario tras probar
  las frases de encuentro en partida real).
  - **Pausa tras la frase de encuentro**: `_announce_encounter` no paraba, así
    que el texto (intro o provocación) se perdía entre esa línea y la ficha
    de combate que sale justo detrás. Ahora, si imprime algo, pide "Presiona
    Enter para continuar..." antes de seguir; una repetición sin nada que
    decir (enemigo normal ya visto) no pide nada.
  - **Pantalla de victoria**: el oro y la XP obtenidos ahora muestran también
    el total/progreso actual — `💰 Oro obtenido: X (Total: Y)` y `✨ XP
    obtenida: +X (Nivel N: XP/XP necesaria)` —, y ya no se anuncia el nombre
    del siguiente enemigo desbloqueado (`✨ ¡NUEVO ENEMIGO DESBLOQUEADO!`
    eliminado): sigue desbloqueándose igual, pero el jugador debe descubrir
    quién es explorando, no leerlo en la pantalla de victoria. De paso se
    quitó el "Has obtenido X XP." que imprimía `Player.gain_experience()`
    por su cuenta, redundante con la nueva línea de `_handle_victory` (su
    único caller).
  - **Estadísticas del equipo a la vista**: en "Personaje → Estadísticas" y en
    "Equipar Armadura", cada hueco ocupado muestra ahora, junto al nombre,
    las estadísticas que otorga esa pieza (`Armor.get_stats_info()`, el mismo
    texto que ya se usaba en el botín de la victoria) — antes había que
    desequipar/volver a equipar o mirar la tienda para recordar qué daba cada
    cosa.
  - Tropiezo de esta ronda: la pausa nueva rompió varios tests de
    `test_battle.py` que encadenaban respuestas fijas de `console.ask` (p. ej.
    los de auto-batalla en cadena) porque el primer "Enter" de la pausa se
    comía la respuesta pensada para el menú siguiente — no era un bloqueo
    real de teclado, sino un bucle infinito local (`_player_menu` reintentando
    con `""` para siempre) que parecía un cuelgue. Se detectó instalando
    temporalmente `pytest-timeout` (no es una dependencia del proyecto,
    solo se usó para depurar) y se arregló añadiendo la respuesta extra en la
    posición correcta de cada secuencia mockeada.
  - Tests: `tests/test_battle.py` (la pausa solo cuando imprime algo; oro
    total y XP/nivel en la pantalla de victoria; el nombre del siguiente
    enemigo ya no se anuncia), `tests/test_player.py` (`show_stats()` lista
    las estadísticas del equipo), `tests/test_menus.py` (`_equip_armor_flow`
    hace lo mismo).

- [x] **Piedrablanca ya no puede acabar en combate al Explorar** (fix,
  feedback del usuario tras el merge de la v0.14.0-d). Motivo: el GDD dice
  explícitamente "Piedrablanca (hub, no enemies)" — es la aldea segura —,
  pero `_zone_candidates()` trataba cualquier zona sin roster propio igual:
  si no había enemigos declarados, caía a "cualquier enemigo ya
  desbloqueado", así que se podía "explorar" la plaza del pueblo y toparse
  con un Goblin o hasta con El Carnicero.
  - `Zone` (`world/zone.py`) gana un campo `is_hub: bool = False`, `True`
    solo en Piedrablanca (`world/data/piedrablanca.py`). Distingue dos
    situaciones que antes se trataban igual: un roster todavía sin diseñar
    (la Ciénaga de los Ahogados, que sí tendrá su propio bestiario en una
    sub-fase futura) frente a una zona que, por diseño, nunca tiene
    enemigos (solo Piedrablanca).
  - `_zone_candidates()`: si `zone.is_hub`, devuelve `[]` siempre, sin el
    fallback a "cualquier enemigo desbloqueado". La Ciénaga sigue exactamente
    igual que antes (el fallback sigue siendo el comportamiento correcto ahí,
    es temporal hasta que le toque su sub-fase).
  - `_explore()`: en un hub la rama de combate nunca se activa —
    `encounter_chance` pasa a ser 0 en vez de `_EXPLORE_ENCOUNTER_CHANCE`
    (0.65) —, pero el hallazgo de oro/pociones conserva exactamente su
    propia probabilidad (`_EXPLORE_DISCOVERY_CHANCE`, 0.15): la franja que
    antes iba a combate pasa a ser "nada de interés", no se la queda el
    hallazgo por error (hubiera inflado el hallazgo de 15% a 80%).
  - `_hunt_flow()`: en un hub, "Cazar..." avisa con un mensaje distinto
    ("Esto es una zona segura; aquí no hay nada que cazar.") antes incluso
    de mirar qué hay derrotado.
  - Tests: `tests/test_world.py` (`is_hub` en Piedrablanca, y que ninguna
    otra zona lo hereda sin querer), `tests/test_exploration.py` (el
    fallback de la Ciénaga se mantiene reescribiendo los tests que antes
    usaban Piedrablanca para probarlo; nuevos tests de que Piedrablanca
    nunca lucha aunque tengas el Dragón desbloqueado, de que el hallazgo
    conserva su probabilidad real y no la inflada, y del mensaje propio de
    "Cazar..." en un hub).

- [x] **El hallazgo de Explorar en Piedrablanca deja de ser infinito**
  (feedback del usuario, misma ronda que el fix de "no hay combate en el
  hub"). Motivo: al quitar el combate del hub, el hallazgo de oro/poción
  seguía saliendo cada vez que tocaba esa franja de la tirada — sin
  enemigos que farmear, el jugador podía quedarse quieto en el pueblo y
  Explorar sin fin para oro y pociones gratis.
  - `_give_discovery_potion(player)` / `_give_discovery_gold(player)`:
    extraídos de `_discovery` (mismo mensaje/objeto de siempre), ahora
    reutilizados también por el hub.
  - `_hub_discovery(player, zone)`: cada tipo de hallazgo (oro, poción) tiene
    su propio flag de una sola vez en `mundo["banderas"]`
    (`hallazgo_oro_<zona>` / `hallazgo_pocion_<zona>`, mismo patrón que los
    flags de diálogo). Con los dos disponibles, la tirada es la misma que en
    `_discovery`; agotado uno, se da directamente el que falta. Con los dos
    ya encontrados, Explorar muestra "Ya has encontrado todo lo que había
    que encontrar en Piedrablanca." en vez de otra recompensa.
  - Una zona normal (`_discovery`, `not zone.is_hub`) no cambia: el
    oro/pociones de un bosque o un páramo sigue sin límite, tiene sentido
    que la naturaleza no se agote igual que un pueblo pequeño.
  - Tests: `tests/test_exploration.py` — cada tipo sale como mucho una vez
    (primero uno, luego el otro aunque la tirada favorezca al ya agotado),
    y el mensaje de "ya no queda nada" una vez encontrados ambos.

- [x] **Tabla completa del bestiario (Excel) + poder de jugador/enemigo solo
  en DEBUG** (petición del usuario, a mayores tras el fix de Piedrablanca).
  - Tabla: `bestiario_valeterna.xlsx`, generada extrayendo los datos
    directamente del código (instancia real de cada uno de los 20 enemigos,
    `drop_table()`, `power_score()`/`target_score()` de
    `power_budget.py`) para que no haya errores de transcripción — entregada
    al usuario como archivo, no versionada en el repo (es una referencia de
    diseño, no algo que el código consuma). Columnas, en el orden elegido:
    Zona, Tier, Rango, Nombre, Arquetipo, Distintivo/Mecánica, Inflige,
    Débil a, Resiste, Inmune a, HP, Ataque, Armadura, Res. Mágica,
    Prob./Daño Crítico, Velocidad, Precisión, Evasión, Pen.
    Armadura/Mágica, Oro, Experiencia, Botín, **Poder real** y **Objetivo de
    poder** (las dos últimas, del `power_budget.py`: se añadió "Poder real"
    además de lo pedido porque es el contraste que hace útil la
    herramienta). "Arquetipo" es la única columna sin fuente directa en el
    código — una etiqueta de una línea escrita a mano por enemigo, a partir
    de su `SIGNATURE`/`DESCRIPTION`.
  - **Modo DEBUG** (`config/debug.py::is_debug()`): activado solo por la
    variable de entorno `VALETERNA_DEBUG` (mismo patrón que `$CI` en
    `updater.py` o `$JRT_CRASH_WEBHOOK` en `crash_reporting.py`), nunca
    desde dentro del juego — ni siquiera el personaje "admin" lo activa, es
    una herramienta de desarrollo, no un cheat de partida. Se usa en
    `ui/formatting.py::print_player_enemy_info()`: añade una línea
    "[DEBUG] Poder: X" bajo la ficha de cada combatiente. La del jugador usa
    sus totales reales (arma/armadura equipada incluida, vía
    `get_total_*()`); la del enemigo, `enemy.stats` directamente. A
    diferencia del resto de esa ficha, el poder del enemigo se muestra
    siempre, incluso sin haberlo derrotado nunca (`revealed=False`) — es
    para testear, no información que un jugador vaya a leer.
  - Tests: `tests/test_debug.py` (parseo de la variable de entorno),
    `tests/test_formatting.py` (sin DEBUG no sale nada; con DEBUG sale para
    los dos; el del enemigo ignora `revealed`).

- [x] **v0.14.0-e: Bosque de los Susurros a 10 enemigos** (GDD §4.1/§4.7).
  Mismo patrón que Los Yermos (v0.14.0-c): Orco, Espíritu Vengativo y Troll
  (tiers 1-3) se quedan tal cual, y se añaden 7 enemigos nuevos siguiendo la
  plantilla de tiers del GDD §4.1 (1-4/6/8 estándar, 5/7/9 élite, 10
  guardián). El guardián se ató a la lore ya escrita del Claro del Altar
  ("lo que se ata aquí no descansa; lo que lo ata, tampoco") — de ahí "El
  Enraizado".
  - **Roster** (tier · rango · nombre · mecánica): 4 · estándar · Araña
    Tejesombras · mordisco venenoso; 5 · élite · Druida Corrupto ·
    autocuración + maldición (oscuridad); 6 · estándar · Oso Espectral ·
    vida robada (nueva mecánica, cura con parte del daño infligido en cada
    golpe, no solo bajo un umbral de vida); 7 · élite · Enjambre de
    Polillas Pálidas · segundo golpe periódico + veneno; 8 · estándar ·
    Lobo Umbrío · acecha tras la primera derrota (como el Goblin); 9 ·
    élite · Ent Corrompido · golpe de raíces inesquivable (como el Gólem);
    10 · guardián · El Enraizado · autocuración bajo 40% + maldición al
    golpear (oscuridad), abre el Cañón del Trueno.
  - Todas las mecánicas reutilizan patrones ya implementados (nada de
    estados nuevos) — decisión explícita del usuario: "las mecánicas las
    revisaremos más detalladamente más adelante, por ahora pondremos algo
    como lo que tenemos, pero seguramente alguna se cambie según vaya
    probando el juego para que no sea repetitivo".
  - **El tema central de esta ronda: dificultad progresiva de verdad.** El
    usuario señaló que si se llega al Bosque es porque se ha superado Los
    Yermos, así que el Bosque tiene que ser más difícil que Los Yermos, y
    así sucesivamente con cada zona — no basta con que el enemigo tier 1
    del Bosque supere el objetivo *formal* de su propio tier 1 (que
    reinicia bajo en cada zona nueva), tiene que superar de verdad al
    enemigo que el jugador acaba de vencer. El problema concreto: Troll
    (tier 3, ya implementado antes de que existiera `power_budget.py`)
    tiene un poder real de ~38.062, muy por encima de su propio objetivo
    formal (~10.336) — diseñar los tiers 4-10 contra la curva objetivo en
    vez de contra el poder real de Troll habría hecho que la dificultad
    *bajara* justo después de él, justo lo contrario de lo pedido.
  - **Solución**: cada tier nuevo se dimensionó para superar el poder real
    (no el objetivo formal) del tier anterior, con una progresión de
    Troll (~38k) → Araña (~46k) → Druida (~52k) → Oso Espectral (~62k) →
    Enjambre (~69k) → Lobo Umbrío (~82k) → Ent Corrompido (~99k) → El
    Enraizado (~112k) — y el poder real de El Enraizado se dejó
    deliberadamente por debajo del de Gárgola (~120k, primer enemigo del
    Cañón del Trueno) para que la propia transición de zona también sea
    progresiva. Consecuencia aceptada: 6 de los 7 enemigos nuevos (todos
    menos Araña Tejesombras) caen fuera del rango `[tier1, tier10]` que
    marca la curva formal de su zona — se documentó explícitamente en
    `tests/test_power_budget.py::_KNOWN_OUT_OF_RANGE`, con el motivo, en
    vez de forzarlos a encajar y romper la progresión real.
  - Cadena de desbloqueo: `Troll → Araña Tejesombras → Druida Corrupto →
    Oso Espectral → Enjambre de Polillas Pálidas → Lobo Umbrío → Ent
    Corrompido → El Enraizado → Gárgola` (el resto de la cadena, sin
    cambios).
  - El Enraizado es el segundo enemigo marcado `ENCOUNTER_KIND="guardian"`
    (tras El Carnicero) con su propia frase de encuentro y provocaciones,
    usando el sistema de v0.14.0-d.
  - Tests: `tests/test_bosque_10.py` (15 tests: mecánicas de los 7 enemigos
    nuevos), `tests/test_new_enemies.py` (cadena de desbloqueo
    actualizada), `tests/test_power_budget.py` (excepciones documentadas).
    Probado también con un combate simulado completo de extremo a extremo
    contra los 8 enemigos de la cadena hasta El Enraizado (victoria en
    todos, desbloqueo correcto de Gárgola al final).

- [x] **Poder del jugador en Estadísticas, solo en DEBUG** (feedback del
  usuario). Faltaba en "Personaje → Estadísticas" — solo se veía en la ficha
  previa a un combate. `Player.show_stats()` ahora imprime la misma línea
  "[DEBUG] Poder: X" (usando `get_attack_range()`/`get_magic_attack_range()`
  y los `get_total_*()` de siempre, con equipo incluido), bajo el mismo
  `is_debug()` de `config/debug.py`.
- [x] **Rata Gigante ahora es más poderosa que el Goblin** (feedback del
  usuario, playtest real): el diseño original de v0.14.0-c le dio a la Rata
  Gigante el tier 1 (más flojo) y al Goblin el tier 2, con el razonamiento
  de que el Goblin debía seguir siendo el primer encuentro del juego aunque
  su tier de diseño fuese más alto — pero eso significaba que el segundo
  enemigo que el jugador se encuentra de verdad (Rata Gigante, justo después
  de vencer al Goblin) era más débil que el primero, lo contrario de lo que
  se siente jugando. Subida de HP28→34, ataque 6-10→8-13, velocidad 14→15
  (armadura sin cambios): su poder real pasa de ~3.214 a ~5.489, ya por
  encima del Goblin (~4.532).
- [ ] **Pendiente de discutir con más profundidad: el poder del jugador crece
  demasiado rápido con nivel + equipo, frente al de los enemigos** (feedback
  del usuario, playtest real, v0.14.0-e). Datos concretos que dio el
  usuario: personaje recién creado, poder ~8.062; nivel 2, ~15.480 (+92% en
  un solo nivel); tras 19 combates en Auto-Batalla Turbo contra el Goblin
  (subiendo casi al nivel 4) y con una única Espada Goblin equipada (+4 de
  daño, un drop bastante común, 10% de probabilidad), poder ~30.326 — con
  eso, según el propio usuario, "básicamente me podría pasar prácticamente
  todo Los Yermos", y en la práctica se lo pasó en una prueba rápida.
  - El usuario planteó dos vías (no excluyentes): frenar cuánto poder gana
    el jugador por nivel/equipo, o subir el poder de los enemigos en
    función del nivel/equipo esperado del jugador en cada punto de la
    cadena — y preguntó si abordarlo ya o dejarlo anotado para después de
    terminar de rellenar el roster de las zonas que faltan (Ciénaga, Cañón,
    Torre/Necrópolis, Ciudadela, Corazón de la Brecha).
  - Decisión: **anotado para más adelante**, no abordado en esta sesión —
    es un rebalanceo transversal (afecta la curva de subida de nivel, el
    daño de las armas que sueltan los enemigos, y probablemente las stats
    de varios de los 27 enemigos ya implementados), y hacerlo a medias
    ahora, con la mitad del roster todavía sin diseñar, arriesga tener que
    repetirlo cuando existan datos de la cadena completa. Encaja con el
    rebalanceo de los 14 originales que ya estaba pendiente (ver más
    arriba, "junto con el rebalanceo completo de la cadena de 14 enemigos")
    — se puede hacer todo en la misma pasada.
  - Sospechas para cuando se aborde, a falta de medir con datos reales: (1)
    el multiplicador de daño crítico de las armas parece generoso para lo
    pronto que se consiguen (un dropeo del Goblin al 10% de probabilidad ya
    da +4 de daño, un salto grande sobre el 8-12 base); (2) los saltos de
    nivel tempranos (`Player._required_xp_for_level`, el "damping" de
    niveles 2-9) puede que compriman demasiado rápido la curva de XP contra
    lo rápido que sube el poder real; (3) el propio Auto-Batalla Turbo hace
    trivial acumular decenas de combates sin fricción, así que cualquier
    curva de crecimiento se nota antes y con más fuerza que en juego manual
    — merece la pena medir ambos modos por separado.

## Pulido final (casi lo último antes de 1.0)

- [ ] **Más sonidos de ataque por clase / elemento.** Hoy todo ataque suena
  `hit`/`slash` al azar. El Arcanista debería sonar a magia, el Guerrero a
  espada/contundente, etc.; los hechizos elementales de enemigos y jugador,
  a su elemento (fuego, rayo, hielo…). Ampliar `audio/catalog.py` y elegir el
  SFX según quién ataca y con qué.
- [ ] **Revisar/mejorar la música** (más pistas, mejor encaje por
  zona/situación). Junto con la música por élite/guardián ya anotada arriba.
