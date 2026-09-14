from valeterna.items.potions.potion_base import Potion
from valeterna.ui import console


class AntidotePotion(Potion):
    """Elimina de golpe los estados negativos con daño/bloqueo por turno
    (veneno, quemadura, parálisis, congelación, combustión). No toca buffs ni
    maldiciones de stats (desarmado/maldicion/confusion), que tienen su propia
    lógica."""

    # "combustion" (v0.11.0-c) es la fusión de quemado+veneno: sigue siendo
    # curable, ya que ambos ingredientes por separado ya lo eran.
    CURABLE = ("veneno", "quemado", "paralizado", "congelado", "combustion")

    def __init__(self, name: str, description: str, value: int):
        super().__init__(name, description, value, duration=0)

    def use(self, player) -> bool:
        curados = [e for e in player.status_effects if e["name"] in self.CURABLE]
        if not curados:
            console.error("No tienes ningún estado que el antídoto pueda neutralizar.")
            return False

        for effect in curados:
            player.status_effects.remove(effect)
        nombres = ", ".join(e["name"] for e in curados)
        console.success(f"El antídoto neutraliza: {nombres}.")
        return True

    def get_stats_info(self) -> str:
        return console.colorize("Cura veneno, quemadura, parálisis, congelación y combustión", console.Fore.GREEN)

    @classmethod
    def from_dict(cls, data: dict) -> "AntidotePotion":
        return cls(data["name"], data["description"], data["value"])
