import random

from valeterna.characters.enemies.enemy_base import Enemy
from valeterna.characters.stats import Stats, resolve_hit
from valeterna.items.equipment import Armor, Weapon
from valeterna.items.materials import Material
from valeterna.items.potions import HealingPotion
from valeterna.ui import console


class HorrorDeProfundidad(Enemy):
    DESCRIPTION = "Nadie le ha visto entero. Lo que sale del agua es solo la parte que no le importa enseñar."
    SIGNATURE = "Coletazo aturdidor: un golpe más fuerte de lo normal que puede dejarte aturdido."
    ELEMENTS_DEALT = frozenset()
    INFLICTS = frozenset({"aturdido"})
    ENCOUNTER_LINE = (
        "Algo enorme rompe la calma del agua profunda. No te da tiempo a ver bien al Horror de Profundidad."
    )

    def __init__(self):
        super().__init__(
            "Horror de Profundidad",
            Stats(
                595,
                595,
                26,
                35,
                15,
                magic_resist=2,
                speed=10,
                precision=9,
                evasion=3,
                crit_chance=0.06,
                crit_damage=1.6,
                armor_penetration=5,
            ),
            gold_min=205,
            gold_max=245,
        )

    def perform_turn(self, player) -> None:
        # Un turno de cada cinco, de media, coletazo en vez de golpe normal.
        if random.random() < 0.2:
            self._tail_slam(player)
        else:
            super().perform_turn(player)

    def _tail_slam(self, player) -> None:
        print(console.colorize(f"{self.name} se alza sobre el agua y prepara un coletazo...", console.Fore.RED))

        if not resolve_hit(self.stats.precision, player.get_total_evasion()):
            print(
                f"El coletazo cae, pero {console.colorize(player.name, console.Fore.GREEN)} logra apartarse a tiempo."
            )
            return

        damage = int(self.get_attack_damage() * 1.6)
        final_damage = player.take_damage(damage, armor_penetration=self.stats.armor_penetration)
        print(f"¡Coletazo aturdidor! {console.colorize(str(final_damage), console.Fore.RED)} de daño.")

        if random.random() < 0.4:
            player.apply_status("aturdido", 1)
            console.warning("¡El golpe te ha dejado aturdido!")

    def drop_item(self) -> list:
        items = []
        if random.random() <= 0.5:
            items.append(HealingPotion("Poción de Salud", "Restaura 20 HP", 2, 20))
        if random.random() <= 0.3:
            items.append(
                Material(
                    "Carne de Profundidad",
                    "Pálida y fría; no debería seguir moviéndose fuera del agua.",
                    13,
                    rarity="Poco común",
                )
            )
        if random.random() <= 0.08:
            items.append(Weapon("Garra de Profundidad", "Curvada como un anzuelo del tamaño de un brazo.", 27, 18))
        if random.random() <= 0.08:
            items.append(
                Armor(
                    "Cinturón de Profundidad",
                    "Escamoso al tacto; sigue húmedo mucho después de sacarlo del agua.",
                    32,
                    slot="cinturon",
                    defense=7,
                    max_health=15,
                )
            )
        return items
