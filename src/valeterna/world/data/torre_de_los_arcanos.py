from valeterna.world.zone import Zone

ZONE = Zone(
    id="torre_de_los_arcanos",
    name="Torre de los Arcanos / Necrópolis",
    theme="Torre de magos + cementerio",
    enemies=("Mago", "Nigromante"),
    sub_locations=("Biblioteca", "Cripta"),
    key_npcs=("Sella",),
)
