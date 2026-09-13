from valeterna.items.equipment import Armor, Weapon
from valeterna.items.factory import item_factory
from valeterna.ui import console


class CraftingRecipe:
    """Una receta: materiales + oro requeridos, y una plantilla del objeto resultante."""

    def __init__(self, name: str, materials: dict, gold_cost: int, result_template):
        self.name = name
        self.materials = materials  # {"Piel de Troll": 2}
        self.gold_cost = gold_cost
        self.result_template = result_template

    def create_result(self):
        """Crea una copia independiente de la plantilla para entregar al jugador."""
        return item_factory(self.result_template.to_dict())

    def can_craft(self, player) -> bool:
        if player.inventory.gold < self.gold_cost:
            return False
        return all(player.inventory.has_item(mat, qty) for mat, qty in self.materials.items())

    def is_discovered(self, player) -> bool:
        """Solo se muestra en la herrería si el jugador ha conseguido alguna vez
        (aunque ya no le queden en el inventario) todos los materiales que pide."""
        return all(mat in player.inventory.discovered_materials for mat in self.materials)

    def missing_requirements(self, player) -> list:
        """Lista en texto lo que le falta al jugador para poder craftear esta receta."""
        missing = []
        if player.inventory.gold < self.gold_cost:
            missing.append(f"oro (tienes {player.inventory.gold}, hacen falta {self.gold_cost})")
        for mat, qty in self.materials.items():
            have = player.inventory.quantities.get(mat, 0)
            if have < qty:
                missing.append(f"{mat} (tienes {have}, hacen falta {qty})")
        return missing

    def __str__(self) -> str:
        materials_str = ", ".join(
            f"{console.colorize(name, console.Fore.LIGHTBLACK_EX)} x{qty}" for name, qty in self.materials.items()
        )
        gold = console.colorize(f"{self.gold_cost} oro", console.Fore.YELLOW, bright=True)
        name = console.colorize(self.name, console.Fore.CYAN, bright=True)
        return console.tint_status(
            f"{name} | Requiere: {materials_str} + {gold} | [{self.result_template.get_stats_info()}]"
        )


