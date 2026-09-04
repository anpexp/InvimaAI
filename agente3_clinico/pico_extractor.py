"""Extracción estructurada mínima de características de estudio (diseño,
número de participantes, población, comparador, desenlace) a partir del
fragmento de evidencia primaria que sustenta una afirmación del Módulo 2.

Puramente basada en patrones de texto explícitos -- si un patrón no
aparece literalmente en el fragmento, ese campo se omite. Nunca se
inventa ni se infiere un valor no presente (misma regla de oro que
llm_client.py)."""
from __future__ import annotations

import re
from typing import Optional

_PATRON_DISENO = re.compile(
    r"(fase\s+[IVX]+[^,\.]*|aleatorizad[oa][^,\.]*|doble\s+ciego[^,\.]*)", re.IGNORECASE
)
_PATRON_N = re.compile(r"(\d+)\s+pacientes", re.IGNORECASE)
_PATRON_POBLACION = re.compile(r"pacientes\s+([a-záéíóúñ]+(?:\s+con\s+[^,\.]+)?)", re.IGNORECASE)
_PATRON_COMPARADOR = re.compile(r"comparador\s+([^,\.]+)|frente a\s+([^,\.]+)", re.IGNORECASE)
_PATRON_DESENLACE = re.compile(
    r"\b(?:HR|OR|RR)\s*[:=]?\s*[\d.]+(?:,\s*IC\s*9[05]%\s*[\d.]+-[\d.]+)?", re.IGNORECASE
)


def extraer_caracteristicas_estudio(texto: str) -> Optional[str]:
    """Devuelve un resumen estructurado tipo 'Diseño: ... · N=... ·
    Población: ... · Comparador: ... · Desenlace: ...', o None si el
    fragmento no parece describir un estudio (no hay nada que extraer)."""
    if "fase" not in texto.lower() and "estudio" not in texto.lower():
        return None

    partes = []

    m = _PATRON_DISENO.search(texto)
    if m:
        partes.append(f"Diseño: {m.group(1).strip()}")

    m = _PATRON_N.search(texto)
    if m:
        partes.append(f"N={m.group(1)} participantes")

    m = _PATRON_POBLACION.search(texto)
    if m:
        partes.append(f"Población: {m.group(1).strip()}")

    m = _PATRON_COMPARADOR.search(texto)
    if m:
        comparador = (m.group(1) or m.group(2) or "").strip()
        if comparador:
            partes.append(f"Comparador: {comparador}")
    elif "placebo" in texto.lower():
        partes.append("Comparador: placebo")

    m = _PATRON_DESENLACE.search(texto)
    if m:
        partes.append(f"Desenlace reportado: {m.group(0).strip()}")

    if not partes:
        return None
    return " · ".join(partes)
