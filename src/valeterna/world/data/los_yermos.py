from valeterna.world.zone import Zone

ZONE = Zone(
    id="los_yermos",
    name="Los Yermos",
    theme="Tierras salvajes en torno al pueblo",
    enemies=("Goblin", "Huargo", "Esqueleto", "Bandido"),
    sub_locations=("Campamento de bandidos", "Túmulo"),
    key_npcs=("Cael",),
)
