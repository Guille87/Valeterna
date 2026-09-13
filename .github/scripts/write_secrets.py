"""Genera src/valeterna/config/secrets.py a partir de los secrets del
repositorio, para que el .exe del Release lleve el informe de errores a Discord.

Si no hay ningún secreto configurado, no escribe nada y el juego funciona igual
(sin envío de crashes y sin modo admin), gracias a config/secret_store.py.

Se usa solo desde el workflow de release; nunca toca el secrets.py de nadie en local.
"""

import os
from pathlib import Path

KEYS = ("CRASH_WEBHOOK_URL", "CRASH_MENTION_USER_ID", "ADMIN_PASSWORD_HASH")
values = {key: os.environ.get(key, "") for key in KEYS}

if not any(values.values()):
    print("Sin secretos configurados; el .exe saldrá sin informe de errores a Discord.")
    raise SystemExit(0)

target = Path("src/valeterna/config/secrets.py")
lines = ['"""Generado por el workflow de release desde los secrets del repositorio."""', ""]
lines += [f"{key} = {value!r}" for key, value in values.items()]
target.write_text("\n".join(lines) + "\n", encoding="utf-8")
print(f"{target} generado con: {', '.join(k for k, v in values.items() if v)}")
