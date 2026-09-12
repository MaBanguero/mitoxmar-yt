#!/usr/bin/env python3
"""Test del automator real: open_youtube_link via puente Chrome."""
import os, sys, time
os.environ['ANDROID_ADB_SERVER_PORT'] = os.getenv('CUSTOM_ADB_PORT', '5037')
# el automator lee CUSTOM_ADB_PORT del env
sys.path.insert(0, '/home/marvin/Downloads/yt-mitoxmar')
from api.utils.youtube_automator import YouTubeAutomator

SERIAL = sys.argv[1] if len(sys.argv) > 1 else 'R5CX31SBCAE'
URL = sys.argv[2] if len(sys.argv) > 2 else 'https://www.youtube.com/watch?v=dQw4w9WgXcQ'

a = YouTubeAutomator(SERIAL)
print("=== abriendo via puente Chrome ===")
a.open_youtube_link(URL)
print("=== foreground tras abrir ===")
print(a.device.app_current())
print("=== duracion total (time_bar_total_time) ===")
tot = a.device(resourceId='com.google.android.youtube:id/time_bar_total_time')
print("exists:", tot.exists, "| texto:", repr(tot.get_text() if tot.exists else None))
