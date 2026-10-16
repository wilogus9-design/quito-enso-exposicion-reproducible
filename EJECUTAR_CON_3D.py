"""Reproduce resultados y restaura/verifica el atlas con una sola ejecución.

Instalar primero requirements.txt. --abrir abre el visor local al terminar.
"""
from pathlib import Path
import argparse
import subprocess
import sys

ROOT = Path(__file__).resolve().parent

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--abrir', action='store_true')
    args = parser.parse_args()
    subprocess.run([sys.executable, str(ROOT / 'reproducir.py')], check=True, cwd=ROOT)
    subprocess.run([sys.executable, str(ROOT / 'atlas_3d/preparar_3d.py'), '--abrir' if args.abrir else '--verificar'], check=True, cwd=ROOT)
