"""
Esquema del contrato de datos que TODOS los agentes deben respetar
al responder al Orquestador. No modificar los nombres de campos:
el Dashboard (Dev 1) depende de que sean exactamente estos.
"""
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
    categoria_riesgo: str  # "ALTO" | "MEDIO" | "BAJO"
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
    estado_procesamiento: str  # "COMPLETADO" | "PARCIAL" | "ERROR"
    fecha_analisis: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    hallazgos: List[Hallazgo] = Field(default_factory=list)


# ---- Modelos de ENTRADA (lo que ustedes reciben del expediente mock) ----

class ModuloCampo(BaseModel):
    """Un mismo atributo (nombre, concentración, condición de almacenamiento...)
    tal como aparece reportado en un módulo específico del dossier."""
    modulo: str            # ej. "M1", "M3", "M8"
    valor: str
    documento_id: str
    version: str = "v1.0"
    fecha_documento: str = "N/A"
    pagina_folio: str = "N/A"
    entidad_responsable: str = "N/A"


class ExpedienteInput(BaseModel):
    expediente_id: str
    producto_codigo: str
    producto_nombre: str
    tipo_producto: str = "SINTESIS_QUIMICA"  # SINTESIS_QUIMICA | BIOLOGICO | VACUNA
    molecula: Optional[str] = None
    nombre_por_modulo: List[ModuloCampo] = Field(default_factory=list)
    concentracion_por_modulo: List[ModuloCampo] = Field(default_factory=list)
    almacenamiento_por_modulo: List[ModuloCampo] = Field(default_factory=list)
