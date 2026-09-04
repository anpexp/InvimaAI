"""Mismo contrato de salida que el Agente 2 — no cambiar los nombres de campo."""
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class UbicacionExacta(BaseModel):
    documento_id: str
    modulo_seccion: str
    version: str
    fecha_documento: str
    pagina_folio: str
    entidad_responsable: str


class Hallazgo(BaseModel):
    id_hallazgo: str
    categoria_riesgo: str
    respuesta: str
    evidencia_citada: str
    ubicacion_exacta: UbicacionExacta
    nivel_confianza: float
    contradicciones_detectadas: List[str] = Field(default_factory=list)
    informacion_faltante: List[str] = Field(default_factory=list)
    limitaciones_ia: str
    accion_sugerida_evaluador: str


class RespuestaAgente(BaseModel):
    expediente_id: str
    producto_codigo: str
    producto_nombre: str
    agente_origen: str
    estado_procesamiento: str
    fecha_analisis: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    hallazgos: List[Hallazgo] = Field(default_factory=list)


# ---- Entrada ----

class EvidenciaFragmento(BaseModel):
    id: str
    modulo: str  # "M3" | "M4" | "M5"
    texto: str
    documento_id: str
    version: str = "v1.0"
    fecha_documento: str = "N/A"
    pagina_folio: str = "N/A"
    entidad_responsable: str = "N/A"


class AfirmacionClinica(BaseModel):
    id: str
    texto: str  # afirmación tal como aparece en el resumen (Módulo 2)
    documento_id: str = "M2"
    pagina_folio: str = "N/A"


class ExpedienteClinicoInput(BaseModel):
    expediente_id: str
    producto_codigo: str
    producto_nombre: str
    tipo_producto: str = "SINTESIS_QUIMICA"  # SINTESIS_QUIMICA | BIOLOGICO | VACUNA
    afirmaciones_modulo2: List[AfirmacionClinica] = Field(default_factory=list)
    evidencia_primaria: List[EvidenciaFragmento] = Field(default_factory=list)
