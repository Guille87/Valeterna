from valeterna.crafting.forge import Forge
from valeterna.items.materials import Material


def _give(player, name: str, quantity: int = 1, rarity: str = "Común"):
    for _ in range(quantity):
        player.inventory.add_item(Material(name, "desc", 1, rarity=rarity))


def _give_piel_de_troll(player, quantity: int = 2):
    _give(player, "Piel de Troll", quantity, rarity="Legendario")


def _find_recipe(forge, name):
    return next(r for r in forge.recipes if r.name == name)


def test_craft_with_materials_and_gold_succeeds(player):
    forge = Forge()
    recipe = forge.recipes[0]
    _give_piel_de_troll(player)
    player.inventory.gold = 200

    assert recipe.can_craft(player) is True
    forge._craft(player, recipe)

    assert player.inventory.gold == 0
    assert "Piel de Troll" not in player.inventory.quantities
    assert "Armadura Regenerativa" in player.inventory.quantities


def test_craft_without_enough_gold_does_nothing(player):
    forge = Forge()
    recipe = forge.recipes[0]
    _give_piel_de_troll(player)
    player.inventory.gold = 199

    assert recipe.can_craft(player) is False
    forge._craft(player, recipe)

    assert player.inventory.gold == 199
    assert player.inventory.quantities["Piel de Troll"] == 2
    assert "Armadura Regenerativa" not in player.inventory.quantities


def test_craft_without_material_does_nothing(player):
    forge = Forge()
    recipe = forge.recipes[0]
    player.inventory.gold = 500  # oro de sobra, pero sin el material

    assert recipe.can_craft(player) is False
    forge._craft(player, recipe)

    assert player.inventory.gold == 500
    assert "Armadura Regenerativa" not in player.inventory.quantities


def test_craft_guantes_de_combate_consumes_two_different_materials(player):
    forge = Forge()
    recipe = _find_recipe(forge, "Guantes de Combate")
    _give(player, "Colmillo de Goblin", 25)
    _give(player, "Colmillo de Orco", 25)
    player.inventory.gold = 60

    assert recipe.can_craft(player) is True
    forge._craft(player, recipe)

    assert player.inventory.gold == 0
    assert "Colmillo de Goblin" not in player.inventory.quantities
    assert "Colmillo de Orco" not in player.inventory.quantities
    assert player.equipped_armor.get("guantes") is None  # craftear no equipa automáticamente
    assert "Guantes de Combate" in player.inventory.quantities


def test_craft_brazales_arcanos_grants_element_and_magic_resist(player):
    forge = Forge()
    recipe = _find_recipe(forge, "Brazales Arcanos")
    _give(player, "Esencia Arcana", 8, rarity="Raro")
    _give(player, "Esencia Espectral", 25, rarity="Raro")
    player.inventory.gold = 80

    assert recipe.can_craft(player) is True
    forge._craft(player, recipe)
    brazales = next(i for i in player.inventory.items if i.name == "Brazales Arcanos")

    assert brazales.element == "fuego"
    assert brazales.magic_resist == 3


def test_craft_amuleto_de_resistencia(player):
    forge = Forge()
    recipe = _find_recipe(forge, "Amuleto de Resistencia")
    _give(player, "Esencia Arcana", 8, rarity="Raro")
    _give(player, "Fragmento de Hueso", 25)
    _give(player, "Pluma Corrupta", 15, rarity="Raro")
    player.inventory.gold = 90

    assert recipe.can_craft(player) is True
    forge._craft(player, recipe)
    amuleto = next(i for i in player.inventory.items if i.name == "Amuleto de Resistencia")

    assert amuleto.slot == "amuleto"
    assert amuleto.magic_resist == 5
    assert amuleto.defense == 2


def test_recipe_hidden_until_all_its_materials_are_discovered(player):
    forge = Forge()
    recipe = _find_recipe(forge, "Guantes de Combate")

    assert recipe.is_discovered(player) is False

    _give(player, "Colmillo de Goblin", 1)
    assert recipe.is_discovered(player) is False  # falta el Colmillo de Orco

    _give(player, "Colmillo de Orco", 1)
    assert recipe.is_discovered(player) is True


def test_recipe_stays_discovered_after_materials_are_consumed(player):
    forge = Forge()
    recipe = _find_recipe(forge, "Botas Ligeras")
    _give(player, "Colmillo de Goblin", 25)
    _give(player, "Colmillo de Huargo", 25)
    player.inventory.gold = 30

    forge._craft(player, recipe)  # consume ambos materiales por completo

    assert "Colmillo de Goblin" not in player.inventory.quantities
    assert recipe.is_discovered(player) is True


def test_open_only_lists_discovered_recipes(player, monkeypatch, capsys):
    forge = Forge()
    _give(player, "Piel de Troll", 2, rarity="Legendario")  # solo descubre Armadura Regenerativa
    player.inventory.gold = 1000

    monkeypatch.setattr("valeterna.crafting.forge.console.ask", lambda prompt: "2")  # "Volver"

    forge.open(player)

    output_lines = capsys.readouterr().out.splitlines()
    shown_recipe_lines = [line for line in output_lines if "Requiere:" in line]
    assert len(shown_recipe_lines) == 1
    assert "Armadura Regenerativa" in shown_recipe_lines[0]
    assert any("por descubrir" in line for line in output_lines)