class Forge:
    def __init__(self):
        self.recipes = [
            CraftingRecipe(
                name="Armadura Regenerativa",
                # Piel de Troll cae al 5%, el drop más raro del juego junto con la
                # Esencia Arcana: con solo 2 unidades ya hacen falta ~40 Trolls de
                # media, a la altura de ser el mejor peto craftable del juego.
                materials={"Piel de Troll": 2},
                gold_cost=200,
                result_template=Armor(
                    "Armadura Regenerativa",
                    "Forjada con la piel imperecedera de un Troll; aún parece palpitar con vida propia.",
                    value=60,
                    slot="peto",
                    defense=14,
                    max_health=35,
                    regen=8,
                ),
            ),
            CraftingRecipe(
                name="Daga Envenenada",
                # Único arma craftable del juego (el resto de recetas son de
                # armadura); da una segunda vía además del drop del Huargo para
                # conseguir un arma de veneno.
                materials={"Colmillo de Huargo": 25, "Capa de Sombras": 25},
                gold_cost=45,
                result_template=Weapon(
                    "Daga Envenenada",
                    "Forjada con colmillos que todavía destilan un veneno letal.",
                    value=22,
                    damage=10,
                    element="veneno",
                ),
            ),
            CraftingRecipe(
                name="Espada Consagrada",
                # Primera arma craftable de sagrado/oscuridad/arcano (v0.11.0-b).
                # Forjada con los restos de dos criaturas que ahora son débiles
                # a lo sagrado (Esqueleto, Espíritu Vengativo) — la luz que las
                # castiga a ellas se queda impregnada en el metal.
                materials={"Fragmento de Hueso": 25, "Esencia Espectral": 25},
                gold_cost=75,
                result_template=Weapon(
                    "Espada Consagrada",
                    "Una hoja purificada con los restos de quienes la luz ya castigó.",
                    value=32,
                    damage=14,
                    element="sagrado",
                ),
            ),
            CraftingRecipe(
                name="Daga Umbría",
                materials={"Capa de Sombras": 25, "Pluma Corrupta": 15},
                gold_cost=95,
                result_template=Weapon(
                    "Daga Umbría",
                    "Forjada fundiendo la sombra de un bandido con la corrupción de un ángel caído.",
                    value=40,
                    damage=18,
                    element="oscuridad",
                ),
            ),
            CraftingRecipe(
                name="Vara Arcana",
                materials={"Esencia Arcana": 8, "Núcleo de Gólem": 15},
                gold_cost=110,
                result_template=Weapon(
                    "Vara Arcana",
                    "Un núcleo de piedra imbuido con energía arcana que apenas logra contener.",
                    value=45,
                    damage=16,
                    element="arcano",
                ),
            ),
            CraftingRecipe(
                name="Guantes de Combate",
                materials={"Colmillo de Goblin": 25, "Colmillo de Orco": 25},
                gold_cost=60,
                result_template=Armor(
                    "Guantes de Combate",
                    "Refuerzos de cuero y colmillos afilados cosidos en los nudillos.",
                    value=15,
                    slot="guantes",
                    crit_chance=0.05,
                    crit_damage=0.15,
                ),
            ),
            CraftingRecipe(
                name="Brazales Arcanos",
                materials={"Esencia Arcana": 8, "Esencia Espectral": 25},
                gold_cost=80,
                result_template=Armor(
                    "Brazales Arcanos",
                    "Energía mágica condensada en forma de brazales; arden con un fuego que no quema al portador.",
                    value=25,
                    slot="brazales",
                    crit_chance=0.05,
                    magic_resist=3,
                    element="fuego",
                ),
            ),
            CraftingRecipe(
                name="Hombreras Reforzadas",
                materials={"Colmillo de Orco": 25, "Fragmento de Hueso": 25, "Fragmento de Gárgola": 15},
                gold_cost=70,
                result_template=Armor(
                    "Hombreras Reforzadas",
                    "Placas de hueso y colmillo unidas con remaches toscos pero efectivos.",
                    value=18,
                    slot="hombreras",
                    precision=3,
                    defense=2,
                    max_health=15,
                ),
            ),
            CraftingRecipe(
                name="Cinturón de Resistencia",
                materials={"Fragmento de Hueso": 25, "Núcleo de Gólem": 15},
                gold_cost=40,
                result_template=Armor(
                    "Cinturón de Resistencia",
                    "Tejido con fragmentos óseos que parecen absorber el dolor, tanto físico como arcano.",
                    value=12,
                    slot="cinturon",
                    defense=3,
                    max_health=15,
                    magic_resist=4,
                    # "tanto físico como arcano" ya lo decía la descripción original;
                    # primera fuente de resistencia elemental del jugador (v0.11.0-b).
                    resist={"arcano": 0.10},
                ),
            ),
            CraftingRecipe(
                name="Perneras de Placa",
                materials={"Colmillo de Orco": 25, "Capa de Sombras": 25},
                gold_cost=50,
                result_template=Armor(
                    "Perneras de Placa",
                    "Protección rígida para las piernas, forjada con colmillos de orco fundidos.",
                    value=14,
                    slot="perneras",
                    evasion=2,
                    defense=3,
                    max_health=12,
                ),
            ),
            CraftingRecipe(
                name="Botas Ligeras",
                materials={"Colmillo de Goblin": 25, "Colmillo de Huargo": 25},
                gold_cost=30,
                result_template=Armor(
                    "Botas Ligeras",
                    "Suelas flexibles que facilitan golpear en el punto justo y moverse con más soltura.",
                    value=10,
                    slot="botas",
                    crit_damage=0.10,
                    speed=3,
                ),
            ),
            CraftingRecipe(
                name="Anillo de Fuerza",
                materials={"Colmillo de Orco": 25, "Fragmento de Hueso": 25, "Ceniza Infernal": 15},
                gold_cost=55,
                result_template=Armor(
                    "Anillo de Fuerza",
                    "Un aro pesado grabado con runas de poder bruto.",
                    value=16,
                    slot="anillo",
                    crit_damage=0.12,
                    damage=3,
                ),
            ),
            CraftingRecipe(
                name="Anillo de Precisión",
                materials={"Colmillo de Goblin": 25, "Esencia Arcana": 8, "Polvo de Hueso Negro": 15},
                gold_cost=65,
                result_template=Armor(
                    "Anillo de Precisión",
                    "Un aro fino que agudiza el instinto para encontrar el punto débil.",
                    value=20,
                    slot="anillo",
                    crit_damage=0.12,
                ),
            ),
            CraftingRecipe(
                name="Amuleto de Resistencia",
                materials={"Esencia Arcana": 8, "Fragmento de Hueso": 25, "Pluma Corrupta": 15},
                gold_cost=90,
                result_template=Armor(
                    "Amuleto de Resistencia",
                    "Un talismán que envuelve al portador en una tenue barrera contra la magia.",
                    value=28,
                    slot="amuleto",
                    defense=2,
                    magic_resist=5,
                    # Pluma Corrupta (Ángel Caído): un rastro de esa misma corrupción
                    # protege de la oscuridad (v0.11.0-b).
                    resist={"oscuridad": 0.10},
                ),
            ),
            CraftingRecipe(
                name="Anillo de Vitalidad",
                # Escama de Dragón cae al 35% pero de la pelea más difícil del
                # juego (el jefe final): 5 unidades ya representan un farmeo real
                # de postgame, sin llegar a los ~70 Dragones que pedirían 25.
                materials={"Fragmento de Hueso": 25, "Escama de Dragón": 5},
                gold_cost=45,
                result_template=Armor(
                    "Anillo de Vitalidad",
                    "Un aro sencillo grabado con símbolos de sanación; late al mismo ritmo que el corazón.",
                    value=14,
                    slot="anillo",
                    crit_damage=0.16,
                    regen=2,
                    # Un anillo de sanación defiende bien contra lo sagrado: el
                    # estado que inflige ("consagrado") bloquea la autocuración,
                    # así que menos daño de ese elemento es una defensa afín
                    # (v0.11.0-b).
                    resist={"sagrado": 0.10},
                ),
            ),
        ]

    def open(self, player) -> None:
        """Punto de entrada del menú interactivo de la herrería."""
        while True:
            print(console.colorize("\n--- HERRERÍA ---", console.Fore.YELLOW, bright=True))
            print(
                f"Oro disponible: {console.colorize(f'{player.inventory.gold} oro', console.Fore.YELLOW, bright=True)}"
            )

            visible_recipes = [r for r in self.recipes if r.is_discovered(player)]
            hidden_count = len(self.recipes) - len(visible_recipes)

            if not visible_recipes:
                print(
                    "Todavía no has descubierto ningún material craftable. Derrota enemigos y consigue sus materiales."
                )
                if hidden_count:
                    print(
                        console.colorize(f"({hidden_count} recetas más por descubrir)", console.Fore.BLACK, bright=True)
                    )
                return

            for idx, recipe in enumerate(visible_recipes, 1):
                print(f"{console.colorize(f'{idx}.', console.Fore.CYAN)} {recipe}")
            print(f"{console.colorize(f'{len(visible_recipes) + 1}.', console.Fore.CYAN)} Volver")
            if hidden_count:
                print(
                    console.colorize(
                        f"({hidden_count} recetas más por descubrir consiguiendo nuevos materiales)",
                        console.Fore.BLACK,
                        bright=True,
                    )
                )

            choice = console.ask(f"\nElige qué craftear (1-{len(visible_recipes) + 1}): ")
            if not choice.isdigit():
                console.error("Entrada no válida.")
                continue

            idx = int(choice) - 1
            if idx == len(visible_recipes):
                return
            if not (0 <= idx < len(visible_recipes)):
                console.error("Opción fuera de rango.")
                continue

            self._craft(player, visible_recipes[idx])

    def _craft(self, player, recipe: CraftingRecipe) -> None:
        if not recipe.can_craft(player):
            console.error("Te falta lo siguiente: " + ", ".join(recipe.missing_requirements(player)))
            return

        player.inventory.gold -= recipe.gold_cost
        for mat, qty in recipe.materials.items():
            player.inventory.consume_item(mat, qty)

        player.inventory.add_item(recipe.create_result())
        console.success(f"¡Has forjado {recipe.name}!")
