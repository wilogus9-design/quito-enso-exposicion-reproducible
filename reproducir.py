"""Punto único: hashes, controles, benchmark, inferencia completa y prioridad NBI.

python reproducir.py                  # Reproduce todo, sin red ni tokens.
python reproducir.py --solo-benchmark # Evaluación pequeña, sin mapa completo.
python reproducir.py --geotiff        # También raster GIS; requiere rasterio.
python reproducir.py --reentrenar --key temporal__vias_fabdem --device cpu
"""
import os
os.environ.setdefault('OPENBLAS_NUM_THREADS', '1')
os.environ.setdefault('OMP_NUM_THREADS', '1')
from pathlib import Path
import argparse
import csv
import hashlib
import json
import time
import numpy as np
from modelo import evaluar, ensamble, inferir, logsumexp

ROOT = Path(__file__).resolve().parent
SEEDS = (5101, 5102, 5103)
MODELS = ('red_residual', 'ancla_acotada')


def read_csv(path):
    with path.open(encoding='utf-8-sig', newline='') as stream:
        return list(csv.DictReader(stream))


def write_csv(path, rows):
    if not rows:
        raise ValueError('Tabla vacía: ' + str(path))
    with path.open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def verify_hashes(root=ROOT):
    manifest = json.loads((root / 'MANIFEST.json').read_text(encoding='utf-8'))
    for item in manifest['files']:
        path = root / item['name']
        if path.parent != root or not path.is_file():
            raise ValueError('Archivo ausente o ruta fuera del paquete: ' + item['name'])
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if digest != item['sha256']:
            raise ValueError('SHA-256 no coincide: ' + item['name'])
    print(f"SHA-256: {len(manifest['files'])} archivos verificados", flush=True)
    return manifest


def benchmark(out):
    states = json.loads((ROOT / 'PARAMETROS.json').read_text(encoding='utf-8'))
    selection = json.loads((ROOT / 'SELECCION.json').read_text(encoding='utf-8'))
    rows, differences = [], []
    rng = np.random.default_rng(11109)
    with np.load(ROOT / 'PESOS.npz', allow_pickle=False) as weights, \
         np.load(ROOT / 'REFERENCIAS_PREDICCIONES.npz', allow_pickle=False) as refs:
        for key, st in states.items():
            with np.load(ROOT / f'DATOS_{key}.npz', allow_pickle=False) as z:
                data = {k: z[k] for k in z.files}
            e, b = data['etest'], data['btest']
            valid = data['valid_e'][e]
            Xb = data['Xb'][b]
            Xe = data['Xe'][e].reshape(-1, Xb.shape[1])
            predictions = {}
            for model in ('loglineal', 'red_libre'):
                predictions[model] = (refs[key + '__' + model + '__fe'], refs[key + '__' + model + '__fb'])
            predictions['ancla_acotada'] = (data['Xe'][e] @ data['anchor'], Xb @ data['anchor'])
            for bound in (0.25, 1.0):
                label = str(bound).replace('.', 'p')
                fes, fbs = [], []
                for seed in SEEDS:
                    prefix = key + '__B' + label + '__s' + str(seed)
                    fe, ae = inferir(Xe, weights, prefix, bound)
                    fb, ab = inferir(Xb, weights, prefix, bound)
                    assert np.max(np.abs(fe - ae)) <= bound + 1e-4
                    assert np.max(np.abs(fb - ab)) <= bound + 1e-4
                    fes.append(fe.reshape(valid.shape))
                    fbs.append(fb)
                predictions['residual_B' + str(bound)] = ensamble(fes, fbs)
            chosen = selection[key]['bound_selected_by_calibration']
            assert chosen == max(selection[key]['mean_calibration_scores'])[1]
            predictions['residual_cal'] = predictions['residual_B' + str(chosen)]
            vectors = {}
            block = data['block'][e]
            for model, (fe, fb) in predictions.items():
                ev, cap = evaluar(fe, fb, valid)
                vectors[model] = ev
                rows.append(dict(protocolo=st['protocol'], variante=st['variant'], modelo=model,
                    n_test=int(e.sum()), n_bloques=len(np.unique(block)),
                    log_densidad_relativa=float(ev.mean()), captura_top10pct_soporte=float(cap.mean()),
                    bound_selected_by_calibration=chosen if model == 'residual_cal' else ''))
            unique = np.unique(block)
            counts = np.array([(block == k).sum() for k in unique])
            draw = rng.integers(0, len(unique), (3000, len(unique)))
            for other in ('loglineal', 'ancla_acotada', 'red_libre'):
                delta = vectors['residual_cal'] - vectors[other]
                sums = np.array([delta[block == k].sum() for k in unique])
                simulated = sums[draw].sum(1) / counts[draw].sum(1)
                lo, hi = np.quantile(simulated, (0.025, 0.975))
                differences.append(dict(protocolo=st['protocol'], variante=st['variant'], comparador=other,
                    delta_log_densidad_residual=float(delta.mean()), rango95_inf=float(lo), rango95_sup=float(hi),
                    n_bloques=len(unique), inferencia='exploratoria por bloques; extensión posterior a V10'))
            print('Benchmark:', key, flush=True)
    reference = read_csv(ROOT / 'REFERENCIA_comparacion_modelos.csv')
    expected = {(r['protocolo'], r['variante'], r['modelo']): r for r in reference}
    errors = []
    for row in rows:
        old = expected[(row['protocolo'], row['variante'], row['modelo'])]
        for name in ('log_densidad_relativa', 'captura_top10pct_soporte'):
            errors.append(abs(row[name] - float(old[name])))
    if max(errors) > 2e-5:
        raise AssertionError('Benchmark no replica la referencia: ' + str(max(errors)))
    write_csv(out / 'comparacion_modelos.csv', rows)
    write_csv(out / 'diferencias_emparejadas.csv', differences)
    return {'n_model_comparisons': len(rows), 'max_metric_error': max(errors),
            'legacy_comparators_from_frozen_predictions': True}


