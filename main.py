"""
API REST de Agentes Ruth Inmobiliaria
Desplegada en Railway para acceso 24/7
Todos los agentes disponibles via endpoints REST.
"""
import os
import json
import sys
import logging
from datetime import datetime

from flask import Flask, request, jsonify
import requests

# Configurar logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# Añadir el directorio base al path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

# Cargar configuración desde variables de entorno (Railway) o config.json
def load_config():
    config = {}
    config_path = os.path.join(BASE_DIR, "config", "config.json")
    if os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
    # Las variables de entorno tienen prioridad (Railway)
    env_map = {
        "OPENROUTER_API_KEY": "OPENROUTER_API_KEY",
        "SUPABASE_URL": "SUPABASE_URL",
        "SUPABASE_KEY": "SUPABASE_KEY",
        "MODEL": "MODEL",
        "GHL_API_KEY": "GHL_API_KEY",
        "COMPOSIO_API_KEY": "COMPOSIO_API_KEY",
        "ELEVENLABS_API_KEY": "ELEVENLABS_API_KEY",
        "INMOVILLA_API_KEY": "INMOVILLA_API_KEY",
        "HEYGEN_API_KEY": "HEYGEN_API_KEY",
    }
    for env_key, config_key in env_map.items():
        if os.environ.get(env_key):
            config[config_key] = os.environ[env_key]
    return config

CONFIG = load_config()

app = Flask(__name__)


# ─── SUPABASE ────────────────────────────────────────

SUPABASE_URL = CONFIG.get("SUPABASE_URL", "")
SUPABASE_KEY = CONFIG.get("SUPABASE_KEY", "")
SUPABASE_HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=minimal",
}


def supabase_insert(table, data):
    """Inserta un registro en Supabase."""
    if not SUPABASE_URL or not SUPABASE_KEY:
        logger.warning("Supabase no configurado")
        return False
    try:
        url = f"{SUPABASE_URL}/rest/v1/{table}"
        resp = requests.post(url, headers=SUPABASE_HEADERS, json=data, timeout=10)
        if resp.status_code in (200, 201, 204):
            return True
        logger.warning(f"Supabase insert error {resp.status_code}: {resp.text}")
        return False
    except Exception as e:
        logger.error(f"Supabase insert exception: {e}")
        return False


def supabase_select(table, filters=None, limit=10):
    """Consulta registros en Supabase."""
    if not SUPABASE_URL or not SUPABASE_KEY:
        return []
    try:
        url = f"{SUPABASE_URL}/rest/v1/{table}"
        headers = {**SUPABASE_HEADERS, "Prefer": "count=exact"}
        params = {"limit": limit, "order": "timestamp.desc"}
        if filters:
            params.update(filters)
        resp = requests.get(url, headers=headers, params=params, timeout=10)
        if resp.status_code == 200:
            return resp.json()
        return []
    except Exception as e:
        logger.error(f"Supabase select exception: {e}")
        return []


# ─── ZOE (Secretaria) ─────────────────────────────────

OPENROUTER_API_KEY = CONFIG.get("OPENROUTER_API_KEY", "")
MODEL = CONFIG.get("MODEL", "deepseek/deepseek-v4-flash")


def zoe_responder(mensaje, historial=None):
    """Procesa un mensaje con ZOE via OpenRouter y guarda en Supabase."""
    if not OPENROUTER_API_KEY or "AQUI" in OPENROUTER_API_KEY:
        return "⚠️ ZOE no tiene conexión con la IA. Configura OPENROUTER_API_KEY."

    system_prompt = """Eres ZOE, la secretaria IA de Ruth Inmobiliaria (RB Inmobiliaria).
Trabajas para Ruth Blanco, agente inmobiliario en Castelldefels, Gavà y Viladecans.

TUS CAPACIDADES:
- Redactar contratos de alquiler y arras
- Generar facturas profesionales
- Leer y extraer información de PDFs y documentos
- Guardar y recuperar memoria (clientes, propiedades, etc.)
- Generar informes de mercado, actividad y resúmenes
- Responder preguntas sobre la empresa y sus procesos

INSTRUCCIONES:
- Eres PROFESIONAL pero CERCANA, como una secretaria de confianza
- Respuestas en español, claras y directas
- Si no sabes algo, dilo honestamente"""

    messages = [{"role": "system", "content": system_prompt}]

    if historial:
        for h in historial:
            messages.append({"role": "user", "content": h.get("mensaje", "")})
            if h.get("respuesta"):
                messages.append({"role": "assistant", "content": h["respuesta"]})

    messages.append({"role": "user", "content": mensaje})

    try:
        resp = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://ruthinmobiliaria.com",
            },
            json={
                "model": MODEL,
                "messages": messages,
                "temperature": 0.3,
                "max_tokens": 2048,
            },
            timeout=30,
        )

        if resp.status_code != 200:
            logger.error(f"OpenRouter error {resp.status_code}: {resp.text}")
            return f"❌ Error de conexión con la IA: {resp.status_code}"

        respuesta = resp.json()["choices"][0]["message"]["content"]

        supabase_insert("conversaciones", {
            "agente": "ZOE",
            "usuario": "Ruth",
            "mensaje": mensaje,
            "respuesta": respuesta,
            "timestamp": datetime.utcnow().isoformat(),
        })

        return respuesta

    except Exception as e:
        logger.error(f"ZOE error: {e}")
        return f"❌ Error: {e}"


