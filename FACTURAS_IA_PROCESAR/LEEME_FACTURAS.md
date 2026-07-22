# 🧾 PROTOCOLO DE PROCESAMIENTO DE FACTURAS (IA)

Este sistema permite a **Zia** automatizar la contabilidad básica de la inmobiliaria.

## ¿Cómo funciona?
1.  **Depósito:** Ruth deposita las facturas en PDF o imagen en esta carpeta (`RUTH_INMOBILIARIA/FACTURAS_IA_PROCESAR`).
2.  **Extracción:** La IA lee automáticamente:
    *   Emisor (Endesa, Telefónica, Proveedores, etc.).
    *   Base Imponible, IVA y Total.
    *   Fecha de vencimiento.
3.  **Registro:** Los datos se guardan en el "Cerebro" (Supabase) y se prepara un resumen mensual.
4.  **Alerta:** Si una factura es inusualmente alta o está cerca de vencer, Zia envía una alerta al Dashboard.

## Estado Actual
*   [X] Carpeta creada.
*   [ ] Integración con OCR completada.
*   [ ] Vinculación con panel de facturación en Dashboard.

---
*Zia: "Ruth, solo tienes que arrastrar el archivo aquí, yo me encargo del resto."*