def map_scores(out):
    meta = json.loads((ROOT / 'GRILLA.json').read_text(encoding='utf-8'))
    selection = json.loads((ROOT / 'SELECCION.json').read_text(encoding='utf-8'))
    key = meta['key']
    bound = selection[key]['bound_selected_by_calibration']
    label = str(bound).replace('.', 'p')
    n = meta['n_generated']
    raw = np.lib.format.open_memmap(out / 'scores_crudos.npy', mode='w+', dtype=np.float32, shape=(n, 4))
    offset = 0
    parts = sorted(ROOT.glob('PIXELES_*.npz'))
    if not parts:
        raise FileNotFoundError('Faltan bloques PIXELES_*.npz')
    with np.load(ROOT / 'PESOS.npz', allow_pickle=False) as weights:
        for path in parts:
            with np.load(path, allow_pickle=False) as z:
                X = z['X']
                for j, seed in enumerate(SEEDS):
                    prefix = key + '__B' + label + '__s' + str(seed)
                    fe, anchor = inferir(X, weights, prefix, bound)
                    raw[offset:offset + len(X), j] = fe
                    if j == 0:
                        raw[offset:offset + len(X), 3] = anchor
                offset += len(X)
            print('Inferencia:', offset, '/', n, flush=True)
    if offset != n:
        raise ValueError('Denominador de píxeles incompleto')
    raw.flush()
    norms = [float(logsumexp(raw[:, j].astype(float)) - np.log(n)) for j in range(4)]
    scores = np.lib.format.open_memmap(out / 'scores.npy', mode='w+', dtype=np.float32, shape=(n, 2))
    for start in range(0, n, 250000):
        block = raw[start:start + 250000]
        scores[start:start + len(block), 0] = logsumexp(block[:, :3].astype(float) - np.array(norms[:3]), axis=1) - np.log(3)
        scores[start:start + len(block), 1] = block[:, 3] - norms[3]
    scores.flush()
    maxerror, offset = 0.0, 0
    for path in parts:
        with np.load(path, allow_pickle=False) as z:
            old = z['referencia_score']
            maxerror = max(maxerror, float(np.abs(scores[offset:offset + len(old)] - old).max()))
            offset += len(old)
    if maxerror > 2e-5:
        raise AssertionError('Mapa no replica el cálculo original: ' + str(maxerror))
    return scores, {'n_pixels': n, 'normalizers': norms, 'max_pixel_error': maxerror,
                    'map_interpretation': 'densidad relativa sobre construido, no P(inundación)'}


