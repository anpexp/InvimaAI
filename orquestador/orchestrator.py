"""Orquestador Principal — Hackatón INVIMA del Futuro.

Consolida los hallazgos de los Agentes 1 (Legal), 2 (Reliance/Calidad) y
3 (Clínico) en una sola matriz temporal en memoria, y expone el flujo
Human-in-the-Loop (HITL) que el Dashboard (app.py) consume: el evaluador
humano aprueba, modifica o rechaza cada hallazgo — la IA asiste, nunca
decide por sí sola.

El Agente 1 (Legal y Triaje, `../Agente1`) ya es un microservicio real
que expone `POST /analyze/legal` y respeta el mismo contrato de salida
que los Agentes 2 y 3. Si por alguna razón `AGENTE1_URL` queda vacío o el
servicio no responde, este orquestador degrada con gracia a hallazgos
simulados para AGENTE_1_LEGAL (ver mock_dossiers.py) para que el flujo
HITL del rol LEGAL siga siendo demostrable.
"""
from __future__ import annotations

import asyncio
import logging
import os
import re
import unicodedata
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from consulta_dossier import responder_pregunta
from corpus_documental import construir_corpus
from mock_dossiers import (
    DEMO_PRODUCTO_CODIGO,
    DEMO_PRODUCTO_NOMBRE,
    DEMO_TITULAR,
    dossier_agente1,
    dossier_agente2,
    dossier_agente3,
    hallazgos_agente1_legal_mock,
)
from memoria_transversal import memoria
from models import (
    AgenteEstado,
    AntecedenteHistorico,
    CitaDocumental,
    ConsultaDossierRequest,
    ConsultaDossierResponse,
    DecisionHITL,
    DecisionRequest,
    EstadoRevision,
    Hallazgo,
    HallazgoConsolidado,
    OrquestacionRequest,
    OrquestacionResponse,
    PrioridadTramite,
    ResumenExpediente,
    ROL_A_AGENTE,
    RespuestaAgente,
    RolEvaluador,
)

load_dotenv()  # sin esto, orquestador/.env nunca se leía en ejecuciones locales

logger = logging.getLogger("orquestador")
logging.basicConfig(level=logging.INFO)

AGENTE1_URL = os.getenv("AGENTE1_URL", "http://localhost:8001/analyze/legal")  # vacío = forzar modo simulado
AGENTE2_URL = os.getenv("AGENTE2_URL", "http://localhost:8002/agente2/analizar")
AGENTE3_URL = os.getenv("AGENTE3_URL", "http://localhost:8003/agente3/analizar")
HTTP_TIMEOUT = float(os.getenv("AGENTE_TIMEOUT_SEGUNDOS", "15"))

