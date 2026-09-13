"""PLANTILLA de secretos. Cópiala a ``secrets.py`` (mismo directorio) y rellena
los valores. ``secrets.py`` está en ``.gitignore`` y no se sube al repositorio.

    cp src/valeterna/config/secrets.example.py src/valeterna/config/secrets.py

Todos los valores son opcionales: si dejas uno vacío, esa función queda
desactivada (sin webhook = no se envían crashes; sin hash de admin = el nombre
"admin" deja de ser especial).
"""

# --- Informes de error a Discord (config/crash_reporting.py) ---

# URL del webhook del canal de errores (Ajustes del canal -> Integraciones ->
# Webhooks -> Copiar URL).
CRASH_WEBHOOK_URL = ""

# ID numérico de Discord al que mencionar en cada crash, para que te llegue una
# notificación. Actívate el "Modo desarrollador" en Discord (Ajustes -> Avanzado),
# luego clic derecho en tu nombre -> "Copiar ID de usuario". Déjalo vacío para
# no mencionar a nadie.
CRASH_MENTION_USER_ID = ""


# --- Modo admin / debug (ui/menus.py) ---

# Hash SHA-256 de la contraseña del modo admin. Genera el tuyo con:
#   python -c "import hashlib; print(hashlib.sha256('TU_CONTRASEÑA'.encode()).hexdigest())"
ADMIN_PASSWORD_HASH = ""
