# Fuentes, atribución y alcance de la publicación

El código original se publica bajo MIT. La licencia MIT **no** se aplica
automáticamente a los datos, las imágenes de terceros o sus derivados.
No se redistribuyen credenciales, encuestas individuales ni las bases de otros autores.

| Fuente | Atribución y condiciones | Qué se incluye |
| --- | --- | --- |
| FABDEM V1-2 | Neal, Hawker, Uhe y colaboradores, University of Bristol. [CC BY-NC-SA 4.0](https://research-information.bris.ac.uk/en/datasets/fabdem-v1-2/). DOI 10.5523/bris.s5hqmjcdj8yo2ibzi9b4ew3sn | Covariables y productos calculados, no mosaico global |
| Copernicus DEM GLO-30 | © DLR e.V. 2010–2014 and © Airbus Defence and Space GmbH 2014–2018, produced using Copernicus WorldDEM-30 | Variables topográficas, con soporte nativo 30 m |
| ESA WorldCover 2021 v200 | [CC BY 4.0](https://esa-worldcover.org/en/data-access). © ESA WorldCover project 2021 / Contains modified Copernicus Sentinel data (2021) processed by ESA WorldCover consortium. DOI 10.5281/zenodo.7254221 | Variables de cobertura y máscara de construido derivadas |
| Municipio del Distrito Metropolitano de Quito, Geoportal | Servicios públicos citados en FUENTES.json. Se mantiene atribución; acceso público no es una nueva concesión MIT | Distancias y geometría parroquial agregada; no bases catastrales originales, titulares ni direcciones |
| Secretaría Nacional de Gestión de Riesgos | Archivo histórico público de eventos, corte 2010–septiembre 2025 | Soporte numérico de reportes sin coordenadas originales, nombres, direcciones ni identificadores del registro |
| Instituto Nacional de Estadística y Censos, censo 2022 | Fuente censal, universos y definiciones conservados | Porcentajes parroquiales y denominadores agregados; no microdatos |
| NOAA, NMME y módulo V07 propio | Referencias y datos públicos citados, salidas procesadas propias | Probabilidades húmedas de escenarios congelados, no reentrenamiento meteorológico |

Los artefactos que contienen derivados FABDEM (`PIXELES_*.npz`, matrices
`*fabdem*.npz`, pesos entrenados con FABDEM y mapas/resultados correspondientes)
se distribuyen para reproducción no comercial bajo **CC BY-NC-SA 4.0**, con
las atribuciones originales. Para evitar inducir a una reutilización comercial
incompatible, el conjunto de matrices y pesos de esta distribución se ofrece
bajo esas condiciones conservadoras, **sin cambiar derechos de las fuentes**.
La atribución de datos y restricciones independientes del proveedor subsisten.
El texto legal está en https://creativecommons.org/licenses/by-nc-sa/4.0/.

Los registros y cartografía municipal originales no se relicencian ni se
redistribuyen. Los scripts históricos permiten consultar las fuentes públicas
originales. Este paquete publica cálculos propios y no una copia del catastro.
OpenStreetMap no fue un predictor: la consulta falló y su ausencia no se
codificó como inexistencia de estructuras.

La autoría de la metodología aplicada, código propio, modelos y análisis
corresponde a Wilson Gustavo Morales Lastra. La autoría de las observaciones,
productos satelitales y bases institucionales corresponde a sus productores.
El paquete de Canavire y colaboradores es un antecedente ajeno y no se incluye.
La asistencia computacional en la preparación no constituye coautoría humana.

## Atlas tridimensional de la versión 1.1.0

`atlas_3d` publica una edición preparada del proyecto QGIS y del visor local.
Incluye recortes y derivados de terreno/cobertura con las condiciones indicadas
arriba; FABDEM y sus derivados siguen CC BY-NC-SA 4.0. El proveedor confirma
esa licencia en https://research-information.bris.ac.uk/en/datasets/fabdem-v1-2/.
Las partes binarias se reúnen sin cambiar los valores ni las atribuciones.

No se incluyen las redes municipales originales ni los puntos originales de
los reportes de inundación en la edición pública. Los servicios de referencia
consultados no establecieron una licencia de redistribución suficiente para
añadirlos al repositorio; sus enlaces se conservan para consulta directa.
Las rutas y depresiones digitales calculadas, las geometrías parroquiales
procesadas y los indicadores agregados sí se incluyen. La licencia MIT del
software no reemplaza los términos de los datos ni la licencia de Three.js,
incluida por separado. No se publican cartas editoriales ni documentos de firma.
