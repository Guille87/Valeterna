# Guía de contribución

<p align="center"><a href="../CONTRIBUTING.md">English</a> · <a href="CONTRIBUTING_es.md">Español</a></p>

Gracias por tu interés. El proyecto es pequeño; estas son las convenciones.

## Antes de empezar

- **Python 3.10 o superior** (la CI prueba 3.10–3.13). `pip install -e ".[dev]"`
  trae `pytest`, `pytest-cov` y `ruff`; no hace falta nada más.
- **Solo Windows** por ahora (`msvcrt` se usa en `combat/battle.py` para que el
  modo auto-batalla pueda cancelarse con `q`).
- Los comandos habituales están en el [README](README_es.md); la arquitectura,
  en [CLAUDE.md](../CLAUDE.md); el historial detallado de balance, en [TODO.md](../TODO.md).

## Flujo de trabajo

1. Crea una rama a partir de `main`.
2. Un commit por unidad lógica de cambio.
3. Ejecuta `ruff format .`, luego `ruff check .`, luego `pyright`, y luego `pytest`: debe pasar todo.
4. Abre una *pull request*. La CI ejecuta Ruff y los tests en Python 3.10–3.13
   (Windows) y actualiza el badge de cobertura; tiene que quedar en verde.

## Convenciones

- **Código y comentarios en español**, consistente con el resto del proyecto.
  No hay capa de i18n: los textos del juego se imprimen directamente.
- **Todo color de terminal pasa por `ui/console.py`** (`success` / `error` /
  `warning` / `info` / `colorize`), nunca `colorama` directo.
- **Mensajes de commit**: prefijo `feat:`, `fix:`, `docs:`, `refactor:`,
  `test:`, `ci:`, `build:`, `style:` o `chore:`, y el resto en imperativo.
- Sin línea `Co-Authored-By` de herramientas de IA en los commits.
- **Compatibilidad de partidas**: al añadir un campo a `Stats` o al guardado,
  léelo de vuelta con `.get(clave, valor_por_defecto)` en
  `persistence/save_load.py` para que las partidas de versiones anteriores sigan
  cargando. Hay tests que cargan partidas mínimas/antiguas.

## Añadir un enemigo o un objeto

El patrón completo está en [CLAUDE.md](../CLAUDE.md):

- **Enemigo**: un archivo en `characters/enemies/` con una clase que hereda de
  `Enemy` y sobreescribe `perform_turn()` / `drop_item()`; registra el nombre en
  español en `ui/menus.py::_get_enemy_instance()` y colócalo en
  `combat/battle.py::ENEMY_PROGRESSION`.
- **Objeto**: registra la clase en `items/factory.py::_ITEM_CLASSES` e implementa
  `to_dict()` / `from_dict()`, o el guardado/carga lo descartará en silencio.

Todo cambio de lógica va con su test.

## Regenerar la captura del README

`docs/screenshot.svg` la genera `tools/capture_screenshot.py` (un combate real,
con semilla fija, renderizado como SVG de terminal). Para actualizarla:

```bash
pip install ansitoimg
python tools/capture_screenshot.py
```

## Publicar una versión

- Sube `version` en `pyproject.toml` y vuelve a ejecutar `pip install -e .` para
  que `valeterna.__version__` coja el valor nuevo en local (la CI y la
  build de release siempre instalan desde cero, así que ahí siempre es correcto).
- Mueve lo que corresponda de *Unreleased* a la nueva versión en
  [`CHANGELOG.md`](../CHANGELOG.md) y [`docs/CHANGELOG_es.md`](CHANGELOG_es.md).
- Crea el tag y empújalo:

  ```bash
  git tag vX.Y.Z && git push origin vX.Y.Z
  ```

El workflow de release construye el paquete de Windows y lo adjunta al GitHub
Release, junto con un archivo `SHA256SUMS`. Ambos son obligatorios: el
auto-updater del juego empaquetado se niega a aplicar un release que no tenga su
pareja `-windows.zip` + `SHA256SUMS`.
