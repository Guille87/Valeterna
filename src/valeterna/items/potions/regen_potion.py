from valeterna.items.potions.potion_base import Potion
from valeterna.ui import console


class RegenPotion(Potion):
    def __init__(self, name: str, description: str, value: int, regen_amount: int, duration: int):
        super().__init__(name, description, value, duration)
        self.regen_amount = regen_amount
        self.is_combat_only = True

    def use(self, player) -> bool:
        if getattr(player, "in_combat", False):
            # Usamos el método apply_status que ya tienes en Player
            player.apply_status("regeneración", self.duration, power=self.regen_amount)
            console.success("¡Te sientes revitalizado! Recuperarás vida cada turno.")
            return True

        console.error("Esta poción solo surte efecto durante el fragor de la batalla.")
        return False

    def get_stats_info(self) -> str:
        return console.colorize(f"Regen: {self.regen_amount} HP/turno ({self.duration} turnos)", console.Fore.GREEN)

    def to_dict(self) -> dict:
        data = super().to_dict()
        data["regen_amount"] = self.regen_amount
        return data

    @classmethod
    def from_dict(cls, data: dict) -> "RegenPotion":
        return cls(data["name"], data["description"], data["value"], data["regen_amount"], data["duration"])
