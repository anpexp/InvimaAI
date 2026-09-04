"""
Cliente mínimo para OpenFDA. Es de solo-lectura y sin autenticación,
pero puede fallar por red o por no encontrar la molécula: en ambos casos
debe degradar con gracia (nunca tumbar el request del agente).
"""
import requests
from typing import Optional, Dict, Any

OPENFDA_URL = "https://api.fda.gov/drug/label.json"


def buscar_historial_fda(molecula: str, timeout: float = 4.0) -> Dict[str, Any]:
    """
    Devuelve algo como:
      {"encontrado": True, "num_registros": 3, "detalle": "..."}
      {"encontrado": False, "motivo": "sin_resultados" | "error_red"}
    """
    if not molecula:
        return {"encontrado": False, "motivo": "sin_molecula"}

    try:
        resp = requests.get(
            OPENFDA_URL,
            params={"search": f"openfda.generic_name:{molecula}", "limit": 1},
            timeout=timeout,
        )
        if resp.status_code != 200:
            return {"encontrado": False, "motivo": f"http_{resp.status_code}"}

        data = resp.json()
        total = data.get("meta", {}).get("results", {}).get("total", 0)
        if total > 0:
            return {
                "encontrado": True,
                "num_registros": total,
                "detalle": f"{molecula} tiene {total} registro(s) previos en FDA (openFDA drug label).",
            }
        return {"encontrado": False, "motivo": "sin_resultados"}

    except requests.RequestException:
        return {"encontrado": False, "motivo": "error_red"}
