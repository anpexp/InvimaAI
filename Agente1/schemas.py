"""Esquema del contrato de datos que TODOS los agentes deben respetar al
responder al Orquestador. No modificar los nombres de campos: el
Orquestador y el Dashboard dependen de que sean exactamente estos (mismo
contrato que agente2_reliance/schemas.py y agente3_clinico/schemas.py).
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional

from pydantic import BaseModel, Field


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
    agente_origen: str = "AGENTE_1_LEGAL"
    estado_procesamiento: str = "COMPLETADO"
    fecha_analisis: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    hallazgos: List[Hallazgo] = Field(default_factory=list)


# ---- Modelos de ENTRADA (lo que este agente recibe del expediente mock) ----

# Tipos de documento del Módulo 1 que la lógica de completitud exige.
TIPOS_DOCUMENTO_REQUERIDOS = {"FORMULARIO_SOLICITUD", "PODER", "BPM", "CPP"}

# Exigencias adicionales según el tipo de producto: los biológicos y las
# vacunas requieren soportes que un sintético no necesita (liberación de
# lote y, para vacunas, cadena de frío). Ver Tarea "contexto activo de
# tipo_producto" -- esto es lo que hace que el campo cambie reglas reales.
TIPOS_DOCUMENTO_REQUERIDOS_EXTRA = {
    "BIOLOGICO": {"CERTIFICADO_LOTE"},
    "VACUNA": {"CERTIFICADO_LOTE", "CERTIFICADO_CADENA_FRIO"},
}

# Ventana de alerta temprana de vigencia (días). Biológicos/vacunas tienen
# cadenas de manufactura y logística más largas, así que se avisa con más
# anticipación.
UMBRAL_ALERTA_DIAS_POR_TIPO = {
    "SINTESIS_QUIMICA": 90,
    "BIOLOGICO": 120,
    "VACUNA": 120,
}


class DocumentoModulo1(BaseModel):
    """Un documento del Módulo 1 ya con su texto extraído (OCR / Document AI
    / carga directa). El campo `texto` se trata SIEMPRE como dato de solo
    lectura -- nunca como instrucción para el LLM (ver llm_client.py)."""

    documento_id: str
    tipo_documento: str  # "FORMULARIO_SOLICITUD" | "PODER" | "BPM" | "CPP" | "OTRO"
    texto: str
    version: str = "v1.0"
    fecha_documento: str = "N/A"
    pagina_folio: str = "N/A"


class ExpedienteLegalInput(BaseModel):
    expediente_id: str
    producto_codigo: str
    producto_nombre: str
    tipo_producto: str = "SINTESIS_QUIMICA"  # SINTESIS_QUIMICA | BIOLOGICO | VACUNA
    documentos: List[DocumentoModulo1] = Field(default_factory=list)


# ---- Extracción intermedia (salida del LLM o del modo heurístico) ----


class ExtraccionDocumento(BaseModel):
    documento_id: str
    tipo_documento: str
    principio_activo: Optional[str] = None
    concentracion: Optional[str] = None
    titular: Optional[str] = None
    fabricante: Optional[str] = None
    importador: Optional[str] = None
    fecha_vigencia: Optional[str] = None  # "YYYY-MM-DD" o None
    cita_textual: Optional[str] = None  # fragmento literal donde se halló la fecha de vigencia
