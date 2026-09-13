import random

from valeterna import i18n
from valeterna.characters.stats import Stats, apply_mitigation, resolve_hit
from valeterna.combat.elements import affinity_multiplier
from valeterna.ui import console


def status_label(name: str) -> str:
    """Nombre legible de un estado alterado (`fractura_magica` -> `fractura mágica`)."""
    return i18n.t(f"status.{name}")


class Enemy:
    # --- Afinidades elementales (GDD §5). Las subclases sobrescriben estos
    # conjuntos de clase.
    WEAKNESSES: frozenset = frozenset()
    RESISTANCES: frozenset = frozenset()
    IMMUNE_ELEMENTS: frozenset = frozenset()
    IMMUNE_STATUSES: frozenset = frozenset()

    def __init__(self, name: str, stats: Stats, gold_min: int, gold_max: int):
        self.name = name
        self.stats = stats  # Objeto de la clase Stats
        self.gold_min = gold_min
        self.gold_max = gold_max
        # Estados alterados: [{"name": "quemado", "duration": 3, "power": 0}, ...]
        self.status_effects: list[dict] = []
        # Mensajes a mostrar DESPUÉS del resumen del turno (barras de vida),
        # no en mitad de él: cambios de estado tipo "se ha enfurecido".
        self._announcements: list[str] = []

    def get_gold_drop(self) -> int:
        return random.randint(self.gold_min, self.gold_max)

    def announce(self, message: str) -> None:
        """Encola un mensaje para mostrarlo tras el resumen del turno."""
        self._announcements.append(message)

    def pop_announcements(self) -> list[str]:
        msgs, self._announcements = self._announcements, []
        return msgs

    # --- AFINIDADES ---

    def affinity_for(self, elements) -> float:
        """Multiplicador de daño del ataque (`elements`: normalmente 1 elemento)
        contra este enemigo, combinando debilidades/resistencias/inmunidades."""
        cls = type(self)
        return affinity_multiplier(
            elements,
            weaknesses=cls.WEAKNESSES,
            resistances=cls.RESISTANCES,
            immune_elements=cls.IMMUNE_ELEMENTS,
        )

    def resists_element(self, element: str | None) -> bool:
        return bool(element) and element in type(self).RESISTANCES

    def is_immune_to_status(self, name: str) -> bool:
        return name in type(self).IMMUNE_STATUSES

    # --- DAÑO ---

    def take_damage(
        self,
        damage: int,
        defeated_enemies: list | None = None,
        element: str | None = None,
        is_magical: bool = False,
        armor_penetration: int = 0,
        magic_penetration: int = 0,
    ) -> int:
        # Multiplicador elemental (débil / resistente / inmune).
        damage = int(damage * self.affinity_for({element}))

        # "consagrado": el objetivo recibe +25 % de daño de todo.
        if any(e["name"] == "consagrado" for e in self.status_effects):
            damage = int(damage * 1.25)

        if is_magical:
            # "fractura mágica": la resistencia mágica cuenta como 0 mientras dure.
            fractured = any(e["name"] == "fractura_magica" for e in self.status_effects)
            base_resist = 0 if fractured else self.stats.magic_resist
            mitigation = base_resist - magic_penetration
        else:
            mitigation = self.stats.armor - armor_penetration
        actual_damage = apply_mitigation(damage, mitigation)
        self.stats.health -= actual_damage
        return actual_damage

    def is_alive(self) -> bool:
        return self.stats.health > 0

    def get_attack_damage(self) -> int:
        dmg = random.randint(self.stats.min_atk, self.stats.max_atk)
        # "quemado" reduce el ataque FÍSICO a la mitad (los ataques mágicos de
        # los enemigos calculan su daño aparte y no pasan por aquí).
        if any(e["name"] == "quemado" for e in self.status_effects):
            dmg //= 2
        return dmg

    # --- CURACIÓN (para los enemigos que se curan: Troll, Mago, Ángel Caído) ---

    def heal(self, amount: int) -> int:
        """Cura `amount` HP respetando `consagrado` (bloquea la autocuración) y
        `marchito` (la reduce a la mitad). Devuelve el HP realmente curado."""
        if any(e["name"] == "consagrado" for e in self.status_effects):
            return 0
        if any(e["name"] == "marchito" for e in self.status_effects):
            amount //= 2
        before = self.stats.health
        self.stats.health = min(self.stats.max_health, self.stats.health + amount)
        return self.stats.health - before

    # --- ESTADOS ALTERADOS ---

    def apply_status(self, name: str, duration: int, power: int = 0) -> bool:
        """Aplica un estado. Devuelve False (sin efecto) si el enemigo es inmune
        a él. Si ya lo tiene, refresca la duración al máximo de ambas."""
        if self.is_immune_to_status(name):
            return False
        for effect in self.status_effects:
            if effect["name"] == name:
                effect["duration"] = max(effect["duration"], duration)
                effect["power"] = max(effect.get("power", 0), power)
                return True
        self.status_effects.append({"name": name, "duration": duration, "power": power, "fresh": True})
        return True

    def on_turn_start(self) -> bool:
        """Procesa los estados al inicio del turno del enemigo. Devuelve si puede
        actuar (parálisis/congelación pueden hacerle perder el turno)."""
        can_act = True
        for effect in self.status_effects[:]:
            if effect["name"] == "congelado":
                # Primer turno congelado seguro; después, 20% por turno de romperlo.
                if not effect.get("fresh") and random.random() < 0.20:
                    console.info(i18n.t("combat.enemy_thaws", name=self.name))
                    self.status_effects.remove(effect)
                else:
                    effect["fresh"] = False
                    print(console.colorize(i18n.t("combat.enemy_frozen", name=self.name), console.Fore.BLUE))
                    can_act = False
                    break
            elif effect["name"] == "paralizado":
                if effect.get("fresh") or random.random() < 0.5:
                    console.warning(i18n.t("combat.enemy_paralysed", name=self.name))
                    can_act = False
                effect["fresh"] = False
            elif effect["name"] == "aturdido":
                console.warning(i18n.t("combat.enemy_stunned", name=self.name))
                can_act = False

        for effect in self.status_effects[:]:
            if effect["name"] == "quemado":
                dmg = max(1, self.stats.max_health // 16)
                self.stats.health -= dmg
                console.error(i18n.t("combat.enemy_burn", amount=dmg, name=self.name))
            elif effect["name"] == "veneno":
                dmg = max(1, self.stats.max_health // 8)
                self.stats.health -= dmg
                console.success(i18n.t("combat.enemy_poison", amount=dmg, name=self.name))
            elif effect["name"] == "sangrado":
                dmg = max(1, self.stats.max_health // 12)
                self.stats.health -= dmg
                console.error(i18n.t("combat.enemy_bleed", amount=dmg, name=self.name))

        return can_act

    def on_turn_end(self) -> None:
        """Regeneración de salud pasiva por defecto (self.stats.regen == 0 para
        la mayoría de enemigos: solo los "aptos" para regenerar la usan, p. ej.
        el Troll, que además personaliza el mensaje sobrescribiendo este método)."""
        if self.stats.regen > 0 and self.is_alive() and self.stats.health < self.stats.max_health:
            healed = self.heal(self.stats.regen)
            if healed > 0:
                console.success(i18n.t("combat.enemy_regen", name=self.name, amount=healed))

    def decay_status_effects(self) -> None:
        """Descuenta un turno a cada estado y elimina los caducados. Se llama al
        final del turno del enemigo, después de on_turn_end()."""
        for effect in self.status_effects[:]:
            effect["duration"] -= 1
            if effect["duration"] <= 0:
                console.info(i18n.t("combat.status_faded_enemy", status=status_label(effect["name"]), name=self.name))
                self.status_effects.remove(effect)

    # --- TURNO ---

    def perform_turn(self, player) -> None:
        """Lógica por defecto: atacar. Las subclases pueden sobrescribir esto."""
        if not resolve_hit(self.stats.precision, player.get_total_evasion()):
            print(
                f"{console.colorize(self.name, console.Fore.RED)} ataca, pero "
                f"{console.colorize(player.name, console.Fore.GREEN)} esquiva el golpe."
            )
            return

        damage = self.get_attack_damage()

        is_crit = random.random() < self.stats.crit_chance
        if is_crit:
            damage = int(damage * self.stats.crit_damage)

        final_damage = player.take_damage(damage, armor_penetration=self.stats.armor_penetration)

        print(
            f"{console.colorize(self.name, console.Fore.RED)} ataca y hace "
            f"{console.colorize(str(final_damage), console.Fore.RED)} de daño."
            f"{console.crit_suffix(is_crit)}"
        )

    def drop_item(self) -> list:
        """Por defecto no sueltan nada, las subclases lo implementan."""
        return []
