# Autenticación, solicitudes y tokens

Este es un repositorio de investigación, **no una aplicación con cuentas de
usuarios**. No tiene servidor de login, contraseña del modelo ni JWT propios.

## Componentes y flujo real

| Ruta | Flujo de solicitud | Credenciales |
| --- | --- | --- |
| Reproducción incluida | reproducir.py → archivos locales → SHA-256 → modelo.py → tablas/mapa | Ninguna; no hace solicitudes de red |
| Consulta de fuentes públicas | descargar_fuentes.py → HTTPS del servicio oficial → JSON numérico/metadatos | Ninguna, cuando el proveedor mantiene acceso anónimo |
| Consulta opcional Earth Engine | inicializar_ee → ee.Initialize → proveedor OAuth Google → servicio EE | Credenciales locales del usuario, fuera del repositorio |
| Creación inicial GitHub | navegador con sesión ya iniciada → formulario HTTPS de GitHub → repositorio público | Cookie de sesión administrada por GitHub y navegador; no se exportó al código |
| Carga del paquete | navegador con sesión ya iniciada → carga HTTPS visible de GitHub → commit público | Cookie de sesión administrada por GitHub y navegador; no se exportó al código |
| Reutilización por otra persona | descarga pública/clone → ejecución local | No necesita credenciales del autor |

`descargar_fuentes.py` verifica URLs HTTPS de un conjunto cerrado de fuentes,
no acepta URLs arbitrarias con secretos y no coloca credenciales en parámetros.
La ruta opcional EE no se invoca desde reproducir.py. No confundir la revisión
de metadatos con una nueva descarga integral de todos los datos satelitales.

## Earth Engine opcional

Según la [documentación oficial](https://developers.google.com/earth-engine/guides/auth),
`ee.Initialize()` usa credenciales Earth Engine previamente guardadas o las
credenciales predeterminadas de Google. Cada reproductor debe configurar su
propio proyecto autorizado. El paquete no copia el proyecto ni la cuenta del autor.

La biblioteca obtiene tokens de acceso del proveedor OAuth; si procede, los
renueva con las credenciales locales. El script propio no manipula, imprime,
persiste ni devuelve esos tokens. Si falta autenticación, el usuario ejecuta
el flujo oficial `earthengine authenticate` por su cuenta, fuera del repositorio.
No publicar el archivo `~/.config/earthengine/credentials`, cuentas de servicio
ni `GOOGLE_APPLICATION_CREDENTIALS`. Tampoco enviarlos por issues o chat.

```bash
python -m pip install earthengine-api
earthengine authenticate
python descargar_fuentes.py --earthengine --project SU_PROYECTO
```

NASA PPS/Earthdata no es necesario para los datos congelados de esta entrega.
Las credenciales usadas en otras investigaciones no se incorporan aquí.

## GitHub

La creación inicial y la carga de la versión 1.0.0 usan la sesión de navegador
ya abierta. La automatización interactúa con controles visibles de GitHub; no
lee cookies ni fabrica solicitudes autenticadas. Se cargaron exclusivamente los
archivos raíz enumerados por MANIFEST.json y el propio manifiesto. No se creó un
PAT, clave SSH o aplicación OAuth para este repositorio.
Para contribuciones posteriores se puede usar la autenticación oficial de GitHub
CLI o Git Credential Manager, guardando secretos en el almacén local correspondiente,
nunca dentro de un archivo versionado. Consulte [autenticación de GitHub](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/about-authentication-to-github).

Los hashes comprueban consistencia con MANIFEST.json, no certifican identidad
del autor ni reemplazan una firma. El repositorio público ofrece lectura anónima;
las escrituras quedan bajo las autorizaciones de GitHub de su propietario.

## Comprobación posterior a la publicación

El 2026-10-10 se clonó públicamente el repositorio en una carpeta independiente
y se verificó el snapshot `1e09b74130100e193f1626a8baf23b17adb86bd3`.
Coincidieron los 64 hashes declarados en MANIFEST.json. Desde esa descarga,
`python reproducir.py` aprobó las siete pruebas, reconstruyó 48 comparaciones,
infirió 2993619 píxeles y reprodujo los seis escenarios para 65 parroquias sin
usar credenciales. La documentación de este resultado se añadió después de esa
ejecución; no cambia código, datos, pesos ni resultados científicos.
