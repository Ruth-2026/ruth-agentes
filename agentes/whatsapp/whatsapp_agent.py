"""
WHATSAPP - Agente de Mensajería de Ruth Inmobiliaria
Gestiona WhatsApp Business, avisos, agenda y comunicaciones.
"""
import os
import json
from datetime import datetime

BASE_DIR = r"D:\aplexgrow_antigravity\RUTH_INMOBILIARIA"
CONFIG_FILE = os.path.join(BASE_DIR, "config", "config.json")


def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


CONFIG = load_config()


class WhatsAppAgent:
    """Agente WHATSAPP: Gestión de mensajería WhatsApp Business."""

    def __init__(self):
        self.config = load_config()
        self.phone = self.config.get("WHATSAPP_PHONE", "+34604542760")

    def enviar_mensaje(self, telefono: str, mensaje: str) -> dict:
        """Envía un mensaje de WhatsApp (simulado sin API real)."""
        return {
            "status": "mock",
            "message": f"Mensaje a {telefono}: '{mensaje[:80]}...'",
            "nota": "API de WhatsApp no conectada. Se enviará cuando se configure.",
        }

    def crear_plantilla(self, nombre: str, cuerpo: str) -> dict:
        """Crea una plantilla de mensaje para WhatsApp Business API."""
        return {
            "nombre": nombre,
            "cuerpo": cuerpo,
            "status": "mock",
            "nota": "Requiere WhatsApp Business API para envío real",
        }

    def generar_aviso_visita(self, datos: dict) -> str:
        """Genera un aviso de visita para el propietario."""
        propiedad = datos.get("propiedad", "la propiedad")
        fecha = datos.get("fecha", "por confirmar")
        cliente = datos.get("cliente", "un cliente")
        telefono = datos.get("telefono", "")

        mensaje = (
            f"📋 Nueva visita agendada\n"
            f"🏠 Propiedad: {propiedad}\n"
            f"🗓️ Fecha: {fecha}\n"
            f"👤 Cliente: {cliente}\n"
            f"📞 Teléfono: {telefono}\n\n"
            f"¿Confirma la visita? Responder SÍ o NO."
        )
        return mensaje

    def generar_seguimiento(self, datos: dict) -> str:
        """Genera un mensaje de seguimiento post-visita."""
        cliente = datos.get("cliente", "")
        propiedad = datos.get("propiedad", "")
        interes = datos.get("nivel_interes", "medio")

        if interes == "alto":
            mensaje = (
                f"Hola {cliente}, ¿qué tal te pareció {propiedad}?\n"
                f"Si te ha gustado, podemos agendar una segunda visita o "
                f"hablar sobre las condiciones. 🏠\n"
                f"Un saludo, Ruth Blanco — Inmobiliaria Castelldefels"
            )
        elif interes == "bajo":
            mensaje = (
                f"Hola {cliente}, gracias por tu tiempo.\n"
                f"Te envío por WhatsApp las fotos y datos de otras propiedades "
                f"que podrían interesarte. ¡Mantengamos el contacto! 🏡\n"
                f"— Ruth Blanco"
            )
        else:
            mensaje = (
                f"Gracias por visitar {propiedad}, {cliente}.\n"
                f"¿Tienes alguna pregunta? Estoy aquí para ayudarte. 😊\n"
                f"— Ruth Blanco · 639.101.451"
            )

        return mensaje

    def gestionar_agenda(self, accion: str, datos: dict = None) -> str:
        """Gestiona la agenda de visitas."""
        agenda_file = os.path.join(BASE_DIR, "output", "agenda.json")
        os.makedirs(os.path.dirname(agenda_file), exist_ok=True)

        if not os.path.exists(agenda_file):
            with open(agenda_file, "w") as f:
                json.dump([], f)

        with open(agenda_file, "r") as f:
            agenda = json.load(f)

        if accion == "ver":
            if not agenda:
                return "📅 Agenda vacía. No hay visitas programadas."
            resultado = "📅 Próximas visitas:\n"
            for i, visita in enumerate(agenda[-10:], 1):
                resultado += (
                    f"  {i}. {visita.get('fecha', '?')} - {visita.get('propiedad', '?')} "
                    f"({visita.get('cliente', 'sin nombre')})\n"
                )
            return resultado

        elif accion == "add" and datos:
            agenda.append({
                **datos,
                "registrada": datetime.now().isoformat(),
            })
            with open(agenda_file, "w") as f:
                json.dump(agenda, f, indent=2, ensure_ascii=False)
            return f"✅ Visita añadida: {datos.get('fecha', '?')} - {datos.get('propiedad', '?')}"

        return "Indica la acción: ver, add con datos (fecha, propiedad, cliente, telefono)"

    def generar_respuesta_automatica(self, mensaje: str) -> str:
        """Genera una respuesta automática para WhatsApp."""
        hora = datetime.now().hour

        if hora < 9 or hora >= 21:
            return (
                "Gracias por tu mensaje 🏡\n"
                "Nuestro horario de atención es de 9:00 a 21:00.\n"
                "Te responderemos lo antes posible.\n"
                "— Ruth Blanco · Castelldefels · 639.101.451"
            )

        respuestas_rapidas = {
            "hola": "¡Hola! 👋 Soy Ruth Blanco, tu inmobiliaria en Castelldefels y Gavà. ¿En qué puedo ayudarte?",
            "precio": "¿Te refieres a alguna propiedad en concreto? Envíame el nombre o zona y te paso los detalles 💰",
            "visita": "¡Genial! ¿Qué día y hora te vendría bien? Te confirmo enseguida 🗓️",
            "info": "Claro, ¿qué información necesitas sobre la propiedad? Zona, precio, metros cuadrados...",
        }

        for clave, respuesta in respuestas_rapidas.items():
            if clave in mensaje.lower():
                return respuesta

        return (
            "Gracias por tu mensaje 🙏\n"
            "Estoy preparando la información para ti. "
            "¿Podrías indicarme qué propiedad o zona te interesa?\n"
            "— Ruth Blanco · 639.101.451"
        )

    def execute(self, task: str) -> str:
        """Punto de entrada principal."""
        task_lower = task.lower()

        if "enviar" in task_lower:
            return "WHATSAPP necesita el número de teléfono y el mensaje. Envíamelos."

        elif "agenda" in task_lower:
            if "añadir" in task_lower or "add" in task_lower:
                return "Indica fecha, propiedad, cliente y teléfono para añadir a la agenda."
            return self.gestionar_agenda("ver")

        elif "aviso" in task_lower or "visita" in task_lower:
            return "WHATSAPP prepara el aviso. Envíame los datos: propiedad, fecha, cliente, teléfono."

        elif "seguimiento" in task_lower:
            return "Necesito: nombre del cliente, propiedad y nivel de interés (alto/medio/bajo)."

        elif "respuesta" in task_lower or "auto" in task_lower:
            return "WHATSAPP puede generar respuestas automáticas. Envíame el mensaje del cliente."

        else:
            return (
                f"[WHATSAPP] Gestiono WhatsApp de Ruth: avisos, agenda, seguimientos y respuestas.\n"
                f"Teléfono configurado: {self.phone}\n"
                f"¿Qué necesitas?"
            )