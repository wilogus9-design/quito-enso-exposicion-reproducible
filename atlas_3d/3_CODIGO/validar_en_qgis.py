"""Ejecutar en la consola Python de QGIS después de abrir quito_multicapa.qgz.

No instala nada y no cambia datos. Escribe el resultado de apertura nativa
en 5_VERIFICACION/control_qgis_nativo.json. La comprobación 3D sigue siendo
visual: abrir una vista guardada y comprobar que el relieve se dibuje.
"""
from pathlib import Path
import json
from qgis.core import QgsProject, Qgis

project=QgsProject.instance()
root=Path(project.fileName()).resolve().parents[1]
if not (root/'1_PROYECTO_QGIS/indice_proyecto.json').is_file():
    raise RuntimeError('Abra primero el proyecto quito_multicapa.qgz de esta entrega.')
invalid=[{'nombre':layer.name(),'fuente':layer.source()}for layer in project.mapLayers().values()if not layer.isValid()]
themes=project.mapThemeCollection().mapThemes()
views=[view.attribute('name')for view in project.viewsManager().get3DViews()]
result={'version_qgis':Qgis.QGIS_VERSION,'capas':len(project.mapLayers()),'capas_invalidas':invalid,
    'temas':themes,'vistas_3d':views,'renderizado_3d_comprobado':False}
(root/'5_VERIFICACION/control_qgis_nativo.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(result,ensure_ascii=False,indent=2))
assert not invalid, 'Hay capas inválidas; consulte el informe.'
assert len(themes)==9 and len(views)==4
print('Fuentes y vistas cargadas. Falta la inspección visual de una vista 3D.')
