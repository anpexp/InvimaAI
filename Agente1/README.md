# Agente 1: Legal y Triaje (Módulo 1) — Hackatón INVIMA del Futuro

Automatiza tareas de bajo riesgo del Módulo 1 (Legal/Administrativo):
inventario documental, validación de integridad, extracción de metadatos
y control de vigencias de certificados (BPM/CPP/Poderes). **Nunca emite
una decisión final** — cada hallazgo trae su propia
`accion_sugerida_evaluador` para que el evaluador humano decida.

## Correr localmente (sin Docker)

```bash
cd Agente1
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # opcional: sin GEMINI_API_KEY usa el modo heurístico
uvicorn agent_legal:app --reload --port 8001
```

```bash
curl -X POST http://127.0.0.1:8001/analyze/legal \
  -H "Content-Type: application/json" \
  -d @sample_input.json
```

`sample_input.json` trae 3 documentos del Módulo 1 (Formulario, BPM, CPP)
de un caso CORAZILIMAB con 3 problemas deliberados para el demo:

- **Falta el Poder** de representación legal → hallazgo de completitud (ALTO).
- El fabricante del **BPM** no coincide con el declarado en el **Formulario** → hallazgo de coherencia de roles (ALTO).
- El **CPP** ya está vencido y el **BPM** vence en menos de 90 días → dos hallazgos de vigencia (ALTO y MEDIO).

## Correr con Docker

```bash
docker build -t invima-agente1 .
docker run --rm -p 8001:8001 --env-file .env invima-agente1
curl http://127.0.0.1:8001/health
```

## Extracción: Gemini o modo heurístico

`llm_client.py` extrae, por cada documento, principio activo,
concentración, titular, fabricante, importador y fecha de vigencia, con
el `SYSTEM_PROMPT` exacto exigido para evitar alucinaciones (no infiere
fechas ni roles faltantes; si no hay dato explícito, devuelve `null`).

- Con `GEMINI_API_KEY` configurada, usa Gemini (temperatura 0.0,
  `response_mime_type=application/json`).
- Sin la clave, usa un extractor heurístico determinista (regex) para que
  el demo sea reproducible sin red ni credenciales.

El texto de cada documento (`doc.texto`) se trata siempre como **dato de
solo lectura**: se entrega al modelo delimitado explícitamente con la
instrucción de ignorar cualquier instrucción que contenga, para
prevenir prompt injection desde un documento cargado por el solicitante.

## Lógica de negocio (`validation_rules.py`)

1. **Completitud** — exige `FORMULARIO_SOLICITUD`, `PODER`, `BPM` y `CPP`;
   si falta alguno, genera un hallazgo `ALTO` con `informacion_faltante`.
2. **Coherencia de roles** — compara el fabricante declarado en el
   formulario contra el reportado en el BPM.
3. **Vigencias** — compara cada fecha de vigencia extraída contra hoy:
   vencido → `ALTO`, vence en menos de 90 días → `MEDIO`, si no → `BAJO`.

## Integración con el Orquestador

El Orquestador (`../orquestador/orchestrator.py`) llama a este agente en
`AGENTE1_URL` (por defecto `http://localhost:8001/analyze/legal`). Si el
servicio no está disponible, el Orquestador degrada con gracia usando
hallazgos simulados en su lugar — ver `../orquestador/mock_dossiers.py`.
