"""Agente 1: Legal y Triaje — Hackatón INVIMA del Futuro.

Automatiza tareas de bajo riesgo del Módulo 1 (Legal/Administrativo):
inventario documental, validación de integridad, extracción de
metadatos y control de vigencias de certificados (BPM/CPP/Poderes).

Regla inquebrantable: este agente NUNCA emite una decisión final. Cada
hallazgo trae su propia `accion_sugerida_evaluador` -- la decisión
siempre es del evaluador humano (ver Orquestador / Dashboard).
"""
from fastapi import FastAPI, HTTPException

from llm_client import extraer_documento
from schemas import ExpedienteLegalInput, ExtraccionDocumento, Hallazgo, RespuestaAgente
from validation_rules import (
    validar_completitud,
    validar_coherencia_campo,
    validar_coherencia_roles,
    validar_vigencias,
)

app = FastAPI(title="INVIMA Agente 1 - Legal y Triaje (Módulo 1)", version="0.1.0")

AGENTE_ORIGEN = "AGENTE_1_LEGAL"


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "agente": AGENTE_ORIGEN}


@app.post("/analyze/legal", response_model=RespuestaAgente)
def analyze_legal(expediente: ExpedienteLegalInput) -> RespuestaAgente:
    try:
        extracciones: list[ExtraccionDocumento] = [extraer_documento(doc) for doc in expediente.documentos]
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Error extrayendo metadatos del Módulo 1: {exc}") from exc

    contador = [0]
    hallazgos: list[Hallazgo] = []

    completitud = validar_completitud(extracciones, contador, tipo_producto=expediente.tipo_producto)
    if completitud:
        hallazgos.append(completitud)

    # Coherencia de roles: fabricante (formulario vs. BPM) + titular e
    # importador transversal a todos los documentos que los declaren.
    hallazgos += validar_coherencia_roles(expediente.documentos, extracciones, contador)
    hallazgos += validar_coherencia_campo("titular", "titular", expediente.documentos, extracciones, contador)
    hallazgos += validar_coherencia_campo("importador", "importador", expediente.documentos, extracciones, contador)

    hallazgos += validar_vigencias(
        expediente.documentos, extracciones, contador, tipo_producto=expediente.tipo_producto
    )

    return RespuestaAgente(
        expediente_id=expediente.expediente_id,
        producto_codigo=expediente.producto_codigo,
        producto_nombre=expediente.producto_nombre,
        agente_origen=AGENTE_ORIGEN,
        estado_procesamiento="COMPLETADO",
        hallazgos=hallazgos,
    )
