"""Test de deteccion/omision rapida de anuncios + lectura de duracion.

Uso:
    .venv/bin/python -u test_ads.py <video_id_or_url>

Abre un video via el puente Chrome, monitorea los anuncios y los omite en
cuanto aparece el boton, luego reporta la duracion detectada y los tiempos.
"""
import sys
import time
import uiautomator2 as u2

from api.utils.youtube_automator import YouTubeAutomator

DEVICE_ID = "R5CX31SBCAE"
MONITOR_SECONDS = 90


def main():
    url = sys.argv[1] if len(sys.argv) > 1 else "https://www.youtube.com/watch?v=9bZkp7q19f0"
    a = YouTubeAutomator.__new__(YouTubeAutomator)
    a.device_id = DEVICE_ID
    a.device = u2.connect(DEVICE_ID)

    print(f"=== Abriendo {url} via puente Chrome ===", flush=True)
    a.open_youtube_link(url)
    print("=== Video abierto. Monitoreando anuncios ===", flush=True)

    start = time.time()
    anuncios = 0
    while time.time() - start < MONITOR_SECONDS:
        est = a._estado_reproduccion()
        if est["hay_anuncio"]:
            anuncios += 1
            print(f"[{time.time() - start:.1f}s] ANUNCIO detectado "
                  f"(seekbar_total={est['total']}s skip={est['skip']})", flush=True)
            t0 = time.time()
            a.saltar_anuncio()
            print(f"    saltar_anuncio en {time.time() - t0:.1f}s", flush=True)
        else:
            time.sleep(1)

    print(f"=== Fin: anuncios detectados={anuncios} ===", flush=True)
    est = a._estado_reproduccion()
    print(f"estado final: hay_anuncio={est['hay_anuncio']} total={est['total']}s", flush=True)
    d = a._obtener_duracion_video()
    print(f"duracion video detectada: {d}s", flush=True)


if __name__ == "__main__":
    main()
