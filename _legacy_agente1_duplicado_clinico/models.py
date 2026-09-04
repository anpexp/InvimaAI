from datetime import datetime, timezone
from enum import Enum
from typing import List

from pydantic import BaseModel, Field


class RiskCategory(str, Enum):
    BAJO = "BAJO"
    MEDIO = "MEDIO"
    ALTO = "ALTO"


class Location(BaseModel):
    documento_id: str
    modulo_seccion: str
    version: str
    fecha_documento: str
    pagina_folio: str
    entidad_responsable: str = "No especificada"


class Finding(BaseModel):
    id_hallazgo: str
    categoria_riesgo: RiskCategory
    respuesta: str
    evidencia_citada: str
    ubicacion_exacta: Location
    nivel_confianza: float = Field(ge=0.0, le=1.0)
    contradicciones_detectadas: List[str] = Field(default_factory=list)
    informacion_faltante: List[str] = Field(default_factory=list)
    limitaciones_ia: str
    accion_sugerida_evaluador: str


class ClinicalAnalysisRequest(BaseModel):
    expediente_id: str = Field(min_length=1)
    producto_codigo: str = Field(min_length=1)
    producto_nombre: str = Field(min_length=1)
    claim: str = Field(min_length=1)
    tipo_producto: str = "SINTESIS_QUIMICA"
    top_k: int = Field(default=5, ge=1, le=20)


class ClinicalAnalysisResponse(BaseModel):
    expediente_id: str
    producto_codigo: str
    producto_nombre: str
    agente_origen: str = "AGENTE_3_CLINICO"
    estado_procesamiento: str = "COMPLETADO"
    fecha_analisis: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    hallazgos: List[Finding]