# ─── ENDPOINTS API ────────────────────────────────────

AGENTS_INFO = {
    "zoe": {
        "name": "ZOE",
        "rol": "Secretaria IA",
        "descripcion": "Documentos, contratos, facturas, memoria, informes",
        "endpoints": {
            "chat": "POST /zoe/chat  Body: {\"mensaje\": \"...\"}",
            "historial": "GET /zoe/historial?limite=10",
            "memoria": "GET/POST /zoe/memoria",
        }
    },
    "ani": {
        "name": "ANI",
        "rol": "Formularios",
        "descripcion": "Rellena Inmovilla, GHL y CRMs automáticamente",
        "endpoints": {
            "ejecutar": "POST /ani/ejecutar  Body: {\"tarea\": \"...\"}",
            "contacto_ghl": "POST /ani/contacto-ghl",
            "oportunidad_ghl": "POST /ani/oportunidad-ghl",
            "propiedad_inmovilla": "POST /ani/propiedad-inmovilla",
        }
    },
    "lisa": {
        "name": "LISA",
        "rol": "Marketing",
        "descripcion": "Reels, clones de voz, contenido redes sociales",
        "endpoints": {
            "ejecutar": "POST /lisa/ejecutar  Body: {\"tarea\": \"...\"}",
            "script_reel": "POST /lisa/script-reel",
            "voz": "POST /lisa/voz",
            "post": "POST /lisa/post",
        }
    },
    "neo": {
        "name": "NEO",
        "rol": "Radar Inmobiliario",
        "descripcion": "Busca vendedores particulares en portales y redes",
        "endpoints": {
            "ejecutar": "POST /neo/ejecutar  Body: {\"tarea\": \"...\"}",
            "buscar": "POST /neo/buscar",
        }
    },
    "roy": {
        "name": "ROY",
        "rol": "Orquestador",
        "descripcion": "Coordina todos los agentes usando LangGraph",
        "endpoints": {
            "ejecutar": "POST /roy/ejecutar  Body: {\"tarea\": \"...\"}",
        }
    },
    "whatsapp": {
        "name": "WHATSAPP",
        "rol": "Mensajería",
        "descripcion": "WhatsApp Business, avisos, agenda, seguimientos",
        "endpoints": {
            "ejecutar": "POST /whatsapp/ejecutar  Body: {\"tarea\": \"...\"}",
            "enviar": "POST /whatsapp/enviar",
            "aviso_visita": "POST /whatsapp/aviso-visita",
        }
    },
}


@app.route("/")
def home():
    return jsonify({
        "agencia": "Ruth Inmobiliaria",
        "api": "Agentes IA 24/7",
        "version": "2.0",
        "agentes": {k: {"nombre": v["name"], "rol": v["rol"], "descripcion": v["descripcion"]} for k, v in AGENTS_INFO.items()},
        "health": "GET /health",
    })


@app.route("/health")
def health():
    return jsonify({
        "status": "ok",
        "version": "2.0",
        "supabase": bool(SUPABASE_URL and SUPABASE_KEY),
        "openrouter": bool(OPENROUTER_API_KEY and "AQUI" not in OPENROUTER_API_KEY),
        "agentes_disponibles": list(AGENTS_INFO.keys()),
        "timestamp": datetime.utcnow().isoformat(),
    })


# ═══════════════════════════════════════════════════════
# ZOE - Secretaria
# ═══════════════════════════════════════════════════════

@app.route("/zoe/chat", methods=["POST"])
def zoe_chat():
    """Endpoint principal para hablar con ZOE."""
    data = request.get_json(force=True)
    mensaje = data.get("mensaje", "").strip()
    if not mensaje:
        return jsonify({"error": "El campo 'mensaje' es obligatorio"}), 400

    historial = None
    h = data.get("historial")
    if h:
        historial = h[-10:]

    respuesta = zoe_responder(mensaje, historial)

    if respuesta.startswith("⚠️") or respuesta.startswith("❌"):
        return jsonify({"error": respuesta}), 500

    return jsonify({
        "agente": "ZOE",
        "mensaje": mensaje,
        "respuesta": respuesta,
        "timestamp": datetime.utcnow().isoformat(),
    })


