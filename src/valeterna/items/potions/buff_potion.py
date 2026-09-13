from valeterna.items.potions.potion_base import Potion
from valeterna.ui import console


class StatBuffPotion(Potion):
    def __init__(self, name: str, description: str, value: int, stat_name: str, boost: int, duration: int):
        super().__init__(name, description, value, duration)
        self.stat_name = stat_name  # e.g., "defense" o "min_atk"
        self.boost = boost
        self.is_combat_only = True

    def use(self, player) -> bool:
        if getattr(player, "in_combat", False):
            # Sumamos +1 a la duración para compensar el turno actual de uso
            # Así, si la poción es de 3 turnos, el jugador atacará 3 veces con el buff.
            self.duration += 1

            # El ítem se encarga de añadirse a la lista de efectos del jugador
            player.active_effects.append(self)

            # Aplicamos el efecto inicial
            current_val = getattr(player.stats, self.stat_name)
            setattr(player.stats, self.stat_name, current_val + self.boost)

            print(
                console.colorize(
                    f"¡Efecto {self.name} activado! (+{self.boost} {self.stat_name} por {self.duration} turnos)",
                    console.Fore.CYAN,
                )
            )
            return True

        console.error("No puedes usar este objeto fuera del combate.")
        return False

    def remove(self, player) -> None:
        current_val = getattr(player.stats, self.stat_name)
        setattr(player.stats, self.stat_name, current_val - self.boost)
        print(f"El efecto de {self.name} ha terminado.")

    def to_dict(self) -> dict:
        data = super().to_dict()
        data.update({"stat_name": self.stat_name, "boost": self.boost})
        return data

    def get_stats_info(self) -> str:
        return console.colorize(f"+{self.boost} {self.stat_name} ({self.duration} turnos)", console.Fore.CYAN)

    @classmethod
    def from_dict(cls, data: dict) -> "StatBuffPotion":
        return cls(data["name"], data["description"], data["value"], data["stat_name"], data["boost"], data["duration"])
