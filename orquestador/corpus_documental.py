"""Corpus documental citable de un expediente -- reutiliza los mismos
payloads que el Orquestador ya envía a los Agentes 1, 2 y 3 (ver
mock_dossiers.py) para no duplicar el dossier simulado en dos lugares.

Cada elemento del corpus es un fragmento con su documento_id y folio
EXACTOS, para que /orquestador/consultar pueda citar el documento real
en vez de inventar una referencia."""
from __future__ import annotations

from typing import Any, Dict, List

from mock_dossiers import dossier_agente1, dossier_agente2, dossier_agente3

_ETIQUETA_ATRIBUTO = {
    "nombre_por_modulo": "nombre del producto",
    "concentracion_por_modulo": "concentración",
    "almacenamiento_por_modulo": "condición de almacenamiento",
}


def construir_corpus(
    expediente_id: str, producto_codigo: str, producto_nombre: str, tipo_producto: str = "SINTESIS_QUIMICA"
) -> List[Dict[str, Any]]:
    corpus: List[Dict[str, Any]] = []

    # --- Agente 1 (Legal): documentos del Módulo 1 tal cual ---
    d1 = dossier_agente1(expediente_id, producto_codigo, producto_nombre, tipo_producto)
    for doc in d1["documentos"]:
        corpus.append(
            {
                "documento_id": doc["documento_id"],
                "modulo_seccion": f"M1 / Legal — {doc['tipo_documento']}",
                "pagina_folio": doc["pagina_folio"],
                "version": doc.get("version", "N/A"),
                "fecha_documento": doc.get("fecha_documento", "N/A"),
                "entidad_responsable": "N/A",
                "texto": doc["texto"],
            }
        )

    # --- Agente 2 (Reliance): comparaciones por módulo, convertidas a texto citable ---
    d2 = dossier_agente2(expediente_id, producto_codigo, producto_nombre, tipo_producto)
    for campo_lista, etiqueta in _ETIQUETA_ATRIBUTO.items():
        for campo in d2.get(campo_lista, []):
            corpus.append(
                {
                    "documento_id": campo["documento_id"],
                    "modulo_seccion": f"{campo['modulo']} / Calidad-Reliance — {etiqueta}",
                    "pagina_folio": campo["pagina_folio"],
                    "version": campo.get("version", "N/A"),
                    "fecha_documento": campo.get("fecha_documento", "N/A"),
                    "entidad_responsable": campo.get("entidad_responsable", "N/A"),
                    "texto": f"Módulo {campo['modulo']} reporta {etiqueta}: '{campo['valor']}'.",
                }
            )

    # --- Agente 3 (Clínico): afirmaciones del Módulo 2 + evidencia primaria ---
    d3 = dossier_agente3(expediente_id, producto_codigo, producto_nombre, tipo_producto)
    for af in d3.get("afirmaciones_modulo2", []):
        corpus.append(
            {
                "documento_id": af["documento_id"],
                "modulo_seccion": "M2 (resumen clínico)",
                "pagina_folio": af["pagina_folio"],
                "version": "N/A",
                "fecha_documento": "N/A",
                "entidad_responsable": "N/A",
                "texto": af["texto"],
            }
        )
    for ev in d3.get("evidencia_primaria", []):
        corpus.append(
            {
                "documento_id": ev["documento_id"],
                "modulo_seccion": f"{ev['modulo']} (evidencia primaria)",
                "pagina_folio": ev["pagina_folio"],
                "version": ev.get("version", "N/A"),
                "fecha_documento": ev.get("fecha_documento", "N/A"),
                "entidad_responsable": ev.get("entidad_responsable", "N/A"),
                "texto": ev["texto"],
            }
        )

    return corpus
