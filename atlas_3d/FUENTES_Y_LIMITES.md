# Fuentes, soporte espacial y límites de la reconstrucción

Esta es una organización y visualización de los datos ya usados por el estudio, no una adquisición LiDAR ni una estimación nueva. El CRS horizontal es WGS 84 / UTM 17S, EPSG:32717, metros. Las cotas se conservan como valores de FABDEM; no se corrigió ni comprobó un datum vertical local mediante puntos de control. La exageración vertical del visor sólo modifica la visualización y no las cotas consultadas.

## Fuentes

| Insumo | Uso y soporte | Procedencia conservada |
|---|---|---|
| FABDEM V1-2 | Relieve y derivados hidrológicos digitales; aproximadamente 30 m | V10, exportación alineada ya controlada; [repositorio de Bristol](https://data.bris.ac.uk/data/dataset/s5hqmjcdj8yo2ibzi9b4ew3sn), [Hawker et al.](https://doi.org/10.1088/1748-9326/ac4d4f) |
| Copernicus DEM y HEM | Altitud usada por la red, pendiente, posición y relieve local; control HEM, 30 m | V05; se conserva el DSM y sus bandas derivadas, sin confundirlo con FABDEM |
| ESA WorldCover 2021 v200 | Cobertura y construido; malla 10 m | V05; [producto y DOI](https://doi.org/10.5281/zenodo.7254221), [atribución y condiciones](https://esa-worldcover.org/en/data-access) |
| Vías, ríos, quebradas, colectores y microcuencas | Referencias vectoriales y covariables de proximidad | Cartografía municipal usada en V05/V10; [servicio PUGS](https://geoquito.quito.gob.ec/server/rest/services/web_reference_dmot/plan_de_uso_y_gestion_del_suelo_2024/MapServer/) |
| Reportes de inundación | 331 localizaciones históricas del inventario ya procesado; no huellas de agua | SNGR, subconjunto V05 con fecha hasta 2025-09-30. La localización de un reporte puede ser imprecisa; no es etiqueta de todos los píxeles cercanos |
| Censo 2022 / capa municipal parroquial | NBI, saneamiento, agua y hacinamiento, 65 parroquias | V12, atributos originales conservados en `parroquias`. NBI: personas; saneamiento/agua: viviendas; hacinamiento: hogares |
| Puntajes territoriales V12 | Comparador loglineal, red residual, decil exacto y control del soporte | Copias y reconstrucción desde los puntajes completos del estudio; no entrenamiento nuevo |
| Pronóstico de lluvia V07 | Probabilidad de lluvia trimestral superior al percentil 80 histórico y mediana en mm | Emisión congelada 2026-10-09, noviembre 2026–enero 2027; antecedentes hasta agosto de 2026; 186 celdas nativas de 0.05°. Se conserva el modelo `red_ENSO__beta_PIT` |

Los archivos de `5_VERIFICACION/control_capas.json` identifican las rutas originales y los SHA256 de las ocho copias fuente. Las tablas del GeoPackage conservan los atributos de las capas originales. La reconstrucción no actualiza sus fechas de observación: la fecha de creación de este proyecto no convierte una fuente histórica en información actual.

## Relación con el modelo

Las 25 entradas físicas pueden explorarse como 14 variables continuas y once indicadores de clases WorldCover. El mapa de cobertura es una sola clasificación. HEM, borde externo y soporte acotado se muestran además como controles; no son automáticamente predictores adicionales. La densidad relativa tiene normalización territorial y no es una probabilidad. En los GeoTIFF de percentiles, el valor almacenado se divide por 100 para obtener el percentil 0–100; no se divide para convertirlo en probabilidad.

Las áreas finales ponderan el construido prioritario por probabilidad húmeda y, alternativamente, por proporción NBI u otra carencia. Sus unidades son **ha ponderadas**, no personas afectadas ni hectáreas físicamente inundadas. NBI ya integra carencias de servicios en su definición: no se suma con saneamiento o agua como si fueran dimensiones independientes.

## Qué no se agregó

No se añadieron alturas de edificios sintéticas, texturas fotográficas generadas, roturas, profundidad de agua, aforos o tuberías que no estuvieran medidos. La variable de proximidad a estructuras OSM cuya fuente no pudo recuperarse no se presenta como evidencia; las alturas GEDI experimentales tampoco se usan para construir edificios ficticios. Las redes lineales municipales no prueban capacidad, continuidad ni estado de mantenimiento del drenaje.

El construido válido excluye 28776 píxeles por falta de covariables de base en la aplicación original. Otros 84 píxeles válidos (0.84 ha) quedaron sin asignación parroquial; se conservan en el ráster, sin adjudicarlos artificialmente a una parroquia. El decil contiene 299362 píxeles (2993.62 ha) sobre todo el dominio válido, por lo que su suma parroquial puede diferir ligeramente.

La malla y los polígonos simplificados del navegador son para exploración. Los vectores completos están en el GeoPackage. La lluvia conserva su soporte original aunque se dibuje sobre un terreno detallado. Ni las texturas ni el relieve certifican extensión o profundidad de inundación futura por píxel.

## Atribuciones y términos

© ESA WorldCover project 2021 / Contains modified Copernicus Sentinel data (2021) processed by ESA WorldCover consortium. WorldCover: CC BY 4.0.

FABDEM y los derivados que lo incorporan: conservar atribución y condiciones CC BY-NC-SA 4.0. La licencia del artículo metodológico no reemplaza la licencia del conjunto de datos. Copernicus DEM y los datos municipales conservan sus términos de origen; esta entrega no concede permisos adicionales ni declara una licencia única sobre todo el GeoPackage.

El código original del visor y de preparación corresponde a Wilson Gustavo Morales Lastra y sigue la licencia MIT del repositorio. Esa licencia no se extiende a los datos. Three.js 0.160.0 y OrbitControls se incluyen con su licencia MIT, en `4_VISOR/vendor/THREE-LICENSE.txt`.

El esquema QGIS se contrastó con las clases oficiales `Qgs3DMapSettings`, `QgsDemTerrainSettings`, `QgsCameraController` y `QgsMapThemeCollection`, rama release-3_44. La documentación de referencia es la [vista 3D de QGIS 3.44](https://docs.qgis.org/3.44/en/docs/user_manual/map_views/3d_map_view.html). Los archivos de código QGIS descargados sólo se conservan como referencia técnica en `5_VERIFICACION/REFERENCIA`; no forman parte del código nuevo ni cambian sus licencias GPL.

## Edición pública de 16 de octubre de 2026

La copia local completa se conserva por separado. Esta edición excluye los registros originales de inundación y las redes municipales originales: ríos, quebradas, colectores, microcuencas y vías. Las referencias y los scripts de construcción histórica permiten identificar las fuentes; no se concede una licencia de redistribución que sus servicios no especifican. Las geometrías parroquiales y los indicadores agregados corresponden a los derivados del paquete reproducible. Las capas excluidas no intervienen en la reproducción de los resultados congelados.

No se incluyen titulares catastrales, domicilios, encuestas individuales, credenciales ni documentos de firma. El proyecto QGIS conserva 45 entradas, nueve temas y cuatro cámaras. Su apertura nativa en QGIS no se certifica mediante los controles XML. Los scripts históricos de construcción requieren los insumos de las versiones originales; el punto de entrada público restaura y comprueba la entrega ya construida.
