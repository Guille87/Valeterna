import random

from valeterna.characters.base import Character
from valeterna.characters.classes import CharClass, get_profile
from valeterna.characters.stats import Stats, apply_mitigation
from valeterna.combat.elements import (
    COMBUSTION_MERGE_NAMES,
    COMBUSTION_STATUS,
    SHATTER_DAMAGE_MULT,
    is_shatter_hit,
    is_status_blocked_by_combustion,
    resolve_status_reaction,
)
from valeterna.inventory.inventory import Inventory
from valeterna.items.equipment import ARMOR_SLOTS, slot_label
from valeterna.ui import console
from valeterna.world.map import ZONE_ORDER


class Player(Character):
    def __init__(self, name: str, stats: Stats, char_class: CharClass | str | None = None):
        super().__init__(name, stats)
        # Clase de personaje (GDD §6.1). Por defecto Vagabundo = el personaje de
        # siempre. Guía los stats de arranque (ui/menus.py), los multiplicadores
        # de crecimiento por nivel y si el ataque estándar es mágico.
        self._class_profile = get_profile(char_class)
        self.level = 1
        self.experience = 0
        # Ids de las habilidades activas equipadas (≤4, GDD §6.2). Se persiste.
        self.equipped_skills: list[str] = []
        # Elemento elegido para este combate (pasiva "Sintonía" del Arcanista);
        # lo limpia _restore_player() al terminar la pelea.
        self.battle_element: str | None = None
        # Escudo de Maná (activa del Arcanista): absorbe el próximo golpe.
        self.mana_shield = False
        # Represalia (pasiva del Guerrero): ¿recibió un golpe físico este turno?
        # Se pone en take_damage y lo consulta/limpia el bucle de combate.
        self.took_physical_hit = False
        # ¿El último take_damage() disparó la reacción "fusión" (rayo contra
        # congelado)? La consulta quien intente aplicar el paralizado normal del
        # rayo justo después (p. ej. Mago._cast_thunder), para no hacerlo encima
        # de una reacción que ya "ha gastado" ese golpe.
        self.just_shattered = False
        # Si el último apply_status() disparó la reacción "combustión", su
        # nombre — ver pop_status_reaction_message().
        self.last_status_reaction: str | None = None
        self.inventory = Inventory(self)
        self.equipped_weapon = None
        self.equipped_armor = {slot: None for slot in ARMOR_SLOTS}
        self.just_leveled_up = False
        self.in_combat = False
        # Postura defensiva (acción "Defender" en combate): mientras está activa,
        # take_damage() reduce a la mitad el daño recibido. Dura hasta el
        # siguiente turno del jugador, que la limpia en combat/battle.py.
        self.defending = False

        # Sistema de estados alterados: [{"name": "quemado", "duration": 3, "power": 5}, ...]
        self.status_effects = []
        # Sistema de pociones de Stats
        self.active_effects = []
        # Veces que se ha derrotado a cada enemigo (por nombre), no solo la primera
        # vez (a diferencia de defeated_enemies, que solo marca "ya visto"). Usado
        # por el Bestiario.
        self.enemy_kill_counts: dict[str, int] = {}

        # Estado de mundo (GDD §8/§9.4): posición actual, zonas ya visitadas,
        # misiones, banderas de historia, diálogos vistos, diario y mejor
        # oleada de la Arena. zona_actual/zonas_visitadas ya las usa
        # ui/exploration.py::zone_loop() (v0.12.0-b); el resto (misiones,
        # banderas, dialogos_vistos, diario, arena_mejor_oleada) sigue sin
        # usarse, a la espera de misiones/diálogo/Arena.
        self.mundo: dict = {
            "zona_actual": ZONE_ORDER[0],
            "zonas_visitadas": [ZONE_ORDER[0]],
            "misiones": {},
            "banderas": set(),
            "dialogos_vistos": set(),
            "diario": [],
            "arena_mejor_oleada": 0,
        }

    # --- LÓGICA DE COMBATE ---

    def take_damage(
        self,
        amount: int,
        is_fire: bool = False,
        is_magical: bool = False,
        armor_penetration: int = 0,
        magic_penetration: int = 0,
        element: str | None = None,
    ) -> int:
        """Calcula el daño final tras aplicar armadura o resistencia mágica y lo resta de la vida."""
        if element:
            resist_pct = self.get_total_resist(element)
            if resist_pct:
                amount = round(amount * (1 - resist_pct))

        # Reacción "fusión": un golpe de rayo contra un jugador congelado rompe
        # el hielo al instante y hace daño extra, en vez del paralizado normal.
        self.just_shattered = is_shatter_hit(element, {e["name"] for e in self.status_effects})
        if self.just_shattered:
            amount = int(amount * SHATTER_DAMAGE_MULT)
            self.status_effects = [e for e in self.status_effects if e["name"] != "congelado"]

        if is_magical:
            mitigation = self.get_total_magic_resist() - magic_penetration
        else:
            mitigation = self.get_total_armor() - armor_penetration
        final_damage = apply_mitigation(amount, mitigation)

        # Pasivas que reducen el daño físico recibido (p. ej. "Piel de Piedra").
        if not is_magical and final_damage > 0:
            for skill in self._active_passives():
                mult = skill.params.get("phys_dmg_taken_mult")
                if mult is not None:
                    final_damage = max(1, round(final_damage * mult))

        # Postura defensiva: el golpe entra a la mitad.
        if self.defending and final_damage > 0:
            final_damage //= 2
            console.info(f"🛡️ Tu postura defensiva reduce el golpe a {final_damage}.")

        # Escudo de Maná (activa del Arcanista): absorbe por completo el próximo
        # golpe que fuese a hacer daño, y se consume.
        if self.mana_shield and final_damage > 0:
            self.mana_shield = False
            console.info("🛡️ El escudo de maná absorbe el golpe por completo.")
            return 0

        # Represalia (Guerrero): registrar que se recibió un golpe físico real.
        if not is_magical and final_damage > 0:
            self.took_physical_hit = True

        self.stats.health -= final_damage

        if is_fire:
            # Si recibimos fuego, buscamos el efecto 'congelado' y lo borramos
            congelado = next((e for e in self.status_effects if e["name"] == "congelado"), None)
            if congelado:
                self.status_effects.remove(congelado)
                console.warning("¡El calor del ataque ha derretido el hielo!")

        if self.just_shattered:
            print(
                console.colorize(
                    "⚡❄️ ¡El rayo hace añicos el hielo que te envolvía, sufres daño extra!",
                    console.Fore.YELLOW,
                    bright=True,
                )
            )

        return final_damage

    @property
    def char_class(self) -> CharClass:
        return self._class_profile.id

    @char_class.setter
    def char_class(self, value: CharClass | str | None) -> None:
        self._class_profile = get_profile(value)

    @property
    def class_name(self) -> str:
        """Nombre visible de la clase (p. ej. "Aventurero")."""
        return self._class_profile.name

    def is_magical_attacker(self) -> bool:
        """El ataque estándar es mágico y escala con `poder_magico` (Arcanista)."""
        return self._class_profile.is_magical_attacker

    # --- HABILIDADES (GDD §6.2) ---

    def known_skills(self) -> list:
        """Habilidades ya aprendidas según clase y nivel."""
        from valeterna.characters import skills

        return skills.known_skills(self.char_class, self.level)

    def known_active_skills(self) -> list:
        return [s for s in self.known_skills() if s.is_active]

    def _active_passives(self) -> list:
        from valeterna.characters.skills import SkillKind

        return [s for s in self.known_skills() if s.kind is SkillKind.PASSIVE]

    def has_passive(self, skill_id: str) -> bool:
        """¿El jugador tiene aprendida esa pasiva?"""
        return any(s.id == skill_id for s in self._active_passives())

    def passive_param(self, skill_id: str, key: str, default=None):
        """Valor de un `params[...]` de una pasiva aprendida (o `default`)."""
        for skill in self._active_passives():
            if skill.id == skill_id:
                return skill.params.get(key, default)
        return default

    def get_equipped_active_skills(self) -> list:
        """Las activas equipadas que además siguen siendo válidas (conocidas)."""
        known = {s.id: s for s in self.known_active_skills()}
        return [known[sid] for sid in self.equipped_skills if sid in known]

    def sanitize_equipped_skills(self) -> None:
        """Deja en `equipped_skills` solo ids de activas conocidas, sin repetir y
        como mucho `MAX_EQUIPPED_ACTIVES` (tras cargar partida o cambiar de clase)."""
        from valeterna.characters.skills import MAX_EQUIPPED_ACTIVES

        known = {s.id for s in self.known_active_skills()}
        seen: list[str] = []
        for sid in self.equipped_skills:
            if sid in known and sid not in seen:
                seen.append(sid)
        self.equipped_skills = seen[:MAX_EQUIPPED_ACTIVES]

    def autoequip_skills(self) -> None:
        """Equipa las activas conocidas que quepan (para no obligar a pasar por el
        menú cuando solo hay una o dos)."""
        from valeterna.characters.skills import MAX_EQUIPPED_ACTIVES

        self.equipped_skills = [s.id for s in self.known_active_skills()][:MAX_EQUIPPED_ACTIVES]

    def _low_hp_defense_mult(self) -> float:
        """Multiplicador extra sobre armadura/res. mágica de pasivas tipo
        "Aguante" cuando el jugador está por debajo del 30% de vida."""
        if self.stats.health >= 0.3 * self.stats.max_health:
            return 1.0
        mult = 1.0
        for skill in self._active_passives():
            mult += skill.params.get("low_hp_defense_pct", 0.0)
        return mult

    def get_total_magic_power(self) -> int:
        """Poder mágico total (hoy solo el stat base; ningún equipo lo otorga aún)."""
        return self.stats.magic_power

    def get_magic_attack_range(self) -> tuple[int, int]:
        """Rango de daño del ataque mágico estándar del Arcanista, derivado del
        poder mágico (no del arma). La quemadura —solo física— no lo reduce."""
        power = self.get_total_magic_power()
        return power, power + max(1, power // 3)

    def get_attack_damage(self) -> int:
        """Genera un valor de daño aleatorio basado en el rango actual."""
        if self.is_magical_attacker():
            min_atk, max_atk = self.get_magic_attack_range()
        else:
            min_atk, max_atk = self.get_attack_range()
        return random.randint(min_atk, max_atk)

    def get_attack_range(self) -> tuple[int, int]:
        """Devuelve el rango de ataque sumando el arma y el equipo (p. ej. anillos) equipados."""
        # Desarmado (Bandido): el bonus del arma no cuenta mientras dure el estado.
        is_disarmed = any(e["name"] == "desarmado" for e in self.status_effects)
        weapon_bonus = self.equipped_weapon.damage if self.equipped_weapon and not is_disarmed else 0
        armor_bonus = sum(item.damage for item in self.equipped_armor.values() if item)
        bonus = weapon_bonus + armor_bonus
        min_atk = self.stats.min_atk + bonus
        max_atk = self.stats.max_atk + bonus

        # Penalización por Quemadura (y Combustión, que la incluye): Ataque a la mitad
        if any(e["name"] in ("quemado", "combustion") for e in self.status_effects):
            min_atk //= 2
            max_atk //= 2

        return min_atk, max_atk

    def get_total_armor(self) -> int:
        """Devuelve la armadura total sumando todas las piezas equipadas."""
        bonus = sum(item.defense for item in self.equipped_armor.values() if item)
        total = self.stats.armor + bonus

        # Maldición (Espíritu Vengativo): resta armadura mientras dure el estado.
        curse = next((e for e in self.status_effects if e["name"] == "maldicion"), None)
        if curse:
            total = max(0, total - curse.get("power", 0))

        return round(total * self._low_hp_defense_mult())  # "Aguante" con poca vida

    def get_total_magic_resist(self) -> int:
        """Devuelve la resistencia mágica total sumando todas las piezas equipadas."""
        bonus = sum(item.magic_resist for item in self.equipped_armor.values() if item)
        total = self.stats.magic_resist + bonus
        return round(total * self._low_hp_defense_mult())  # "Aguante" con poca vida

    def get_total_resist(self, element: str) -> float:
        """% de reducción de daño de `element` (0.0-1.0) sumada de toda la
        armadura equipada, aplicada en take_damage() antes de la mitigación
        por armadura/resistencia mágica. Tope 75%: ninguna combinación de
        equipo debería anular un elemento por completo, solo la inmunidad de
        un enemigo hace eso en el otro sentido."""
        total = sum(item.resist.get(element, 0.0) for item in self.equipped_armor.values() if item)
        return min(total, 0.75)

    def get_total_crit_chance(self) -> float:
        """Devuelve la probabilidad de golpe crítico total sumando todas las piezas equipadas."""
        bonus = sum(item.crit_chance for item in self.equipped_armor.values() if item)
        return self.stats.crit_chance + bonus

    def get_total_crit_damage(self) -> float:
        """Devuelve el multiplicador de daño crítico total sumando todas las piezas equipadas."""
        bonus = sum(item.crit_damage for item in self.equipped_armor.values() if item)
        return self.stats.crit_damage + bonus

    def get_total_speed(self) -> int:
        """Devuelve la velocidad total sumando todas las piezas equipadas (en la práctica, solo las botas)."""
        bonus = sum(item.speed for item in self.equipped_armor.values() if item)
        return self.stats.speed + bonus

    def get_total_precision(self) -> int:
        """Devuelve la precisión total sumando todas las piezas equipadas (stat base de las hombreras)."""
        bonus = sum(item.precision for item in self.equipped_armor.values() if item)
        return self.stats.precision + bonus

    def get_total_evasion(self) -> int:
        """Devuelve la evasión total sumando todas las piezas equipadas (stat base de las perneras)."""
        bonus = sum(item.evasion for item in self.equipped_armor.values() if item)
        bonus += sum(s.params.get("evasion", 0) for s in self._active_passives())  # p. ej. "Reflejos"
        total = self.stats.evasion + bonus

        # Confusión (Demonio): resta evasión mientras dure el estado.
        confusion = next((e for e in self.status_effects if e["name"] == "confusion"), None)
        if confusion:
            total = max(0, total - confusion.get("power", 0))

        return total

    def get_total_armor_penetration(self) -> int:
        """Devuelve la penetración de armadura total (hoy solo el stat base; el equipo no otorga todavía)."""
        return self.stats.armor_penetration

    def get_total_regen(self) -> int:
        """Devuelve la regeneración de salud total sumando todas las piezas equipadas.

        A diferencia del resto de get_total_*, el stat base (Stats.regen) es
        siempre 0 para el jugador: esta stat no sube al subir de nivel, solo
        se consigue vía objetos (típicamente anillos/amuleto).
        """
        bonus = sum(item.regen for item in self.equipped_armor.values() if item)
        return self.stats.regen + bonus

    def get_total_magic_penetration(self) -> int:
        """Devuelve la penetración mágica total (hoy solo el stat base; el equipo no otorga todavía)."""
        return self.stats.magic_penetration

    def get_equipped_element(self) -> str | None:
        """Devuelve el elemento del ataque: el elegido este combate por la pasiva
        "Sintonía" si lo hay, si no el del arma equipada (salvo desarmado), y en
        último lugar el de los brazales."""
        is_disarmed = any(e["name"] == "desarmado" for e in self.status_effects)
        if self.battle_element and not is_disarmed:
            return self.battle_element
        if self.equipped_weapon and self.equipped_weapon.element and not is_disarmed:
            return self.equipped_weapon.element
        brazales = self.equipped_armor.get("brazales")
        return brazales.element if brazales else None

    def is_alive(self) -> bool:
        return self.stats.health > 0

    # --- GESTIÓN DE TURNOS Y ESTADOS ---

    def on_turn_start(self) -> bool:
        """Procesa los estados alterados al inicio del turno."""
        can_act = True
        # 1. Comprobación de estados que bloquean el turno
        for effect in self.status_effects[:]:
            if effect["name"] == "congelado":
                # El primer turno tras congelarte pierdes el turno seguro; a
                # partir de ahí hay un 20% por turno de romper el hielo.
                if not effect.get("fresh") and random.random() < 0.20:
                    console.info("¡El hielo se rompe! Te has descongelado.")
                    self.status_effects.remove(effect)
                else:
                    effect["fresh"] = False
                    print(console.colorize("❄️ Estás congelado y no puedes moverte.", console.Fore.BLUE))
                    # Si está congelado, no procesamos parálisis, pero SÍ veneno/quemadura más abajo
                    can_act = False
                    break  # Salimos del check de movimiento, pero seguimos con el daño

            elif effect["name"] == "paralizado":
                # Primer turno seguro; después, 50% por turno.
                if effect.get("fresh") or random.random() < 0.5:
                    console.warning("⚡ ¡La parálisis te impide actuar!")
                    can_act = False
                effect["fresh"] = False

            elif effect["name"] == "aturdido":
                # Aturdimiento: pierdes el turno mientras dure (sin tirada).
                console.warning("💫 ¡Estás aturdido y pierdes el turno!")
                can_act = False

        # 2. Procesamiento de daño/curación (Ocurre aunque no puedas actuar)
        for effect in self.status_effects[:]:
            if effect["name"] == "quemado":
                dmg = max(1, self.stats.max_health // 16)
                self.stats.health -= dmg
                console.error(f"🔥 La quemadura te quita {dmg} HP.")

            elif effect["name"] == "veneno":
                dmg = max(1, self.stats.max_health // 8)
                self.stats.health -= dmg
                console.success(f"☣️ El veneno te quita {dmg} HP.")

            elif effect["name"] == "sangrado":
                dmg = max(1, self.stats.max_health // 12)
                self.stats.health -= dmg
                console.error(f"🩸 El sangrado te quita {dmg} HP.")

            elif effect["name"] == "combustion":
                dmg = max(1, self.stats.max_health // 6)
                self.stats.health -= dmg
                console.error(f"🔥☣️ La combustión te quita {dmg} HP.")

            elif effect["name"] == "regeneración":
                heal = effect.get("power", 0)
                self.stats.health = min(self.stats.max_health, self.stats.health + heal)
                console.success(f"❤️ La regeneración te cura {heal} HP.")

        # 3. Regeneración de salud pasiva por equipo (no es un status temporal,
        # se aplica todos los turnos mientras el objeto siga puesto).
        passive_regen = self.get_total_regen()
        if passive_regen > 0 and self.stats.health < self.stats.max_health:
            self.stats.health = min(self.stats.max_health, self.stats.health + passive_regen)
            console.success(f"💚 Tu regeneración te cura {passive_regen} HP.")

        return can_act

    def on_turn_end(self) -> None:
        """Se ejecuta al terminar el turno (jugador y enemigo han actuado)."""
        for effect in self.status_effects[:]:
            effect["duration"] -= 1
            if effect["duration"] <= 0:
                console.info(f"✨ El efecto de {effect['name']} ha desaparecido.")
                self.status_effects.remove(effect)
        # Los turnos restantes de cada estado se ven en las barras de vida
        # (print_status), así no hay que repetir un "persistirá por N turnos".

        for buff in self.active_effects[:]:
            buff.duration -= 1
            if buff.duration <= 0:
                buff.remove(self)  # Llama al método remove de StatBuffPotion
                self.active_effects.remove(buff)

    def apply_status(self, name: str, duration: int, power: int = 0) -> None:
        """Añade un nuevo estado alterado.

        Reacción "combustión": si `name` es quemado/veneno y el otro de la
        pareja ya está presente, los funde en un único estado combustión más
        dañino en vez de dejarlos coexistir (`last_status_reaction` queda listo
        para que `pop_status_reaction_message()` lo anuncie, DESPUÉS de que
        quien llamó imprima su propio mensaje de "te has quemado/envenenado").
        Mientras la combustión ya esté activa, un nuevo intento de quemar o
        envenenar no hace nada (ni refresca duración, ni vuelve a fundirlos)."""
        self.last_status_reaction = None
        current_names = {e["name"] for e in self.status_effects}
        if is_status_blocked_by_combustion(current_names, name):
            return
        reaction = resolve_status_reaction(current_names, name)
        if reaction:
            merged_duration = duration
            for effect in self.status_effects[:]:
                if effect["name"] in COMBUSTION_MERGE_NAMES:
                    merged_duration = max(merged_duration, effect["duration"])
                    self.status_effects.remove(effect)
            self.status_effects.append({"name": reaction, "duration": merged_duration, "power": power, "fresh": True})
            self.last_status_reaction = reaction
            return

        # Evitamos duplicados, solo refrescamos duración si ya existe
        for effect in self.status_effects:
            if effect["name"] == name:
                effect["duration"] = max(effect["duration"], duration)
                return

        self.status_effects.append({"name": name, "duration": duration, "power": power, "fresh": True})

    def pop_status_reaction_message(self) -> str | None:
        """Si el último `apply_status()` disparó la reacción "combustión",
        devuelve su mensaje (y limpia el flag); `None` si no hubo ninguna.
        Se llama DESPUÉS del mensaje propio de quien aplicó el estado, para
        que el orden en pantalla sea "te has quemado" y luego "se funden en
        combustión", no al revés."""
        if self.last_status_reaction != COMBUSTION_STATUS:
            return None
        self.last_status_reaction = None
        return console.colorize(
            "🔥☣️ ¡El fuego y el veneno se funden en combustión dentro de ti!",
            console.Fore.LIGHTGREEN_EX,
            bright=True,
        )

    # --- PROGRESIÓN ---

    def gain_experience(self, amount: int) -> None:
        self.experience += amount
        console.info(f"Has obtenido {amount} XP.")
        while self.experience >= self.required_xp():
            self._level_up()

    @staticmethod
    def _required_xp_for_level(level: int) -> int:
        """Umbral de XP acumulada (no un coste que se descuenta, ver
        gain_experience()) para pasar de `level` al siguiente.

        Nivel 1 -> 2 deliberadamente muy barato (8 XP: el mínimo que da
        incluso el primer Goblin, gold_min=4 * 2): la primera victoria del
        juego ya sube de nivel siempre.

        Los niveles 2-9 aplican un "descuento" sobre la curva normal de abajo
        que se va cerrando poco a poco: empieza en ~50% del coste normal en
        el nivel 2 (98.68 * 0.5 ≈ 49, un punto intermedio calculado a
        propósito entre los 8 XP del nivel 1 y los 98 XP que pedía la curva
        original sin suavizar) y llega al 100% en el nivel 10 — subir sigue
        siendo rápido y gratificante justo después de empezar, y se va
        ralentizando de forma gradual hasta la curva de siempre en vez de dar
        un salto brusco de golpe (que es lo que pasaba antes de suavizarlo:
        nivel 1->2 costaba 8 XP y nivel 2->3 ya pedía 375, un frenazo
        demasiado repentino).
        """
        if level == 1:
            return 8

        lv = float(level)
        base_cost = 100 * ((lv - 1) ** 0.95) * lv * (lv + 1) / (6 + lv**2 / 50)
        damping = min(1.0, 0.5 + (lv - 2) * 0.0625)
        return int(base_cost * damping)

    def required_xp(self) -> int:
        """Fórmula de curva de experiencia escalable.

        gain_experience() nunca resetea self.experience (es un umbral
        acumulado, no un coste que se descuenta al subir), así que este valor
        TIENE que ser no decreciente con el nivel — si no, una sola pelea
        pequeña podría subir más de un nivel de golpe. El `max()` con el
        umbral del nivel anterior lo garantiza sin tener que cuadrar a mano
        la fórmula y el descuento para que ya salgan siempre en orden.
        """
        cost = self._required_xp_for_level(self.level)
        if self.level > 1:
            cost = max(cost, self._required_xp_for_level(self.level - 1))
        return cost

    # Ritmo de crecimiento por nivel de cada stat (ganancia media por nivel).
    # Igual que en Pokémon (stat = floor(base + tasa * nivel / 100 + ...)), la
    # cantidad exacta que se gana en un nivel concreto sale de redondear hacia
    # abajo una curva continua, no de un valor fijo ni de una tirada aleatoria:
    # con una tasa fraccionaria (p. ej. 1.5), el resultado alterna +1/+2 de
    # forma determinista, así que la progresión varía de nivel en nivel pero es
    # exactamente la misma en todas las partidas.
    _HEALTH_GROWTH_RATE = 20.0
    _MIN_ATK_GROWTH_RATE = 1.5
    _MAX_ATK_GROWTH_RATE = 2.5
    _ARMOR_GROWTH_RATE = 1.4
    _SPEED_GROWTH_RATE = 1.6
    _PRECISION_GROWTH_RATE = 0.7
    _EVASION_GROWTH_RATE = 0.6

    @staticmethod
    def _growth_gain(rate: float, level: int) -> int:
        """Ganancia determinista para `level` según una tasa continua por nivel."""
        return int(rate * level) - int(rate * (level - 1))

    def _level_up(self) -> None:
        self.level += 1
        self.just_leveled_up = True

        health_gain = self._growth_gain(self._HEALTH_GROWTH_RATE, self.level)
        min_atk_gain = self._growth_gain(self._MIN_ATK_GROWTH_RATE, self.level)
        max_atk_gain = self._growth_gain(self._MAX_ATK_GROWTH_RATE, self.level)
        armor_gain = self._growth_gain(self._ARMOR_GROWTH_RATE * self._class_profile.armor_growth_mult, self.level)
        speed_gain = self._growth_gain(self._SPEED_GROWTH_RATE * self._class_profile.speed_growth_mult, self.level)
        precision_gain = self._growth_gain(self._PRECISION_GROWTH_RATE, self.level)
        evasion_gain = self._growth_gain(self._EVASION_GROWTH_RATE, self.level)

        self.stats.max_health += health_gain
        self.stats.health = self.stats.max_health
        self.stats.min_atk += min_atk_gain
        self.stats.max_atk += max_atk_gain
        self.stats.armor += armor_gain
        self.stats.speed += speed_gain
        self.stats.precision += precision_gain
        self.stats.evasion += evasion_gain

        # La resistencia mágica sube más despacio (cada 2 niveles) y en cantidad
        # fija, mientras no exista equipamiento que la conceda, para no
        # desequilibrar al Mago.
        gained_magic_resist = self.level % 2 == 0
        if gained_magic_resist:
            self.stats.magic_resist += 1

        # Poder mágico: solo crece para la clase que lo usa (Arcanista).
        magic_power_gain = 0
        if self._class_profile.magic_power_growth_rate:
            magic_power_gain = self._growth_gain(self._class_profile.magic_power_growth_rate, self.level)
            self.stats.magic_power += magic_power_gain

        print(f"\n{console.colorize(f'⭐ ¡HAS SUBIDO AL NIVEL {self.level}! ⭐', console.Fore.YELLOW)}")
        stats_line = (
            f"HP Max +{health_gain} | Ataque +{min_atk_gain}-{max_atk_gain} | "
            f"Armadura +{armor_gain} | Velocidad +{speed_gain}"
        )
        if precision_gain:
            stats_line += f" | Precisión +{precision_gain}"
        if evasion_gain:
            stats_line += f" | Evasión +{evasion_gain}"
        if gained_magic_resist:
            stats_line += " | Resistencia Mágica +1"
        if magic_power_gain:
            stats_line += f" | Poder Mágico +{magic_power_gain}"
        print(console.colorize(stats_line, console.Fore.WHITE))

    def show_stats(self) -> None:
        print(f"\n{console.colorize('=' * 10 + ' ESTADÍSTICAS ' + '=' * 10, console.Fore.CYAN)}")
        print(
            f"Nombre: {self.name.ljust(15)} {console.stat_line(f'Nivel: {self.level}', 'nivel')} | "
            f"{console.stat_line(f'XP: {self.experience} / {self.required_xp()}', 'xp')}"
        )
        print(f"Clase: {console.colorize(self._class_profile.name, console.Fore.MAGENTA)}")
        print(console.stat_line(f"Vida: {str(self.stats.health).rjust(4)} / {self.stats.max_health}", "vida"))
        if self.is_magical_attacker():
            lo, hi = self.get_magic_attack_range()
            print(
                console.stat_line(f"Ataque mágico: {lo}-{hi} | Poder Mágico: {self.get_total_magic_power()}", "ataque")
            )
        else:
            lo, hi = self.get_attack_range()
            print(console.stat_line(f"Ataque: {lo}-{hi}", "ataque"))
        print(
            console.stat_line(
                f"Armadura: {self.get_total_armor()} | Resistencia Mágica: {self.get_total_magic_resist()}",
                "armadura",
            )
        )
        print(
            console.stat_line(
                f"Prob. Crítico: {self.get_total_crit_chance() * 100:.0f}% | "
                f"Daño Crítico: {self.get_total_crit_damage() * 100:.0f}%",
                "critico",
            )
        )
        print(console.stat_line(f"Velocidad: {self.get_total_speed()}", "velocidad"))
        print(
            console.stat_line(
                f"Precisión: {self.get_total_precision()} | Evasión: {self.get_total_evasion()}",
                "precision",
            )
        )
        print(
            console.stat_line(
                f"Penetración de Armadura: {self.get_total_armor_penetration()} | "
                f"Penetración Mágica: {self.get_total_magic_penetration()}",
                "penetracion",
            )
        )
        regen = self.get_total_regen()
        if regen:
            print(console.stat_line(f"Regeneración: {regen} HP/turno", "regen"))
        if self.equipped_weapon:
            print(f"Arma: {console.colorize(self.equipped_weapon.name, console.Fore.RED)}")

        print(console.colorize("--- Equipamiento ---", console.Fore.CYAN))
        for slot in ARMOR_SLOTS:
            item = self.equipped_armor.get(slot)
            label = console.colorize(item.name, console.Fore.BLUE) if item else "-- vacío --"
            print(f"  {slot_label(slot)}: {label}")

        print(console.colorize("=" * 34, console.Fore.CYAN))
