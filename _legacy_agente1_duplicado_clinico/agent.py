from __future__ import annotations

import json
import os
import re
from typing import Any, Dict, List

from dotenv import load_dotenv

from models import ClinicalAnalysisResponse, Finding, Location, RiskCategory
from retriever import Evidence, EvidenceRetriever, get_retriever

load_dotenv()

SYSTEM_PROMPT = (
    "Eres un asistente regulatorio estricto. NO debes inferir significancia clínica, "
    "NO debes inventar datos faltantes y NO debes completar resultados que no estén en "
    "el texto extraído. Debes diferenciar claramente el valor reportado de la "
    "interpretación. Si la evidencia no soporta la afirmación, decláralo explícitamente. "
    "Cada conclusión debe citar el documento, versión y folio exacto."
)


def _location(evidence: Evidence) -> Location:
    metadata = evidence.metadata
    return Location(
        documento_id=metadata["document_id"],
        modulo_seccion=metadata["modulo_seccion"],
        version=metadata["version"],
        fecha_documento=metadata["fecha"],
        pagina_folio=metadata["rango_folios"],
    )


def _extract_pico(text: str) -> str:
    if "estudio pivotal" not in text.lower():
        return "No aplica: la evidencia no identifica un estudio pivotal."
    population = re.search(r"en (\d+ [^\.]+?)\. La intervencion", text, re.IGNORECASE)
    intervention = re.search(r"La intervencion fue ([^\.]+?)\.", text, re.IGNORECASE)
    comparator = re.search(r"comparada contra ([^\.]+?)\.", text, re.IGNORECASE)
    outcome = re.search(r"desenlace primario reportado fue ([^\.]+?)\.", text, re.IGNORECASE)
    return (
        f"Poblacion: {population.group(1) if population else 'no reportada'}; "
        f"Intervencion: {intervention.group(1) if intervention else 'no reportada'}; "
        f"Comparador: {comparator.group(1) if comparator else 'no reportado'}; "
        f"Desenlace: {outcome.group(1) if outcome else 'no reportado'}."
    )


def _find_contradictions(evidence: List[Evidence]) -> List[str]:
    half_lives = []
    for item in evidence:
        match = re.search(r"vida media.*?([0-9]+(?:\.[0-9]+)?)\s*horas", item.text, re.IGNORECASE)
        if match:
            half_lives.append((match.group(1), item.metadata["document_id"]))
    if len({value for value, _ in half_lives}) > 1:
        values = ", ".join(f"{value} horas ({document_id})" for value, document_id in half_lives)
        return [f"Diferencia numerica en vida media t1/2: {values}."]
    return []


def _local_finding(claim: str, evidence: Evidence, index: int, contradictions: List[str]) -> Finding:
    claim_terms = set(re.findall(r"[a-z0-9]{4,}", claim.lower()))
    evidence_terms = set(re.findall(r"[a-z0-9]{4,}", evidence.text.lower()))
    overlap = len(claim_terms & evidence_terms) / max(len(claim_terms), 1)
    supported = overlap >= 0.18
    return Finding(
        id_hallazgo=f"H3-{index:03d}",
        categoria_riesgo=RiskCategory.BAJO if supported else RiskCategory.MEDIO,
        respuesta=(
            "La evidencia recuperada contiene coincidencias textuales con la afirmacion; "
            f"esto demuestra trazabilidad, no significancia clinica. {_extract_pico(evidence.text)}"
            if supported
            else "La evidencia recuperada no soporta de forma suficiente la afirmacion; requiere revision documental."
        ),
        evidencia_citada=evidence.text,
        ubicacion_exacta=_location(evidence),
        nivel_confianza=round(min(0.95, 0.45 + overlap), 2),
        contradicciones_detectadas=contradictions,
        informacion_faltante=["Resultado estadistico y contexto clinico"] if not supported else [],
        limitaciones_ia="Modo local: no se uso un LLM y no se evalua impacto clinico ni causalidad.",
        accion_sugerida_evaluador="Verificar el texto fuente y confirmar la conclusion con el evaluador clinico.",
    )


def _gemini_findings(claim: str, evidence: List[Evidence]) -> List[Finding]:
    import google.generativeai as genai

    genai.configure(api_key=os.environ["GEMINI_API_KEY"])
    model = genai.GenerativeModel(
        os.getenv("GEMINI_MODEL", "gemini-1.5-flash"),
        system_instruction=SYSTEM_PROMPT,
        generation_config={"temperature": 0.0, "response_mime_type": "application/json"},
    )
    context = "\n\n".join(f"EVIDENCIA {i + 1}: {item.text}" for i, item in enumerate(evidence))
    prompt = f"Analiza este claim del Modulo 2: {claim}\n\n{context}\nDevuelve un JSON array de hallazgos. Cada hallazgo debe incluir exactamente los campos del modelo Finding y ubicacion_exacta debe usar los metadatos citados. Si identificas un estudio pivotal, incluye sus variables PICO en respuesta. Compara valores numericos entre documentos y reporta contradicciones sin inferir impacto clinico."
    raw = model.generate_content(prompt).text
    payload = json.loads(raw)
    return [Finding.model_validate(item) for item in payload]


class ClinicalAgent:
    def __init__(self, retriever: EvidenceRetriever | None = None) -> None:
        self.retriever = retriever or get_retriever()

    def analyze(self, expediente_id: str, producto_codigo: str, producto_nombre: str, claim: str, tipo_producto: str = "SINTESIS_QUIMICA", top_k: int = 5) -> ClinicalAnalysisResponse:
        evidence = self.retriever.search(claim, top_k=top_k, tipo_producto=tipo_producto)
        if not evidence:
            findings = [Finding(
                id_hallazgo="H3-001", categoria_riesgo=RiskCategory.ALTO,
                respuesta="No se encontro evidencia primaria recuperable en Modulos 3, 4 o 5.",
                evidencia_citada="", ubicacion_exacta=Location(documento_id="NO_ENCONTRADO", modulo_seccion="", version="", fecha_documento="", pagina_folio=""),
                nivel_confianza=0.99, informacion_faltante=["Evidencia primaria CTD"],
                limitaciones_ia="La ausencia en el indice no prueba ausencia en el expediente.",
                accion_sugerida_evaluador="Revisar el expediente y completar la ingesta antes de concluir.",
            )]
        elif os.getenv("GEMINI_API_KEY"):
            findings = _gemini_findings(claim, evidence)
        else:
            contradictions = _find_contradictions(evidence)
            findings = [_local_finding(claim, item, index, contradictions) for index, item in enumerate(evidence, 1)]
        return ClinicalAnalysisResponse(expediente_id=expediente_id, producto_codigo=producto_codigo, producto_nombre=producto_nombre, hallazgos=findings)
