"""Capa de presentación: centraliza el uso de colorama en toda la aplicación."""

import re

from colorama import Fore, Style

__all__ = [
    "Fore",
    "Style",
    "success",
    "error",
    "warning",
    "info",
    "title",
    "colorize",
    "ask",
    "say",
    "tint_status",
    "STAT_COLORS",
    "stat_line",
    "ELEMENT_COLORS",
    "element_color",
    "crit_suffix",
]

# --- Coloreado automático de estados alterados ---------------------------------
# Cualquier texto que mencione un estado se colorea igual en todo el juego, con
# un color propio por estado. `colorize()` lo aplica solo, así que basta con usar
# los helpers de este módulo.
_STATUS_PATTERNS = (
    (re.compile(r"\b(?:veneno|venenos[oa]s?|envenen\w*)\b", re.IGNORECASE), Fore.GREEN),
    (re.compile(r"\b(?:quemad\w*|quemaduras?|quema)\b", re.IGNORECASE), Fore.RED),
    (re.compile(r"\b(?:par[aá]lisis|paraliz\w*)\b", re.IGNORECASE), Fore.YELLOW),
    (re.compile(r"\b(?:congelaci[oó]n|congelad[oa]s?|congela)\b", re.IGNORECASE), Fore.BLUE),
    # sangrado: rojo claro, distinto del rojo normal de la quemadura.
    (re.compile(r"\b(?:sangrado|sangra\w*|herido de gravedad)\b", re.IGNORECASE), Fore.LIGHTRED_EX),
    # aturdimiento: amarillo claro, distinto del amarillo de la parálisis.
    (re.compile(r"\b(?:aturdi\w*|aturdimiento)\b", re.IGNORECASE), Fore.LIGHTYELLOW_EX),
    (re.compile(r"\b(?:desarmad[oa]s?)\b", re.IGNORECASE), Fore.LIGHTBLACK_EX),
    (re.compile(r"\b(?:maldici[oó]n|maldit[oa]s?)\b", re.IGNORECASE), Fore.MAGENTA),
    (re.compile(r"\b(?:confusi[oó]n|confundid[oa]s?)\b", re.IGNORECASE), Fore.CYAN),
    # contraataque / represalia: magenta claro.
    (re.compile(r"\b(?:contraataqu\w*|contraatac\w*|represalias?)\b", re.IGNORECASE), Fore.LIGHTMAGENTA_EX),
)


def tint_status(text: str, back_to: str = "") -> str:
    """Colorea las palabras de estados alterados dentro de `text`. `back_to` es
    la secuencia de color a la que volver tras cada palabra (para no romper el
    color de una línea que ya venía coloreada)."""

    def _replace(match: re.Match, color: str) -> str:
        return f"{Style.BRIGHT}{color}{match.group(0)}{Style.RESET_ALL}{back_to}"

    for pattern, color in _STATUS_PATTERNS:
        text = pattern.sub(lambda m, c=color: _replace(m, c), text)
    return text


def colorize(text: str, color: str, bright: bool = False) -> str:
    """Envuelve un fragmento de texto en un color, sin resetear el estilo global.
    De paso resalta cualquier estado alterado que se mencione en el texto."""
    prefix = f"{Style.BRIGHT}{color}" if bright else color
    return f"{prefix}{tint_status(text, prefix)}{Style.RESET_ALL}"


def success(message: str) -> None:
    print(colorize(message, Fore.GREEN))


def error(message: str) -> None:
    print(colorize(message, Fore.RED))


def warning(message: str) -> None:
    print(colorize(message, Fore.YELLOW))


def info(message: str) -> None:
    print(colorize(message, Fore.CYAN))


def title(message: str) -> None:
    print(colorize(message, Fore.YELLOW, bright=True))


def say(message: str) -> None:
    """Imprime texto sin color de fondo, pero resaltando los estados alterados."""
    print(tint_status(message))


def ask(prompt: str) -> str:
    """Wrapper fino de input(), punto único para interceptar/testear entradas.

    Si stdin se cierra (Ctrl+Z, entrada canalizada agotada, consola sin TTY),
    salimos limpiamente en vez de dejar que el `EOFError` burbujee hasta
    `app.main()` y se registre como un cierre inesperado (con su informe a
    Discord incluido).
    """
    try:
        return input(prompt)
    except EOFError:
        print()
        raise SystemExit(0) from None


# --- Color por estadística ----------------------------------------------------
# Un color fijo por concepto para que las fichas (jugador, enemigo, bestiario)
# sean más fáciles de leer de un vistazo.
STAT_COLORS = {
    "nivel": Fore.CYAN,
    "vida": Fore.GREEN,
    "ataque": Fore.RED,
    "armadura": Fore.BLUE,
    "magica": Fore.LIGHTBLUE_EX,
    "critico": Fore.YELLOW,
    "velocidad": Fore.MAGENTA,
    "precision": Fore.LIGHTCYAN_EX,
    "evasion": Fore.LIGHTGREEN_EX,
    "penetracion": Fore.LIGHTMAGENTA_EX,
    "regen": Fore.GREEN,
    "kills": Fore.LIGHTYELLOW_EX,
    "oro": Fore.YELLOW,
    "xp": Fore.LIGHTBLACK_EX,
    "elemento": Fore.CYAN,
    "equipo": Fore.BLUE,
}


def stat_line(text: str, key: str, bright: bool = True) -> str:
    """Colorea una línea de estadística según su concepto (`STAT_COLORS`)."""
    return colorize(text, STAT_COLORS.get(key, Fore.WHITE), bright=bright)


# --- Color por elemento de daño ---------------------------------------------
# Mismo criterio que los estados: veneno verde, fuego rojo, rayo amarillo,
# hielo azul (+ los tres nuevos).
ELEMENT_COLORS = {
    "fuego": Fore.RED,
    "veneno": Fore.GREEN,
    "rayo": Fore.YELLOW,
    "hielo": Fore.BLUE,
    "sagrado": Fore.LIGHTWHITE_EX,
    "oscuridad": Fore.MAGENTA,
    "arcano": Fore.CYAN,
}


def element_color(element: str | None):
    """Color de colorama para un elemento (rojo por defecto)."""
    return ELEMENT_COLORS.get(element or "", Fore.RED)


def crit_suffix(is_crit: bool) -> str:
    """Sufijo para pegar al final de la línea de daño cuando ha sido crítico."""
    return colorize("  💥 ¡Golpe crítico!", Fore.YELLOW, bright=True) if is_crit else ""
