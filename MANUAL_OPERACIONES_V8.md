# 🏰 ARQUITECTURA MAESTRA Y REQUISITOS MÍNIMOS: RUTH INMOBILIARIA

Este documento es la **fuente única de verdad** para cualquier IA o desarrollador que trabaje en el proyecto de Ruth Inmobiliaria. Define los requisitos mínimos, la infraestructura aislada y las funciones estrictas de cada agente.

---

## 1. INFRAESTRUCTURA LOCAL HÍBRIDA (CERO CAÍDAS DE SERVIDOR)
Ruth Inmobiliaria operará bajo un modelo **Local + Cloudflare**, eliminando el estrés de mantener servidores externos (nada de PM2 o Contabo cayéndose):
*   **Instalación Local:** El "cerebro" (Python, LangGraph) se instala en el PC principal de la oficina de Ruth. Al usar OpenRouter para la IA, el programa es hiper-ligero y no ralentiza el ordenador.
*   **Acceso Móvil (Cloudflare Tunnel):** Se crea un túnel seguro gratuito. Ruth podrá entrar a su Dashboard desde su iPhone o portátil como si fuera una web normal, siempre y cuando el PC de la oficina esté encendido.
*   **Supabase Propio:** Base de datos independiente en la nube para su memoria y clientes (Cero mantenimiento local).
*   **Composio Propio:** Cuenta independiente para gestionar sus integraciones (Gmail, Inmovilla, etc.).
*   **GoHighLevel (GHL):** Subcuenta propia dentro del sistema.
*   **OpenRouter / LLMs:** API key y facturación independiente.

---

## 2. REGLAS DE SEGURIDAD INQUEBRANTABLES (CERO AUTONOMÍA CRÍTICA)
1.  **Prohibido Borrar o Sobrescribir:** Ningún agente tiene permiso para borrar archivos originales ni sobrescribir plantillas base (ej. Contratos). Todo documento modificado se guarda como un archivo *nuevo*.
2.  **Aprobación Humana Obligatoria (Drafts):** 
    *   Los correos electrónicos redactados por la IA van a "Borradores" (Drafts).
    *   Las publicaciones en redes sociales van a estado "Pendiente de Aprobación" en Mixpost/GHL.
    *   Las acciones en Inmovilla (rellenar formularios) requieren confirmación antes de darle a "Guardar".
3.  **Carpeta de Cuarentena:** Si se ordena borrar algo, la IA lo mueve a `IA_ELIMINAR_REVISAR`. Si se crea un documento, va a `IA_REVISAR_BORRADORES`.

---

## 3. EL ORGANIGRAMA LANGGRAPH (EL ENJAMBRE)

### 👑 ROY (El Orquestador)
*   **Motor:** Kimi 2.6 / Gemini Pro / DeepSeek V4 Pro.
*   **Función:** Recibe las órdenes de voz o texto de Ruth. Entiende el contexto, desglosa la tarea y la envía al agente correspondiente usando Grafos (LangGraph). Habla con los agentes y asegura que la orden se cumpla.

### 📁 Secretaria ZOE (Administración, Legal y Archivos)
*   **Misión:** Gestión de documentos internos y organización de la empresa.
*   **Funciones Mínimas:**
    1.  Mover archivos a las carpetas correctas según las órdenes de Ruth.
    2.  Buscar información en la carpeta `DOCUMENTACION_EMPRESA` (donde están las reglas y contratos).
    3.  **Gestión de Contratos:** Coger un contrato base, rellenarlo con los datos del cliente, e inyectar cláusulas específicas solicitadas por Ruth **sin alterar la plantilla original**.
    4.  Mandar documentos a la impresora remota.

### 📧 Gestora ANI (Comunicaciones, Inmovilla y GHL)
*   **Misión:** Las "manos" en el teclado para el software externo.
*   **Funciones Mínimas:**
    1.  Leer correos y redactar respuestas (guardadas en Borradores).
    2.  Entrar en Inmovilla (vía Composio/Browser) y rellenar fichas de clientes sin borrar datos antiguos.
    3.  Actualizar estados en GoHighLevel si se le pide.
    4.  Asesorar a Ruth sobre qué publicar basándose en el conocimiento de la empresa.

### 🎬 Publicista LISA (Marketing, Vídeo y Prospección Avanzada)
*   **Misión:** Generar impacto visual, autoridad de marca y encontrar clientes ocultos (Hemos unido Marketing y Búsqueda en una sola super-agente).
*   **Funciones Mínimas:**
    1.  **Fábrica de Vídeo:** Usar **fal.ai** para procesar los vídeos. Aplicar clones de voz y ropa. Generar el vídeo en Remotion y dejarlo en el PC para aprobación. Subirlo a Mixpost/GHL.
    2.  **Investigación de Competencia:** Analizar qué publican hoy las agencias en Castelldefels y proponer mejoras.
    3.  **Huella Digital Oculta:** Buscar rastros en internet de gente que necesita servicios inmobiliarios inminentes (búsqueda de mudanzas, herencias, valoraciones de pisos).

---
*Documento sellado y protegido. Cualquier IA que interactúe con el entorno de Ruth Inmobiliaria debe acatar estas reglas como directrices supremas.*
