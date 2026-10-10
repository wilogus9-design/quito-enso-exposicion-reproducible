"""Controles técnicos públicos. No sustituyen validación científica externa."""
from pathlib import Path
import json
import unittest
import numpy as np
from modelo import logsumexp, miembros_decil, evaluar, inferir

ROOT = Path(__file__).resolve().parent


class Tests(unittest.TestCase):
    def test_logsumexp(self):
        self.assertAlmostEqual(float(logsumexp(np.array([1000., 1000.]))), 1000 + np.log(2))

    def test_ties(self):
        self.assertAlmostEqual(float(miembros_decil(np.zeros(100), np.zeros(100)).mean()), 0.1)

    def test_uniform_density(self):
        ev, cap = evaluar(np.zeros((2, 3)), np.zeros(10), np.ones((2, 3), bool))
        np.testing.assert_allclose(ev, 0)
        np.testing.assert_allclose(cap, 0.1)

    def test_no_household_identifiers(self):
        allowed = {'Xe', 'Xb', 'valid_e', 'etrain', 'ecal', 'etest', 'btrain', 'bcal', 'btest',
                   'anchor', 'lo', 'hi', 'clipped_e', 'clipped_b', 'block'}
        for path in ROOT.glob('DATOS_*.npz'):
            with np.load(path, allow_pickle=False) as z:
                self.assertEqual(set(z.files), allowed)
                self.assertFalse(z['Xb'].dtype.hasobject)

    def test_splits_disjoint(self):
        for path in ROOT.glob('DATOS_*.npz'):
            with np.load(path, allow_pickle=False) as z:
                for a, b in [('etrain', 'ecal'), ('etrain', 'etest'), ('ecal', 'etest')]:
                    self.assertFalse(np.any(z[a] & z[b]))
                self.assertTrue(np.all(z['valid_e'].sum(1) >= 5))

    def test_calibration_selection(self):
        selection = json.loads((ROOT / 'SELECCION.json').read_text(encoding='utf-8'))
        for st in selection.values():
            self.assertTrue(st['test_not_used_for_selection'])
            self.assertEqual(max(st['mean_calibration_scores'])[1], st['bound_selected_by_calibration'])

    def test_residual_bound(self):
        key = 'temporal__vias_fabdem'
        with np.load(ROOT / f'DATOS_{key}.npz', allow_pickle=False) as data:
            X = data['Xb'][:2000]
        with np.load(ROOT / 'PESOS.npz', allow_pickle=False) as weights:
            for seed in (5101, 5102, 5103):
                s, a = inferir(X, weights, key + '__B0p25__s' + str(seed), 0.25)
                self.assertLessEqual(float(np.abs(s - a).max()), 0.2501)


def run():
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Tests))
    if not result.wasSuccessful():
        raise AssertionError('Falló una prueba del paquete')


if __name__ == '__main__':
    run()
