import logging
import os
import random

import pygame

logger = logging.getLogger("valeterna.audio")

# "Scaring Crows" (tema inquietante) queda reservado para los combates que son
# un reto de verdad: el tramo final de la cadena, calibrado en su día al
# 73-78% de victorias del jugador (ver TODO.md) — justo por debajo del jefe
# final, que tiene su propio tema épico en vez de este. El resto de peleas
# (más fáciles) comparten el mismo grupo de música que el menú/aventura.
HARD_BATTLE_ENEMIES = {"Gólem de Piedra", "Mago", "Nigromante", "Ángel Caído", "Demonio"}
FINAL_BOSS = "Dragón"


class ResourceManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self.sounds = {}  # SFX: nombre -> pygame.mixer.Sound (varios a la vez, canal libre)
        self.music_paths = {}  # Música: nombre -> ruta de archivo
        self.current_volume_sfx = 0.5
        self.current_volume_music = 0.4
        self.current_track_name = None
        self.mood = "adventure"  # Estado por defecto
        self.target_enemy = None
        self._initialized = True

    def update(self):
        """Se autogestiona según el mood actual: si la pista ya terminó, elige la siguiente."""
        # El mezclador puede estar ya cerrado (p. ej. el juego está saliendo y el
        # hilo de música en segundo plano todavía da una última vuelta): sin esta
        # guarda, pygame lanzaría "Audio device hasn't been opened".
        if not pygame.mixer.get_init():
            return
        if not pygame.mixer.music.get_busy():
            if self.mood == "battle":
                self.play_battle_music(self.target_enemy)
            else:
                self.play_random_adventure_music()

    def set_mood(self, mood, enemy_name=None):
        """Cambia el contexto musical."""
        self.mood = mood
        self.target_enemy = enemy_name

    def has_dedicated_battle_music(self, enemy_name) -> bool:
        """¿Este enemigo tiene tema de combate propio? Hoy: el jefe final y los
        5 enemigos duros del tramo final. El resto (enemigos "estándar")
        comparten el pool de aventura/menú.

        Pendiente (ver TODO.md): cuando existan élites y guardianes de zona,
        serán ellos —no la dificultad calibrada— quienes activen música de
        combate; los enemigos normales de zona nunca cortarán la pista."""
        return enemy_name == FINAL_BOSS or enemy_name in HARD_BATTLE_ENEMIES

    def enter_battle(self, enemy_name) -> None:
        """Entra en combate. Solo cambia la música si el enemigo tiene tema
        propio; contra enemigos estándar se deja sonar lo que hubiera, para no
        cortar la pista una y otra vez en peleas cortas (sobre todo en
        auto-batalla y sus cadenas)."""
        if self.has_dedicated_battle_music(enemy_name):
            self.set_mood("battle", enemy_name)
            self.play_battle_music(enemy_name)

    def exit_battle(self) -> None:
        """Sale de combate. Solo fuerza un cambio de pista si veníamos de música
        de combate dedicada; si sonaba una pista de aventura, sigue sonando."""
        was_battle = self.mood == "battle"
        self.set_mood("adventure")
        if was_battle:
            self.play_random_adventure_music()

    def play_battle_music(self, enemy_name) -> None:
        """Elige y reproduce de inmediato la música de combate del enemigo dado,
        sin esperar a que la pista actual termine (a diferencia de update(),
        que solo actúa cuando pygame.mixer.music ya está libre) — se llama al
        entrar en un combate para que el cambio de música sea instantáneo."""
        if enemy_name == FINAL_BOSS:
            self.play_music("Siege_of_the_Black_Gate")
        elif enemy_name in HARD_BATTLE_ENEMIES:
            self.play_music("scaring_crows")
        else:
            # Enemigos más asequibles: mismo pool que la música de aventura/menú.
            self.play_random_adventure_music()

    def play_random_adventure_music(self):
        adventure_tracks = ["a_robust_crew", "ale_and_anecdotes", "Wanderers_Hearth"]
        chosen = random.choice(adventure_tracks)
        self.play_music(chosen)

    def is_music_playing(self, name):
        """¿Está sonando ahora mismo esta pista en concreto?"""
        return pygame.mixer.music.get_busy() and self.current_track_name == name

    def load_audio(self, name, path, is_music=False):
        if not os.path.exists(path):
            logger.warning("Archivo de audio no encontrado: %s (%s)", path, name)
            print(f"Archivo no encontrado: {path}")
            return

        if is_music:
            # pygame.mixer.music solo puede tener una pista cargada a la vez,
            # así que aquí solo guardamos la ruta; se carga de verdad en
            # play_music(), cuando toque reproducirla.
            self.music_paths[name] = path
            return

        try:
            sound = pygame.mixer.Sound(path)
            sound.set_volume(self.current_volume_sfx)
            self.sounds[name] = sound
        except Exception as e:
            logger.warning("Error al cargar audio %s: %s", name, e)
            print(f"Error al cargar audio {name}: {e}")

    def play_music(self, name, loops=0):
        if name not in self.music_paths:
            return
        if not pygame.mixer.get_init():
            return
        # Si ya está sonando esta misma pista, no la cortamos ni la reiniciamos.
        if self.current_track_name == name and pygame.mixer.music.get_busy():
            return
        try:
            pygame.mixer.music.load(self.music_paths[name])
            pygame.mixer.music.set_volume(self.current_volume_music)
            pygame.mixer.music.play(loops=loops)
            self.current_track_name = name
        except Exception as e:
            logger.warning("Error al reproducir música %s: %s", name, e)
            print(f"Error al reproducir música {name}: {e}")

    def play_sfx(self, name):
        """Reproduce un efecto de sonido si existe en el diccionario."""
        if name in self.sounds:
            self.sounds[name].play()
        else:
            logger.warning("SFX no encontrado: %s", name)
            print(f"SFX {name} no encontrado.")

    def stop_all_music(self):
        pygame.mixer.music.stop()
        self.current_track_name = None

    def set_volume_music(self, volume):
        self.current_volume_music = volume
        pygame.mixer.music.set_volume(volume)

    def set_volume_sfx(self, volume):
        self.current_volume_sfx = volume
        for track in self.sounds.values():
            track.set_volume(volume)
