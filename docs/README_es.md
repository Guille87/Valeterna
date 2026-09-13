# Valeterna

<p align="center"><a href="../README.md">English</a> · <a href="README_es.md">Español</a></p>

[![CI](https://github.com/Guille87/Valeterna/actions/workflows/ci.yml/badge.svg)](https://github.com/Guille87/Valeterna/actions/workflows/ci.yml)
[![Coverage](https://raw.githubusercontent.com/Guille87/Valeterna/badges/coverage.svg)](https://github.com/Guille87/Valeterna/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](../LICENSE)
[![Contributors](https://img.shields.io/github/contributors/Guille87/Valeterna)](https://github.com/Guille87/Valeterna/graphs/contributors)
[![Issues](https://img.shields.io/github/issues/Guille87/Valeterna)](https://github.com/Guille87/Valeterna/issues)
[![Pull requests](https://img.shields.io/github/issues-pr/Guille87/Valeterna)](https://github.com/Guille87/Valeterna/pulls)

**Valeterna** es un RPG de batalla por turnos en consola, en español, escrito en
Python. Enfréntate a una cadena de 14 enemigos, gestiona equipo y pociones,
fabrica objetos en la herrería y haz crecer a tu personaje. Se juega enteramente
en la terminal — no hay ventana gráfica; `colorama` da color y `pygame` (solo el
mixer) pone la música.

<p align="center"><img src="../docs/screenshot.svg" alt="Un combate contra un Goblin: ataque, turnos ATB, victoria y subida de nivel" width="640"></p>

## Características

- Combate **ATB (Active Time Battle)**: el combatiente más rápido actúa más veces,
  no es una alternancia estricta.
- **14 enemigos** con mecánicas propias y una cadena de desbloqueo fija que termina en el Dragón.
- **11 huecos de equipo estilo Diablo**, cada uno con una estadística base garantizada más secundarias aleatorias.
- **Herrería** (12 recetas), **tienda** y un **bestiario** que se completa a medida que ganas.
- Daño físico y mágico, penetración, debilidades elementales y efectos de estado.
- Guardado/carga en JSON con copia de seguridad automática; registro de errores en disco e informe opcional a Discord.

## Requisitos

- Python **3.10 o superior** (la CI prueba 3.10–3.13).
- **Solo Windows** por ahora: el modo auto-batalla usa `msvcrt` para poder cancelarse con `q`.

## Instalación

```powershell
git clone https://github.com/Guille87/Valeterna.git
cd Valeterna
python -m venv env
.\env\Scripts\activate
pip install -e ".[dev]"
```

El extra `[dev]` añade `pytest`, `pytest-cov` y `ruff`. Si solo quieres jugar, `pip install -e .` es suficiente.

## Ejecutar

```bash
python main.py
# o: python -m valeterna
# o, tras instalar: valeterna
```

## Tests

```bash
pytest                              # ejecutar la suite
pytest --cov=valeterna        # con cobertura
ruff check . && ruff format --check .
```

## Generar un ejecutable

```powershell
pip install pyinstaller
pyinstaller Valeterna.spec
```

El resultado queda en `dist\Valeterna\` — copia la **carpeta entera** (necesita
los assets y las DLLs que la acompañan). `config.ini`, `saved_games\` y `logs\` se
crean junto al `.exe`. Usa `--onedir` (el `.spec` ya lo hace), nunca `--onefile`.

El juego empaquetado **se actualiza solo**: al arrancar comprueba si hay una
versión más nueva en los GitHub Releases y, si aceptas, la descarga, verifica su
SHA-256 y se reinicia — `saved_games\` y `config.ini` se conservan. La
comprobación se desactiva en *Opciones*.

El informe opcional de errores a Discord vive en `src/valeterna/config/secrets.py`
(no versionado). Copia `config/secrets.example.py` a `config/secrets.py` y rellénalo
antes de compilar; sin él el juego funciona igual, solo sin informes de errores.

## Documentación

- [Guía de contribución](CONTRIBUTING_es.md) — flujo de trabajo y convenciones.
- [GDD](GDD_es.md) — documento de diseño (mundo, historia, dirección RPG).
- [Roadmap](ROADMAP_es.md) — qué está hecho y qué está planeado.
- [Changelog](CHANGELOG_es.md) — historial de versiones.
- [CLAUDE.md](../CLAUDE.md) — notas de arquitectura detalladas (en inglés).
- [TODO.md](../TODO.md) — historial detallado de decisiones de balance.

## Licencia

[MIT](../LICENSE) © 2026 Guillermo Amado.
