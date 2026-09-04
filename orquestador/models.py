"""Contrato de datos compartido entre el Orquestador y los Agentes 1, 2 y 3.

No modificar los nombres de los campos: los agentes (ver README raíz del
repo) y el dashboard dependen de que sean exactamente estos.
"""
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class RiesgoCategoria(str, Enum):
    BAJO = "BAJO"
    MEDIO = "MEDIO"
    ALTO = "ALTO"


class TipoProducto(str, Enum):
    SINTESIS_QUIMICA = "SINTESIS_QUIMICA"
    BIOLOGICO = "BIOLOGICO"
    VACUNA = "VACUNA"


class RolEvaluador(str, Enum):
    LEGAL = "LEGAL"
    CALIDAD = "CALIDAD"
    CLINICO = "CLINICO"


# Rol del evaluador humano -> agente cuyos hallazgos le corresponde revisar.
ROL_A_AGENTE = {
    RolEvaluador.LEGAL: "AGENTE_1_LEGAL",
    RolEvaluador.CALIDAD: "AGENTE_2_RELIANCE",
    RolEvaluador.CLINICO: "AGENTE_3_CLINICO",
}


class UbicacionExacta(BaseModel):
    documento_id: str
    modulo_seccion: str
    version: str = "N/A"
    fecha_documento: str = "N/A"
    pagina_folio: str = "N/A"
    entidad_responsable: str = "N/A"


class Hallazgo(BaseModel):
    id_hallazgo: str
    categoria_riesgo: RiesgoCategoria
    respuesta: str
    evidencia_citada: str
    ubicacion_exacta: UbicacionExacta
    nivel_confianza: float = Field(ge=0.0, le=1.0)
    contradicciones_detectadas: List[str] = Field(default_factory=list)
    informacion_faltante: List[str] = Field(default_factory=list)
    limitaciones_ia: str
    accion_sugerida_evaluador: str


class RespuestaAgente(BaseModel):
    expediente_id: str
    producto_codigo: str
    producto_nombre: str
    agente_origen: str
    estado_procesamiento: str = "COMPLETADO"
    fecha_analisis: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    hallazgos: List[Hallazgo] = Field(default_factory=list)


class EstadoRevision(str, Enum):
    PENDIENTE = "PENDIENTE"
    APROBADO = "APROBADO"
    MODIFICADO = "MODIFICADO"
    RECHAZADO = "RECHAZADO"


class HallazgoConsolidado(Hallazgo):
    """Un Hallazgo, ya ubicado en la matriz temporal del expediente y con
    su estado de revisión Human-in-the-Loop."""

    agente_origen: str
    expediente_id: str
    producto_codigo: str
    producto_nombre: str
    estado_revision: EstadoRevision = EstadoRevision.PENDIENTE
    respuesta_modificada: Optional[str] = None
    comentario_evaluador: Optional[str] = None
    revisado_por_rol: Optional[str] = None
    revisado_en: Optional[str] = None


class OrquestacionRequest(BaseModel):
    expediente_id: str = Field(min_length=1)
    tipo_producto: TipoProducto
    rol_evaluador: RolEvaluador


class AgenteEstado(BaseModel):
    agente_origen: str
    ok: bool
    detalle: str = ""
    num_hallazgos: int = 0


class AntecedenteHistorico(BaseModel):
    """Un expediente ANTERIOR relacionado con el que se está evaluando
    ahora (mismo producto o misma entidad responsable) — resultado de la
    Memoria Transversal (ver memoria_transversal.py)."""

    expediente_id: str
    producto_codigo: str
    producto_nombre: str
    fecha_analisis: str
    categoria_riesgo_maxima: RiesgoCategoria
    num_hallazgos_alto: int
    entidades_responsables: List[str]
    resumen: str


class PrioridadTramite(str, Enum):
    ALTA = "ALTA"
    MEDIA = "MEDIA"
    BAJA = "BAJA"


class ResumenExpediente(BaseModel):
    """Fila del panel de trámites del Orquestador: clasifica y prioriza
    cada expediente ya procesado, y marca si está incompleto."""

    expediente_id: str
    producto_codigo: str
    producto_nombre: str
    fecha_analisis: str
    categoria_riesgo_maxima: RiesgoCategoria
    num_hallazgos_alto: int
    num_hallazgos: int
    expediente_completo: bool
    informacion_faltante: List[str]
    prioridad: PrioridadTramite
    agentes_disponibles: List[str]
    agentes_no_disponibles: List[str]


class OrquestacionResponse(BaseModel):
    expediente_id: str
    tipo_producto: TipoProducto
    rol_evaluador: RolEvaluador
    estados_agentes: List[AgenteEstado]
    hallazgos: List[HallazgoConsolidado]
    antecedentes_historicos: List[AntecedenteHistorico] = Field(default_factory=list)
    resumen_expediente: Optional[ResumenExpediente] = None


class DecisionHITL(str, Enum):
    APROBAR = "APROBAR"
    MODIFICAR = "MODIFICAR"
    RECHAZAR = "RECHAZAR"


class DecisionRequest(BaseModel):
    expediente_id: str
    id_hallazgo: str
    agente_origen: str
    decision: DecisionHITL
    rol_evaluador: RolEvaluador
    respuesta_modificada: Optional[str] = None
    comentario_evaluador: Optional[str] = None


class CitaDocumental(BaseModel):
    """Una cita al documento REAL del dossier -- nunca una referencia
    inventada. Ver corpus_documental.py y consulta_dossier.py."""

    documento_id: str
    modulo_seccion: str
    pagina_folio: str
    fragmento_citado: str


class ConsultaDossierRequest(BaseModel):
    expediente_id: str = Field(min_length=1)
    tipo_producto: TipoProducto = TipoProducto.SINTESIS_QUIMICA
    pregunta: str = Field(min_length=1, max_length=2000)


class ConsultaDossierResponse(BaseModel):
    expediente_id: str
    pregunta: str
    respuesta: str
    citas: List[CitaDocumental] = Field(default_factory=list)
    modo: str  # "gemini" | "heuristico"
    limitaciones_ia: str = (
        "Respuesta generada a partir del dossier simulado de este expediente; "
        "no reemplaza la lectura completa del expediente por el evaluador."
    )
