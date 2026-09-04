from fastapi import FastAPI, HTTPException

from agent import ClinicalAgent
from models import ClinicalAnalysisRequest, ClinicalAnalysisResponse

app = FastAPI(title="INVIMA Agente 3 - Analisis Clinico y Calidad", version="0.1.0")
agent = ClinicalAgent()


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "chunks_indexados": agent.retriever.count()}


@app.post("/analyze/clinical", response_model=ClinicalAnalysisResponse)
def analyze_clinical(request: ClinicalAnalysisRequest) -> ClinicalAnalysisResponse:
    try:
        return agent.analyze(**request.model_dump())
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Error analizando expediente: {exc}") from exc
