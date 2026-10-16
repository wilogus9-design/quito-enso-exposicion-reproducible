"""Restaura las capas distribuidas en partes y comprueba el atlas 3D.

Sólo utiliza la biblioteca estándar de Python; no descarga datos ni ejecuta
los scripts históricos de construcción. No sobrescribe archivos diferentes.
"""
from pathlib import Path
import argparse
import hashlib
import json
import sqlite3
import subprocess
import sys
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parent


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(4 * 1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def safe_path(relative):
    path = (ROOT / relative).resolve()
    if ROOT not in path.parents:
        raise ValueError('Ruta fuera del atlas: ' + relative)
    return path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--verificar', action='store_true', help='Restaurar, verificar y terminar sin abrir el navegador')
    parser.add_argument('--abrir', action='store_true', help='Abrir el visor después de verificar')
    args = parser.parse_args()
    meta = json.loads((ROOT / 'MANIFEST_3D.json').read_text(encoding='utf-8'))
    restored = 0
    for item in meta['files']:
        target = safe_path(item['path'])
        if target.exists():
            if target.stat().st_size != item['bytes'] or sha(target) != item['sha256']:
                raise ValueError('Archivo distinto; conservarlo y resolver antes de continuar: ' + item['path'])
            continue
        if not item.get('parts'):
            raise FileNotFoundError('Descargue el repositorio completo; falta ' + item['path'])
        parts = []
        for entry in item['parts']:
            part = safe_path(entry['path'])
            if not part.is_file() or part.stat().st_size != entry['bytes'] or sha(part) != entry['sha256']:
                raise ValueError('Parte ausente o corrupta: ' + entry['path'])
            parts.append(part)
        temporary = target.with_name(target.name + '.restaurando')
        target.parent.mkdir(parents=True, exist_ok=True)
        with temporary.open('xb') as output:
            for part in parts:
                with part.open('rb') as stream:
                    for block in iter(lambda: stream.read(4 * 1024 * 1024), b''):
                        output.write(block)
        if temporary.stat().st_size != item['bytes'] or sha(temporary) != item['sha256']:
            raise ValueError('Reconstrucción distinta; se conserva el temporal para inspección.')
        temporary.rename(target)
        restored += 1
        print('Restaurado:', item['path'], flush=True)
    qgs = ROOT / '1_PROYECTO_QGIS/quito_multicapa.qgs'
    project = ET.parse(qgs).getroot()
    layers = project.findall('./projectlayers/maplayer')
    assert len(layers) == meta['layers']
    ids = {x.findtext('id') for x in layers}
    for layer in layers:
        uri = layer.findtext('datasource')
        file = (qgs.parent / uri.split('|')[0]).resolve()
        assert file.is_file() and ROOT in file.parents, uri
    for layer in project.findall('./visibility-presets/visibility-preset/layer'):
        assert layer.get('id') in ids
    assert len(project.findall('./visibility-presets/visibility-preset')) == meta['themes']
    assert len(project.findall('./mapViewDocks3D/view')) == meta['views_3d']
    with zipfile.ZipFile(qgs.with_suffix('.qgz')) as z:
        assert z.testzip() is None and z.read(qgs.name) == qgs.read_bytes()
    with sqlite3.connect(f'file:{(ROOT / "2_CAPAS/vectores_quito.gpkg").as_posix()}?mode=ro', uri=True) as db:
        assert db.execute('PRAGMA integrity_check').fetchone()[0] == 'ok'
        assert {x[0] for x in db.execute('SELECT table_name FROM gpkg_contents')} == set(meta['vector_counts'])
        for table, count in meta['vector_counts'].items():
            assert db.execute('SELECT COUNT(*) FROM "' + table + '"').fetchone()[0] == count
    result = {'verified_files': len(meta['files']), 'restored_files': restored, 'layers': len(layers),
              'qgis_native_verified': False, 'note': 'Integridad y portabilidad; no nueva validación científica.'}
    (ROOT / 'CONTROL_LOCAL_3D.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result, ensure_ascii=False, indent=2), flush=True)
    print('QGIS:', qgs.with_suffix('.qgz'), flush=True)
    if args.abrir or not args.verificar:
        subprocess.run([sys.executable, str(ROOT / 'ABRIR_VISOR.py')], check=True, cwd=ROOT)


if __name__ == '__main__':
    main()
