# INVIMA Agente 3: Analisis Clinico y Calidad

Prototipo de memoria transversal RAG estructurada para comparar claims del Modulo 2 contra evidencia primaria de los Modulos 3, 4 y 5.

## Inicio rapido

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python ingest.py data/demo_ctd.json
uvicorn main:app --reload
```

Luego abrir `http://127.0.0.1:8000/docs` o ejecutar:

```bash
curl -X POST http://127.0.0.1:8000/analyze/clinical \
  -H 'Content-Type: application/json' \
  -d '{"expediente_id":"INV-2026-001","producto_codigo":"PX10","producto_nombre":"Producto X","claim":"El producto redujo la presion arterial sistolica en adultos con hipertension","tipo_producto":"SINTESIS_QUIMICA"}'
```

## Datos y trazabilidad

## Ejecucion con Docker

El servicio escucha en el puerto `8000` dentro del contenedor. Para exponerlo localmente en el puerto `8006`, el mapeo correcto es `8006:8000`:

```bash
docker build -t invima-agil:prototype .
docker run --rm --name invima-agil \
  -p 8006:8000 \
  -v invima_chroma:/app/chroma_db \
  --env-file .env \
  invima-agil:prototype
```

Comprobar estado y documentacion:

```bash
curl http://127.0.0.1:8006/health
# Abrir http://127.0.0.1:8006/docs
```

No escribas `$` delante del valor de la API key. Usa `--env-file .env` o una variable ya definida:

```bash
export GEMINI_API_KEY='TU_API_KEY'
docker run --rm -p 8006:8000 -e GEMINI_API_KEY="$GEMINI_API_KEY" invima-agil:prototype
```

La clave que se haya pegado en una terminal o chat debe revocarse y regenerarse en Google AI Studio.

Cada chunk se almacena con exactamente seis metadatos: `document_id`, `modulo_seccion`, `version`, `fecha`, `rango_folios` y `tipo_producto`. El retriever solo acepta evidencia de los Modulos 3, 4 y 5. La respuesta siempre devuelve el documento, version y rango de folios usado.

Con `GEMINI_API_KEY`, el agente usa Gemini con temperatura `0.0` y el system prompt regulatorio definido en `agent.py`. Sin la clave, usa un comparador lexical determinista para que el demo sea reproducible y no simule una conclusion clinica.

## Formato de ingesta

El archivo JSON puede ser una lista o `{\"documents\": [...]}`. Cada registro requiere `metadata` con el esquema exacto y `text`. Tambien se acepta JSONL.
