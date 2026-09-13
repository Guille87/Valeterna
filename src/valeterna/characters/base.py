import random
from abc import ABC, abstractmethod

from valeterna.characters.stats import Stats


class Character(ABC):
    def __init__(self, name: str, stats: Stats):
        self.name = name
        self.stats = stats
        self.status_effects = []

    @property
    def is_alive(self) -> bool:
        return self.stats.health > 0

    def calculate_base_damage(self) -> int:
        return random.randint(self.stats.min_atk, self.stats.max_atk)

    @abstractmethod
    def take_damage(self, amount: int):
        """Lógica de recepción de daño"""
        pass
