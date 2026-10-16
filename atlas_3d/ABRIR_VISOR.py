"""Abre el atlas 3D local. Sólo necesita Python 3 (biblioteca estándar).

El servidor expone únicamente 4_VISOR en 127.0.0.1, no la investigación
completa ni archivos personales. No usa credenciales ni Internet.
Cerrar esta consola o pulsar Ctrl+C detiene el servidor.
"""
from pathlib import Path
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import argparse
import functools
import threading
import webbrowser

ROOT=Path(__file__).resolve().parent


class Handler(SimpleHTTPRequestHandler):
    extensions_map={**SimpleHTTPRequestHandler.extensions_map,'.js':'text/javascript; charset=utf-8','.css':'text/css; charset=utf-8','.json':'application/json'}

    def end_headers(self):
        self.send_header('Cache-Control','no-cache')
        self.send_header('X-Content-Type-Options','nosniff')
        super().end_headers()

    def list_directory(self,path):
        self.send_error(403,'Listado de directorios deshabilitado')
        return None


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sin-abrir',action='store_true',help='No abrir el navegador automáticamente')
    parser.add_argument('--puerto',type=int,default=8767)
    args=parser.parse_args()
    if not (ROOT/'4_VISOR/datos.js').is_file():
        raise SystemExit('Faltan los datos del visor. Ejecute EJECUTAR_TODO.py --reconstruir.')
    handler=functools.partial(Handler,directory=str(ROOT/'4_VISOR'))
    try:server=ThreadingHTTPServer(('127.0.0.1',args.puerto),handler)
    except OSError:server=ThreadingHTTPServer(('127.0.0.1',0),handler)
    url=f'http://127.0.0.1:{server.server_port}/'
    print('Visor Quito 3D: '+url,flush=True)
    print('Servidor local: no comparte archivos por la red. Ctrl+C para cerrar.',flush=True)
    if not args.sin_abrir:threading.Timer(.7,lambda:webbrowser.open(url)).start()
    try:server.serve_forever()
    except KeyboardInterrupt:pass
    finally:server.server_close()


if __name__=='__main__':main()
