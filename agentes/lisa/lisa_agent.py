"""
LISA - Agente de Marketing de Ruth Inmobiliaria
Genera contenido para redes sociales, Reels, clones de voz y material audiovisual.
"""
import os
import json
import subprocess
from datetime import datetime

BASE_DIR = r"D:\aplexgrow_antigravity\RUTH_INMOBILIARIA"
CONFIG_FILE = os.path.join(BASE_DIR, "config", "config.json")

# Directorios del proyecto
REMOTION_DIR = r"D:\aplexgrow_antigravity\0_STUDIO_MULTIMEDIA\1_REMOTION_REELS"
OUTPUT_VIDEO_DIR = os.path.join(BASE_DIR, "OUTPUT_VIDEO")


def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


CONFIG = load_config()


class LISAAgent:
    """Agente LISA: Marketing, contenido audiovisual y clones de voz."""

    def __init__(self):
        self.config = load_config()
        self.eleven_api_key = self.config.get("ELEVENLABS_API_KEY", "")
        self.heygeng_api_key = self.config.get("HEYGEN_API_KEY", "")

    def _check_config(self, service: str) -> bool:
        if "AQUI" in self.eleven_api_key and service == "voice":
            return False
        return True

    # ── Generación de Reels / Vídeos (Remotion) ────────────

    def generar_script_reel(self, propiedad: dict) -> str:
        """Genera un guion de Reel para una propiedad."""
        tipo = propiedad.get("tipo", "pisos")
        zona = propiedad.get("zona", "Castelldefels")
        precio = propiedad.get("precio", "consultar")
        habitaciones = propiedad.get("habitaciones", "?")

        script = f"""Guion Reel - {tipo.capitalize()} en {zona}
========================================

[HOOK - 3 segundos]
📍 ¡{tipo.capitalize()} espectacular en {zona}!

[PRESENTACIÓN - 10 segundos]
Habitaciones: {habitaciones} | Precio: {precio}€
Ubicación privilegiada en pleno centro.

[VALOR - 10 segundos]
✅ Zona tranquila y bien comunicada
✅ Cerca de transportes y servicios
✅ Ideal para familias o inversión

[CTA - 5 segundos]
📞 ¡Llama ahora para visitarla!
Ruth Blanco - Inmobiliaria en Castelldefels y Gavà
"""
        return script

    def preparar_remotion(self, script: str, datos_propiedad: dict) -> dict:
        """Prepara los assets para renderizado en Remotion."""
        props_path = os.path.join(REMOTION_DIR, "src", "props.json")

        data = {
            "script": script,
            "propiedad": datos_propiedad,
            "agente": "LISA",
            "fecha": datetime.now().isoformat(),
            "zona": datos_propiedad.get("zona", "Castelldefels"),
        }

        try:
            os.makedirs(os.path.dirname(props_path), exist_ok=True)
            with open(props_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return {"status": "ok", "message": "Props de Remotion preparados", "path": props_path}
        except Exception as e:
            return {"error": str(e)}

    def renderizar_reel(self, nombre: str = "reel_default") -> str:
        """Renderiza un Reel con Remotion (npx remotion render)."""
        os.makedirs(OUTPUT_VIDEO_DIR, exist_ok=True)
        salida = os.path.join(OUTPUT_VIDEO_DIR, f"{nombre}.mp4")

        try:
            proc = subprocess.Popen(
                ["npx", "remotion", "render", "src/index.ts", "MainComposition", salida],
                cwd=REMOTION_DIR,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            return (
                f"🎬 LISA está renderizando '{nombre}.mp4'.\n"
                f"   Se guardará en: {salida}\n"
                f"   Proceso PID: {proc.pid}"
            )
        except Exception as e:
            return f"⚠️ Error al iniciar render: {e}"

    # ── Clones de voz (ElevenLabs) ─────────────────────────

    def generar_voz(self, texto: str, voz: str = "es-ES-XimenaNeural") -> dict:
        """Genera audio con ElevenLabs o edge-tts."""
        if "AQUI" in self.eleven_api_key:
            return {
                "error": "ElevenLabs API key no configurada",
                "alternativa": "Usar edge-tts (gratis): es-ES-XimenaNeural",
            }

        try:
            import elevenlabs
            elevenlabs.set_api_key(self.eleven_api_key)

            audio = elevenlabs.generate(
                text=texto,
                voice=elevenlabs.get_voices()[0],
                model="eleven_multilingual_v2",
            )
            return {"status": "ok", "audio_data": audio}
        except Exception as e:
            return {"error": str(e)}

    def generar_voz_gratis(self, texto: str, voz: str = "es-ES-XimenaNeural") -> str:
        """Genera voz con edge-tts (gratis, sin API key)."""
        try:
            import edge_tts
            import asyncio

            async def _gen():
                communicate = edge_tts.Communicate(texto, voz)
                nombre = f"voz_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp3"
                ruta = os.path.join(OUTPUT_VIDEO_DIR, nombre)
                os.makedirs(OUTPUT_VIDEO_DIR, exist_ok=True)
                await communicate.save(ruta)
                return f"🎙️ Audio guardado: {ruta}"

            return asyncio.run(_gen())
        except Exception as e:
            return f"⚠️ Error generando voz: {e}"

    # ── Contenido para redes sociales ──────────────────────

    def generar_post_instagram(self, tipo: str, datos: dict = None) -> str:
        """Genera copy para Instagram según el calendario."""
        calendario = {
            "lunes": "quote",
            "martes": "stat",
            "miercoles": "educational",
            "jueves": "case_study",
            "viernes": "cta",
            "sabado": "bts",
        }

        dia = datetime.now().strftime("%A").lower()
        estilo = calendario.get(dia, "cta")

        posts = {
            "quote": [
                "🏠 Tu hogar ideal te está esperando. Solo tienes que dar el primer paso.",
                "La mejor inversión es la que te da paz. 🏡",
                "No busques perfección, busca 'hogar'.",
            ],
            "stat": [
                "📊 El 78% de los compradores inician su búsqueda online.",
                "🏘️ Castelldefels: precio medio €2.400/m² · Rentabilidad 4.2%",
                "⏰ Las propiedades con tour virtual se venden un 31% más rápido.",
            ],
            "educational": [
                "💡 ¿Sabías que... la primera impresión de un piso se forma en los primeros 90 segundos?",
                "📋 5 documentos que necesitas antes de comprar tu vivienda.",
                "🏦 Tipo fijo vs variable en 2024: ¿cuál te conviene?",
            ],
            "case_study": [
                "✨ Caso real: Familia encontró su hogar en Castelldefels en solo 3 semanas.",
                "🏠 De la búsqueda a las llaves: cómo guiamos a Ana y Marc.",
            ],
            "cta": [
                "📞 ¿Buscas piso en Castelldefels o Gavà? Hablamos. 🏠",
                "🤝 Ruth Blanco — tu inmobiliaria de confianza. Llama al 639.101.451.",
                "🔑 Nuevas propiedades esta semana. ¿Vemos? 👇",
            ],
            "bts": [
                "🎬 Behind the scenes: visita en directo esta mañana ☀️",
                "📸 Preparando el tour virtual de hoy... ¡promete!",
            ],
        }

        return posts.get(estilo, ["[LISA] Publica contenido"])[0]

    def generar_calendario_contenido(self, semanas: int = 4) -> str:
        """Genera un calendario de contenido para las próximas semanas."""
        lineas = ["# 📅 Calendario de Contenidos — Ruth Inmobiliaria"]
        lineas.append(f"# Generado: {datetime.now().strftime('%d/%m/%Y')}\n")

        for w in range(semanas):
            lineas.append(f"\n## Semana {w + 1}")
            for dia in ["lunes", "martes", "miercoles", "jueves", "viernes", "sabado"]:
                post = self.generar_post_instagram(dia)
                lineas.append(f"  {dia.capitalize()}: {post}")

        return "\n".join(lineas)

    def execute(self, task: str) -> str:
        """Punto de entrada principal."""
        task_lower = task.lower()

        if "reel" in task_lower or "video" in task_lower:
            return (
                "LISA prepara el Reel. Necesito los datos de la propiedad:\n"
                "- Tipo (piso, casa, ático)\n"
                "- Zona (Castelldefels, Gavà...)\n"
                "- Precio y habitaciones\n"
                "¿Los tienes?"
            )

        elif "post" in task_lower or "instagram" in task_lower:
            return self.generar_post_instagram("auto")

        elif "calendario" in task_lower:
            return self.generar_calendario_contenido()

        elif "voz" in task_lower or "audio" in task_lower:
            return "LISA puede generar voz. Indica el texto y te lo convierto."

        elif "clone" in task_lower:
            if "AQUI" in self.eleven_api_key:
                return "⚠️ ElevenLabs no configurado. Se puede usar edge-tts gratis."
            return "LISA prepara clones de voz. Envíame el texto y la voz deseada."

        else:
            return (
                f"[LISA] Soy la agente de marketing de Ruth. "
                f"Creo Reels, posts para Instagram, clones de voz y contenido audiovisual. "
                f"¿Qué necesitas hoy?"
            )