@app.route("/zoe/historial", methods=["GET"])
def zoe_historial():
    """Obtiene el historial de conversaciones de ZOE."""
    limite = request.args.get("limite", 10, type=int)
    if limite > 50:
        limite = 50

    conversaciones = supabase_select("conversaciones", limit=limite)

    return jsonify({
        "agente": "ZOE",
        "total": len(conversaciones),
        "conversaciones": conversaciones,
    })


@app.route("/zoe/memoria", methods=["GET", "POST"])
def zoe_memoria():
    """Gestiona la memoria persistente de ZOE."""
    if request.method == "GET":
        agente = request.args.get("agente", "ZOE")
        data = supabase_select("memoria_agentes", {"agente": f"eq.{agente}"}, limit=50)
        return jsonify({"memoria": data})

    data = request.get_json(force=True)
    clave = data.get("clave", "").strip()
    valor = data.get("valor")
    if not clave:
        return jsonify({"error": "El campo 'clave' es obligatorio"}), 400

    ok = supabase_insert("memoria_agentes", {
        "agente": "ZOE",
        "clave": clave,
        "valor": valor,
        "updated_at": datetime.utcnow().isoformat(),
    })

    if ok:
        return jsonify({"status": "ok", "clave": clave, "guardado": True})
    return jsonify({"error": "No se pudo guardar en Supabase"}), 500


# ═══════════════════════════════════════════════════════
# ANI - Formularios
# ═══════════════════════════════════════════════════════

@app.route("/ani/ejecutar", methods=["POST"])
def ani_ejecutar():
    """Ejecuta una tarea en ANI."""
    try:
        from agentes.ani import ANIAgent
        agent = ANIAgent()
        data = request.get_json(force=True)
        tarea = data.get("tarea", "").strip()
        if not tarea:
            return jsonify({"error": "El campo 'tarea' es obligatorio"}), 400
        resultado = agent.execute(tarea)
        return jsonify({"agente": "ANI", "tarea": tarea, "resultado": resultado})
    except Exception as e:
        logger.error(f"ANI error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/ani/contacto-ghl", methods=["POST"])
def ani_contacto_ghl():
    """Crea un contacto en GoHighLevel."""
    try:
        from agentes.ani import ANIAgent
        agent = ANIAgent()
        data = request.get_json(force=True)
        resultado = agent.crear_contacto_ghl(data)
        return jsonify({"agente": "ANI", "accion": "crear_contacto_ghl", "resultado": resultado})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/ani/oportunidad-ghl", methods=["POST"])
def ani_oportunidad_ghl():
    """Crea una oportunidad en GHL."""
    try:
        from agentes.ani import ANIAgent
        agent = ANIAgent()
        data = request.get_json(force=True)
        resultado = agent.crear_opportunidad_ghl(data)
        return jsonify({"agente": "ANI", "accion": "crear_oportunidad_ghl", "resultado": resultado})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/ani/propiedad-inmovilla", methods=["POST"])
def ani_propiedad_inmovilla():
    """Sube una propiedad a Inmovilla."""
    try:
        from agentes.ani import ANIAgent
        agent = ANIAgent()
        data = request.get_json(force=True)
        resultado = agent.subir_propiedad_inmovilla(data)
        return jsonify({"agente": "ANI", "accion": "subir_propiedad_inmovilla", "resultado": resultado})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ═══════════════════════════════════════════════════════
# LISA - Marketing
# ═══════════════════════════════════════════════════════

@app.route("/lisa/ejecutar", methods=["POST"])
def lisa_ejecutar():
    """Ejecuta una tarea en LISA."""
    try:
        from agentes.lisa import LISAAgent
        agent = LISAAgent()
        data = request.get_json(force=True)
        tarea = data.get("tarea", "").strip()
        if not tarea:
            return jsonify({"error": "El campo 'tarea' es obligatorio"}), 400
        resultado = agent.execute(tarea)
        return jsonify({"agente": "LISA", "tarea": tarea, "resultado": resultado})
    except Exception as e:
        logger.error(f"LISA error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/lisa/script-reel", methods=["POST"])
def lisa_script_reel():
    """Genera un guion de Reel para una propiedad."""
    try:
        from agentes.lisa import LISAAgent
        agent = LISAAgent()
        data = request.get_json(force=True)
        resultado = agent.generar_script_reel(data)
        return jsonify({"agente": "LISA", "accion": "script_reel", "script": resultado})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/lisa/voz", methods=["POST"])
def lisa_voz():
    """Genera voz con ElevenLabs."""
    try:
        from agentes.lisa import LISAAgent
        agent = LISAAgent()
        data = request.get_json(force=True)
        texto = data.get("texto", "").strip()
        if not texto:
            return jsonify({"error": "El campo 'texto' es obligatorio"}), 400
        voz = data.get("voz", "es-ES-XimenaNeural")
        resultado = agent.generar_voz(texto, voz)
        return jsonify({"agente": "LISA", "accion": "generar_voz", "resultado": resultado})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/lisa/post", methods=["POST"])