app = FastAPI(title="INVIMA - Orquestador Principal", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# "Matriz temporal en memoria": expediente_id -> {"AGENTE_X:id_hallazgo": HallazgoConsolidado}
# Prototipo de hackatón: vive en memoria del proceso, se pierde al reiniciar.
# (La Memoria Transversal en memoria_transversal.py sí persiste a disco.)
MATRIZ_TEMPORAL: Dict[str, Dict[str, HallazgoConsolidado]] = {}

# Último estado de los 3 agentes por expediente -- necesario para que
# /orquestador/panel pueda marcar un expediente como incompleto (agente
# caído o hallazgo con información faltante) sin tener que re-ejecutar
# la orquestación completa.
ULTIMO_ESTADO_AGENTES: Dict[str, List[AgenteEstado]] = {}


# --------------------------------------------------------------------------
# Seguridad: cualquier texto que venga de un dossier (mock o real, incluido
# lo que un solicitante haya escrito en su documentación) se trata SIEMPRE
# como dato de solo lectura, string plano. Nunca se interpola en un prompt,
# comando de shell o query ejecutados por el orquestador — solo viaja como
# valor de campo dentro de un payload JSON tipado (Pydantic) hacia cada
# agente. sanitize_payload() además retira caracteres de control y limita
# la longitud antes de reenviar cualquier texto.
# --------------------------------------------------------------------------
_CONTROL_CHARS = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
MAX_TEXT_LEN = 8000


def sanitize_text(valor: Any) -> Any:
    if not isinstance(valor, str):
        return valor
    limpio = unicodedata.normalize("NFC", valor)
    limpio = _CONTROL_CHARS.sub("", limpio)
    return limpio[:MAX_TEXT_LEN]


def sanitize_payload(payload: Any) -> Any:
    if isinstance(payload, dict):
        return {clave: sanitize_payload(valor) for clave, valor in payload.items()}
    if isinstance(payload, list):
        return [sanitize_payload(valor) for valor in payload]
    return sanitize_text(payload)


# --------------------------------------------------------------------------
# Llamadas asíncronas a los agentes
# --------------------------------------------------------------------------
async def _llamar_agente(client: httpx.AsyncClient, url: str, payload: Dict[str, Any]) -> RespuestaAgente:
    resp = await client.post(url, json=sanitize_payload(payload), timeout=HTTP_TIMEOUT)
    resp.raise_for_status()
    return RespuestaAgente.model_validate(resp.json())


async def _obtener_agente1(
    client: httpx.AsyncClient, expediente_id: str, producto_codigo: str, producto_nombre: str, tipo_producto: str
) -> RespuestaAgente:
    if AGENTE1_URL:
        return await _llamar_agente(
            client, AGENTE1_URL, dossier_agente1(expediente_id, producto_codigo, producto_nombre, tipo_producto)
        )
    # AGENTE1_URL vacío a propósito: degradar a hallazgos simulados.
    hallazgos_crudos = sanitize_payload(hallazgos_agente1_legal_mock(producto_nombre, DEMO_TITULAR))
    return RespuestaAgente(
        expediente_id=expediente_id,
        producto_codigo=producto_codigo,
        producto_nombre=producto_nombre,
        agente_origen="AGENTE_1_LEGAL",
        estado_procesamiento="COMPLETADO (SIMULADO)",
        hallazgos=[Hallazgo.model_validate(h) for h in hallazgos_crudos],
    )


async def _obtener_agente2(
    client: httpx.AsyncClient, expediente_id: str, producto_codigo: str, producto_nombre: str, tipo_producto: str
) -> RespuestaAgente:
    return await _llamar_agente(
        client, AGENTE2_URL, dossier_agente2(expediente_id, producto_codigo, producto_nombre, tipo_producto)
    )


async def _obtener_agente3(
    client: httpx.AsyncClient, expediente_id: str, producto_codigo: str, producto_nombre: str, tipo_producto: str
) -> RespuestaAgente:
    return await _llamar_agente(
        client, AGENTE3_URL, dossier_agente3(expediente_id, producto_codigo, producto_nombre, tipo_producto)
    )


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


def _clasificar_prioridad(categoria_maxima: str, completo: bool) -> PrioridadTramite:
    """Clasifica y prioriza el trámite: un expediente incompleto SIEMPRE
    es prioridad ALTA (hay que resolverlo antes de poder evaluarlo a
    fondo), independientemente de qué tan grave sea lo que ya se alcanzó
    a revisar."""
    if not completo or categoria_maxima == "ALTO":
        return PrioridadTramite.ALTA
    if categoria_maxima == "MEDIO":
        return PrioridadTramite.MEDIA
    return PrioridadTramite.BAJA


def _construir_resumen_expediente(
    expediente_id: str, producto_codigo: str, producto_nombre: str
) -> ResumenExpediente:
    """Detecta expedientes incompletos y calcula la prioridad del trámite
    a partir de la matriz consolidada + el último estado de los agentes.
    Esta es la función de "clasificar y priorizar trámites" del
    Orquestador."""
    hallazgos = list(MATRIZ_TEMPORAL.get(expediente_id, {}).values())
    estados = ULTIMO_ESTADO_AGENTES.get(expediente_id, [])

    categoria_maxima = "BAJO"
    if any(h.categoria_riesgo == "ALTO" for h in hallazgos):
        categoria_maxima = "ALTO"
    elif any(h.categoria_riesgo == "MEDIO" for h in hallazgos):
        categoria_maxima = "MEDIO"

    informacion_faltante = sorted({item for h in hallazgos for item in h.informacion_faltante})
    agentes_disponibles = [e.agente_origen for e in estados if e.ok]
    agentes_no_disponibles = [e.agente_origen for e in estados if not e.ok]

    completo = not agentes_no_disponibles and not informacion_faltante

    return ResumenExpediente(
        expediente_id=expediente_id,
        producto_codigo=producto_codigo,
        producto_nombre=producto_nombre,
        fecha_analisis=datetime.now(timezone.utc).isoformat(),
        categoria_riesgo_maxima=categoria_maxima,
        num_hallazgos_alto=sum(1 for h in hallazgos if h.categoria_riesgo == "ALTO"),
        num_hallazgos=len(hallazgos),
        expediente_completo=completo,
        informacion_faltante=informacion_faltante,
        prioridad=_clasificar_prioridad(categoria_maxima, completo),
        agentes_disponibles=agentes_disponibles,
        agentes_no_disponibles=agentes_no_disponibles,
    )


@app.post("/orquestador/analizar", response_model=OrquestacionResponse)
async def analizar(request: OrquestacionRequest) -> OrquestacionResponse:
    """Simula la carga documental del expediente y llama a los 3 agentes
    en paralelo. Si un agente falla o no está disponible, el resto de la
    orquestación continúa (degradación con gracia) y el estado del agente
    caído queda visible para el evaluador."""
    producto_codigo = DEMO_PRODUCTO_CODIGO
    producto_nombre = DEMO_PRODUCTO_NOMBRE
    tipo_producto = request.tipo_producto.value

    async with httpx.AsyncClient() as client:
        nombres_agentes = ["AGENTE_1_LEGAL", "AGENTE_2_RELIANCE", "AGENTE_3_CLINICO"]
        resultados = await asyncio.gather(
            _obtener_agente1(client, request.expediente_id, producto_codigo, producto_nombre, tipo_producto),
            _obtener_agente2(client, request.expediente_id, producto_codigo, producto_nombre, tipo_producto),
            _obtener_agente3(client, request.expediente_id, producto_codigo, producto_nombre, tipo_producto),
            return_exceptions=True,
        )

    estados: List[AgenteEstado] = []
    matriz_expediente = MATRIZ_TEMPORAL.setdefault(request.expediente_id, {})

    for agente_origen, resultado in zip(nombres_agentes, resultados):
        if isinstance(resultado, Exception):
            logger.warning("Agente %s no disponible: %s", agente_origen, resultado)
            estados.append(AgenteEstado(agente_origen=agente_origen, ok=False, detalle=str(resultado)))
            continue

        estados.append(AgenteEstado(agente_origen=agente_origen, ok=True, num_hallazgos=len(resultado.hallazgos)))
        for hallazgo in resultado.hallazgos:
            clave = f"{agente_origen}:{hallazgo.id_hallazgo}"
            previo = matriz_expediente.get(clave)
            matriz_expediente[clave] = HallazgoConsolidado(
                **hallazgo.model_dump(),
                agente_origen=agente_origen,
                expediente_id=request.expediente_id,
                producto_codigo=producto_codigo,
                producto_nombre=producto_nombre,
                # Preserva decisiones HITL previas si se vuelve a ejecutar la orquestación.
                estado_revision=previo.estado_revision if previo else EstadoRevision.PENDIENTE,
                respuesta_modificada=previo.respuesta_modificada if previo else None,
                comentario_evaluador=previo.comentario_evaluador if previo else None,
                revisado_por_rol=previo.revisado_por_rol if previo else None,
                revisado_en=previo.revisado_en if previo else None,
            )

    ULTIMO_ESTADO_AGENTES[request.expediente_id] = estados

    # Memoria Transversal: registra este expediente y recupera antecedentes
    # de otros expedientes ya evaluados para el mismo producto/entidad.
    todos_los_hallazgos = list(matriz_expediente.values())
    memoria.registrar_expediente(request.expediente_id, producto_codigo, producto_nombre, todos_los_hallazgos)
    antecedentes = memoria.buscar_antecedentes(request.expediente_id, producto_codigo, producto_nombre)

    resumen_expediente = _construir_resumen_expediente(request.expediente_id, producto_codigo, producto_nombre)

    agente_del_rol = ROL_A_AGENTE[request.rol_evaluador]
    hallazgos_rol = [h for h in matriz_expediente.values() if h.agente_origen == agente_del_rol]

    return OrquestacionResponse(
        expediente_id=request.expediente_id,
        tipo_producto=request.tipo_producto,
        rol_evaluador=request.rol_evaluador,
        estados_agentes=estados,
        hallazgos=hallazgos_rol,
        antecedentes_historicos=antecedentes,
        resumen_expediente=resumen_expediente,
    )


@app.get("/orquestador/matriz/{expediente_id}", response_model=List[HallazgoConsolidado])
def obtener_matriz(expediente_id: str, rol_evaluador: Optional[str] = None) -> List[HallazgoConsolidado]:
    """Lee la matriz temporal ya consolidada (sin volver a llamar a los
    agentes) — útil para refrescar la vista tras una decisión HITL o un
    cambio de rol."""
    matriz_expediente = MATRIZ_TEMPORAL.get(expediente_id, {})
    hallazgos = list(matriz_expediente.values())
    if rol_evaluador:
        try:
            agente = ROL_A_AGENTE[RolEvaluador(rol_evaluador)]
        except ValueError:
            raise HTTPException(status_code=400, detail=f"rol_evaluador inválido: {rol_evaluador}")
        hallazgos = [h for h in hallazgos if h.agente_origen == agente]
    return hallazgos


@app.post("/orquestador/hallazgo/decision", response_model=HallazgoConsolidado)
def registrar_decision(request: DecisionRequest) -> HallazgoConsolidado:
    """Autoridad humana: registra la decisión del evaluador sobre un
    hallazgo puntual. La IA nunca aprueba ni rechaza sus propios hallazgos."""
    matriz_expediente = MATRIZ_TEMPORAL.get(request.expediente_id)
    clave = f"{request.agente_origen}:{request.id_hallazgo}"
    if not matriz_expediente or clave not in matriz_expediente:
        raise HTTPException(
            status_code=404,
            detail="Hallazgo no encontrado en la matriz temporal. Ejecute primero /orquestador/analizar.",
        )

    hallazgo = matriz_expediente[clave]

    if request.decision == DecisionHITL.APROBAR:
        hallazgo.estado_revision = EstadoRevision.APROBADO
    elif request.decision == DecisionHITL.MODIFICAR:
        if not request.respuesta_modificada:
            raise HTTPException(status_code=400, detail="Debe incluir 'respuesta_modificada' para modificar el hallazgo.")
        hallazgo.estado_revision = EstadoRevision.MODIFICADO
        hallazgo.respuesta_modificada = sanitize_text(request.respuesta_modificada)
    elif request.decision == DecisionHITL.RECHAZAR:
        hallazgo.estado_revision = EstadoRevision.RECHAZADO

    if request.comentario_evaluador:
        hallazgo.comentario_evaluador = sanitize_text(request.comentario_evaluador)
    hallazgo.revisado_por_rol = request.rol_evaluador.value
    hallazgo.revisado_en = datetime.now(timezone.utc).isoformat()

    matriz_expediente[clave] = hallazgo
    return hallazgo


@app.get("/orquestador/informe/{expediente_id}", response_model=List[HallazgoConsolidado])
def obtener_informe(expediente_id: str) -> List[HallazgoConsolidado]:
    """Informe final: solo los hallazgos que un evaluador humano aprobó o
    modificó explícitamente. Nunca incluye hallazgos pendientes ni
    rechazados — refleja exclusivamente la decisión humana."""
    matriz_expediente = MATRIZ_TEMPORAL.get(expediente_id, {})
    return [
        h
        for h in matriz_expediente.values()
        if h.estado_revision in (EstadoRevision.APROBADO, EstadoRevision.MODIFICADO)
    ]


@app.get("/orquestador/panel", response_model=List[ResumenExpediente])
def panel_tramites() -> List[ResumenExpediente]:
    """Clasificar y priorizar trámites: un expediente por fila, con su
    prioridad (ALTA/MEDIA/BAJA) y si está completo. Ordenado por
    prioridad -- lo que el evaluador debería atender primero queda
    arriba. Cubre solo los expedientes procesados en esta ejecución del
    proceso (la matriz temporal no persiste a disco; la Memoria
    Transversal sí, ver /orquestador/antecedentes)."""
    resumenes: List[ResumenExpediente] = []
    for expediente_id, hallazgos_por_clave in MATRIZ_TEMPORAL.items():
        hallazgos = list(hallazgos_por_clave.values())
        if not hallazgos:
            continue
        resumenes.append(
            _construir_resumen_expediente(expediente_id, hallazgos[0].producto_codigo, hallazgos[0].producto_nombre)
        )

    orden_prioridad = {PrioridadTramite.ALTA: 0, PrioridadTramite.MEDIA: 1, PrioridadTramite.BAJA: 2}
    resumenes.sort(key=lambda r: (orden_prioridad[r.prioridad], r.expediente_id))
    return resumenes


@app.get("/orquestador/antecedentes/{expediente_id}", response_model=List[AntecedenteHistorico])
def antecedentes_expediente(expediente_id: str) -> List[AntecedenteHistorico]:
    """Memoria Transversal: antecedentes de otros expedientes (mismo
    producto o misma entidad responsable) sin volver a ejecutar la
    orquestación completa."""
    hallazgos = list(MATRIZ_TEMPORAL.get(expediente_id, {}).values())
    if not hallazgos:
        raise HTTPException(
            status_code=404, detail="Expediente no encontrado. Ejecute primero /orquestador/analizar."
        )
    return memoria.buscar_antecedentes(expediente_id, hallazgos[0].producto_codigo, hallazgos[0].producto_nombre)


@app.post("/orquestador/consultar", response_model=ConsultaDossierResponse)
def consultar_dossier(request: ConsultaDossierRequest) -> ConsultaDossierResponse:
    """Barra de consulta sobre el dossier: responde una pregunta libre del
    evaluador citando el documento_id y folio EXACTOS del expediente
    simulado (nunca una referencia inventada). Con GEMINI_API_KEY usa
    Gemini con grounding estricto; sin ella, degrada a un buscador
    heurístico por palabras clave. Nunca reemplaza la lectura del
    expediente por el evaluador ni emite una decisión regulatoria."""
    pregunta = sanitize_text(request.pregunta)
    corpus = construir_corpus(
        request.expediente_id, DEMO_PRODUCTO_CODIGO, DEMO_PRODUCTO_NOMBRE, request.tipo_producto.value
    )
    resultado = responder_pregunta(pregunta, corpus)

    return ConsultaDossierResponse(
        expediente_id=request.expediente_id,
        pregunta=pregunta,
        respuesta=resultado["respuesta"],
        citas=[CitaDocumental.model_validate(c) for c in resultado["citas"]],
        modo=resultado["modo"],
    )
