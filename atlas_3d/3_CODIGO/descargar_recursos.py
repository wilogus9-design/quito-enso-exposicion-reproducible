"""Descarga sólo bibliotecas y esquemas públicos; no descarga datos de usuarios."""
from pathlib import Path
import hashlib
import json
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
resources = {
    '4_VISOR/vendor/three.module.js': 'https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.module.js',
    '4_VISOR/vendor/OrbitControls.js': 'https://cdn.jsdelivr.net/npm/three@0.160.0/examples/jsm/controls/OrbitControls.js',
    '4_VISOR/vendor/THREE-LICENSE.txt': 'https://cdn.jsdelivr.net/npm/three@0.160.0/LICENSE',
    '5_VERIFICACION/REFERENCIA/qgs3dmapsettings.cpp': 'https://raw.githubusercontent.com/qgis/QGIS/release-3_44/src/3d/qgs3dmapsettings.cpp',
    '5_VERIFICACION/REFERENCIA/qgsdemterrainsettings.cpp': 'https://raw.githubusercontent.com/qgis/QGIS/release-3_44/src/3d/terrain/qgsdemterrainsettings.cpp',
    '5_VERIFICACION/REFERENCIA/qgsabstractterrainsettings.cpp': 'https://raw.githubusercontent.com/qgis/QGIS/release-3_44/src/3d/terrain/qgsabstractterrainsettings.cpp',
    '5_VERIFICACION/REFERENCIA/qgs3dmapcanvaswidget.cpp': 'https://raw.githubusercontent.com/qgis/QGIS/release-3_44/src/app/3d/qgs3dmapcanvaswidget.cpp',
    '5_VERIFICACION/REFERENCIA/qgisapp.cpp': 'https://raw.githubusercontent.com/qgis/QGIS/release-3_44/src/app/qgisapp.cpp',
    '5_VERIFICACION/REFERENCIA/qgscamerapose.cpp': 'https://raw.githubusercontent.com/qgis/QGIS/release-3_44/src/3d/qgscamerapose.cpp',
    '5_VERIFICACION/REFERENCIA/qgscameracontroller.cpp': 'https://raw.githubusercontent.com/qgis/QGIS/release-3_44/src/3d/qgscameracontroller.cpp',
    '5_VERIFICACION/REFERENCIA/qgsprojectviewsettings.cpp': 'https://raw.githubusercontent.com/qgis/QGIS/release-3_44/src/core/project/qgsprojectviewsettings.cpp',
    '5_VERIFICACION/REFERENCIA/qgsproject.cpp': 'https://raw.githubusercontent.com/qgis/QGIS/release-3_44/src/core/project/qgsproject.cpp',
    '5_VERIFICACION/REFERENCIA/qgsmapthemecollection.cpp': 'https://raw.githubusercontent.com/qgis/QGIS/release-3_44/src/core/qgsmapthemecollection.cpp',
}
records = []
for relative, url in resources.items():
    destination = ROOT / relative
    destination.parent.mkdir(parents=True, exist_ok=True)
    try:
        if not destination.exists():
            request = urllib.request.Request(url, headers={'User-Agent':'Quito-3D-research/1.0'})
            with urllib.request.urlopen(request, timeout=50) as response:
                destination.write_bytes(response.read())
        records.append({'file':relative, 'source':url, 'bytes':destination.stat().st_size,
                        'sha256':hashlib.sha256(destination.read_bytes()).hexdigest()})
        print(relative, destination.stat().st_size, flush=True)
    except Exception as error:
        records.append({'file':relative, 'source':url, 'error':str(error)})
        print('No disponible:', relative, type(error).__name__, flush=True)
(ROOT/'5_VERIFICACION/recursos_publicos.json').write_text(json.dumps(records, indent=2), encoding='utf-8')
