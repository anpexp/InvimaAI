"""
Reglas deterministas de comparación cruzada entre módulos.
Nada de LLM aquí: son comparaciones de strings/valores, que es justo
lo que hace a este agente rápido y confiable para el demo.
"""
from itertools import combinations
from typing import List
from schemas import ModuloCampo, Hallazgo, UbicacionExacta

CATEGORIA_POR_ATRIBUTO = {
    "nombre": "ALTO",
    "concentracion": "ALTO",
    "almacenamiento": "MEDIO",
}

# Biológicos y vacunas dependen de cadena de frío: cualquier discrepancia
# de almacenamiento entre módulos es crítica, no solo un riesgo medio.
TIPOS_PRODUCTO_CADENA_FRIO_CRITICA = {"BIOLOGICO", "VACUNA"}


def _normalizar(valor: str) -> str:
    return " ".join(valor.strip().lower().split())


def comparar_atributo(
    atributo: str,
    campos: List[ModuloCampo],
    contador: List[int],
    tipo_producto: str = "SINTESIS_QUIMICA",
) -> List[Hallazgo]:
    """Compara un mismo atributo (ej. concentración) reportado en varios
    módulos. Genera un hallazgo por cada par de módulos que difiere."""
    hallazgos: List[Hallazgo] = []

    categoria = CATEGORIA_POR_ATRIBUTO.get(atributo, "MEDIO")
    if atributo == "almacenamiento" and tipo_producto in TIPOS_PRODUCTO_CADENA_FRIO_CRITICA:
        categoria = "ALTO"

    for campo_a, campo_b in combinations(campos, 2):
        if _normalizar(campo_a.valor) == _normalizar(campo_b.valor):
            continue

        contador[0] += 1
        hid = f"HLZ-{contador[0]:03d}"

        nota_tipo_producto = (
            f" Riesgo elevado por tratarse de un producto {tipo_producto.lower().replace('_', ' ')} "
            "sujeto a cadena de frío."
            if categoria == "ALTO" and atributo == "almacenamiento" and tipo_producto in TIPOS_PRODUCTO_CADENA_FRIO_CRITICA
            else ""
        )

        hallazgos.append(
            Hallazgo(
                id_hallazgo=hid,
                categoria_riesgo=categoria,
                respuesta=(
                    f"Inconsistencia en {atributo} entre "
                    f"{campo_a.modulo} y {campo_b.modulo}.{nota_tipo_producto}"
                ),
                evidencia_citada=(
                    f"{campo_a.modulo} indica '{campo_a.valor}'. "
                    f"{campo_b.modulo} indica '{campo_b.valor}'."
                ),
                ubicacion_exacta=UbicacionExacta(
                    documento_id=f"Cross-reference {campo_a.modulo} vs {campo_b.modulo}",
                    modulo_seccion=f"{campo_a.modulo} / {campo_b.modulo}",
                    version=campo_a.version,
                    fecha_documento=campo_a.fecha_documento,
                    pagina_folio=f"{campo_a.modulo}: {campo_a.pagina_folio} / {campo_b.modulo}: {campo_b.pagina_folio}",
                    entidad_responsable=campo_a.entidad_responsable,
                ),
                nivel_confianza=0.99,
                contradicciones_detectadas=[
                    f"Conflicto de {atributo}: {campo_a.modulo} ('{campo_a.valor}') "
                    f"vs {campo_b.modulo} ('{campo_b.valor}')"
                ],
                informacion_faltante=[],
                limitaciones_ia=(
                    "No se infiere cuál valor es el correcto, solo se detecta "
                    "la discrepancia entre módulos."
                ),
                accion_sugerida_evaluador=(
                    f"Emitir requerimiento de aclaración técnica sobre {atributo} real."
                ),
            )
        )

    return hallazgos
