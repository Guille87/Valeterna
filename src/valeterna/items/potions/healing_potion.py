from valeterna.items.potions.potion_base import Potion
from valeterna.ui import console


class HealingPotion(Potion):
    def __init__(self, name: str, description: str, value: int, heal_amount: int):
        super().__init__(name, description, value, duration=0)
        self.heal_amount = heal_amount

    def use(self, player) -> bool:
        player.stats.health += self.heal_amount
        print(f"Te has curado {self.heal_amount} HP.")
        return True

    def to_dict(self) -> dict:
        data = super().to_dict()
        data["heal_amount"] = self.heal_amount
        return data

    def get_stats_info(self) -> str:
        return console.colorize(f"Cura: {self.heal_amount} HP", console.Fore.GREEN)

    @classmethod
    def from_dict(cls, data: dict) -> "HealingPotion":
        return cls(data["name"], data["description"], data["value"], data["heal_amount"])
