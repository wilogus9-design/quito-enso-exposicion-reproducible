# Atlas tridimensional de Quito

Edición pública del proyecto multicapa preparado para el estudio **Pobreza y
priorización ante inundaciones en Quito**. Autor del código y la reconstrucción:
Wilson Gustavo Morales Lastra, investigador independiente, Quito, Ecuador.
Contacto: wilogus9@gmail.com. La autoría y las contribuciones del artículo se
documentan por separado en `../AUTORES_ARTICULO.json`.

## Abrir en otro equipo

Descargue el repositorio completo o clónelo. Desde esta carpeta ejecute:

```bash
python preparar_3d.py
```

La entrada comprueba los archivos, reúne las capas grandes distribuidas en
partes y abre el visor en el navegador mediante un servidor local. Requiere
Python 3.10 o posterior, sin librerías adicionales ni cuentas. No abra el HTML
con doble clic. Cerrar la consola o pulsar Ctrl+C detiene el servidor.

Para verificar sin abrir el navegador:

```bash
python preparar_3d.py --verificar
```

Después puede abrir `1_PROYECTO_QGIS/quito_multicapa.qgz` en QGIS 3.44. Conserve
la carpeta completa y sus rutas relativas. No confunda la comprobación de
archivos/XML con una prueba nativa de renderizado: esta última no se ha
certificado. Hay 45 entradas de capa, nueve temas y cuatro vistas 3D.

## Qué se puede explorar

El visor representa el relieve FABDEM y permite alternar cobertura WorldCover,
covariables topográficas, susceptibilidad, construido prioritario, probabilidad
de lluvia trimestral y prioridades parroquiales. Incluye pobreza por necesidades
básicas insatisfechas, saneamiento, agua y hacinamiento del censo 2022, además
de rutas de escorrentía y depresiones digitales calculadas por el estudio.
Los valores y las áreas consultadas se conservan en su soporte original; las
mallas y texturas del navegador se generalizan para una navegación ágil.

Los resultados y los escenarios son los congelados el 9 de octubre de 2026;
la publicación no los actualiza. La escena es una visualización del terreno y
los resultados del estudio, no una simulación hidráulica ni una reconstrucción
fotogramétrica de edificios. Consulte `FUENTES_Y_LIMITES.md` y el inventario.

## Edición pública y reconstrucción histórica

La entrega local completa se conserva sin modificaciones. Por precaución de
redistribución, esta edición no incluye las redes municipales originales ni
las coordenadas originales de los reportes de inundación. Sus controles del
visor están deshabilitados. No incluye catastro individual ni encuestas de
hogares. La omisión de estas referencias gráficas no cambia los modelos,
los rásteres de resultados ni las prioridades parroquiales reproducibles.

`3_CODIGO` conserva los scripts de preparación histórica y sus requisitos;
para rehacer esa construcción se necesitan los insumos de las versiones
originales que esos scripts identifican. El punto de entrada público restaura
y verifica los archivos preparados, sin fingir que vuelve a descargar o
reprocesar todas las fuentes. La reproducción estadística se ejecuta desde
la raíz mediante `python reproducir.py`.

## Atribución y licencias

El software original sigue la licencia MIT del repositorio. Los datos no
adquieren esa licencia: FABDEM y sus derivados mantienen CC BY-NC-SA 4.0;
WorldCover conserva CC BY 4.0 y su atribución Copernicus. Three.js y OrbitControls
incluyen su aviso MIT en `4_VISOR/vendor/THREE-LICENSE.txt`. Los datos agregados
y las fuentes institucionales conservan sus condiciones y atribuciones.
No se incluyen claves, contraseñas, documentos firmados ni correspondencia
editorial. `MANIFEST_3D.json` registra tamaños y SHA-256 para comprobar una
descarga completa. Las partes no son nuevas observaciones ni nuevas capas.