def lisa_post():
    """Genera un post para Instagram."""
    try:
        from agentes.lisa import LISAAgent
        agent = LISAAgent()
        data = request.get_json(force=True)
        tipo = data.get("tipo", "venta")
        resultado = agent.generar_post_instagram(tipo, data)
        return jsonify({"agente": "LISA", "accion": "generar_post", "resultado": resultado})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ═══════════════════════════════════════════════════════
# NEO - Radar Inmobiliario
# ═══════════════════════════════════════════════════════

@app.route("/neo/ejecutar", methods=["POST"])
def neo_ejecutar():
    """Ejecuta una tarea en NEO."""
    try:
        from agentes.neo import NEOAgent
        agent = NEOAgent()
        data = request.get_json(force=True)
        tarea = data.get("tarea", "").strip()
        if not tarea:
            return jsonify({"error": "El campo 'tarea' es obligatorio"}), 400
        resultado = agent.execute(tarea)
        return jsonify({"agente": "NEO", "tarea": tarea, "resultado": resultado})
    except Exception as e:
        logger.error(f"NEO error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/neo/buscar", methods=["POST"])
def neo_buscar():
    """Busca propiedades en portales inmobiliarios."""
    try:
        from agentes.neo import NEOAgent
        agent = NEOAgent()
        data = request.get_json(force=True)
        zona = data.get("zona", "castelldefels")
        tipo = data.get("tipo", "venta")
        resultados_idealista = agent.buscar_idealista(zona, tipo)
        resultados_fotocasa = agent.buscar_fotocasa(zona)
        return jsonify({
            "agente": "NEO",
            "zona": zona,
            "idealista": resultados_idealista,
            "fotocasa": resultados_fotocasa,
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ═══════════════════════════════════════════════════════
# ROY - Orquestador (LangGraph)
# ═══════════════════════════════════════════════════════

@app.route("/roy/ejecutar", methods=["POST"])
def roy_ejecutar():
    """Ejecuta una orden a través del orquestador ROY (LangGraph)."""
    try:
        from agentes.roy import run
        data = request.get_json(force=True)
        tarea = data.get("tarea", "").strip()
        if not tarea:
            return jsonify({"error": "El campo 'tarea' es obligatorio"}), 400
        resultado = run(tarea)
        return jsonify({"agente": "ROY", "tarea": tarea, "resultado": resultado})
    except Exception as e:
        logger.error(f"ROY error: {e}")
        return jsonify({"error": str(e)}), 500


# ═══════════════════════════════════════════════════════
# WHATSAPP - Mensajería
# ═══════════════════════════════════════════════════════

@app.route("/whatsapp/ejecutar", methods=["POST"])
def whatsapp_ejecutar():
    """Ejecuta una tarea en WHATSAPP."""
    try:
        from agentes.whatsapp import WhatsAppAgent
        agent = WhatsAppAgent()
        data = request.get_json(force=True)
        tarea = data.get("tarea", "").strip()
        if not tarea:
            return jsonify({"error": "El campo 'tarea' es obligatorio"}), 400
        resultado = agent.execute(tarea)
        return jsonify({"agente": "WHATSAPP", "tarea": tarea, "resultado": resultado})
    except Exception as e:
        logger.error(f"WHATSAPP error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/whatsapp/enviar", methods=["POST"])
def whatsapp_enviar():
    """Envía un mensaje de WhatsApp."""
    try:
        from agentes.whatsapp import WhatsAppAgent
        agent = WhatsAppAgent()
        data = request.get_json(force=True)
        telefono = data.get("telefono", "").strip()
        mensaje = data.get("mensaje", "").strip()
        if not telefono or not mensaje:
            return jsonify({"error": "Los campos 'telefono' y 'mensaje' son obligatorios"}), 400
        resultado = agent.enviar_mensaje(telefono, mensaje)
        return jsonify({"agente": "WHATSAPP", "resultado": resultado})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/whatsapp/aviso-visita", methods=["POST"])
def whatsapp_aviso_visita():
    """Genera un aviso de visita para WhatsApp."""
    try:
        from agentes.whatsapp import WhatsAppAgent
        agent = WhatsAppAgent()
        data = request.get_json(force=True)
        resultado = agent.generar_aviso_visita(data)
        return jsonify({"agente": "WHATSAPP", "aviso": resultado})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ─── INICIO ───────────────────────────────────────────

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    logger.info(f"🟢 Ruth Agentes API iniciada en puerto {port}")
    logger.info(f"📋 Agentes disponibles: {', '.join(AGENTS_INFO.keys())}")
    app.run(host="0.0.0.0", port=port, debug=False)
