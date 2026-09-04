# Hackatón INVIMA del Futuro — Agentes 1, 2, 3 + Orquestador + Dashboards

Cinco piezas, cada una en su carpeta:

- **`Agente1/`** — Legal y Triaje (Módulo 1): completitud documental,
  coherencia de roles y vigencias de BPM/CPP/Poderes.
- **`agente2_reliance/`** — Reliance y Consistencia Transversal (M1/M3/M8).
- **`agente3_clinico/`** — Clínico: afirmaciones del Módulo 2 vs. evidencia primaria.
- **`orquestador/`** — Orquestador Principal + Dashboard HITL en Streamlit,
  consume los 3 agentes de arriba.
- **`invima-pathfinder/`** — Dashboard alterno en React (mockup "InvimaAI").
  El rol **Evaluador Técnico → pestaña INVAIA** llama de verdad al
  Orquestador y renderiza su matriz de hallazgos con el mismo flujo HITL
  (ver `src/lib/orquestador-api.ts` y `src/components/invima/HallazgosPanel.tsx`).
  También tiene una pestaña **"Consulta"**: barra de búsqueda libre sobre
  el dossier, respondida por Gemini con citas al documento real (ver
  `ConsultaDossier.tsx` y `orquestador/consulta_dossier.py`).

Los 3 agentes ya corren y devuelven el mismo JSON del contrato — lo que
falta es afinar la lógica con datos/reglas reales del caso que vayan a
presentar.

## Probar todo el programa con un solo comando

```bash
docker compose up --build
```

Levanta los 5 servicios en red:

| Servicio | URL |
|---|---|
| Agente 1 (Legal) | http://localhost:8001/docs |
| Agente 2 (Reliance) | http://localhost:8002/docs |
| Agente 3 (Clínico) | http://localhost:8003/docs |
| Orquestador (API) | http://localhost:8080/docs |
| Dashboard Streamlit | http://localhost:8501 |
| Dashboard React (InvimaAI) | http://localhost:5173 |

En el dashboard React: elegir rol **"Evaluador Técnico"** → pestaña
**"Evaluación"** → **"Abrir expediente"** en cualquier tarjeta → pestaña
**"INVAIA"** → **"Ejecutar orquestación"**. El expediente de demo usa
siempre el mismo caso CORAZILIMAB internamente (ver
`orquestador/mock_dossiers.py`), independientemente de qué tarjeta se
abra — es la carga documental simulada.

## Contrato de salida (no tocar los nombres de campo)

Los 3 agentes devuelven el mismo esquema `RespuestaAgente` con un array
`hallazgos[]`. El Orquestador itera sobre ese array sin importarle cuál
agente lo generó — por eso `agente_origen` existe.

## Correr cada agente localmente (sin Docker, para desarrollar rápido)

```bash
cd Agente1
pip install -r requirements.txt
uvicorn agent_legal:app --reload --port 8001

# en otra terminal
curl -X POST http://127.0.0.1:8001/analyze/legal \
  -H "Content-Type: application/json" \
  -d @sample_input.json
```

```bash
cd agente2_reliance
pip install -r requirements.txt
uvicorn main:app --reload --port 8002

# en otra terminal
curl -X POST http://127.0.0.1:8002/agente2/analizar \
  -H "Content-Type: application/json" \
  -d @sample_input.json
```

```bash
cd agente3_clinico
pip install -r requirements.txt
uvicorn main:app --reload --port 8003

curl -X POST http://127.0.0.1:8003/agente3/analizar \
  -H "Content-Type: application/json" \
  -d @sample_input.json
```

Y el Orquestador + Dashboard (ver `orquestador/README.md` para el detalle):

```bash
cd orquestador
pip install -r requirements.txt
uvicorn orchestrator:app --reload --port 8080
# en otra terminal
streamlit run app.py
```

Y el dashboard React (ver `invima-pathfinder/README.md` si existe, o la
sección de arriba):

```bash
cd invima-pathfinder
bun install   # o npm/pnpm si no tienen bun
cp .env.example .env
bun run dev
```

Para correr los 5 servicios juntos sin instalar nada localmente, usar
`docker compose up --build` (ver arriba).

## Qué ya está resuelto

**Orquestador — funciones que antes faltaban por completo:**
- **Memoria Transversal** (`orquestador/memoria_transversal.py`): cruza el
  expediente actual con expedientes ya evaluados del mismo producto o la
  misma entidad responsable, persistido a disco (no es Chroma/Pinecone,
  es un almacén propio JSON — lo que importa es la función, no la
  herramienta). Cada `POST /orquestador/analizar` devuelve
  `antecedentes_historicos`.
- **Clasificar y priorizar trámites**: `GET /orquestador/panel` lista
  todos los expedientes procesados con su prioridad (ALTA/MEDIA/BAJA) y
  si están completos.
- **Detectar expedientes incompletos**: cruza `informacion_faltante` de
  los 3 agentes + qué agentes respondieron, expuesto en
  `resumen_expediente` de cada análisis y en el panel.
- **Barra de consulta del dossier** (`POST /orquestador/consultar`):
  pregunta libre sobre el expediente, respondida citando el
  `documento_id`/folio exacto (Gemini con `GEMINI_API_KEY`, o buscador
  heurístico sin ella). Disponible en la pestaña "Consulta" (React) y en
  "🔎 Pregúntele al dossier" (Streamlit). Probado end-to-end con clave
  real: Gemini detecta la discrepancia de fabricante formulario-vs-BPM y
  la vigencia del CPP, citando ambos documentos.
- **`tipo_producto` ya cambia reglas reales** en los 3 agentes (antes era
  un campo decorativo que se guardaba pero no se usaba — ver detalle por
  agente abajo).

