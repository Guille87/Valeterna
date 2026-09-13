# Política de seguridad

<p align="center"><a href="../SECURITY.md">English</a> · <a href="SECURITY_es.md">Español</a></p>

## Versiones con soporte

Es un proyecto pequeño y personal. Solo la última versión publicada y `main`
reciben correcciones.

## Cómo informar de una vulnerabilidad

Por favor, **no abras un issue público** para problemas de seguridad.

Escribe a **guillermo_amado@hotmail.es** con:

- una descripción del problema y su impacto,
- los pasos para reproducirlo,
- la versión o el commit afectado.

Recibirás un acuse de recibo en unos días. Cuando haya una corrección lista se
publicará y se dará crédito a quien lo reportó, salvo que prefieras el anonimato.

## Notas de alcance

- El informe opcional de errores a Discord (`config/crash_reporting.py`) censura
  el nombre de usuario del sistema y las rutas del perfil antes de enviar nada, y
  está desactivado por defecto (opt-in).
- El panel de administración/debug es un cheat de un jugador protegido por un
  hash de contraseña en el `config/secrets.py` no versionado; no es una frontera
  de seguridad.

## Modelo de amenazas del auto-update

La build de Windows puede actualizarse sola (`src/valeterna/updater.py`).
Aplicar una actualización es siempre una acción explícita del jugador; la
comprobación al arrancar es un GET HTTPS a la API de GitHub y no envía nada.

- **Qué se protege:** la actualización se descarga por HTTPS desde el GitHub
  Release y su SHA-256 se compara con el archivo `SHA256SUMS` publicado en ese
  mismo Release antes de aplicar nada. Un hash que no cuadra, un `SHA256SUMS`
  ausente o una versión que no sea estrictamente más nueva que la instalada
  abortan la actualización. Esto protege ante una descarga corrupta o un atacante
  en la red.
- **Qué no se protege:** cualquiera que pueda publicar un Release en el
  repositorio (una cuenta de mantenedor comprometida) puede publicar un hash
  válido para una build maliciosa. La mitigación prevista es una firma Ed25519
  detached verificada en `updater.verify()` con una clave pública incrustada en
  el binario.
