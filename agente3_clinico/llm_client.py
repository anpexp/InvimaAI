"""
Evalúa si una afirmación del Módulo 2 encuentra soporte en la evidencia
primaria recuperada por el RAGStore.

MODO_HEURISTICO (por defecto, sin llaves ni red): usa el score de
similitud TF-IDF como proxy de soporte. Es suficiente para demo y NUNCA
falla por falta de credenciales.

MODO_LLM (opcional): si existe la variable de entorno GOOGLE_API_KEY,
intenta usar Gemini/MedGemma para una evaluación más fina. Si la llamada
falla por cualquier motivo (red, cuota, modelo no disponible), cae de
vuelta al modo heurístico — el agente jamás debe tumbarse por esto.

Regla de oro (no negociable): este cliente NO completa datos faltantes
ni infiere significancia clínica. Si no hay soporte suficiente, lo dice
explícitamente en vez de inventar una respuesta.
"""
import os
from dataclasses import dataclass
from typing import List
from rag_store import ResultadoBusqueda

UMBRAL_SOPORTE = 0.15  # score TF-IDF mínimo para considerar "sustentada"

# Biológicos y vacunas exigen evidencia más robusta antes de considerar
# sustentada una afirmación del Módulo 2 -- mayor escrutinio regulatorio.
UMBRAL_SOPORTE_POR_TIPO = {
    "SINTESIS_QUIMICA": 0.15,
    "BIOLOGICO": 0.22,
    "VACUNA": 0.22,
}


@dataclass
class EvaluacionSoporte:
    sustentada: bool
    nivel_confianza: float
    explicacion: str
    modo: str  # "heuristico" | "llm"


def _evaluar_heuristico(
    afirmacion: str, candidatos: List[ResultadoBusqueda], umbral: float = UMBRAL_SOPORTE
) -> EvaluacionSoporte:
    if not candidatos or candidatos[0].score < umbral:
        return EvaluacionSoporte(
            sustentada=False,
            nivel_confianza=round(candidatos[0].score, 2) if candidatos else 0.0,
            explicacion="No se encontró evidencia primaria suficientemente relacionada con esta afirmación.",
            modo="heuristico",
        )
    mejor = candidatos[0]
    return EvaluacionSoporte(
        sustentada=True,
        nivel_confianza=round(mejor.score, 2),
        explicacion=f"La afirmación coincide con evidencia en {mejor.fragmento.modulo} ({mejor.fragmento.documento_id}).",
        modo="heuristico",
    )


def _evaluar_con_llm(afirmacion: str, candidatos: List[ResultadoBusqueda]) -> EvaluacionSoporte:
    """
    Placeholder de integración real con MedGemma / Gemini (Agent Platform
    o Google AI Studio). Se deja explícito y aislado para que, si consiguen
    acceso durante el hackathon, solo tengan que llenar esta función —
    el resto del agente no cambia.
    """
    raise NotImplementedError(
        "Conectar aquí la llamada real a MedGemma/Gemini. "
        "El prompt debe terminar exigiendo el JSON del contrato, "
        "y el sistema debe instruir explícitamente: "
        "'No infieras significancia clínica ni completes datos faltantes; "
        "si la evidencia no sustenta la afirmación, dilo explícitamente.'"
    )


def evaluar_soporte(
    afirmacion: str, candidatos: List[ResultadoBusqueda], tipo_producto: str = "SINTESIS_QUIMICA"
) -> EvaluacionSoporte:
    umbral = UMBRAL_SOPORTE_POR_TIPO.get(tipo_producto, UMBRAL_SOPORTE)
    if os.getenv("GOOGLE_API_KEY"):
        try:
            return _evaluar_con_llm(afirmacion, candidatos)
        except Exception:
            pass  # degradar con gracia al modo heurístico
    return _evaluar_heuristico(afirmacion, candidatos, umbral)