**Agente 1 (Legal y Triaje):**
- Extrae por documento (Formulario, Poder, BPM, CPP) principio activo,
  concentración, titular, fabricante, importador y fecha de vigencia, con
  el system prompt anti-alucinación exigido (nunca infiere fechas/roles
  faltantes; usa `null` si no está explícito).
- Con `GEMINI_API_KEY` usa Gemini (temperatura 0.0); sin ella, un
  extractor heurístico determinista (regex) para que el demo funcione sin
  red ni credenciales. `GEMINI_MODEL` por defecto es `gemini-flash-latest`
  (alias que Google mantiene apuntando al flash vigente — `gemini-1.5-flash`
  ya fue retirado y devuelve 404; si ven ese error, confirmen que
  `GEMINI_MODEL` no quedó fijado a una versión vieja en su `.env`).
- Valida completitud (documentos obligatorios faltantes — **más
  exigente para BIOLOGICO/VACUNA**: exige `CERTIFICADO_LOTE` y
  `CERTIFICADO_CADENA_FRIO`), coherencia de roles (fabricante,
  **titular e importador** transversal a todos los documentos, no solo
  formulario-vs-BPM) y vigencias tempranas (`< 90 días` para síntesis
  química, `< 120 días` para biológicos/vacunas). Probado end-to-end con
  `sample_input.json` y con Docker.
- Conectado al Orquestador vía `AGENTE1_URL` — ya no usa hallazgos
  simulados por defecto.

**Agente 2 (Reliance y Consistencia):**
- Compara nombre / concentración / condición de almacenamiento entre
  módulos (M1, M3, M8) y genera un `hallazgo` por cada discrepancia,
  siguiendo el mismo ejemplo del `CORAZILIMAB` que armaron en la reunión.
- Discrepancia de almacenamiento = riesgo **ALTO** (no MEDIO) para
  biológicos/vacunas, por sensibilidad de cadena de frío.
- Consulta openFDA por la molécula (sin API key). Si openFDA falla o no
  hay red, degrada con gracia — no tumba el request.
- Probado end-to-end con `sample_input.json` (trae 3 inconsistencias
  deliberadas para que se vea el caso "feo" en el demo).

**Agente 3 (Clínico):**
- Memoria mínima con TF-IDF (`rag_store.py`) — sin Chroma ni Pinecone,
  para no depender de infraestructura extra en 2+ horas.
- Compara cada afirmación del Módulo 2 contra la evidencia primaria
  (M3/M4/M5) y marca ALTO riesgo + `informacion_faltante` cuando NO hay
  soporte — en vez de inventar una respuesta. Umbral de soporte más
  estricto (0.22 vs. 0.15) para biológicos/vacunas.
- **Extracción estructurada de características del estudio**
  (`pico_extractor.py`): cuando una afirmación sí encuentra soporte,
  extrae diseño, N, población, comparador y desenlace del fragmento de
  evidencia (solo si están explícitos en el texto — nunca los infiere).
- `llm_client.py` tiene un gancho (`_evaluar_con_llm`) para conectar
  MedGemma/Gemini real si consiguen acceso durante el hackathon — el
  resto del agente no cambia. Sin llave configurada, usa el modo
  heurístico (TF-IDF) automáticamente.

**Dashboard React (`invima-pathfinder`):**
- La pestaña "INVAIA" del rol Evaluador Técnico ya no simula nada: llama
  de verdad a `POST /orquestador/analizar` y `GET /orquestador/matriz`.
- **Vista personalizada por especialidad**: antes mostraba los 3 agentes
  a la vez; ahora hay un selector Legal/Calidad/Clínico que filtra —
  igual que el dashboard Streamlit — y solo trae hallazgos del agente
  correspondiente.
- Muestra `resumen_expediente` (prioridad, completo/incompleto) y
  `antecedentes_historicos` (Memoria Transversal) de cada expediente.
- Probado end-to-end con Playwright contra los 5 servicios levantados por
  `docker compose up --build`.
- `VITE_ORQUESTADOR_URL` (ver `invima-pathfinder/.env.example`) apunta a
  `http://localhost:8080` porque el fetch corre en el navegador del
  usuario, no dentro del contenedor.

## Qué les falta decidir/ajustar

1. **Dossiers reales**: reemplacen `sample_input.json` por datos del caso
   que van a presentar en el demo (o mock más elaborado).
2. **Umbral de soporte** (`UMBRAL_SOPORTE` en `llm_client.py` del Agente 3):
   ajústenlo si con su dataset real quedan falsos positivos/negativos.
3. **Conexión real a MedGemma/Gemini** si el equipo consigue credenciales
   de Agent Platform — llenar `_evaluar_con_llm`.
4. ~~Confirmar con Dev 1 el puerto/URL exactos donde el Orquestador va a
   buscar cada agente~~ — resuelto: Agente 1 en `:8001`, Agente 2 en
   `:8002`, Agente 3 en `:8003` (ver `orquestador/.env.example`).

### Gaps de herramienta (no de funcionalidad) que siguen abiertos

Estos quedaron fuera a propósito en la última ronda porque son cambios de
*stack*, no de comportamiento — ver conversación de auditoría para el
detalle completo:

- Agent Platform / ADK (orquestador y Agente 1 corren en FastAPI plano).
- Document AI (los agentes reciben texto ya extraído; no hay ingesta de
  PDF/imagen real).
- Verificación de **firmas**: sigue sin implementarse — requiere análisis
  de imagen/documento, no solo texto.
- Google Antigravity / PubChem / UniProt / ChEMBL (Agente 2 solo consulta
  OpenFDA).
- MedGemma / Gemini Notebook (Agente 3 sigue 100% heurístico salvo que se
  configure `GOOGLE_API_KEY` y se implemente `_evaluar_con_llm`).
