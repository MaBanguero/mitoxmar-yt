#!/usr/bin/env python3
"""Test unitario de funciones puras del automator (sin dispositivo)."""
import sys, os
sys.path.insert(0, '/home/marvin/Downloads/yt-mitoxmar')

# No conectar dispositivo: solo probar metodos puros via una instancia sin init
from api.utils.youtube_automator import YouTubeAutomator

# Crear instancia sin ejecutar __init__ (object.__new__)
a = object.__new__(YouTubeAutomator)

print("=== _extraer_termino_busqueda ===")
tests = [
    ("https://www.youtube.com/watch?v=dQw4w9WgXcQ", "dQw4w9WgXcQ"),
    ("https://youtu.be/dQw4w9WgXcQ", "dQw4w9WgXcQ"),
    ("https://www.youtube.com/shorts/abc123XYZ_-", "abc123XYZ_-"),
    ("https://www.youtube.com/live/xyz789abc", "xyz789abc"),
    ("https://www.youtube.com/playlist?list=PL1234567890abcdefghij", "PL1234567890abcdefghij"),
    ("https://www.youtube.com/@RickAstleyYT", "@RickAstleyYT"),
    ("https://www.youtube.com/channel/UCuAXFkgsw1L7xaCfnd5JJOw", "UCuAXFkgsw1L7xaCfnd5JJOw"),
    ("https://www.youtube.com/watch?v=abc&list=PLxyz", "abc"),  # watch?v= tiene prioridad
]
ok = True
for url, expected in tests:
    got = a._extraer_termino_busqueda(url)
    status = "OK" if got == expected else "FAIL"
    if got != expected:
        ok = False
    print(f"  {status}: {url} -> {got!r} (esperado {expected!r})")

print("\n=== calcular_tiempo_retencion ===")
import random
random.seed(42)
# duracion 200s, rango fijo 30-100 -> resultado entre 60 y 200
for _ in range(5):
    r = a.calcular_tiempo_retencion(200, 30, 100)
    assert 60 <= r <= 200, f"fuera de rango: {r}"
print("  200s @ 30-100% -> muestras:", [a.calcular_tiempo_retencion(200, 30, 100) for _ in range(5)])
# 5-100 en 100s
print("  100s @ 5-100% -> muestras:", [a.calcular_tiempo_retencion(100, 5, 100) for _ in range(5)])
# clamp
print("  clamp min: 100s @ 0% ->", a.calcular_tiempo_retencion(100, 0, 0))
print("  duracion 0 ->", a.calcular_tiempo_retencion(0, 30, 100))

print("\n" + ("TODOS OK" if ok else "HUBO FALLOS"))
