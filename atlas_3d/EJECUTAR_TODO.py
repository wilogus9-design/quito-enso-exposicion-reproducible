"""Entrada única del atlas público. python EJECUTAR_TODO.py --verificar."""
from pathlib import Path
import subprocess
import sys

if __name__ == '__main__':
    raise SystemExit(subprocess.call([sys.executable, str(Path(__file__).resolve().with_name('preparar_3d.py')), *sys.argv[1:]]))
