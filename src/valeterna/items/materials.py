from valeterna.items.item_base import Item
from valeterna.ui import console


class Material(Item):
    def __init__(self, name: str, description: str, value: int, rarity: str = "Común"):
        super().__init__(name, description, value)
        self.rarity = rarity

    def use(self, player) -> bool:
        console.warning("Este objeto es un material de artesanía. No puedes usarlo directamente.")
        return False

    def to_dict(self) -> dict:
        data = super().to_dict()
        data["rarity"] = self.rarity
        return data

    @classmethod
    def from_dict(cls, data: dict) -> "Material":
        return cls(data["name"], data["description"], data["value"], data.get("rarity", "Común"))
