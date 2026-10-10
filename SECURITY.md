# Seguridad y privacidad

No se solicita ninguna contraseña para reproducir el estudio. No envíe
contraseñas, tokens, cookies, claves privadas o archivos de cuentas de servicio
en issues, commits, anexos o correos de depuración.

Los pesos y matrices de la ruta pública están en formato numérico NPZ y se
abren con `allow_pickle=False`. No se cargan checkpoints arbitrarios `.pt` ni
scripts descargados durante la ejecución estándar. MANIFEST.json contiene
SHA-256 de cada archivo del paquete. Esto detecta alteraciones respecto del
manifiesto, no hace seguro un manifiesto obtenido de una fuente no confiable.

La revisión previa a publicación busca formatos de tokens, claves privadas,
contraseñas embebidas y campos privados, también dentro del archivo histórico.
Es una comprobación preventiva, no una auditoría de seguridad certificada.
La sesión GitHub permanece en el navegador; no se extrae ni se publica.
Las credenciales de Earth Engine o NASA se mantienen fuera del repositorio.

No se publican microdatos ENEMDU ni identificadores prediales/personales.
Los reportes sólo aparecen como covariables sin coordenadas originales o
narraciones. Los píxeles describen cobertura física pública, no la condición
económica de habitantes identificables. El contexto NBI permanece agregado.

Si una credencial se publica por error, revóquela en el proveedor antes de
limpiar archivos o historia Git. Eliminarla del último commit no la revoca.
Para fallos técnicos, envíe versión y comando sin secretos ni datos personales.
