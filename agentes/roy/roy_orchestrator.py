"""
ROY - Orquestador Principal (LangGraph)
Coordina todos los agentes de Ruth Inmobiliaria.
"""
import os
import json
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI

# --- CONFIGURACIÓN ---
BASE_DIR = r"D:\aplexgrow_antigravity\RUTH_INMOBILIARIA"
CONFIG_FILE = os.path.join(BASE_DIR, "config", "config.json")

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

CONFIG = load_config()

def _get_api_key():
    return os.environ.get("OPENROUTER_API_KEY") or CONFIG.get("OPENROUTER_API_KEY", "")

def _get_base_url():
    return os.environ.get("OPENROUTER_BASE_URL") or CONFIG.get("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")

def _get_model():
    return os.environ.get("MODEL") or CONFIG.get("MODEL", "deepseek/deepseek-v4-flash")

# --- ESTADO DEL GRAFO ---
from typing import TypedDict

class AgentState(TypedDict):
    task: str
    agent: str
    result: str
    next_agent: str
    error: str

# --- LLM ---
def get_llm():
    return ChatOpenAI(
        model=_get_model(),
        openai_api_key=_get_api_key(),
        openai_api_base=_get_base_url(),
        temperature=0.3,
        max_tokens=2048,
    )

# --- PROMPT DEL ORQUESTADOR ---
ROY_SYSTEM = """
Eres ROY, el orquestador de los agentes de Ruth Inmobiliaria (RB Inmobiliaria).
Tu trabajo es analizar la orden de Ruth y decidir que agente debe ejecutarla.

AGENTES DISPONIBLES:
- ZOE: Secretaria. Documentos, contratos, facturas, base de conocimiento, informes.
- ANI: Formularios. Rellena Inmovilla y GHL.
- LISA: Marketing. Clones de voz/ropa, Reels, contenido redes sociales.
- NEO: Radar. Busca particulares vendiendo pisos, captacion clientes, senales de venta.
- WHATSAPP: Gestiona WhatsApp, avisos, agenda.

REGLAS:
1. Responde SOLO en formato JSON: {"agent": "NOMBRE_AGENTE", "task": "descripcion de la tarea"}
2. Si la orden no tiene sentido, responde: {"agent": "NONE", "task": "No entendi la orden."}
3. Si Ruth pregunta algo sobre su empresa/documentos, asigna a ZOE.
4. Si Ruth pide buscar clientes o propiedades, asigna a NEO.
5. Si Ruth pide hacer un documento o contrato, asigna a ZOE.
6. Si Ruth pide rellenar Inmovilla o GHL, asigna a ANI.
7. Si Ruth pide contenido de marketing o clones, asigna a LISA.
8. Si Ruth pide gestionar WhatsApp, agenda o avisos, asigna a WHATSAPP.
"""

def roy_node(state):
    llm = get_llm()
    response = llm.invoke([
        {"role": "system", "content": ROY_SYSTEM},
        {"role": "user", "content": state["task"]}
    ])
    try:
        clean = response.content.replace("```json", "").replace("```", "").strip()
        decision = json.loads(clean)
        state["agent"] = decision.get("agent", "NONE")
        state["task"] = decision.get("task", "")
        state["next_agent"] = state["agent"]
    except Exception as e:
        state["agent"] = "NONE"
        state["error"] = f"ROY no pudo decidir: {e}"
        state["next_agent"] = "END"
    return state

def zoe_node(state):
    from agentes.zoe import ZOEAgent
    agent = ZOEAgent()
    state["result"] = agent.execute(state["task"])
    state["next_agent"] = "END"
    return state

def ani_node(state):
    from agentes.ani import ANIAgent
    agent = ANIAgent()
    state["result"] = agent.execute(state["task"])
    state["next_agent"] = "END"
    return state

def lisa_node(state):
    from agentes.lisa import LISAAgent
    agent = LISAAgent()
    state["result"] = agent.execute(state["task"])
    state["next_agent"] = "END"
    return state

def neo_node(state):
    from agentes.neo import NEOAgent
    agent = NEOAgent()
    state["result"] = agent.execute(state["task"])
    state["next_agent"] = "END"
    return state

def whatsapp_node(state):
    from agentes.whatsapp import WhatsAppAgent
    agent = WhatsAppAgent()
    state["result"] = agent.execute(state["task"])
    state["next_agent"] = "END"
    return state

# --- CONSTRUCCIÓN DEL GRAFO ---
def build_graph():
    graph = StateGraph(AgentState)
    graph.add_node("roy", roy_node)
    graph.add_node("zoe", zoe_node)
    graph.add_node("ani", ani_node)
    graph.add_node("lisa", lisa_node)
    graph.add_node("neo", neo_node)
    graph.add_node("whatsapp", whatsapp_node)

    graph.set_entry_point("roy")

    def route(state):
        agent = state.get("next_agent", "END")
        if agent in ["ZOE", "ANI", "LISA", "NEO", "WHATSAPP"]:
            return agent.lower()
        return "END"

    graph.add_conditional_edges("roy", route)
    for agent in ["zoe", "ani", "lisa", "neo", "whatsapp"]:
        graph.add_edge(agent, END)

    return graph.compile()

# --- EJECUCIÓN ---
def run(task):
    app = build_graph()
    initial_state = AgentState(task=task, agent="", result="", next_agent="", error="")
    final_state = app.invoke(initial_state)
    return final_state.get("result", "No se obtuvo resultado.")

if __name__ == "__main__":
    import sys
    task = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else input("Orden para Ruth: ")
    print(run(task))