def priorities(out, scores):
    meta = json.loads((ROOT / 'GRILLA.json').read_text(encoding='utf-8'))
    units = meta['weather_units']
    nc = len(units)
    counts = {'construido': np.zeros((66, nc), dtype=np.int64)}
    for model in MODELS:
        for q in (80, 90, 95):
            counts[f'{model}_q{q}'] = np.zeros((66, nc), dtype=np.int64)
    thresholds = {(model, q): float(np.quantile(scores[:, j].astype(np.float64), q / 100))
                  for j, model in enumerate(MODELS) for q in (80, 90, 95)}
    reference_scores = np.concatenate([np.load(path, allow_pickle=False)['referencia_score']
                                      for path in sorted(ROOT.glob('PIXELES_*.npz'))])
    ref_thresholds = {(model, q): float(np.quantile(reference_scores[:, j].astype(np.float64), q / 100))
                      for j, model in enumerate(MODELS) for q in (80, 90, 95)}
    boundary_changes = {f'{model}_q{q}': 0 for model in MODELS for q in (80, 90, 95)}
    offset = 0
    for path in sorted(ROOT.glob('PIXELES_*.npz')):
        with np.load(path, allow_pickle=False) as z:
            pid, wid = z['pid'].astype(int), z['wid'].astype(int)
            size = len(pid)
            assert ((pid >= 0) & (pid <= 65) & (wid >= 0) & (wid < nc)).all()
            counts['construido'] += np.bincount(pid * nc + wid, minlength=66 * nc).reshape(66, nc)
            for j, model in enumerate(MODELS):
                for q in (80, 90, 95):
                    use = scores[offset:offset + size, j] >= thresholds[(model, q)]
                    old_use = reference_scores[offset:offset + size, j] >= ref_thresholds[(model, q)]
                    changed = use != old_use
                    # Sólo admitir discrepancias explicadas por redondeo en el umbral.
                    if changed.any():
                        distance = np.abs(scores[offset:offset + size, j][changed] - thresholds[(model, q)])
                        old_distance = np.abs(reference_scores[offset:offset + size, j][changed] - ref_thresholds[(model, q)])
                        if max(float(distance.max()), float(old_distance.max())) > 2e-5:
                            raise AssertionError('Cambió una clasificación fuera de la tolerancia numérica')
                        boundary_changes[f'{model}_q{q}'] += int(changed.sum())
                    counts[f'{model}_q{q}'] += np.bincount(pid[use] * nc + wid[use], minlength=66 * nc).reshape(66, nc)
            offset += size
    with np.load(ROOT / 'REFERENCIA_intersecciones.npz', allow_pickle=False) as old:
        for name, values in counts.items():
            delta = int(np.abs(values - old[name]).sum())
            if delta > boundary_changes.get(name, 0):
                raise AssertionError('Intersecciones de prioridad no coinciden: ' + name)
    if boundary_changes['red_residual_q90'] or boundary_changes['ancla_acotada_q90']:
        raise AssertionError('Cambió el decil primario: revisar precisión antes de aceptar esta reproducción')
    social = read_csv(ROOT / 'DATOS_PARROQUIAS.csv')
    weather = read_csv(ROOT / 'DATOS_LLUVIA_ESCENARIOS.csv')
    weather_models = list(dict.fromkeys(r['modelo'] for r in weather))
    rows = []
    for wmodel in weather_models:
        index = {r['unit']: float(r['p_humedo']) for r in weather if r['modelo'] == wmodel}
        prob = np.array([index[u] for u in units])
        assert np.isfinite(prob).all() and ((prob >= 0) & (prob <= 1)).all()
        for model in MODELS:
            areas = counts[model + '_q90'][1:] @ prob * 0.01
            objective = areas * np.array([float(r['pc_pnbi']) for r in social]) / 100
            for i, original in enumerate(social):
                row = dict(original)
                row.update(modelo_territorial=model, modelo_lluvia=wmodel,
                    construido_ha=float(counts['construido'][i + 1].sum() * 0.01),
                    area_prioritaria_ha=float(counts[model + '_q90'][i + 1].sum() * 0.01),
                    area_prioritaria_ponderada_humedad_ha=float(areas[i]), indice_NBI_ha_ponderadas=float(objective[i]),
                    ranking_area=int((areas > areas[i]).sum() + 1) if areas[i] > 0 else '',
                    ranking_NBI=int((objective > objective[i]).sum() + 1) if objective[i] > 0 else '')
                for label, field in [('saneamiento', 'pc_SH'), ('agua', 'pc_FSA'), ('hacinamiento', 'pc_HAC')]:
                    row['indice_' + label + '_ha_ponderadas'] = float(areas[i] * float(original[field]) / 100)
                rows.append(row)
    reference = read_csv(ROOT / 'REFERENCIA_prioridad_integrada.csv')
    ref = {(r['parroquia'], r['modelo_territorial'], r['modelo_lluvia']): r for r in reference}
    errors = []
    for row in rows:
        old = ref[(row['parroquia'], row['modelo_territorial'], row['modelo_lluvia'])]
        for field in ['construido_ha', 'area_prioritaria_ha', 'area_prioritaria_ponderada_humedad_ha', 'indice_NBI_ha_ponderadas']:
            errors.append(abs(row[field] - float(old[field])))
    if max(errors) > 1e-6:
        raise AssertionError('Prioridad social no coincide: ' + str(max(errors)))
    write_csv(out / 'prioridad_integrada.csv', rows)
    primary = [r for r in rows if r['modelo_territorial'] == 'red_residual' and r['modelo_lluvia'] == 'red_ENSO__beta_PIT']
    summaries = []
    for field in ['construido_ha', 'area_prioritaria_ha', 'pc_pnbi', 'pc_SH', 'pc_FSA', 'pc_HAC',
                  'area_prioritaria_ponderada_humedad_ha', 'indice_NBI_ha_ponderadas']:
        x = np.array([float(r[field]) for r in primary])
        summaries.append(dict(variable=field, N=len(x), media=float(x.mean()), desv_estandar=float(x.std(ddof=1)),
                              minimo=float(x.min()), maximo=float(x.max())))
    write_csv(out / 'summarize_parroquias.csv', summaries)
    # Publica sólo geometría censal agregada, nunca viviendas o personas de encuestas.
    geo = json.loads((ROOT / 'DATOS_GEOMETRIA_PARROQUIAL.geojson').read_text(encoding='utf-8'))
    current = {r['parroquia']: r for r in primary}
    for feature in geo['features']:
        code = str(feature['properties']['parroquia']).zfill(6)
        feature['properties'] = {**current[code], 'interpretacion': 'Prioridad parroquial; NBI no localizado por píxel'}
    (out / 'prioridad_quito.geojson').write_text(json.dumps(geo, ensure_ascii=False), encoding='utf-8')
    return {'n_parishes': len(primary), 'n_scenarios': len(weather_models) * 2,
            'max_priority_error': max(errors), 'numerical_boundary_pixels': boundary_changes,
            'top13': [r['nombre'] for r in sorted(primary, key=lambda r: float(r['ranking_NBI'] or 999))[:13]]}


