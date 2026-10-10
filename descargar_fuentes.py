"""Consulta metadatos públicos. EE opcional usa credenciales externas oficiales.

No descarga ni ejecuta código remoto y no actualiza la muestra publicada.
"""
from pathlib import Path
import argparse
import json
import urllib.error
import urllib.request

SOURCES = {
    'quito_red_hidrica': 'https://geoquito.quito.gob.ec/server/rest/services/web_reference_dmot/plan_de_uso_y_gestion_del_suelo_2024/MapServer/11?f=pjson',
    'quito_vias': 'https://geoquito.quito.gob.ec/server/rest/services/web_reference_dmot/plan_de_uso_y_gestion_del_suelo_2024/MapServer/71?f=pjson',
    'quito_parroquias': 'https://geoquito.quito.gob.ec/server/rest/services/Hosted/Parroquias_DMQ/FeatureServer/0?f=pjson',
}


def inicializar_ee(project):
    if not project:
        raise ValueError('Indique su propio proyecto autorizado con --project')
    import ee
    try:
        ee.Initialize(project=project)
    except Exception:
        # No imprimir objetos de credenciales o errores que puedan contener URLs firmadas.
        raise RuntimeError('No se pudo inicializar EE. Configure autenticación y proyecto con el flujo oficial.') from None
    return ee


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--earthengine', action='store_true')
    parser.add_argument('--project')
    parser.add_argument('--salida', type=Path, default=Path('resultados/metadatos_fuentes'))
    args = parser.parse_args()
    args.salida.mkdir(parents=True, exist_ok=True)
    for name, url in SOURCES.items():
        try:
            request = urllib.request.Request(url, headers={'User-Agent': 'Quito-reproducible-research/1.0'})
            with urllib.request.urlopen(request, timeout=60) as response:
                data = json.load(response)
            if data.get('error'):
                raise ValueError('Servicio devolvió error')
            (args.salida / (name + '.json')).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
            print(name, 'metadatos descargados')
        except (OSError, ValueError):
            print(name, 'no disponible; el paquete congelado sigue ejecutable')
    if args.earthengine:
        ee = inicializar_ee(args.project)
        data = ee.ImageCollection('ESA/WorldCover/v200').first().bandNames().getInfo()
        (args.salida / 'earthengine_bandas_worldcover.json').write_text(json.dumps(data), encoding='utf-8')
        print('Earth Engine: metadatos consultados sin almacenar tokens')


if __name__ == '__main__':
    main()
