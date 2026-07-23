"""
ANI - Agente de Formularios de Ruth Inmobiliaria
Rellena formularios en Inmovilla, GHL, CRM y plataformas externas.
"""
import os
import json
import requests
from datetime import datetime

BASE_DIR = os.environ.get("DATA_DIR", os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
CONFIG_FILE = os.path.join(BASE_DIR, "config", "config.json")


def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


CONFIG = load_config()


class ANIAgent:
    """Agente ANI: Rellena formularios y CRMs para Ruth."""

    def __init__(self):
        self.config = load_config()
        self.ghl_api_key = self.config.get("GHL_API_KEY", "")
        self.ghl_location_id = self.config.get("GHL_LOCATION_ID", "")
        self.inmovilla_api_key = self.config.get("INMOVILLA_API_KEY", "")

    def _check_config(self, service: str) -> bool:
        """Verifica que haya API key para el servicio."""
        if "AQUI" in self.ghl_api_key or "AQUI" in self.inmovilla_api_key:
            return False
        return True

    # ── GoHighLevel (GHL) ──────────────────────────────────

    def crear_contacto_ghl(self, datos: dict) -> dict:
        """Crea un contacto en GoHighLevel."""
        if not self._check_config("ghl"):
            return {"error": "Falta GHL_API_KEY en config.json"}

        try:
            url = f"https://services.leadconnectorhq.com/contacts/"
            headers = {
                "Authorization": f"Bearer {self.ghl_api_key}",
                "Content-Type": "application/json",
                "Version": "2021-07-28",
            }
            payload = {
                "firstName": datos.get("nombre", ""),
                "lastName": datos.get("apellido", ""),
                "email": datos.get("email", ""),
                "phone": datos.get("telefono", ""),
                "locationId": self.ghl_location_id,
                "address": datos.get("direccion", ""),
                "customFields": datos.get("campos_extra", {}),
            }
            resp = requests.post(url, json=payload, headers=headers, timeout=15)
            return {"status": resp.status_code, "data": resp.json()}
        except Exception as e:
            return {"error": str(e)}

    def crear_opportunidad_ghl(self, datos: dict) -> dict:
        """Crea una oportunidad en GHL pipeline."""
        if not self._check_config("ghl"):
            return {"error": "Falta GHL_API_KEY en config.json"}

        try:
            url = f"https://services.leadconnectorhq.com/opportunities/"
            headers = {
                "Authorization": f"Bearer {self.ghl_api_key}",
                "Content-Type": "application/json",
                "Version": "2021-07-28",
            }
            payload = {
                "name": datos.get("nombre", "Nueva oportunidad"),
                "contactId": datos.get("contact_id", ""),
                "pipelineId": datos.get("pipeline_id", ""),
                "stageId": datos.get("stage_id", ""),
                "locationId": self.ghl_location_id,
                "monetaryValue": datos.get("valor", 0),
                "source": datos.get("fuente", "Web"),
            }
            resp = requests.post(url, json=payload, headers=headers, timeout=15)
            return {"status": resp.status_code, "data": resp.json()}
        except Exception as e:
            return {"error": str(e)}

    def buscar_contacto_ghl(self, nombre: str) -> dict:
        """Busca un contacto en GHL por nombre."""
        if not self._check_config("ghl"):
            return {"error": "Falta GHL_API_KEY en config.json"}

        try:
            url = f"https://services.leadconnectorhq.com/contacts/search"
            headers = {
                "Authorization": f"Bearer {self.ghl_api_key}",
                "Version": "2021-07-28",
            }
            params = {"locationId": self.ghl_location_id, "query": nombre}
            resp = requests.get(url, headers=headers, params=params, timeout=15)
            return {"status": resp.status_code, "data": resp.json()}
        except Exception as e:
            return {"error": str(e)}

    # ── Inmovilla ───────────────────────────────────────────

    def subir_propiedad_inmovilla(self, datos: dict) -> dict:
        """Sube una propiedad a Inmovilla."""
        if not self._check_config("inmovilla"):
            return {"error": "Falta INMOVILLA_API_KEY en config.json"}

        try:
            url = "https://api.inmovilla.com/v2/properties"
            headers = {
                "Authorization": f"Bearer {self.inmovilla_api_key}",
                "Content-Type": "application/json",
            }
            payload = {
                "title": datos.get("titulo", ""),
                "price": datos.get("precio", 0),
                "location": datos.get("ubicacion", ""),
                "type": datos.get("tipo", "piso"),
                "rooms": datos.get("habitaciones", 0),
                "bathrooms": datos.get("banos", 0),
                "area": datos.get("superficie", 0),
                "description": datos.get("descripcion", ""),
                "images": datos.get("imagenes", []),
            }
            resp = requests.post(url, json=payload, headers=headers, timeout=15)
            return {"status": resp.status_code, "data": resp.json()}
        except Exception as e:
            return {"error": str(e)}

    def actualizar_propiedad_inmovilla(self, propiedad_id: str, datos: dict) -> dict:
        """Actualiza una propiedad existente en Inmovilla."""
        if not self._check_config("inmovilla"):
            return {"error": "Falta INMOVILLA_API_KEY en config.json"}

        try:
            url = f"https://api.inmovilla.com/v2/properties/{propiedad_id}"
            headers = {
                "Authorization": f"Bearer {self.inmovilla_api_key}",
                "Content-Type": "application/json",
            }
            resp = requests.put(url, json=datos, headers=headers, timeout=15)
            return {"status": resp.status_code, "data": resp.json()}
        except Exception as e:
            return {"error": str(e)}

    def listar_propiedades_inmovilla(self) -> dict:
        """Lista las propiedades activas en Inmovilla."""
        if not self._check_config("inmovilla"):
            return {"error": "Falta INMOVILLA_API_KEY en config.json"}

        try:
            url = "https://api.inmovilla.com/v2/properties"
            headers = {
                "Authorization": f"Bearer {self.inmovilla_api_key}",
            }
            params = {"status": "active", "limit": 100}
            resp = requests.get(url, headers=headers, params=params, timeout=15)
            return {"status": resp.status_code, "data": resp.json()}
        except Exception as e:
            return {"error": str(e)}

    # ── Generar formulario como HTML ───────────────────────

    def generar_formulario_html(self, campos: list, titulo: str = "Formulario") -> str:
        """Genera un formulario HTML rellenable."""
        html = f"<h2>{titulo}</h2><form>\n"
        for campo in campos:
            nombre = campo.get("nombre", "")
            tipo = campo.get("tipo", "text")
            obligatorio = "required" if campo.get("obligatorio") else ""
            html += (
                f'<label>{nombre}:</label><br>'
                f'<input type="{tipo}" name="{nombre}" {obligatorio}><br><br>\n'
            )
        html += '<button type="submit">Enviar</button></form>'
        return html

    def execute(self, task: str) -> str:
        """Punto de entrada principal."""
        task_lower = task.lower()

        if "listar" in task_lower and "propiedad" in task_lower:
            result = self.listar_propiedades_inmovilla()
            if "error" in result:
                return f"⚠️ {result['error']}"
            return f"Propiedades en Inmovilla: {json.dumps(result, indent=2, ensure_ascii=False)[:2000]}"

        # --- BLOQUEO DE SEGURIDAD ESTRICTO PARA MODIFICACIONES ---
        es_modificacion = any(palabra in task_lower for palabra in ["crear", "subir", "actualizar", "borrar", "eliminar", "modificar", "contacto", "oportunidad", "pipeline", "propiedad"])
        if es_modificacion and "listar" not in task_lower and "buscar" not in task_lower:
            if "autorización expresa confirmada" not in task_lower and "autorizacion expresa confirmada" not in task_lower:
                return "🛑 **BLOQUEO DE SEGURIDAD ACTIVADO**: No tienes permiso para borrar, modificar ni añadir datos en Inmovilla o GHL. Para ejecutar esta acción, debes incluir exactamente la frase 'autorización expresa confirmada' en tu orden."

        if "contacto" in task_lower and ("ghl" in task_lower or "crm" in task_lower):
            return "ANI necesita los datos del contacto (nombre, email, telefono). Enviamelos y los creo en GHL."

        elif "oportunidad" in task_lower or "pipeline" in task_lower:
            if not self._check_config("ghl"):
                return "⚠️ Falta GHL_API_KEY. Configuralo en config.json."
            return "ANI necesita los datos de la oportunidad (nombre, pipeline, contacto). Enviamelos."

        elif "propiedad" in task_lower and "inmovilla" in task_lower:
            if not self._check_config("inmovilla"):
                return "⚠️ Falta INMOVILLA_API_KEY. Configuralo en config.json."
            return "ANI necesita los datos de la propiedad (titulo, precio, ubicacion, habitaciones, etc.). Enviamelos y la subo."

        elif "formulario" in task_lower:
            return "ANI genera formularios HTML. Indica que campos necesitas."


        else:
            return f"[ANI] Soy la agente de formularios. Trabajo con GHL, Inmovilla y genero formularios web. Que necesitas? (API keys aun no configuradas)"