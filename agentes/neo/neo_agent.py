"""
NEO - Agente Radar de Propiedades de Ruth Inmobiliaria
Busca particulares vendiendo pisos en Castelldefels, Gavà y Viladecans.
Detecta señales de venta en redes sociales y portales inmobiliarios.
"""
import os
import json
import re
import requests
from datetime import datetime
from bs4 import BeautifulSoup

BASE_DIR = r"D:\aplexgrow_antigravity\RUTH_INMOBILIARIA"
CONFIG_FILE = os.path.join(BASE_DIR, "config", "config.json")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
LOGS_DIR = os.path.join(BASE_DIR, "logs")


def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


CONFIG = load_config()
ZONAS = CONFIG.get("ZONAS", ["Castelldefels", "Gavà", "Viladecans"])


class NEOAgent:
    """Agente NEO: Radar de propiedades y captación de clientes."""

    def __init__(self):
        self.name = "NEO"
        self.log_file = os.path.join(LOGS_DIR, "neo.log")
        os.makedirs(LOGS_DIR, exist_ok=True)
        os.makedirs(OUTPUT_DIR, exist_ok=True)

    def log(self, msg: str):
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(f"[{ts}] {msg}\n")

    # ── BÚSQUEDA EN PORTALES ──────────────────────────────────

    def buscar_idealista(self, zona: str = "castelldefels", tipo: str = "venta") -> list:
        """Busca propiedades en Idealista (scraping básico)."""
        try:
            url = f"https://www.idealista.com/{tipo}-inmuebles/{zona}/"
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept": "text/html,application/xhtml+xml",
            }
            resp = requests.get(url, headers=headers, timeout=15)
            if resp.status_code != 200:
                return [{"error": f"HTTP {resp.status_code} al acceder a Idealista"}]

            soup = BeautifulSoup(resp.text, "html.parser")
            items = soup.select("article.item") or soup.select("div.item-info-container")
            resultados = []
            for item in items[:10]:
                titulo = item.get_text(strip=True)[:100] if item.get_text(strip=True) else ""
                if titulo:
                    resultados.append({"fuente": "Idealista", "texto": titulo, "zona": zona})
            return resultados if resultados else [
                {"fuente": "Idealista", "info": f"Búsqueda en {zona} completada", "zona": zona}
            ]
        except Exception as e:
            self.log(f"Error Idealista: {e}")
            return [{"error": f"Error accediendo a Idealista: {e}"}]

    def buscar_fotocasa(self, zona: str = "castelldefels") -> list:
        """Busca propiedades en Fotocasa."""
        try:
            url = f"https://www.fotocasa.es/{zona}/"
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            }
            resp = requests.get(url, headers=headers, timeout=15)
            if resp.status_code != 200:
                return [{"error": f"HTTP {resp.status_code} al acceder a Fotocasa"}]

            soup = BeautifulSoup(resp.text, "html.parser")
            items = soup.select("article.card") or soup.select("div.re-Card")
            resultados = []
            for item in items[:10]:
                texto = item.get_text(strip=True)[:150] if item.get_text(strip=True) else ""
                if texto:
                    resultados.append({"fuente": "Fotocasa", "texto": texto, "zona": zona})
            return resultados if resultados else [
                {"fuente": "Fotocasa", "info": f"Búsqueda en {zona} completada", "zona": zona}
            ]
        except Exception as e:
            self.log(f"Error Fotocasa: {e}")
            return [{"error": f"Error accediendo a Fotocasa: {e}"}]

    def buscar_particulares(self, zonas: list = None) -> list:
        """Busca particulares vendiendo (sin inmobiliaria) en portales."""
        zonas = zonas or ZONAS
        todos = []
        for zona in zonas:
            zona_slug = zona.lower().replace(" ", "-").replace("á", "a").replace("è", "e").replace("é", "e")
            self.log(f"Buscando en {zona}...")
            idealista = self.buscar_idealista(zona_slug)
            fotocasa = self.buscar_fotocasa(zona_slug)
            todos.extend(idealista)
            todos.extend(fotocasa)
        return todos

    # ── DETECCIÓN DE SEÑALES EN REDES ─────────────────────────

    def detectar_senales_venta(self, texto: str) -> dict:
        """Detecta si un texto contiene señales de que alguien quiere vender."""
        señales = {
            "vendo_piso": r"\bvendo\s+(piso|casa|ático|local|propiedad|inmueble)\b",
            "vendo_directo": r"\bvendo\s+(directo|particular|sin\s+inmobiliaria)\b",
            "me_marcho": r"\b(me\s+marcho|cambio\s+de\s+ciudad|me\s+voy\s+fuera)\b",
            "herencia": r"\b(herencia|heredo|heredado)\b",
            "necesito_vender": r"\b(necesito\s+vender|urge\s+vender|vendo\s+urge)\b",
            "quiero_vender": r"\b(quiero\s+vender|busco\s+comprador)\b",
            "precio": r"\b(precio|€|euros?|oferta)\b",
        }
        encontradas = []
        for nombre, patron in señales.items():
            if re.search(patron, texto, re.IGNORECASE):
                encontradas.append(nombre)
        return {
            "tiene_senales": len(encontradas) > 0,
            "señales": encontradas,
            "intensidad": len(encontradas),
        }

    # ── GENERACIÓN DE INFORMES ─────────────────────────────────

    def generar_informe_captacion(self, resultados: list) -> str:
        """Genera un informe de captación con los resultados encontrados."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        informe = [
            f"📡 INFORME DE CAPTACIÓN - NEO RADAR",
            f"🕐 {timestamp}",
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━",
        ]

        fuentes = {}
        for r in resultados:
            fuente = r.get("fuente", "desconocida")
            if fuente not in fuentes:
                fuentes[fuente] = []
            fuentes[fuente].append(r)

        for fuente, items in fuentes.items():
            informe.append(f"\n📌 {fuente}: {len(items)} resultados")
            for item in items[:5]:
                texto = item.get("texto") or item.get("info", "")
                if texto and len(texto) > 10:
                    senales = self.detectar_senales_venta(texto)
                    icono = "🔴" if senales["tiene_senales"] else "⚪"
                    informe.append(f"  {icono} {texto[:120]}")

        informe.append(f"\n━━━━━━━━━━━━━━━━━━━━━━━━━━")
        informe.append(f"✅ Búsqueda completada en {len(set(r.get('fuente','') for r in resultados))} fuentes.")

        # Guardar informe
        nombre_archivo = f"INFORME_NEO_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        ruta = os.path.join(OUTPUT_DIR, nombre_archivo)
        with open(ruta, "w", encoding="utf-8") as f:
            f.write("\n".join(informe))

        self.log(f"Informe generado: {ruta}")
        return "\n".join(informe)

    # ── EJECUCIÓN PRINCIPAL ────────────────────────────────────

    def execute(self, task: str) -> str:
        """Punto de entrada principal."""
        task_lower = task.lower()

        if "buscar" in task_lower or "captacion" in task_lower or "radar" in task_lower:
            self.log(f"Iniciando búsqueda: {task}")
            resultados = self.buscar_particulares()
            return self.generar_informe_captacion(resultados)

        elif "idealista" in task_lower:
            # Extraer zona si se especifica
            zona = "castelldefels"
            for z in ZONAS:
                if z.lower() in task_lower:
                    zona = z.lower().replace(" ", "-").replace("á", "a")
                    break
            resultados = self.buscar_idealista(zona)
            return f"📡 NEO buscó en Idealista ({zona}):\n" + "\n".join(
                r.get("texto", r.get("info", str(r)))[:150] for r in resultados[:5]
            )

        elif "fotocasa" in task_lower:
            zona = next((z.lower() for z in ZONAS if z.lower() in task_lower), "castelldefels")
            zona_slug = zona.replace(" ", "-").replace("á", "a")
            resultados = self.buscar_fotocasa(zona_slug)
            return f"📡 NEO buscó en Fotocasa ({zona}):\n" + "\n".join(
                r.get("texto", r.get("info", str(r)))[:150] for r in resultados[:5]
            )

        elif "señales" in task_lower or "senales" in task_lower:
            # Detectar señales en un texto
            return json.dumps(self.detectar_senales_venta(task), indent=2, ensure_ascii=False)

        else:
            return (
                f"[NEO] Soy el Radar de propiedades de Ruth. Puedo:\n"
                f"• 🔍 Buscar propiedades en Idealista y Fotocasa\n"
                f"• 🎯 Detectar particulares vendiendo sin inmobiliaria\n"
                f"• 📊 Generar informes de captación\n"
                f"• 📡 Detectar señales de venta en textos\n"
                f"¿Qué zona quieres que busque? (Castelldefels, Gavà, Viladecans)"
            )


# Función para compatibilidad con el main.py
def execute(task: str) -> str:
    agent = NEOAgent()
    return agent.execute(task)