#!/usr/bin/env python3
"""Verifica lectura de duracion tras el puente (ad handling + time_bar_total_time)."""
import os, sys, time
os.environ['ANDROID_ADB_SERVER_PORT'] = os.getenv('CUSTOM_ADB_PORT', '5037')
sys.path.insert(0, '/home/marvin/Downloads/yt-mitoxmar')
from api.utils.youtube_automator import YouTubeAutomator

SERIAL = sys.argv[1] if len(sys.argv) > 1 else 'R5CX31SBCAE'
URL = sys.argv[2] if len(sys.argv) > 2 else 'https://www.youtube.com/watch?v=dQw4w9WgXcQ'

a = YouTubeAutomator(SERIAL)
a.open_youtube_link(URL)
a.random_sleep(5, 8)

print("=== estado tras puente ===")
print("foreground:", a.device.app_current())
xml = a.device.dump_hierarchy()
if 'ad_progress_text' in xml or 'Patrocinado' in xml or 'ME GUSTA EL ANUNCIO' in xml:
    print(">>> HAY ANUNCIO. Llamando saltar_anuncio()...")
    a.saltar_anuncio()
    a.random_sleep(3, 5)

print("=== leyendo duracion (tocar player) ===")
vp = '//*[@content-desc="Reproductor de video"]'
if a.element_exists(vp):
    a.click_element(vp)
    a.short_sleep(1)
dur = a.get_element_text(resource_id="com.google.android.youtube:id/time_bar_total_time")
print("time_bar_total_time:", repr(dur))
if dur:
    secs = a.parse_duration_to_seconds(dur)
    ret = a.calcular_tiempo_retencion(secs, 30, 100)
    print(f"duracion={secs}s -> retencion 30-100% = {ret}s")
else:
    print("(duracion no leida; puede seguir el anuncio o el control oculto)")
