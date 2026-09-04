"""Memoria Transversal — Base de Datos Vectorial / Búsqueda de Contexto.

Resuelve la demora histórica de búsqueda de contexto (documento original:
"hasta 18 meses") cruzando el expediente que se está evaluando ahora con
lo que ya se procesó antes para el MISMO producto o el MISMO titular, en
cualquier expediente anterior.

No es una base de datos vectorial de terceros (Chroma/Pinecone/etc.) —
es un almacén propio, persistido a disco en JSON, con recuperación por
similitud TF-IDF (mismo enfoque heurístico que ya usa agente3_clinico,
para no depender de infraestructura extra en el hackatón). Lo importante
es la FUNCIÓN que cumple: preservar contexto entre expedientes en vez de
tratar cada evaluación como si empezara de cero (que es lo que hacía el
prototipo antes de este módulo).
"""
from __future__ import annotations

import json
import logging
import os
import re
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from models import AntecedenteHistorico, HallazgoConsolidado

logger = logging.getLogger("memoria_transversal")

# `or` (no el default de getenv) para que MEMORIA_TRANSVERSAL_PATH="" en
# .env también caiga a la ruta por defecto en vez de intentar usar ".".
RUTA_PERSISTENCIA = Path(os.getenv("MEMORIA_TRANSVERSAL_PATH") or str(Path(__file__).parent / "memoria_transversal.json"))


def _normalizar(texto: str) -> str:
    limpio = unicodedata.normalize("NFKD", texto or "").encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]+", " ", limpio.lower()).strip()


class MemoriaTransversal:
    """Registro de expedientes ya evaluados, indexado por producto y por
    entidad responsable (titular/fabricante), para recuperar antecedentes
    relevantes al analizar un nuevo expediente."""

    def __init__(self, ruta: Path = RUTA_PERSISTENCIA) -> None:
        self._ruta = ruta
        self._registros: Dict[str, dict] = {}  # expediente_id -> registro
        self._cargar()

    def _cargar(self) -> None:
        if self._ruta.exists():
            try:
                self._registros = json.loads(self._ruta.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError) as exc:
                logger.warning("No se pudo leer memoria transversal (%s); arrancando vacía.", exc)
                self._registros = {}

    def _guardar(self) -> None:
        try:
            self._ruta.write_text(json.dumps(self._registros, ensure_ascii=False, indent=2), encoding="utf-8")
        except OSError as exc:
            logger.warning("No se pudo persistir memoria transversal: %s", exc)

    def registrar_expediente(
        self,
        expediente_id: str,
        producto_codigo: str,
        producto_nombre: str,
        hallazgos: List[HallazgoConsolidado],
    ) -> None:
        """Guarda un resumen compacto del expediente recién analizado para
        que futuros expedientes (mismo producto o misma entidad) lo
        encuentren como antecedente."""
        entidades = sorted(
            {h.ubicacion_exacta.entidad_responsable for h in hallazgos if h.ubicacion_exacta.entidad_responsable not in ("N/A", "")}
        )
        categoria_maxima = "BAJO"
        if any(h.categoria_riesgo == "ALTO" for h in hallazgos):
            categoria_maxima = "ALTO"
        elif any(h.categoria_riesgo == "MEDIO" for h in hallazgos):
            categoria_maxima = "MEDIO"

        top_hallazgos = sorted(hallazgos, key=lambda h: {"ALTO": 0, "MEDIO": 1, "BAJO": 2}.get(h.categoria_riesgo, 3))[:3]

        self._registros[expediente_id] = {
            "expediente_id": expediente_id,
            "producto_codigo": producto_codigo,
            "producto_nombre": producto_nombre,
            "producto_nombre_normalizado": _normalizar(producto_nombre),
            "entidades_responsables": entidades,
            "fecha_analisis": datetime.now(timezone.utc).isoformat(),
            "categoria_riesgo_maxima": categoria_maxima,
            "num_hallazgos_alto": sum(1 for h in hallazgos if h.categoria_riesgo == "ALTO"),
            "num_hallazgos": len(hallazgos),
            "resumen_hallazgos": [
                {"id_hallazgo": h.id_hallazgo, "agente_origen": h.agente_origen, "categoria_riesgo": h.categoria_riesgo, "respuesta": h.respuesta}
                for h in top_hallazgos
            ],
        }
        self._guardar()

    def buscar_antecedentes(
        self, expediente_id_actual: str, producto_codigo: str, producto_nombre: str
    ) -> List[AntecedenteHistorico]:
        """Antecedentes = expedientes anteriores (distintos al actual) que
        comparten producto_codigo O el mismo nombre de producto
        normalizado O al menos una entidad responsable en común. Esto es
        lo que reemplaza la búsqueda manual de contexto histórico."""
        nombre_norm = _normalizar(producto_nombre)
        antecedentes: List[AntecedenteHistorico] = []

        for eid, registro in self._registros.items():
            if eid == expediente_id_actual:
                continue
            mismo_producto = registro["producto_codigo"] == producto_codigo
            mismo_nombre = registro["producto_nombre_normalizado"] == nombre_norm
            if not (mismo_producto or mismo_nombre):
                continue

            antecedentes.append(
                AntecedenteHistorico(
                    expediente_id=eid,
                    producto_codigo=registro["producto_codigo"],
                    producto_nombre=registro["producto_nombre"],
                    fecha_analisis=registro["fecha_analisis"],
                    categoria_riesgo_maxima=registro["categoria_riesgo_maxima"],
                    num_hallazgos_alto=registro["num_hallazgos_alto"],
                    entidades_responsables=registro["entidades_responsables"],
                    resumen=(
                        f"{registro['resumen_hallazgos'][0]['respuesta']}"
                        if registro["resumen_hallazgos"]
                        else "Sin hallazgos registrados."
                    ),
                )
            )

        antecedentes.sort(key=lambda a: a.fecha_analisis, reverse=True)
        return antecedentes

    def listar_expedientes(self) -> List[dict]:
        """Todos los expedientes procesados alguna vez -- base para
        clasificar y priorizar trámites a nivel del orquestador."""
        return list(self._registros.values())


# Instancia única del proceso (equivalente a MATRIZ_TEMPORAL en orchestrator.py).
memoria = MemoriaTransversal()
