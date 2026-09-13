"""Capa de textos traducibles (GDD §9.1).

Todo el texto de cara al jugador **nuevo** se escribe con `t("clave", **kwargs)`
en vez de una cadena literal. El texto ya existente se irá migrando poco a poco.

    from valeterna import i18n
    print(i18n.t("combat.enemy_succumbs", name="Goblin"))

El idioma activo se fija al arrancar (`config.ini` `[IDIOMA] idioma`, por
defecto `es`). Si una clave no existe en el catálogo activo, se cae al catálogo
`es`, y si tampoco está, se devuelve la propia clave (nunca revienta).
"""

from valeterna.i18n.catalog_es import CATALOG as _CATALOG_ES

_CATALOGS: dict[str, dict[str, str]] = {"es": _CATALOG_ES}
DEFAULT_LOCALE = "es"
_locale = DEFAULT_LOCALE


def available_locales() -> list[str]:
    return sorted(_CATALOGS)


def has(key: str) -> bool:
    """¿Existe esta clave en el idioma activo o en el catálogo `es`?"""
    return key in _CATALOGS.get(_locale, {}) or key in _CATALOG_ES


def get_locale() -> str:
    return _locale


def set_locale(code: str) -> None:
    """Fija el idioma activo. Un código desconocido cae al de por defecto."""
    global _locale
    _locale = code if code in _CATALOGS else DEFAULT_LOCALE


def t(key: str, /, **kwargs) -> str:
    """Devuelve el texto de `key` en el idioma activo, con `kwargs` interpolados
    (`{name}` -> `kwargs["name"]`). Si falta la clave o un parámetro, degrada de
    forma segura en vez de lanzar."""
    template = _CATALOGS.get(_locale, {}).get(key) or _CATALOG_ES.get(key) or key
    try:
        return template.format(**kwargs) if kwargs else template
    except (KeyError, IndexError):
        return template
