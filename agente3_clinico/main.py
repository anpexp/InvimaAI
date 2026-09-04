from fastapi import FastAPI
from schemas import ExpedienteClinicoInput, RespuestaAgente, Hallazgo, UbicacionExacta
from rag_store import RAGStore
from llm_client import evaluar_soporte
from pico_extractor import extraer_caracteristicas_estudio

app = FastAPI(title="Agente 3 - Análisis Clínico y Calidad")

AGENTE_ORIGEN = "AGENTE_3_CLINICO"


@app.get("/health")
def health():
    return {"status": "ok", "agente": AGENTE_ORIGEN}


@app.post("/agente3/analizar", response_model=RespuestaAgente)
def analizar(expediente: ExpedienteClinicoInput):
    store = RAGStore()
    store.cargar(expediente.evidencia_primaria)

    hallazgos: list[Hallazgo] = []

    for i, afirmacion in enumerate(expediente.afirmaciones_modulo2, start=1):
        candidatos = store.buscar(afirmacion.texto, top_k=2)
        evaluacion = evaluar_soporte(afirmacion.texto, candidatos, expediente.tipo_producto)

        hid = f"HLZ-{i:03d}"

        if evaluacion.sustentada:
            mejor = candidatos[0].fragmento
            caracteristicas = extraer_caracteristicas_estudio(mejor.texto)
            respuesta = f"La afirmación del Módulo 2 encuentra soporte en evidencia primaria: \"{afirmacion.texto}\""
            if caracteristicas:
                respuesta += f" Características del estudio (extracción automática): {caracteristicas}."
            hallazgos.append(
                Hallazgo(
                    id_hallazgo=hid,
                    categoria_riesgo="BAJO",
                    respuesta=respuesta,
                    evidencia_citada=mejor.texto,
                    ubicacion_exacta=UbicacionExacta(
                        documento_id=mejor.documento_id,
                        modulo_seccion=f"{mejor.modulo} (evidencia primaria) / M2 (resumen: {afirmacion.pagina_folio})",
                        version=mejor.version,
                        fecha_documento=mejor.fecha_documento,
                        pagina_folio=mejor.pagina_folio,
                        entidad_responsable=mejor.entidad_responsable,
                    ),
                    nivel_confianza=evaluacion.nivel_confianza,
                    contradicciones_detectadas=[],
                    informacion_faltante=[],
                    limitaciones_ia=(
                        "Coincidencia calculada por similitud textual "
                        f"(modo {evaluacion.modo}); no reemplaza la lectura "
                        "clínica del evaluador."
                    ),
                    accion_sugerida_evaluador="Confirmar la lectura clínica de la coincidencia señalada.",
                )
            )
        else:
            hallazgos.append(
                Hallazgo(
                    id_hallazgo=hid,
                    categoria_riesgo="ALTO",
                    respuesta=f"La afirmación del Módulo 2 NO encuentra soporte suficiente en la evidencia primaria: \"{afirmacion.texto}\"",
                    evidencia_citada=evaluacion.explicacion,
                    ubicacion_exacta=UbicacionExacta(
                        documento_id=afirmacion.documento_id,
                        modulo_seccion="M2 (resumen clínico)",
                        version="v1.0",
                        fecha_documento="N/A",
                        pagina_folio=afirmacion.pagina_folio,
                        entidad_responsable="N/A",
                    ),
                    nivel_confianza=evaluacion.nivel_confianza,
                    contradicciones_detectadas=[],
                    informacion_faltante=[
                        "No se identificó evidencia primaria (M3/M4/M5) que sustente esta afirmación."
                    ],
                    limitaciones_ia=(
                        "El agente no infiere significancia clínica ni completa "
                        "datos faltantes: reporta la ausencia de soporte tal cual "
                        f"se detectó (modo {evaluacion.modo})."
                    ),
                    accion_sugerida_evaluador="Solicitar al solicitante que referencie la evidencia primaria específica que sustenta esta afirmación.",
                )
            )

    return RespuestaAgente(
        expediente_id=expediente.expediente_id,
        producto_codigo=expediente.producto_codigo,
        producto_nombre=expediente.producto_nombre,
        agente_origen=AGENTE_ORIGEN,
        estado_procesamiento="COMPLETADO",
        hallazgos=hallazgos,
    )