def geotiff(out, scores):
    try:
        import rasterio
        from rasterio.transform import Affine
        from rasterio.windows import Window
    except ImportError as error:
        raise SystemExit('Para GeoTIFF instale: python -m pip install rasterio') from error
    meta = json.loads((ROOT / 'GRILLA.json').read_text(encoding='utf-8'))
    flat = np.concatenate([np.load(p, allow_pickle=False)['flat'] for p in sorted(ROOT.glob('PIXELES_*.npz'))])
    profile = dict(driver='GTiff', width=meta['width'], height=meta['height'], count=1, dtype='float32',
                   crs=meta['crs'], transform=Affine(*meta['transform']), nodata=-9999,
                   compress='deflate', predictor=3, tiled=True, blockxsize=256, blockysize=256)
    for j, model in enumerate(MODELS):
        with rasterio.open(out / (model + '_10m.tif'), 'w', **profile) as target:
            target.update_tags(interpretation='Log densidad relativa; no P(inundación)', terrain_native_m=30,
                               built_source='ESA WorldCover 2021', data_snapshot='2026-10-09')
            for row in range(0, meta['height'], 64):
                count = min(64, meta['height'] - row)
                start, end = np.searchsorted(flat, [row * meta['width'], (row + count) * meta['width']])
                a = np.full(count * meta['width'], -9999, np.float32)
                a[flat[start:end] - row * meta['width']] = scores[start:end, j]
                target.write(a.reshape(count, meta['width']), 1, window=Window(0, row, meta['width'], count))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--solo-benchmark', action='store_true')
    parser.add_argument('--geotiff', action='store_true')
    parser.add_argument('--reentrenar', action='store_true')
    parser.add_argument('--key', default='temporal__vias_fabdem')
    parser.add_argument('--device', choices=['cpu', 'cuda', 'auto'], default='cpu')
    parser.add_argument('--salida', type=Path, default=ROOT / 'resultados')
    args = parser.parse_args()
    started = time.perf_counter()
    args.salida.mkdir(parents=True, exist_ok=True)
    verify_hashes()
    import pruebas
    pruebas.run()
    audit = {'benchmark': benchmark(args.salida)}
    if not args.solo_benchmark:
        scores, audit['mapa'] = map_scores(args.salida)
        audit['prioridad'] = priorities(args.salida, scores)
        if args.geotiff:
            geotiff(args.salida, scores)
    if args.reentrenar:
        from entrenar import train
        audit['reentrenamiento'] = train(args.key, args.device, args.salida / 'reentrenamiento')
    audit['elapsed_seconds'] = time.perf_counter() - started
    audit['credentials_used'] = False
    (args.salida / 'VERIFICACION.json').write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(audit, ensure_ascii=False, indent=2), flush=True)


if __name__ == '__main__':
    main()
