"""
API REST de Agentes Ruth Inmobiliaria
Desplegada en Railway para acceso 24/7
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

    # Añadir historial si hay
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

        # Guardar conversación en Supabase
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

@app.route("/")
def home():
    return jsonify({
        "agente": "ZOE - Secretaria de Ruth Inmobiliaria",
        "estado": "activa",
        "endpoints": {
            "chat": "POST /zoe/chat  Body: {\"mensaje\": \"...\"}",
            "historial": "GET /zoe/historial?limite=10",
            "health": "GET /health",
        }
    })


@app.route("/health")
def health():
    return jsonify({
        "status": "ok",
        "agente": "ZOE",
        "supabase": bool(SUPABASE_URL and SUPABASE_KEY),
        "openrouter": bool(OPENROUTER_API_KEY and "AQUI" not in OPENROUTER_API_KEY),
        "timestamp": datetime.utcnow().isoformat(),
    })


@app.route("/zoe/chat", methods=["POST"])
def zoe_chat():
    """Endpoint principal para hablar con ZOE."""
    data = request.get_json(force=True)
    mensaje = data.get("mensaje", "").strip()
    if not mensaje:
        return jsonify({"error": "El campo 'mensaje' es obligatorio"}), 400

    # Obtener historial opcional
    historial = None
    h = data.get("historial")
    if h:
        historial = h[-10:]  # Últimas 10 conversaciones

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

    # POST: guardar en memoria
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


# ─── INICIO ───────────────────────────────────────────

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    logger.info(f"🟢 ZOE API iniciada en puerto {port}")
    app.run(host="0.0.0.0", port=port, debug=False)
