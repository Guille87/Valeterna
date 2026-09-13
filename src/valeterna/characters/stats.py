import random

# Tirada de acierto compartida por el ataque estándar del jugador
# (combat/battle.py::_execute_turn) y el ataque por defecto del enemigo
# (characters/enemies/enemy_base.py::Enemy.perform_turn). Vive aquí, en un
# módulo hoja sin dependencias de combate ni de personajes concretos, para que
# ambos puedan importarla sin crear un ciclo de imports.
BASE_HIT_CHANCE = 100
MIN_HIT_CHANCE = 5
MAX_HIT_CHANCE = 100


# Curva de reducción de daño por defensa, estilo Raid: Shadow Legends. En vez de
# restar la armadura (lineal: o es inútil o es un muro), se reduce un porcentaje
# con rendimientos decrecientes: reduccion = DEF / (DEF + K). Cada punto de
# armadura vale un poco menos que el anterior y el daño nunca llega a 0.
# K está escalado a los números de este juego (armaduras de ~2 a ~25): con K=20,
# armadura 20 reduce el 50%, armadura 5 reduce el 20%.
DEFENSE_SOFTENING = 20


def apply_mitigation(amount: int, mitigation: int) -> int:
    """Aplica la reducción de daño por defensa (`mitigation` = armadura o
    resistencia mágica, ya con la penetración del atacante restada). Un `amount`
    de 0 sigue haciendo 0; cualquier golpe real hace al menos 1."""
    if amount <= 0:
        return 0
    mitigation = max(0, mitigation)
    reduced = amount * DEFENSE_SOFTENING / (mitigation + DEFENSE_SOFTENING)
    return max(1, round(reduced))


def resolve_hit(attacker_precision: int, defender_evasion: int) -> bool:
    """Tirada de acierto: precisión del atacante vs evasión del defensor.

    Parte de un 100% de acierto base: contra evasión 0, el atacante acierta
    siempre (la evasión es la única fuente de esquivar, no un margen de fallo
    "de base" que existiera incluso sin evasión). Cada punto de evasión del
    defensor por encima de la precisión del atacante resta 1% de acierto, con
    un suelo del 5% (un ataque nunca falla al 100% aunque la evasión sea
    altísima) y techo del 100%.
    """
    chance = BASE_HIT_CHANCE + attacker_precision - defender_evasion
    chance = max(MIN_HIT_CHANCE, min(MAX_HIT_CHANCE, chance))
    return random.random() * 100 < chance


class Stats:
    """Maneja las estadísticas básicas con validación de límites."""

    def __init__(
        self,
        health: int,
        max_health: int,
        min_atk: int,
        max_atk: int,
        armor: int,
        magic_resist: int = 0,
        crit_chance: float = 0.0,
        crit_damage: float = 1.5,
        speed: int = 10,
        precision: int = 0,
        evasion: int = 0,
        armor_penetration: int = 0,
        magic_penetration: int = 0,
        regen: int = 0,
        magic_power: int = 0,
    ):
        self.max_health = max_health
        self._health = health
        self.min_atk = min_atk
        self.max_atk = max_atk
        self.armor = armor
        self.magic_resist = magic_resist
        self.crit_chance = crit_chance
        self.crit_damage = crit_damage
        # Velocidad: alimenta el sistema de barra ATB en combat/battle.py (más
        # velocidad = actuar con más frecuencia, no solo "ir primero").
        self.speed = speed
        # Precisión/Evasión: alimentan resolve_hit() de más arriba.
        self.precision = precision
        self.evasion = evasion
        # Penetración: reduce la armadura/resistencia mágica *del objetivo* al
        # calcular la mitigación en take_damage (Player.take_damage /
        # Enemy.take_damage), no es un stat propio de "recibir" daño.
        self.armor_penetration = armor_penetration
        self.magic_penetration = magic_penetration
        # Regeneración de salud pasiva (HP curados cada turno, aplicada por
        # quien la use — Player.on_turn_start() / Enemy.on_turn_end()).
        self.regen = regen
        # Poder mágico: fuente de daño del ataque estándar del Arcanista
        # (is_magical). 0 para el resto de clases y para todos los enemigos.
        self.magic_power = magic_power

    @property
    def health(self) -> int:
        return self._health

    @health.setter
    def health(self, value: int) -> None:
        # Encapsulamiento: Aseguramos que la vida esté en el rango [0, max_health]
        self._health = max(0, min(value, self.max_health))

    def __str__(self) -> str:
        return (
            f"HP: {self.health}/{self.max_health} | ATK: {self.min_atk}-{self.max_atk} "
            f"| ARM: {self.armor} | RES.MAG: {self.magic_resist} "
            f"| CRIT: {self.crit_chance * 100:.0f}% x{self.crit_damage:.2f}"
        )
