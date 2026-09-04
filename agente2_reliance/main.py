from fastapi import FastAPI
from schemas import ExpedienteInput, RespuestaAgente, Hallazgo, UbicacionExacta
from consistency_rules import comparar_atributo
from openfda_client import buscar_historial_fda

app = FastAPI(title="Agente 2 - Reliance y Consistencia Transversal")

AGENTE_ORIGEN = "AGENTE_2_RELIANCE"


@app.get("/health")
def health():
    return {"status": "ok", "agente": AGENTE_ORIGEN}


@app.post("/agente2/analizar", response_model=RespuestaAgente)
def analizar(expediente: ExpedienteInput):
    contador = [0]
    hallazgos: list[Hallazgo] = []

    # 1. Consistencia cruzada entre módulos (M1 / M3 / M8, etc.)
    hallazgos += comparar_atributo("nombre", expediente.nombre_por_modulo, contador, expediente.tipo_producto)
    hallazgos += comparar_atributo(
        "concentracion", expediente.concentracion_por_modulo, contador, expediente.tipo_producto
    )
    hallazgos += comparar_atributo(
        "almacenamiento", expediente.almacenamiento_por_modulo, contador, expediente.tipo_producto
    )

    # 2. Reliance: historial regulatorio internacional (OpenFDA)
    fda = buscar_historial_fda(expediente.molecula or expediente.producto_nombre)
    contador[0] += 1
    hid = f"HLZ-{contador[0]:03d}"

    if fda.get("encontrado"):
        hallazgos.append(
            Hallazgo(
                id_hallazgo=hid,
                categoria_riesgo="BAJO",
                respuesta=fda["detalle"],
                evidencia_citada=f"openFDA drug/label — {fda['num_registros']} registro(s)",
                ubicacion_exacta=UbicacionExacta(
                    documento_id="openFDA",
                    modulo_seccion="Reliance / Antecedentes internacionales",
                    version="N/A",
                    fecha_documento="N/A",
                    pagina_folio="N/A",
                    entidad_responsable="FDA",
                ),
                nivel_confianza=0.9,
                contradicciones_detectadas=[],
                informacion_faltante=[],
                limitaciones_ia="Búsqueda automática por nombre genérico; puede haber variantes de escritura no capturadas.",
                accion_sugerida_evaluador="Considerar como antecedente de referencia (reliance) en la evaluación.",
            )
        )
    else:
        hallazgos.append(
            Hallazgo(
                id_hallazgo=hid,
                categoria_riesgo="BAJO",
                respuesta="No se encontró antecedente regulatorio en openFDA para esta molécula.",
                evidencia_citada=f"Motivo: {fda.get('motivo', 'desconocido')}",
                ubicacion_exacta=UbicacionExacta(
                    documento_id="openFDA",
                    modulo_seccion="Reliance / Antecedentes internacionales",
                    version="N/A",
                    fecha_documento="N/A",
                    pagina_folio="N/A",
                    entidad_responsable="FDA",
                ),
                nivel_confianza=0.5,
                contradicciones_detectadas=[],
                informacion_faltante=["No hay antecedente de reliance disponible automáticamente."],
                limitaciones_ia="Ausencia de resultado no implica ausencia de aprobación; puede ser un fallo de red o de nomenclatura.",
                accion_sugerida_evaluador="Verificar manualmente antecedentes internacionales si el caso lo amerita.",
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
