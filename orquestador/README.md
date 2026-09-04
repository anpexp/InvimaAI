# Orquestador Principal + Dashboard (Dev 1) — Hackatón INVIMA del Futuro

Human-in-the-Loop: la IA propone, el evaluador humano aprueba, modifica o
rechaza. Este panel no reemplaza al evaluador ni su responsabilidad.

## Agente 1 (Legal)

`../Agente1` es ahora un microservicio real (`POST /analyze/legal`) que
respeta el mismo contrato de salida que los Agentes 2 y 3. El orquestador
le apunta por defecto en `AGENTE1_URL=http://localhost:8001/analyze/legal`.
Si el servicio no responde (o se deja `AGENTE1_URL` vacío a propósito),
`orchestrator.py` degrada con gracia a hallazgos **simulados** para
`AGENTE_1_LEGAL` (ver `mock_dossiers.py::hallazgos_agente1_legal_mock`) en
vez de fallar toda la petición.

## Correr todo localmente (sin Docker)

En 4 terminales distintas, desde la raíz del repo:

```bash
# Terminal 1 — Agente 1 (Legal)
cd Agente1 && pip install -r requirements.txt
uvicorn agent_legal:app --reload --port 8001

# Terminal 2 — Agente 2 (Reliance)
cd agente2_reliance && pip install -r requirements.txt
uvicorn main:app --reload --port 8002

# Terminal 3 — Agente 3 (Clínico)
cd agente3_clinico && pip install -r requirements.txt
uvicorn main:app --reload --port 8003

# Terminal 4 — Orquestador
cd orquestador && pip install -r requirements.txt
cp .env.example .env
uvicorn orchestrator:app --reload --port 8080
```

Y en una quinta terminal, el dashboard:

```bash
cd orquestador
streamlit run app.py
```

Abrir `http://localhost:8501`, elegir un rol en la barra lateral y pulsar
**"Ejecutar orquestación"**. El expediente de demo ya viene precargado
(`2026-REG-CRZ-001784`, caso CORAZILIMAB) para que los 3 agentes
respondan con hallazgos reales de inmediato.

Si algún agente no está corriendo, el orquestador degrada con gracia:
muestra igual los hallazgos de los agentes disponibles y marca el agente
caído como no disponible en la barra lateral, en vez de fallar toda la
petición.

## Endpoints del Orquestador

- `POST /orquestador/analizar` — `{expediente_id, tipo_producto, rol_evaluador}` → llama a los 3 agentes en paralelo, consolida en la matriz temporal en memoria y devuelve los hallazgos filtrados por rol, más `antecedentes_historicos` y `resumen_expediente` (ver abajo).
- `GET /orquestador/matriz/{expediente_id}?rol_evaluador=...` — relee la matriz ya consolidada (sin volver a llamar a los agentes); usado al cambiar de rol o tras una decisión HITL.
- `POST /orquestador/hallazgo/decision` — registra la decisión humana (`APROBAR` / `MODIFICAR` / `RECHAZAR`) sobre un hallazgo puntual.
- `GET /orquestador/informe/{expediente_id}` — hallazgos aprobados o modificados por un evaluador humano (el único contenido que debería salir en un informe real).
- `GET /orquestador/panel` — **clasificar y priorizar trámites**: un resumen por expediente (prioridad ALTA/MEDIA/BAJA, si está completo, qué información falta), ordenado por prioridad.
- `GET /orquestador/antecedentes/{expediente_id}` — **Memoria Transversal**: expedientes anteriores relacionados (mismo producto o misma entidad responsable), sin volver a ejecutar la orquestación.
- `POST /orquestador/consultar` — `{expediente_id, tipo_producto, pregunta}` → **barra de consulta del dossier**: responde una pregunta libre citando el `documento_id`/folio exactos (ver abajo).

## Barra de consulta del dossier (`consulta_dossier.py` + `corpus_documental.py`)

Pregunta libre en lenguaje natural sobre el expediente, respondida con
citas al documento real (nunca inventadas). `corpus_documental.py`
reutiliza los mismos payloads que ya se envían a los Agentes 1, 2 y 3
(ver `mock_dossiers.py`) para armar un corpus citable único; con
`GEMINI_API_KEY` configurada, Gemini responde con grounding estricto
sobre ese corpus (system prompt exige citar `[documento_id, folio]` en
cada afirmación, y prohíbe inventar datos o emitir una decisión
regulatoria). Sin la clave, o si la llamada falla, degrada a un buscador
heurístico por palabras clave que cita el fragmento más relacionado tal
cual — nunca genera texto nuevo sin evidencia. Probado end-to-end con una
clave real: ver ejemplo en el README raíz.

Disponible en ambos dashboards (pestaña "Consulta" en React, sección
"🔎 Pregúntele al dossier" en Streamlit).

## Memoria Transversal (`memoria_transversal.py`)

Cruza el expediente que se está evaluando con expedientes YA procesados
para el mismo producto o la misma entidad responsable — resuelve la
demora de búsqueda de contexto histórico mencionada en el encargo
original. No es una base de datos vectorial de terceros: es un almacén
propio persistido en `orquestador/memoria_transversal.json` (se crea
solo, no versionar). Cada `POST /orquestador/analizar` registra el
expediente en la memoria y devuelve los antecedentes encontrados en
`antecedentes_historicos`. Para forzar un estado limpio en el demo,
borrar ese archivo (o usar `MEMORIA_TRANSVERSAL_PATH` para apuntar a
otro).

## `tipo_producto` afecta reglas reales, no solo se muestra

- **Agente 1**: biológicos/vacunas exigen `CERTIFICADO_LOTE` adicional
  (y vacunas también `CERTIFICADO_CADENA_FRIO`); la ventana de alerta de
  vigencia sube de 90 a 120 días.
- **Agente 2**: una discrepancia de almacenamiento entre módulos es
  `ALTO` (no `MEDIO`) para biológicos/vacunas, por cadena de frío.
- **Agente 3**: el umbral de soporte de una afirmación clínica sube de
  0.15 a 0.22 para biológicos/vacunas (más escrutinio).
