import os
import time
import random
import subprocess
import threading
from collections import deque
from typing import Optional, List
from dotenv import load_dotenv
import asyncio

# Cargar variables de entorno
load_dotenv()

# Configurar el puerto ADB desde .env (por defecto 5037)
CUSTOM_ADB_PORT = int(os.getenv('CUSTOM_ADB_PORT', '5037'))
os.environ['ANDROID_ADB_SERVER_PORT'] = str(CUSTOM_ADB_PORT)

# Ahora importar uiautomator2
import uiautomator2 as u2

# Tracking de acciones por cuenta/video
from api.utils import tracking_db


class YouTubeAutomator:
    """Clase para automatización de YouTube con uiautomator2"""

    def __init__(self, device_id: str, cambiar_cuentas: bool = True):
        """
        Inicializa la conexión con el dispositivo

        Args:
            device_id: ID del dispositivo ADB
            cambiar_cuentas: si es False, no se rota entre cuentas (usa solo la cuenta actual)
        """
        self.device_id = device_id
        self.device: Optional[u2.Device] = None
        self.cuentas_usadas: List[str] = []  # Tracking de cuentas usadas en esta sesión
        self.sin_cuentas_disponibles = False
        self.cambiar_cuentas = cambiar_cuentas

        # Tracking de acciones por cuenta/video
        self.cuenta_actual: Optional[str] = None
        self.video_id_actual: Optional[str] = None
        self.comentarios_asignar: List[str] = []
        self.comentario_idx = 0

        # Leer número de cuentas desde variable de entorno (default: 5)
        self.cuentas_por_dispositivo = int(os.getenv('CUENTAS_POR_DISPOSITIVO', '5'))
        print(f"⚙️ [{self.device_id}] Configuración: {self.cuentas_por_dispositivo} cuentas por dispositivo | cambiar_cuentas={self.cambiar_cuentas}")

        # PASO 1: Verificar que el dispositivo esté online
        if not self.verificar_y_reconectar():
            raise Exception(f"Dispositivo {self.device_id} no disponible")

        # PASO 2: Resetear dispositivo ANTES de conectar
        self._reset_device_services()

        # PASO 3: Conectar con uiautomator2
        self.connect()

    def _reset_device_services(self):
        """Resetea los servicios UIAutomator2 antes de conectar"""
        try:
            import subprocess
            ADB_PATH = 'adb'

            # Force-stop apps
            subprocess.run(
                [ADB_PATH, '-P', str(CUSTOM_ADB_PORT), '-s', self.device_id, 'shell', 'am', 'force-stop',
                 'com.github.uiautomator'],
                capture_output=True, timeout=5
            )

            # Matar procesos
            subprocess.run(
                [ADB_PATH, '-P', str(CUSTOM_ADB_PORT), '-s', self.device_id, 'shell', 'pkill', '-9', 'uiautomator'],
                capture_output=True, timeout=5
            )
            subprocess.run(
                [ADB_PATH, '-P', str(CUSTOM_ADB_PORT), '-s', self.device_id, 'shell', 'pkill', '-9', 'atd'],
                capture_output=True, timeout=5
            )

            # Limpiar accessibility services (KEY para "already registered")
            subprocess.run(
                [ADB_PATH, '-P', str(CUSTOM_ADB_PORT), '-s', self.device_id, 'shell', 'settings', 'put', 'secure',
                 'enabled_accessibility_services', 'null'],
                capture_output=True, timeout=5
            )

            # Pequeña pausa para que los cambios tomen efecto
            time.sleep(0.5)

        except Exception as e:
            # No fallar si el reset falla, solo advertir
            print(f"⚠️ [{self.device_id}] Advertencia al resetear servicios: {e}")

    def connect(self):
        """Conecta con el dispositivo via uiautomator2"""
        try:
            self.device = u2.connect(self.device_id)
            print(f"✅ [{self.device_id}] Conectado via uiautomator2")
        except Exception as e:
            print(f"❌ [{self.device_id}] Error conectando: {e}")
            raise

    def verificar_y_reconectar(self) -> bool:
        """
        Verifica si el dispositivo está online y reconecta si es necesario

        Returns:
            True si el dispositivo está online, False si no se pudo reconectar
        """
        try:
            import subprocess
            ADB_PATH = 'adb'

            # Verificar si el dispositivo está online
            result = subprocess.run(
                [ADB_PATH, '-P', str(CUSTOM_ADB_PORT), 'devices'],
                capture_output=True,
                text=True,
                timeout=10
            )

            devices_output = result.stdout

            # Verificar si nuestro dispositivo aparece como "device" (online)
            if f"{self.device_id}\tdevice" in devices_output:
                print(f"✅ [{self.device_id}] Dispositivo online")
                return True

            # Si no está online, intentar reconectar
            print(f"⚠️ [{self.device_id}] Dispositivo no online, intentando reconectar...")

            # Si es USB, solo necesitamos esperar
            if ":" not in self.device_id:
                print(f"🔌 [{self.device_id}] Dispositivo USB, esperando reconexión...")
                time.sleep(3)

                # Verificar de nuevo
                result = subprocess.run(
                    [ADB_PATH, '-P', str(CUSTOM_ADB_PORT), 'devices'],
                    capture_output=True,
                    text=True,
                    timeout=10
                )

                if f"{self.device_id}\tdevice" in result.stdout:
                    print(f"✅ [{self.device_id}] Reconectado exitosamente")
                    # Reconectar uiautomator2
                    self.device = u2.connect(self.device_id)
                    return True
            else:
                # Si es WiFi, intentar reconectar
                print(f"📡 [{self.device_id}] Dispositivo WiFi, intentando reconectar...")
                subprocess.run(
                    [ADB_PATH, '-P', str(CUSTOM_ADB_PORT), 'connect', self.device_id],
                    capture_output=True,
                    timeout=10
                )
                time.sleep(2)

                # Verificar de nuevo
                result = subprocess.run(
                    [ADB_PATH, '-P', str(CUSTOM_ADB_PORT), 'devices'],
                    capture_output=True,
                    text=True,
                    timeout=10
                )

                if f"{self.device_id}\tdevice" in result.stdout:
                    print(f"✅ [{self.device_id}] Reconectado exitosamente")
                    # Reconectar uiautomator2
                    self.device = u2.connect(self.device_id)
                    return True

            print(f"❌ [{self.device_id}] No se pudo reconectar el dispositivo")
            return False

        except Exception as e:
            print(f"❌ [{self.device_id}] Error verificando conexión: {e}")
            return False

    ##############################################################
    # UTILERÍA COPY PASTE
    ##############################################################

    def random_sleep(self, min_seconds: int, max_seconds: int):
        """
        Sleep aleatorio para simular comportamiento humano

        Args:
            min_seconds: Mínimo de segundos
            max_seconds: Máximo de segundos
        """
        sleep_time = random.randint(min_seconds, max_seconds)
        print(f"💤 [{self.device_id}] Esperando {sleep_time} segundos...")
        time.sleep(sleep_time)

    def short_sleep(self, seconds: float = 2.0):
        """Sleep corto entre acciones"""
        time.sleep(seconds)

    def open_youtube_link(self, link_link: str):
        """
        Abre un video/playlist de YouTube usando el puente Chrome:
        abre Chrome -> busca 'youtube' -> click en https://www.youtube.com
        -> se abre la app nativa -> busca el ID del video -> click en el primer resultado.

        Args:
            link_link: URL del video/playlist/canal de YouTube
        """
        try:
            termino = self._extraer_termino_busqueda(link_link)
            self.video_id_actual = termino
            print(f"📱 [{self.device_id}] Abriendo via puente Chrome: {link_link} (termino: {termino})")

            # 1. Abrir Chrome
            self._abrir_chrome()

            # 2. Buscar 'youtube' y click en el resultado -> app nativa
            if not self._buscar_youtube_en_chrome():
                raise Exception("No se pudo abrir YouTube nativo via Chrome")

            # 3. Buscar el video por ID en la app nativa
            if not self._buscar_en_app_nativa(termino):
                raise Exception("No se pudo buscar el video en la app nativa")

            # 4. Click en el primer resultado
            if not self._click_primer_resultado():
                raise Exception("No se encontro un resultado para clickear")

            print(f"✅ [{self.device_id}] Video abierto via puente Chrome")
            self.random_sleep(3, 5)
            self.device.set_orientation("natural")
            self.random_sleep(2, 5)

        except Exception as e:
            print(f"❌ [{self.device_id}] Error abriendo link via Chrome: {e}")
            raise

    ##############################################################
    # PUENTE CHROME -> YOUTUBE NATIVO
    ##############################################################

    def _extraer_termino_busqueda(self, url: str) -> str:
        """Extrae el ID/termino de busqueda de una URL de YouTube."""
        import re
        url = (url or "").strip()
        if not url:
            return ""
        m = re.search(r"youtu\.be/([A-Za-z0-9_-]{6,})", url)
        if m:
            return m.group(1)
        m = re.search(r"youtube\.com/(shorts|live|embed)/([A-Za-z0-9_-]{6,})", url)
        if m:
            return m.group(2)
        m = re.search(r"[?&]v=([A-Za-z0-9_-]{6,})", url)
        if m:
            return m.group(1)
        m = re.search(r"[?&]list=([A-Za-z0-9_-]{6,})", url)
        if m:
            return m.group(1)
        m = re.search(r"youtube\.com/(@[A-Za-z0-9_.-]+)", url)
        if m:
            return m.group(1)
        m = re.search(r"youtube\.com/(channel|c|user)/([A-Za-z0-9_.-]+)", url)
        if m:
            return m.group(2)
        return url

    def _cuenta_tracking(self) -> str:
        """Clave de cuenta para el tracking. Usa el nombre si se conoce, si no device+posicion."""
        return self.cuenta_actual or f"{self.device_id}#{len(self.cuentas_usadas)}"

    def _deberia_ejecutar(self, video_id: str, accion: str) -> bool:
        """True si la accion no se ha ejecutado aun para esta cuenta y video."""
        return not tracking_db.accion_registrada(self._cuenta_tracking(), video_id, accion)

    def _registrar(self, accion: str, valor: str = None):
        """Registra una accion en la DB de tracking para la cuenta y video actuales."""
        if not self.video_id_actual:
            return
        tracking_db.registrar_accion(
            self._cuenta_tracking(), self.device_id, self.video_id_actual, accion, valor
        )

    def _abrir_chrome(self):
        """Cierra Chrome y YouTube (estado inicial) y abre Chrome desde el shell."""
        chrome_pkg = os.getenv("CHROME_PACKAGE", "com.android.chrome")
        # Cerrar ambas apps para asegurar estado inicial limpio
        self.device.app_stop(chrome_pkg)
        self.device.app_stop("com.google.android.youtube")
        self.random_sleep(1, 3)
        self.device.app_start(chrome_pkg)
        self.random_sleep(4, 7)

    def _buscar_youtube_en_chrome(self) -> bool:
        """Busca 'youtube' en la barra de Chrome y click en el resultado para abrir la app nativa."""
        import re
        bar = self.device(resourceId="com.android.chrome:id/url_bar")
        if not bar.exists:
            print(f"❌ [{self.device_id}] Barra de direcciones de Chrome no encontrada")
            return False
        bar.click()
        self.random_sleep(1, 3)
        try:
            # set_text evita el autocompletado de Chrome (send_keys lo dispara)
            bar.set_text("youtube")
        except Exception:
            self.device.send_keys("youtube")
        self.random_sleep(1, 2)
        self.device.press("enter")

        # Polling robusto hasta encontrar el resultado de youtube.com
        target = None
        for _ in range(6):
            self.random_sleep(4, 6)
            xml = self.device.dump_hierarchy()
            # 1) texto exacto de la URL
            for m in re.finditer(r"<node[^>]*>", xml):
                s = m.group(0)
                txt = re.search(r'text="([^"]*)"', s)
                b = re.search(r'bounds="([^"]*)"', s)
                tv = txt.group(1) if txt else ""
                if tv.strip() == "https://www.youtube.com" and b:
                    x1, y1, x2, y2 = [int(v) for v in re.findall(r"\d+", b.group(1))]
                    target = ((x1 + x2) // 2, (y1 + y2) // 2)
                    break
            if target:
                break
            # 2) fallback: content-desc que contenga youtube.com
            for m in re.finditer(r"<node[^>]*>", xml):
                s = m.group(0)
                cd = re.search(r'content-desc="([^"]*)"', s)
                b = re.search(r'bounds="([^"]*)"', s)
                cv = cd.group(1) if cd else ""
                if "youtube.com" in cv and b:
                    x1, y1, x2, y2 = [int(v) for v in re.findall(r"\d+", b.group(1))]
                    target = ((x1 + x2) // 2, (y1 + y2) // 2)
                    break
            if target:
                break

        if not target:
            print(f"❌ [{self.device_id}] No se encontró el resultado de youtube.com en Chrome")
            return False

        self.device.click(target[0], target[1])
        self.random_sleep(5, 8)
        return self._esta_en_youtube_nativo()

    def _esta_en_youtube_nativo(self) -> bool:
        """Verifica si la app nativa de YouTube esta en foreground."""
        try:
            cur = self.device.app_current()
            return cur.get("package") == "com.google.android.youtube"
        except Exception:
            return False

    def _buscar_en_app_nativa(self, termino: str) -> bool:
        """Toca 'Buscar' en la app nativa y escribe el termino de busqueda."""
        btn = self.device(description="Buscar")
        if not btn.exists:
            btn = self.device(resourceId="com.google.android.youtube:id/menu_item_view")
        if not btn.exists:
            print(f"❌ [{self.device_id}] Boton 'Buscar' no encontrado en la app nativa")
            return False
        btn.click()
        self.random_sleep(2, 4)

        se = self.device(resourceId="com.google.android.youtube:id/search_edit_text")
        if not se.exists:
            print(f"❌ [{self.device_id}] Input de busqueda no encontrado")
            return False
        se.click()
        self.random_sleep(1, 2)
        try:
            se.set_text(termino)
        except Exception:
            self.device.send_keys(termino, clear=True)
        self.random_sleep(1, 2)
        self.device.press("enter")
        self.random_sleep(5, 8)
        return True

    def _click_primer_resultado(self) -> bool:
        """Click en el primer resultado (video 'ver vídeo', Short, o playlist)."""
        import re
        xml = self.device.dump_hierarchy()
        target = None

        for marker in ("ver vídeo", "reproducir Short", "reproducir playlist", "Playlist"):
            for m in re.finditer(r"<node[^>]*>", xml):
                s = m.group(0)
                cd = re.search(r'content-desc="([^"]*)"', s)
                b = re.search(r'bounds="([^"]*)"', s)
                cv = cd.group(1) if cd else ""
                if marker in cv and b:
                    x1, y1, x2, y2 = [int(v) for v in re.findall(r"\d+", b.group(1))]
                    target = ((x1 + x2) // 2, (y1 + y2) // 2)
                    break
            if target:
                break

        if not target:
            print(f"❌ [{self.device_id}] No se encontro resultado de video/playlist para clickear")
            return False

        self.device.click(target[0], target[1])
        self.random_sleep(3, 5)
        return True

    def scroll_until_find(self, xpath: str, max_scrolls: int = 10) -> bool:
        """
        Hace scroll hacia arriba hasta encontrar un elemento

        Args:
            xpath: XPath del elemento a buscar
            max_scrolls: Máximo número de scrolls

        Returns:
            True si encontró el elemento, False si no
        """
        print(f"🔍 [{self.device_id}] Buscando elemento: {xpath}")

        for i in range(max_scrolls):
            try:
                # Verificar si el elemento existe
                if self.device.xpath(xpath).exists:
                    print(f"✅ [{self.device_id}] Elemento encontrado")
                    return True

                # Hacer swipe up (scroll down en la pantalla)
                print(f"⬆️ [{self.device_id}] Scroll {i + 1}/{max_scrolls}")
                self.device.swipe_ext("up", scale=0.6)
                self.short_sleep(1.5)

            except Exception as e:
                print(f"⚠️ [{self.device_id}] Error en scroll: {e}")
                continue

        print(f"❌ [{self.device_id}] Elemento no encontrado después de {max_scrolls} scrolls")
        return False

    def long_click_element(self, xpath: str = None, duration: float = 3.0, x: int = None, y: int = None) -> bool:
        """
        Hace long click en un elemento por xpath o coordenadas

        Args:
            xpath: XPath del elemento (opcional si se proporcionan coordenadas)
            duration: Duración del click en segundos
            x: Coordenada X (opcional, requiere Y)
            y: Coordenada Y (opcional, requiere X)

        Returns:
            True si tuvo éxito, False si no
        """
        try:
            # Si se proporcionan coordenadas, usarlas
            if x is not None and y is not None:
                print(f"👆 [{self.device_id}] Long click en coordenadas ({x}, {y}) por {duration}s...")
                self.device.long_click(x, y, duration)
                return True

            # Si no hay coordenadas, usar xpath
            if xpath:
                element = self.device.xpath(xpath)
                if element.exists:
                    print(f"👆 [{self.device_id}] Long click ({duration}s)...")
                    # uiautomator2: usar long_click() sin parámetros
                    element.long_click()
                    self.short_sleep(duration)  # Esperar después del long click
                    return True
                else:
                    print(f"❌ [{self.device_id}] Elemento no existe para long click")
                    return False

            print(f"❌ [{self.device_id}] Debe proporcionar xpath o coordenadas (x, y)")
            return False

        except Exception as e:
            print(f"❌ [{self.device_id}] Error en long click: {e}")
            return False

    def double_tap(self):
        """
        Hace doble tap en el centro de la pantalla usando el método nativo de uiautomator2
        """
        try:
            width, height = self.device.window_size()
            x = width // 2
            y = height // 2
            print(f"👆👆 [{self.device_id}] Doble tap en ({x}, {y})...")
            self.device.double_click(x, y)
            return True
        except Exception as e:
            print(f"❌ [{self.device_id}] Error en doble tap: {e}")
            return False

    def click_element(self, xpath: str) -> bool:
        """
        Hace click en un elemento

        Args:
            xpath: XPath del elemento

        Returns:
            True si tuvo éxito, False si no
        """
        try:
            element = self.device.xpath(xpath)
            if element.exists:
                print(f"👆 [{self.device_id}] Click en elemento")
                element.click()
                return True
            else:
                print(f"❌ [{self.device_id}] Elemento no existe para click")
                return False
        except Exception as e:
            print(f"❌ [{self.device_id}] Error en click: {e}")
            return False

    def element_exists(self, xpath: str) -> bool:
        """
        Verifica si un elemento existe

        Args:
            xpath: XPath del elemento

        Returns:
            True si existe, False si no
        """
        try:
            return self.device.xpath(xpath).exists
        except:
            return False

    def resource_exists(self, resource_id: str) -> bool:
        """
        Verifica si un elemento existe por resource-id

        Args:
            resource_id: Resource ID del elemento

        Returns:
            True si existe, False si no
        """
        try:
            return self.device(resourceId=resource_id).exists
        except:
            return False

    def get_element_text(self, xpath: str = None, resource_id: str = None) -> Optional[str]:
        """
        Obtiene el texto de un elemento por xpath o resource-id

        Args:
            xpath: XPath del elemento (opcional)
            resource_id: Resource ID del elemento (opcional)

        Returns:
            Texto del elemento o None si no existe
        """
        try:
            if resource_id:
                element = self.device(resourceId=resource_id)
                if element.exists:
                    text = element.info.get('text', '')
                    print(f"📝 [{self.device_id}] Texto obtenido de resource-id: '{text}'")
                    return text
            elif xpath:
                element = self.device.xpath(xpath)
                if element.exists:
                    text = element.get_text()
                    print(f"📝 [{self.device_id}] Texto obtenido de xpath: '{text}'")
                    return text

            print(f"❌ [{self.device_id}] Elemento no existe para obtener texto")
            return None

        except Exception as e:
            print(f"❌ [{self.device_id}] Error obteniendo texto: {e}")
            return None

    def parse_duration_to_seconds(self, duration_str: str) -> int:
        """
        Convierte una duración en formato MM:SS o HH:MM:SS a segundos totales

        Args:
            duration_str: String de duración (ej: "12:10", "1:05:30", " / 12:10")

        Returns:
            Segundos totales
        """
        try:
            # Limpiar el string (quitar espacios, " / ", etc)
            duration_str = duration_str.strip().replace(" / ", "").replace("/", "").strip()

            # Separar por ":"
            parts = duration_str.split(":")

            if len(parts) == 2:
                # Formato MM:SS
                minutes = int(parts[0])
                seconds = int(parts[1])
                total_seconds = minutes * 60 + seconds
            elif len(parts) == 3:
                # Formato HH:MM:SS
                hours = int(parts[0])
                minutes = int(parts[1])
                seconds = int(parts[2])
                total_seconds = hours * 3600 + minutes * 60 + seconds
            else:
                print(f"⚠️ [{self.device_id}] Formato de duración no reconocido: {duration_str}")
                return 0

            print(f"⏱️ [{self.device_id}] Duración: {duration_str} = {total_seconds} segundos")
            return total_seconds

        except Exception as e:
            print(f"❌ [{self.device_id}] Error parseando duración: {e}")
            return 0

    def press_back(self):
        """Presiona el botón back"""
        try:
            print(f"◀️ [{self.device_id}] Presionando BACK")
            self.device.press("back")
            self.short_sleep(1)
        except Exception as e:
            print(f"❌ [{self.device_id}] Error presionando back: {e}")

    def swipe_down_until_find(self, xpath: str, max_swipes: int = 5) -> bool:
        """
        Hace swipe de ARRIBA hacia ABAJO hasta encontrar un elemento

        Args:
            xpath: XPath del elemento a buscar
            max_swipes: Máximo número de swipes

        Returns:
            True si encontró el elemento, False si no
        """
        print(f"🔍 [{self.device_id}] Buscando elemento con swipe down: {xpath}")

        for i in range(max_swipes):
            try:
                # Verificar si el elemento existe
                if self.device.xpath(xpath).exists:
                    print(f"✅ [{self.device_id}] Elemento encontrado")
                    return True

                # Hacer swipe down (de arriba hacia abajo)
                print(f"⬇️ [{self.device_id}] Swipe down {i + 1}/{max_swipes}")
                self.device.swipe_ext("down", scale=0.3)  # Swipe ligero
                self.short_sleep(1)

            except Exception as e:
                print(f"⚠️ [{self.device_id}] Error en swipe: {e}")
                continue

        print(f"❌ [{self.device_id}] Elemento no encontrado después de {max_swipes} swipes")
        return False

    def _hay_anuncio(self) -> bool:
        """Detecta si hay un anuncio en reproduccion."""
        return (
            self.resource_exists("com.google.android.youtube:id/ad_progress_text")
            or self.element_exists('//*[contains(@content-desc, "Anuncio")]')
            or self.element_exists('//*[contains(@text, "Patrocinado")]')
        )

    def saltar_anuncio(self):
        """
        Espera a que aparezca el boton de saltar anuncio y lo clickea.
        Maneja: 'Saltar anuncio' / 'Omitir anuncio' / 'Skip ad' (content-desc o text).
        """
        skip_xpaths = [
            '//*[contains(@content-desc, "Saltar")]',
            '//*[contains(@content-desc, "Omitir")]',
            '//*[contains(@content-desc, "Skip")]',
            '//*[contains(@text, "Saltar")]',
            '//*[contains(@text, "Omitir")]',
        ]
        for _ in range(6):  # hasta ~30s
            for xp in skip_xpaths:
                if self.element_exists(xp):
                    if self.click_element(xp):
                        print(f"✅ [{self.device_id}] Anuncio saltado")
                        self.random_sleep(2, 4)
                        return
            if not self._hay_anuncio():
                return  # no hay anuncio presente
            self.random_sleep(4, 6)

    def verificar_es_short(self) -> bool:
        header_text = self.get_element_text(xpath=None,
                                            resource_id='com.google.android.youtube:id/contextual_header_title')
        if header_text and "Shorts" in header_text:
            print(f"✅ [{self.device_id}] Detectado Short")
            return True
        else:
            return self.resource_exists(
                'com.google.android.youtube:id/reel_watch_fragment_root') or self.resource_exists(
                'com.google.android.youtube:id/reel_recycler')

    def cambiar_cuenta(self, segundos_min: int, segundos_max: int) -> bool:
        """
        Cambia a la siguiente cuenta disponible evitando repetir las ya usadas.
        """
        try:
            print(f"[YT][{self.device_id}] Rotando cuenta de YouTube...")
            self.device.app_stop("com.google.android.youtube")
            self.random_sleep(2, 6)

            # Espera adicional entre segundos_min y segundos_max para simular descanso humano
            #self.random_sleep(5, 15)  # TODO PENDIENTE DE USAR segundos_min, segundos_max

            self.device.app_start("com.google.android.youtube")
            self.random_sleep(2, 4)
            self.device.set_orientation("natural")

            # Reproducir video random
            video_random_xpath = '//*[contains(@content-desc, "reproducir video") and not(contains(@content-desc, "Patrocinado"))]'
            video_random_xpath_alt = '//*[contains(@content-desc, "ver video") and not(contains(@content-desc, "Patrocinado"))]'
            if self.scroll_until_find(video_random_xpath) or self.scroll_until_find(video_random_xpath_alt):
                # Intentar hacer click en cualquiera de los dos que exista
                if self.click_element(video_random_xpath) or self.click_element(video_random_xpath_alt):
                    print(f"✅ [{self.device_id}] Video random abierto")
                    self.random_sleep(5, 8)
                    self.saltar_anuncio()  # si aparece anuncio
                    self.random_sleep(30, 60)
                    self.device.press("back")
                else:
                    print(f"⚠️ [{self.device_id}] No se pudo hacer click en el video random")

            self._restart_youtube_app()

            perfil_xpath = '//*[@text="Tú"]'
            cambiar_cuenta_xpath = '//*[@content-desc="Cambiar de cuenta"]'

            if not self.click_element(perfil_xpath):
                print(f"[YT][{self.device_id}] No se encontró el botón 'Tú' para abrir el perfil")
                return False
            self.random_sleep(2, 4)

            if not self.click_element(cambiar_cuenta_xpath):
                print(f"[YT][{self.device_id}] No se encontró la opción 'Cambiar de cuenta'")
                return False
            self.random_sleep(2, 4)

            account_name_resource = "com.google.android.youtube:id/name"
            list_item_xpath = "//android.widget.ListView/android.widget.RelativeLayout"

            def obtener_cuentas_visibles():
                cuentas = []
                try:
                    elementos = self.device.xpath(list_item_xpath).all()
                except Exception as err:
                    print(f"[YT][{self.device_id}] No se pudo obtener la lista de cuentas: {err}")
                    return cuentas

                for idx, item in enumerate(elementos, start=1):
                    item_xpath = item.get_xpath()
                    name_xpath = (
                        f"{item_xpath}//android.widget.TextView[@resource-id='{account_name_resource}']"
                    )
                    name_selector = self.device.xpath(name_xpath)
                    if not name_selector.exists:
                        continue

                    nombre = (name_selector.get_text() or "").strip()
                    if not nombre:
                        continue

                    cuentas.append(
                        {
                            "nombre": nombre,
                            "item_xpath": item_xpath,
                            "es_actual": idx == 1,  # El RelativeLayout[1] corresponde a la cuenta activa
                        }
                    )
                return cuentas

            def registrar_cuenta_actual(cuentas):
                for cuenta in cuentas:
                    if cuenta["es_actual"]:
                        nombre = cuenta["nombre"]
                        if nombre and nombre not in self.cuentas_usadas:
                            self.cuentas_usadas.append(nombre)
                        break

            max_scrolls = 6
            scrolls_realizados = 0
            cuenta_seleccionada = False
            cuentas_vistas = set()
            actual_registrada = False

            while scrolls_realizados <= max_scrolls and not cuenta_seleccionada:
                cuentas_visibles = obtener_cuentas_visibles()

                if not cuentas_visibles:
                    print(f"[YT][{self.device_id}] No se detectaron cuentas en la vista actual.")
                    break

                if not actual_registrada:
                    registrar_cuenta_actual(cuentas_visibles)
                    actual_registrada = True

                for cuenta in cuentas_visibles:
                    nombre_cuenta = cuenta["nombre"]
                    if cuenta["es_actual"]:
                        continue
                    if not nombre_cuenta or nombre_cuenta in self.cuentas_usadas or nombre_cuenta in cuentas_vistas:
                        continue

                    cuentas_vistas.add(nombre_cuenta)
                    print(f"[YT][{self.device_id}] Cambiando a la cuenta: {nombre_cuenta}")
                    if self.device.xpath(cuenta["item_xpath"]).click_exists(timeout=5):
                        self.cuentas_usadas.append(nombre_cuenta)
                        self.cuenta_actual = nombre_cuenta
                        self.random_sleep(3, 5)
                        cuenta_seleccionada = True
                        break

                    print(f"[YT][{self.device_id}] No se pudo seleccionar la cuenta {nombre_cuenta}")

                if cuenta_seleccionada:
                    break

                try:
                    self.device.swipe_ext("up", scale=0.8)
                except Exception as swipe_err:
                    print(f"[YT][{self.device_id}] Error haciendo scroll en la lista de cuentas: {swipe_err}")
                    break

                self.random_sleep(1, 2)
                scrolls_realizados += 1

            if not cuenta_seleccionada:
                print(f"[YT][{self.device_id}] No se encontraron cuentas disponibles sin usar.")
                return False

            print(f"[YT][{self.device_id}] Cambio de cuenta completado.")
            return True

        except Exception as e:
            print(f"[YT][{self.device_id}] Error cambiando de cuenta: {e}")
            return False

    def _should_stop(self, detener_flag: Optional[threading.Event], contexto: str) -> bool:
        """
        Verifica si se solicitó detener el proceso actual.
        """
        if detener_flag and detener_flag.is_set():
            print(f"[YT][{self.device_id}] Detención solicitada durante {contexto}. Abortando proceso.")
            return True
        return False

    def _hay_cuentas_disponibles(self, proceso: str) -> bool:
        """
        Comprueba si aún hay cuentas disponibles para continuar el proceso.
        """
        if self.sin_cuentas_disponibles:
            print(f"[YT][{self.device_id}] Sin cuentas disponibles para continuar {proceso}.")
            return False
        return True

    def _post_proceso_rotacion(
            self,
            proceso: str,
            segundos_min: int,
            segundos_max: int,
            detener_flag: Optional[threading.Event],
            permitir_reuso: bool = False
    ) -> bool:
        """
        Maneja la rotación de cuentas después de finalizar un proceso.
        """
        if detener_flag and detener_flag.is_set():
            return False

        if not self.cambiar_cuentas:
            # Toggle desactivado: no rotar cuentas. Terminar el loop interno
            # (una accion por cuenta actual; el service controla la cantidad).
            return False

        if self.sin_cuentas_disponibles and not permitir_reuso:
            return False

        if len(self.cuentas_usadas) >= self.cuentas_por_dispositivo:
            if permitir_reuso:
                print(f"[YT][{self.device_id}] Todas las cuentas usadas en {proceso}, reiniciando rotación.")
                self.cuentas_usadas = []
                self.sin_cuentas_disponibles = False
            else:
                print(f"[YT][{self.device_id}] Límite de cuentas alcanzado tras {proceso}.")
                self.sin_cuentas_disponibles = True
                return False

        if not self.cambiar_cuenta(segundos_min, segundos_max):
            if permitir_reuso:
                print(f"[YT][{self.device_id}] No se pudo cambiar de cuenta, reiniciando ciclo de cuentas.")
                self.cuentas_usadas = []
                self.sin_cuentas_disponibles = False
                if not self.cambiar_cuenta(segundos_min, segundos_max):
                    print(f"[YT][{self.device_id}] No hay cuentas disponibles para continuar {proceso}.")
                    return False
            else:
                print(f"[YT][{self.device_id}] No se pudo cambiar de cuenta al finalizar {proceso}.")
                self.sin_cuentas_disponibles = True
                return False
        return True

    def _restart_youtube_app(self):
        """Reinicia la aplicación YouTube en el dispositivo."""
        try:
            print(f"[YT][{self.device_id}] Reiniciando YouTube...")
            self.device.app_stop("com.google.android.youtube")
            self.random_sleep(5, 10)
            self.device.app_start("com.google.android.youtube")
            self.random_sleep(5, 10)
            self.device.set_orientation("natural")
            print(f"[YT][{self.device_id}] YouTube reiniciado.")
        except Exception as e:
            print(f"[YT][{self.device_id}] Error reiniciando YouTube: {e}")

    ##############################################################
    # PROCESOS ESPECÍFICOS YOUTUBE
    ##############################################################

    def proceso_calentamiento(self, detener_flag: Optional[threading.Event] = None,
                              retention_min_pct: float = 5, retention_max_pct: float = 100):
        """
        Proceso de calentamiento en YouTube usando el BUSCADOR NATIVO de la app.
        Ve distintos videos con retencion entre retention_min_pct% y retention_max_pct%.
        """
        if not self._hay_cuentas_disponibles("calentamiento"):
            return

        terminos = [
            "música", "noticias", "deportes", "tecnología", "tutorial", "comedia",
            "viajes", "cocina", "documental", "vlog", "ejercicio", "videojuegos",
            "cine", "historia", "ciencia", "podcast", "recetas", "fútbol",
            "motivación", "music", "news", "sports", "technology", "comedy",
            "travel", "cooking", "documentary", "gaming", "movies", "science",
        ]

        try:
            self._restart_youtube_app()

            print(f"🚀 [{self.device_id}] Iniciando proceso de calentamiento...")
            if self._should_stop(detener_flag, "calentamiento"):
                return

            # Duracion de la sesion de calentamiento (3-6 min)
            minutos_calentamiento = random.randint(3, 6) * 60
            print(f"⏱️ [{self.device_id}] Duración de calentamiento: {minutos_calentamiento} segundos")

            while minutos_calentamiento > 0:
                if self._should_stop(detener_flag, "calentamiento"):
                    break

                # Buscar un termino generico en el buscador nativo de la app
                termino = random.choice(terminos)
                print(f"🔍 [{self.device_id}] Buscando: {termino}")
                if not self._buscar_en_app_nativa(termino):
                    print(f"⚠️ [{self.device_id}] No se pudo buscar '{termino}', reintentando")
                    self._volver_a_inicio_youtube()
                    continue

                # Click en el primer resultado
                if not self._click_primer_resultado():
                    print(f"⚠️ [{self.device_id}] No se encontró resultado, reintentando")
                    self._volver_a_inicio_youtube()
                    continue

                self.random_sleep(3, 6)
                self.saltar_anuncio()

                # Retencion porcentual de la duracion del video
                total_seconds = 0
                video_player_xpath = '//*[@content-desc="Reproductor de video"]'
                if self.element_exists(video_player_xpath):
                    self.click_element(video_player_xpath)
                    self.short_sleep(0.5)
                duration_text = self.get_element_text(resource_id="com.google.android.youtube:id/time_bar_total_time")
                if duration_text:
                    total_seconds = self.parse_duration_to_seconds(duration_text)

                if total_seconds > 0:
                    watch_seconds = self.calcular_tiempo_retencion(total_seconds, retention_min_pct, retention_max_pct)
                else:
                    watch_seconds = random.randint(20, 60)

                print(f"▶️ [{self.device_id}] Viendo '{termino}' por {watch_seconds}s "
                      f"(retención {retention_min_pct}-{retention_max_pct}%)")
                self.short_sleep(watch_seconds)
                minutos_calentamiento -= watch_seconds

                # Volver a inicio para el siguiente video
                self._volver_a_inicio_youtube()

            print(f"✅ [{self.device_id}] Proceso de calentamiento completado")

        except Exception as e:
            print(f"❌ [{self.device_id}] Error en proceso de calentamiento: {e}")
            raise
        finally:
            print(f"🏠 [{self.device_id}] Cerrando YouTube...")
            self.device.app_stop("com.google.android.youtube")
            self.short_sleep(2)

    def _volver_a_inicio_youtube(self, max_intentos: int = 3):
        """Presiona BACK hasta volver a la pantalla de inicio de YouTube (donde esta 'Buscar')."""
        for _ in range(max_intentos):
            try:
                btn = self.device(description="Buscar")
                if btn.exists:
                    return
                self.device.press("back")
                self.short_sleep(1)
            except Exception:
                self.short_sleep(1)

    def proceso_likes(self, link_post: str, detener_flag: Optional[threading.Event] = None):
        """
        Proceso de likes en un post de YouTube
        Args:
            link_post: URL de video de Youtube
        """
        if not self._hay_cuentas_disponibles("likes"):
            return
        while self._hay_cuentas_disponibles("likes"):
            try:
                self._restart_youtube_app()

                print(f"🚀 [{self.device_id}] Iniciando proceso de likes en post: {link_post}")
                if self._should_stop(detener_flag, "likes"):
                    break

                # Abrir el post
                self.open_youtube_link(link_post)
                self.random_sleep(5, 8)

                like_button_xpath = '//*[contains(@content-desc, "Me gusta") and not(contains(@content-desc, "No me gusta"))]'
                if self._deberia_ejecutar(self.video_id_actual or "", "like"):
                    if self.verificar_es_short():
                        # COMPORTAMIENTO PARA SHORTS
                        if self.element_exists(like_button_xpath):
                            self.click_element(like_button_xpath)
                            self._registrar("like")
                            print(f"✅ [{self.device_id}] Like realizado")
                        else:
                            print(f"❌ [{self.device_id}] Botón de like no disponible en Short")
                    else:
                        # COMPORTAMIENTO PARA VIDEOS NORMALES
                        self.saltar_anuncio()
                        self.random_sleep(2, 4)
                        if self.element_exists(like_button_xpath):
                            self.click_element(like_button_xpath)
                            self._registrar("like")
                            print(f"✅ [{self.device_id}] Like realizado")
                        else:
                            print(f"❌ [{self.device_id}] Botón de like no encontrado")
                else:
                    print(f"ℹ️ [{self.device_id}] Like ya registrado para esta cuenta/video, saltando")

                self.random_sleep(3, 6)
                print(f"✅ [{self.device_id}] Proceso de likes completado")

            except Exception as e:
                print(f"❌ [{self.device_id}] Error en proceso de likes: {e}")
                raise
            finally:
                # Al finalizar, regresar a pantalla principal
                self.device.press("home")
                self.short_sleep(2)

            if not self._post_proceso_rotacion("likes", 15, 60, detener_flag):
                break

    def proceso_suscripciones(self, link_post: str, detener_flag: Optional[threading.Event] = None) -> int:
        """
        Proceso de suscripciones en un canal de YouTube
        Args:
            link_post: URL de canal de Youtube
        Returns:
            int: cantidad de suscripciones realizadas
        """
        if not self._hay_cuentas_disponibles("suscripciones"):
            return 0

        suscripciones_realizadas = 0

        while self._hay_cuentas_disponibles("suscripciones"):
            if self._should_stop(detener_flag, "suscripciones"):
                break

            suscripcion_exitosa = False
            try:
                self._restart_youtube_app()

                print(f"🚀 [{self.device_id}] Iniciando proceso de suscripciones en canal: {link_post}")

                # Abrir el canal
                self.open_youtube_link(link_post)
                self.random_sleep(5, 8)

                subscribe_button_xpath = '//*[contains(@content-desc, "Suscribirse")]'
                subscribe_button_xpath_alt = '//*[contains(@content-desc, "Suscribirme")]'
                subscribed_xpath = '//*[contains(@content-desc, "Suscrito")]'

                if not self._deberia_ejecutar(self.video_id_actual or "", "suscripcion"):
                    print(f"ℹ️ [{self.device_id}] Suscripción ya registrada para esta cuenta, saltando")
                    suscripcion_exitosa = True
                elif self.element_exists(subscribed_xpath):
                    print(f"ℹ️ [{self.device_id}] Ya aparece como suscrito, saltando esta cuenta")
                    suscripcion_exitosa = True
                    self._registrar("suscripcion")
                elif self.element_exists(subscribe_button_xpath):
                    if self.click_element(subscribe_button_xpath):
                        suscripcion_exitosa = True
                        self._registrar("suscripcion")
                        print(f"✅ [{self.device_id}] Suscripción realizada")
                else:
                    print(f"❌ [{self.device_id}] Botón de suscribirse no encontrado")
                    if not self.click_element(subscribe_button_xpath_alt):
                        print(f"❌ [{self.device_id}] Botón alternativo de suscribirme no encontrado")
                        suscripcion_exitosa = False
                    print(f"✅ [{self.device_id}] Suscripción realizada (alternativo)")

                if suscripcion_exitosa:
                    suscripciones_realizadas += 1
                    self.random_sleep(3, 6)
                    print(f"✅ [{self.device_id}] Proceso de suscripciones completado")
                else:
                    print(f"⚠️ [{self.device_id}] No se logró suscripción en esta cuenta")

            except Exception as e:
                print(f"❌ [{self.device_id}] Error en proceso de suscripciones: {e}")
                raise
            finally:
                self.device.press("home")
                self.short_sleep(2)

            if not self._post_proceso_rotacion("suscripciones", 15, 60, detener_flag):
                break

        return suscripciones_realizadas

    def proceso_compartidas(self, link_post: str, detener_flag: Optional[threading.Event] = None) -> int:
        """
        Proceso de compartidas en un post de YouTube
        Args:
            link_post: URL de video de Youtube
        Returns:
            int: cantidad de compartidas realizadas
        """
        if not self._hay_cuentas_disponibles("compartidas"):
            return 0

        compartidas_realizadas = 0

        while self._hay_cuentas_disponibles("compartidas"):
            if self._should_stop(detener_flag, "compartidas"):
                break

            compartida_exitosa = False
            try:
                self._restart_youtube_app()

                print(f"🚀 [{self.device_id}] Iniciando proceso de compartidas en post: {link_post}")

                # Abrir el post
                self.open_youtube_link(link_post)
                self.random_sleep(5, 8)

                share_button_xpath = '//*[contains(@content-desc, "Compartir")]'
                copy_link_xpath = '//*[@text="Copiar enlace"]'

                if not self.verificar_es_short():
                    self.saltar_anuncio()

                if self.element_exists(share_button_xpath) and self.click_element(share_button_xpath):
                    self.random_sleep(2, 4)

                    if self.element_exists(copy_link_xpath):
                        if self.click_element(copy_link_xpath):
                            compartida_exitosa = True
                            print(f"✅ [{self.device_id}] Enlace copiado al portapapeles")
                    else:
                        print(
                            f"⚠️ [{self.device_id}] Opción de copiar enlace no encontrada, intentando coordenadas fijas")
                        try:
                            self.device.click(191, 1940)
                            compartida_exitosa = True
                            print(f"✅ [{self.device_id}] Compartida forzada mediante coordenadas")
                        except Exception as coord_err:
                            print(
                                f"❌ [{self.device_id}] No se pudo completar la compartida por coordenadas: {coord_err}")
                else:
                    print(f"❌ [{self.device_id}] Botón de compartir no encontrado")

                if compartida_exitosa:
                    self.random_sleep(3, 6)
                    print(f"✅ [{self.device_id}] Proceso de compartidas completado")
                    compartidas_realizadas += 1
                else:
                    print(f"⚠️ [{self.device_id}] Compartida no realizada en esta cuenta")

            except Exception as e:
                print(f"❌ [{self.device_id}] Error en proceso de compartidas: {e}")
                raise
            finally:
                # Al finalizar, regresar a pantalla principal
                self.device.press("home")
                self.short_sleep(2)

            if not self._post_proceso_rotacion("compartidas", 15, 60, detener_flag):
                break

        return compartidas_realizadas

    def calcular_tiempo_retencion(self, duracion_segundos: int, min_pct: float = 30, max_pct: float = 100) -> int:
        """
        Calcula el tiempo de retencion como un porcentaje aleatorio de la duracion del video.

        Args:
            duracion_segundos: duracion total del video en segundos
            min_pct: porcentaje minimo de retencion
            max_pct: porcentaje maximo de retencion

        Returns:
            segundos a reproducir
        """
        if duracion_segundos <= 0:
            return 0
        min_pct = max(0.0, float(min_pct))
        max_pct = min(100.0, max(min_pct, float(max_pct)))
        pct = random.uniform(min_pct, max_pct)
        segundos = int(duracion_segundos * pct / 100.0)
        return max(5, segundos)

    def _interaccion_satisfaccion(self, hacer_like: bool = False, hacer_comentario: bool = False,
                                  hacer_compartir: bool = False,
                                  detener_flag: Optional[threading.Event] = None):
        """
        Realiza las acciones de satisfaccion SELECCIONADAS (deterministas, no probabilisticas)
        en el video ACTUAL (ya abierto). El usuario elige al iniciar el flujo si quiere
        like, comentario y/o compartir.
        """
        if detener_flag and detener_flag.is_set():
            return
        if not (hacer_like or hacer_comentario or hacer_compartir):
            return
        try:
            # Mostrar controles del reproductor si estan ocultos
            video_player_xpath = '//*[@content-desc="Reproductor de video"]'
            if self.element_exists(video_player_xpath):
                self.click_element(video_player_xpath)
                self.short_sleep(0.8)

            if hacer_like and self._like_video_actual():
                self.random_sleep(2, 4)

            if hacer_comentario and self._comentar_video_actual():
                self.random_sleep(2, 4)

            if hacer_compartir and self._compartir_video_actual():
                self.random_sleep(2, 4)
        except Exception as e:
            print(f"⚠️ [{self.device_id}] Error en interaccion satisfaccion: {e}")

    def _like_video_actual(self) -> bool:
        """Da like al video actual (excluye 'No me gusta'), si no se ha hecho antes."""
        if not self._deberia_ejecutar(self.video_id_actual or "", "like"):
            print(f"ℹ️ [{self.device_id}] Like ya registrado para esta cuenta/video, saltando")
            return False
        like_xpath = '//*[contains(@content-desc, "Me gusta") and not(contains(@content-desc, "No me gusta"))]'
        if self.element_exists(like_xpath):
            if self.click_element(like_xpath):
                self._registrar("like")
                print(f"👍 [{self.device_id}] Like realizado (satisfacción)")
                return True
        return False

    def _siguiente_comentario(self) -> str:
        """Devuelve el proximo comentario asignado (o del banco generico si no hay lista)."""
        banco = [
            "Buen video 👍", "Muy bueno", "🔥🔥", "Excelente contenido",
            "Gracias por compartir", "👏👏", "Muy útil", "Gran video",
        ]
        if self.comentarios_asignar:
            c = self.comentarios_asignar[self.comentario_idx % len(self.comentarios_asignar)]
            self.comentario_idx += 1
            return c
        return random.choice(banco)

    def _comentar_video_actual(self) -> bool:
        """Publica un comentario asignado en el video actual (si no se ha comentado antes)."""
        if not self._deberia_ejecutar(self.video_id_actual or "", "comentario"):
            print(f"ℹ️ [{self.device_id}] Comentario ya registrado para esta cuenta/video, saltando")
            return False
        comentario = self._siguiente_comentario()
        try:
            comment_xpath = '//*[contains(@content-desc, "Comentario") or contains(@content-desc, "comentario")]'
            if not self.element_exists(comment_xpath):
                return False
            self.click_element(comment_xpath)
            self.random_sleep(2, 4)

            input_field = self.device(className="android.widget.EditText")
            if not input_field.exists:
                self.press_back()
                return False
            input_field.click()
            self.short_sleep(1)

            self.device.send_keys(comentario, clear=True)
            self.short_sleep(1)
            self.device.press("enter")
            self._registrar("comentario", comentario)
            print(f"💬 [{self.device_id}] Comentario publicado (satisfacción): {comentario}")
            self.random_sleep(1, 2)
            self.press_back()
            return True
        except Exception as e:
            print(f"⚠️ [{self.device_id}] Error comentando: {e}")
            return False

    def _compartir_video_actual(self) -> bool:
        """Copia el enlace del video actual (si no se ha compartido antes)."""
        if not self._deberia_ejecutar(self.video_id_actual or "", "compartir"):
            print(f"ℹ️ [{self.device_id}] Compartir ya registrado para esta cuenta/video, saltando")
            return False
        share_xpath = '//*[contains(@content-desc, "Compartir")]'
        copy_xpath = '//*[@text="Copiar enlace"]'
        if self.element_exists(share_xpath) and self.click_element(share_xpath):
            self.random_sleep(2, 4)
            if self.element_exists(copy_xpath):
                if self.click_element(copy_xpath):
                    self._registrar("compartir")
                    print(f"🔗 [{self.device_id}] Enlace copiado (satisfacción)")
                    self.random_sleep(1, 2)
                    self.press_back()
                    return True
            self.press_back()
        return False

    def proceso_views(
            self,
            link_post: str,
            detener_flag: Optional[threading.Event] = None,
            retention_min_pct: float = 30,
            retention_max_pct: float = 100,
            hacer_like: bool = False,
            hacer_comentario: bool = False,
            hacer_compartir: bool = False,
            comentarios: Optional[List[str]] = None
    ) -> int:
        """
        Proceso de views (retencion) en YouTube. La retencion varia entre
        retention_min_pct% y retention_max_pct% de la duracion del video.

        Returns:
            int: cantidad de sesiones (cuentas) que reprodujeron el video.
        """
        if not link_post:
            print(f"[YT][{self.device_id}] No se proporcionó link para views")
            return 0

        retention_min_pct = max(5.0, float(retention_min_pct))
        retention_max_pct = min(100.0, max(retention_min_pct, float(retention_max_pct)))
        self.comentarios_asignar = list(comentarios or [])

        sesiones_realizadas = 0

        while True:
            if self._should_stop(detener_flag, "views"):
                break

            if self.sin_cuentas_disponibles:
                # Reiniciar listado para poder reutilizar cuentas
                self.cuentas_usadas = []
                self.sin_cuentas_disponibles = False

            try:
                self._restart_youtube_app()

                print(f"🚀 [{self.device_id}] Iniciando proceso de views en post: {link_post}")
                self.open_youtube_link(link_post)
                self.random_sleep(5, 8)

                if self.verificar_es_short():
                    # Shorts: se ven casi completos (son cortos)
                    short_duration = random.randint(25, 55)
                    print(f"🔥 [{self.device_id}] Reproduciendo Short por {short_duration} segundos...")
                    time.sleep(short_duration)
                    self.double_tap()
                    self.random_sleep(2, 4)
                    print(f"✅ [{self.device_id}] Short completado")
                else:
                    self.saltar_anuncio()

                    # Leer duracion total del video (tocar player para mostrar controles)
                    total_seconds = 0
                    video_player_xpath = '//*[@content-desc="Reproductor de video"]'
                    if self.element_exists(video_player_xpath):
                        self.click_element(video_player_xpath)
                        self.short_sleep(0.5)
                    duration_resource_id = "com.google.android.youtube:id/time_bar_total_time"
                    duration_text = self.get_element_text(resource_id=duration_resource_id)
                    if duration_text:
                        total_seconds = self.parse_duration_to_seconds(duration_text)

                    # Retencion porcentual de la duracion
                    if total_seconds > 0:
                        watch_seconds = self.calcular_tiempo_retencion(total_seconds, retention_min_pct, retention_max_pct)
                    else:
                        # Duracion no detectada: fallback
                        watch_seconds = random.randint(45, 90)

                    print(f"▶️ [{self.device_id}] Retencion {retention_min_pct}-{retention_max_pct}%: "
                          f"viendo {watch_seconds}s de {total_seconds}s...")
                    time.sleep(watch_seconds)
                    print(f"✅ [{self.device_id}] Reproducción del video completada ({watch_seconds}s)")

                    # Satisfaccion seleccionada al iniciar el flujo (determinista)
                    self._interaccion_satisfaccion(hacer_like, hacer_comentario, hacer_compartir, detener_flag)

                sesiones_realizadas += 1
                self._registrar("vista")

            except Exception as e:
                print(f"⚠️ [{self.device_id}] Error en proceso de views: {e}")
                raise
            finally:
                self.device.press("home")
                self.short_sleep(2)

            if not self._post_proceso_rotacion("views", 5 * 60, 15 * 60, detener_flag, permitir_reuso=True):
                if detener_flag and detener_flag.is_set():
                    break
                continue

        return sesiones_realizadas

    def proceso_reproducir_playlist(
            self,
            link_post: str,
            detener_flag: Optional[threading.Event] = None,
            retention_min_pct: float = 30,
            retention_max_pct: float = 100
    ):
        """
        Proceso de reproducir playlist en YouTube con detección de fin de lista.
        Retención porcentual por video (retention_min_pct% a retention_max_pct%).
        """
        if not self._hay_cuentas_disponibles("reproducir playlist"):
            return 0

        playlists_completadas = 0
        retention_min_pct = max(5.0, float(retention_min_pct))
        retention_max_pct = min(100.0, max(retention_min_pct, float(retention_max_pct)))

        while self._hay_cuentas_disponibles("reproducir playlist"):
            if self._should_stop(detener_flag, "reproducir playlist"):
                break

            try:
                self._restart_youtube_app()

                print(f"[YT] [{self.device_id}] Iniciando proceso de reproducir playlist: {link_post}")

                # Abrir el post
                self.open_youtube_link(link_post)
                self.random_sleep(5, 8)

                reproducir_playlist_xpath = '//*[contains(@content-desc, "Reproducir")]'
                if self.element_exists(reproducir_playlist_xpath):
                    self.click_element(reproducir_playlist_xpath)
                    print(f"[{self.device_id}] Reproduciendo playlist...")

                    tiempo_total_reproducido = 0
                    continuar_playlist = True
                    video_player_xpath = '//*[@content-desc="Reproductor de video"]'
                    next_video_xpath = '//*[@content-desc="Siguiente video"]'
                    # ID específico para verificar si es clickeable/habilitado
                    next_button_res = "com.google.android.youtube:id/next_gen_button"

                    while continuar_playlist and not self._should_stop(detener_flag, "reproducir playlist"):
                        self.random_sleep(5, 8)
                        self.saltar_anuncio()

                        if self.element_exists(video_player_xpath):
                            print(f"[{self.device_id}] Video cargado correctamente")

                            self.click_element(video_player_xpath)
                            self.short_sleep(0.5)

                            # --- VALIDACIÓN DE FIN DE PLAYLIST ---
                            # Si el botón no existe o no está habilitado (enabled=False), es el fin.

                            boton_next = self.device.xpath(next_video_xpath)
                            print(f"Boton siguiente: {boton_next.exists}, {boton_next.info.get('enabled')} ")
                            if not boton_next.exists or not boton_next.info.get('enabled'):
                                print(
                                    f"🏁 [{self.device_id}] Fin de lista detectado (Botón Siguiente no disponible o deshabilitado)")
                                es_ultimo = True
                            else:
                                es_ultimo = False
                            # -------------------------------------

                            duration_resource_id = "com.google.android.youtube:id/time_bar_total_time"
                            duration_text = self.get_element_text(resource_id=duration_resource_id)

                            if duration_text:
                                total_seconds = self.parse_duration_to_seconds(duration_text)
                                if total_seconds > 0:
                                    watch_seconds = self.calcular_tiempo_retencion(total_seconds, retention_min_pct, retention_max_pct)
                                    print(f"[{self.device_id}] Video de {total_seconds}s, viendo {watch_seconds}s "
                                          f"(retención {retention_min_pct}-{retention_max_pct}%)")
                                    time.sleep(watch_seconds)
                                    tiempo_total_reproducido += watch_seconds
                            else:
                                watch_seconds = random.randint(45, 120)
                                print(f"[{self.device_id}] Duración no detectada, viendo {watch_seconds}s")
                                time.sleep(watch_seconds)
                                tiempo_total_reproducido += watch_seconds

                            if es_ultimo:
                                continuar_playlist = False
                            else:
                                self.click_element(video_player_xpath)
                                self.short_sleep(0.5)
                                if not self.click_element(next_video_xpath):
                                    continuar_playlist = False
                                print(f"[{self.device_id}] Siguiente video abierto")
                                self.random_sleep(5, 8)

                        else:
                            # Si no hay player, intentamos pasar o terminar
                            if es_ultimo:
                                continuar_playlist = False
                            else:
                                self.click_element(video_player_xpath)
                                self.short_sleep(0.5)
                                if not self.click_element(next_video_xpath):
                                    continuar_playlist = False
                                print(f"[{self.device_id}] Avanzando al siguiente video")
                                self.random_sleep(5, 8)

                    playlists_completadas += 1
                    print(
                        f"[{self.device_id}] Playlist completada, tiempo total reproducido: {tiempo_total_reproducido} segundos")
                else:
                    print(f"[{self.device_id}] No se encontró botón para reproducir la playlist")

            except Exception as e:
                print(f"[{self.device_id}] Error en proceso de reproducir playlist: {e}")
                raise
            finally:
                self.device.press("home")
                self.short_sleep(2)

            # Proceso de rotación (No modificado)
            if not self._post_proceso_rotacion("reproducir playlist", 5 * 60, 15 * 60, detener_flag):
                break

        return playlists_completadas

    def proceso_reproducir_live(
            self,
            link_post: str,
            duracion_minutos: int = 10,
            detener_flag: Optional[threading.Event] = None
    ):
        """
        Abre un directo de YouTube y lo mantiene abierto por un tiempo determinado.
        """
        if not self._hay_cuentas_disponibles("reproducir live"):
            return 0

        lives_completados = 0
        tiempo_objetivo_segundos = duracion_minutos * 60

        while self._hay_cuentas_disponibles("reproducir live"):
            if self._should_stop(detener_flag, "reproducir live"):
                break

            try:
                self._restart_youtube_app()
                print(f"[YT] [{self.device_id}] Abriendo Live: {link_post}")

                # Abrir el link del directo
                self.open_youtube_link(link_post)
                self.random_sleep(5, 8)

                # Verificar si es un directo buscando el badge "EN DIRECTO" o "LIVE"
                live_badge_xpath = '//*[contains(@text, "DIRECTO") or contains(@text, "LIVE")]'

                inicio_reproduccion = time.time()
                tiempo_transcurrido = 0

                print(f"[{self.device_id}] Manteniendo Live por {duracion_minutos} minutos...")

                while tiempo_transcurrido < tiempo_objetivo_segundos:
                    if self._should_stop(detener_flag, "reproducir live"):
                        break

                    # Saltar anuncios si aparecen (referencia a tu función saltar_anuncio)
                    self.saltar_anuncio()

                    # Simular interacción ocasional para evitar que la app entre en reposo
                    if random.choice([True, False, False]):
                        self.device.click(500, 500)  # Tocar centro para mostrar UI
                        self.short_sleep(1)

                    # Espera de monitoreo corta
                    self.random_sleep(20, 40)
                    tiempo_transcurrido = time.time() - inicio_reproduccion
                    print(
                        f"⏱️ [{self.device_id}] Progreso Live: {int(tiempo_transcurrido)}/{tiempo_objetivo_segundos}s")

                lives_completados += 1
                print(f"✅ [{self.device_id}] Tiempo de visualización de Live completado.")

            except Exception as e:
                print(f"❌ [{self.device_id}] Error en proceso de Live: {e}")
                raise
            finally:
                self.device.press("home")
                self.short_sleep(2)

            # Rotación de cuenta tras completar el tiempo en el Live
            if not self._post_proceso_rotacion("reproducir live", 2 * 60, 5 * 60, detener_flag):
                break

        return lives_completados

    def proceso_maximizar_perfil_views(self, link_post: str, detener_flag: Optional[threading.Event] = None) -> int:
        """
        Proceso de maximizar perfil views en un canal de YouTube
        Args:
            link_post: URL de canal de Youtube
        """
        if not self._hay_cuentas_disponibles("maximizar perfil views"):
            return 0

        perfiles_procesados = 0

        while self._hay_cuentas_disponibles("maximizar perfil views"):
            if self._should_stop(detener_flag, "maximizar perfil views"):
                break
            try:
                self._restart_youtube_app()

                # Asegurar que el link siempre termine en /shorts
                normalized_link = link_post.rstrip('/')
                if not normalized_link.endswith('/shorts'):
                    normalized_link = f"{normalized_link}/shorts"

                print(f"🚀 [{self.device_id}] Iniciando proceso de maximizar perfil views en canal: {normalized_link}")

                self.open_youtube_link(normalized_link)
                self.random_sleep(5, 8)

                comment_button_xpath = '//*[contains(@content-desc,"comentario")]'
                comment_input_selector = {"className": "android.widget.EditText"}
                share_button_xpath = '//*[contains(@content-desc, "Compartir")]'
                fin_shorts_xpath = '//*[@content-desc="Espera..."]'
                reproducir_short_xpath = '//*[contains(@content-desc,"reproducir Short")]'

                comentarios_cortos = [
                    "🔥🔥🔥",
                    "Buen short 😎",
                    "Tremendo!",
                    "👏👏👏",
                ]

                def chance(percent: float) -> bool:
                    return random.random() * 100 < percent

                def comentar_short() -> bool:
                    if not self.element_exists(comment_button_xpath):
                        return False
                    if not self.click_element(comment_button_xpath):
                        return False
                    self.random_sleep(2, 4)

                    input_field = self.device(**comment_input_selector)
                    if not input_field.exists:
                        self.press_back()
                        return False

                    comentario = random.choice(comentarios_cortos)
                    try:
                        input_field.set_text(comentario)
                    except Exception:
                        self.device.send_keys(comentario, clear=True)
                    self.short_sleep(1)
                    try:
                        self.device.press("enter")
                        print(f"[YT][{self.device_id}] Comentario publicado: {comentario}")
                        self.random_sleep(1, 2)
                        return True
                    finally:
                        self.press_back()

                def compartir_short() -> bool:
                    if not self.element_exists(share_button_xpath):
                        return False
                    if not self.click_element(share_button_xpath):
                        return False
                    self.random_sleep(2, 4)
                    copy_link_xpath = '//*[@text="Copiar enlace"]'
                    if self.element_exists(copy_link_xpath):
                        self.click_element(copy_link_xpath)
                        print(f"[YT][{self.device_id}] Short compartido/copiado")
                        self.random_sleep(1, 2)
                        return True
                    print(f"[YT][{self.device_id}] No se encontró opción de copiar enlace al compartir")
                    self.press_back()
                    return False

                if self.element_exists(reproducir_short_xpath):
                    self.click_element(reproducir_short_xpath)
                    print(f"[YT][{self.device_id}] Reproduciendo primer Short del perfil")
                else:
                    print(f"[YT][{self.device_id}] No se encontró botón de reproducir Short")

                while not self._should_stop(detener_flag, "maximizar shorts"):
                    watch_seconds = random.randint(15, 60)
                    print(f"[YT][{self.device_id}] Viendo Short durante {watch_seconds} segundos")
                    self.short_sleep(watch_seconds)

                    # Si es un anuncio no hacer nada
                    if not self.element_exists('//*[contains(@content-desc,"Anuncio")]') or not self.element_exists(
                            '//*[contains(@content-desc,"Patrocinado")]'):
                        acciones = []
                        if chance(70):
                            self.double_tap()
                            acciones.append("double tap")
                        if chance(25):
                            if comentar_short():
                                acciones.append("comentario")
                        if chance(15):
                            if compartir_short():
                                acciones.append("compartido")

                        if not acciones:
                            print(f"[YT][{self.device_id}] Short visto sin interacción")
                        else:
                            print(f"[YT][{self.device_id}] Acciones realizadas: {', '.join(acciones)}")

                        try:
                            self.device.swipe_ext("up", scale=random.uniform(0.6, 0.9))
                        except Exception as swipe_err:
                            print(f"[YT][{self.device_id}] Error al pasar al siguiente Short: {swipe_err}")
                            self.short_sleep(2)
                    else:
                        print(f"[YT][{self.device_id}] Anuncio detectado, no se realizan interacciones")

                    if self.element_exists(fin_shorts_xpath):
                        print(f"[YT][{self.device_id}] Shorts finalizados, es hora de rotar cuentas")
                        break

                perfiles_procesados += 1

            except Exception as e:
                print(f"❌ [{self.device_id}] Error en proceso de maximizar perfil views: {e}")
                raise
            finally:
                self.device.press("home")
                self.short_sleep(2)

            if not self._post_proceso_rotacion("maximizar perfil views", 5 * 60, 10 * 60, detener_flag):
                break

        return perfiles_procesados

    def proceso_comentarios(
            self,
            link_post: str,
            comentarios: List[str],
            detener_flag: Optional[threading.Event] = None
    ) -> int:
        """
        Proceso de comentarios en un post de YouTube.
        Args:
            link_post: URL del video de YouTube
            comentarios: lista de comentarios a publicar en orden
            detener_flag: flag opcional para detener el proceso de forma segura
        Returns:
            int: cantidad de comentarios publicados exitosamente
        """
        if not self._hay_cuentas_disponibles("comentarios"):
            return 0

        comentarios_pendientes = deque(
            (comentario or "").strip() for comentario in comentarios or [] if (comentario or "").strip()
        )

        if not comentarios_pendientes:
            print(f"[YT][{self.device_id}] No se recibieron comentarios válidos para publicar")
            return 0

        publicados = 0
        comment_box_xpath = '//*[contains(@content-desc,"comentario")]'
        comment_box_xpath = '//androidx.drawerlayout.widget.DrawerLayout/android.widget.FrameLayout[1]/android.view.ViewGroup[1]/android.widget.FrameLayout[2]/android.view.ViewGroup[1]/android.view.ViewGroup[1]/android.widget.FrameLayout[2]/android.view.ViewGroup[1]/android.widget.FrameLayout[1]/android.widget.FrameLayout[1]/android.widget.FrameLayout[1]/android.support.v7.widget.RecyclerView[1]/android.view.ViewGroup[3]/android.view.ViewGroup[1]/android.view.ViewGroup[2]'
        post_button_xpath = '//*[contains(@content-desc,"Enviar")]'

        while comentarios_pendientes and self._hay_cuentas_disponibles("comentarios"):
            if self._should_stop(detener_flag, "comentarios"):
                print(f"[YT][{self.device_id}] Detención solicitada; proceso de comentarios se detiene")
                break

            comentario_actual = comentarios_pendientes[0]
            intento_publicado = False

            try:
                self._restart_youtube_app()

                print(f"[YT][{self.device_id}] Iniciando comentario: {comentario_actual}")
                self.open_youtube_link(link_post)
                self.random_sleep(5, 8)

                if self.verificar_es_short():
                    if not self.element_exists(comment_box_xpath):
                        print(f"[YT][{self.device_id}] Botón de comentar no encontrado")
                        break

                    if not self.click_element(comment_box_xpath):
                        print(f"[YT][{self.device_id}] No se pudo abrir el cuadro de comentarios")
                        break
                else:
                    self.saltar_anuncio()
                    if not self.element_exists(comment_box_xpath):
                        print(f"[YT][{self.device_id}] Botón de comentar no encontrado")
                        break
                    if not self.click_element(comment_box_xpath):
                        print(f"[YT][{self.device_id}] No se pudo abrir el cuadro de comentarios")
                        break
                    self.random_sleep(2, 4)

                    comment_input_selector = {"className": "android.widget.EditText"}
                    input_field = self.device(**comment_input_selector)
                    if not input_field.exists:
                        self.press_back()
                        return False
                    input_field.click()
                    self.short_sleep(1)

                self.random_sleep(2, 4)
                print(f"[YT][{self.device_id}] Escribiendo comentario: {comentario_actual}")
                self.device.send_keys(comentario_actual, clear=True)
                self.short_sleep(1)

                if self.element_exists(post_button_xpath) and self.click_element(post_button_xpath):
                    publicados += 1
                    intento_publicado = True
                    comentarios_pendientes.popleft()
                    print(f"[YT][{self.device_id}] Comentario publicado ({publicados} total)")
                else:
                    print(f"[YT][{self.device_id}] Botón de publicar no encontrado")

                self.device.set_fastinput_ime(False)
                self.random_sleep(3, 6)

            except Exception as e:
                print(f"[YT][{self.device_id}] Error en proceso de comentarios: {e}")
                raise
            finally:
                self.device.press("home")
                self.short_sleep(2)

            if not comentarios_pendientes:
                break

            if not intento_publicado:
                # Evitar loop infinito con el mismo comentario
                comentarios_pendientes.rotate(-1)

            if not self._post_proceso_rotacion("comentarios", 15, 60, detener_flag):
                break

        print(f"[YT][{self.device_id}] Proceso de comentarios finalizado ({publicados} publicados)")
        return publicados