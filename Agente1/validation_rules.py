"""Lógica de negocio del Agente 1 (Tarea 2): completitud documental,
coherencia de roles y alertas tempranas de vigencia sobre lo extraído del
Módulo 1. Nunca emite una decisión final -- cada Hallazgo trae su propia
`accion_sugerida_evaluador` para que el humano decida."""
from __future__ import annotations

from datetime import date, datetime
from itertools import combinations
from typing import Dict, List, Optional, Set, Tuple

from schemas import (
    DocumentoModulo1,
    ExtraccionDocumento,
    Hallazgo,
    TIPOS_DOCUMENTO_REQUERIDOS,
    TIPOS_DOCUMENTO_REQUERIDOS_EXTRA,
    UMBRAL_ALERTA_DIAS_POR_TIPO,
    UbicacionExacta,
)

UMBRAL_ALERTA_DIAS = 90  # fallback si no se reconoce el tipo_producto


def _siguiente_id(contador: List[int]) -> str:
    contador[0] += 1
    return f"HLZ-{contador[0]:03d}"


def _normalizar(texto: str) -> str:
    return " ".join(texto.strip().upper().split())


def _ubicacion(doc: DocumentoModulo1, entidad_responsable: str, modulo_seccion: str) -> UbicacionExacta:
    return UbicacionExacta(
        documento_id=doc.documento_id,
        modulo_seccion=modulo_seccion,
        version=doc.version,
        fecha_documento=doc.fecha_documento,
        pagina_folio=doc.pagina_folio,
        entidad_responsable=entidad_responsable or "N/A",
    )


def validar_completitud(
    extracciones: List[ExtraccionDocumento],
    contador: List[int],
    tipo_producto: str = "SINTESIS_QUIMICA",
) -> Optional[Hallazgo]:
    requeridos = TIPOS_DOCUMENTO_REQUERIDOS | TIPOS_DOCUMENTO_REQUERIDOS_EXTRA.get(tipo_producto, set())
    presentes = {e.tipo_documento for e in extracciones}
    faltantes = sorted(requeridos - presentes)
    if not faltantes:
        return None

    return Hallazgo(
        id_hallazgo=_siguiente_id(contador),
        categoria_riesgo="ALTO",
        respuesta=f"Faltan documentos obligatorios del Módulo 1: {', '.join(faltantes)}.",
        evidencia_citada=f"Tipos de documento recibidos en esta carga: {', '.join(sorted(presentes)) or 'ninguno'}.",
        ubicacion_exacta=UbicacionExacta(
            documento_id="NO_ENCONTRADO",
            modulo_seccion="M1 / Legal",
            version="N/A",
            fecha_documento="N/A",
            pagina_folio="N/A",
            entidad_responsable="N/A",
        ),
        nivel_confianza=0.95,
        contradicciones_detectadas=[],
        informacion_faltante=[f"Documento tipo {f} no presente en el expediente cargado." for f in faltantes],
        limitaciones_ia="La verificación cubre únicamente los documentos efectivamente cargados en esta solicitud; no consulta el expediente físico completo.",
        accion_sugerida_evaluador=f"Solicitar al titular los documentos faltantes ({', '.join(faltantes)}) antes de continuar la evaluación.",
    )


def validar_coherencia_roles(
    documentos: List[DocumentoModulo1],
    extracciones: List[ExtraccionDocumento],
    contador: List[int],
) -> List[Hallazgo]:
    doc_por_id: Dict[str, DocumentoModulo1] = {d.documento_id: d for d in documentos}
    por_tipo: Dict[str, List[ExtraccionDocumento]] = {}
    for e in extracciones:
        por_tipo.setdefault(e.tipo_documento, []).append(e)

    formulario = next(iter(por_tipo.get("FORMULARIO_SOLICITUD", [])), None)
    bpm = next(iter(por_tipo.get("BPM", [])), None)

    hallazgos: List[Hallazgo] = []
    if formulario and bpm and formulario.fabricante and bpm.fabricante:
        if _normalizar(formulario.fabricante) != _normalizar(bpm.fabricante):
            doc_bpm = doc_por_id.get(bpm.documento_id)
            hallazgos.append(
                Hallazgo(
                    id_hallazgo=_siguiente_id(contador),
                    categoria_riesgo="ALTO",
                    respuesta=(
                        f"El fabricante declarado en el formulario de solicitud "
                        f"('{formulario.fabricante}') no coincide con el fabricante "
                        f"reportado en el certificado BPM ('{bpm.fabricante}')."
                    ),
                    evidencia_citada=(
                        f"Formulario: fabricante declarado '{formulario.fabricante}'. "
                        f"BPM: fabricante '{bpm.fabricante}'."
                    ),
                    ubicacion_exacta=_ubicacion(doc_bpm, entidad_responsable=bpm.fabricante, modulo_seccion="M1 / Legal — BPM")
                    if doc_bpm
                    else UbicacionExacta(
                        documento_id=bpm.documento_id,
                        modulo_seccion="M1 / Legal — BPM",
                        version="N/A",
                        fecha_documento="N/A",
                        pagina_folio="N/A",
                        entidad_responsable=bpm.fabricante,
                    ),
                    nivel_confianza=0.85,
                    contradicciones_detectadas=[
                        f"Fabricante en formulario ('{formulario.fabricante}') no coincide con el reportado en el BPM ('{bpm.fabricante}')."
                    ],
                    informacion_faltante=[],
                    limitaciones_ia="Comparación textual normalizada (mayúsculas/espacios); no evalúa si ambas entidades pertenecen al mismo grupo corporativo ni variantes de razón social.",
                    accion_sugerida_evaluador="Solicitar aclaración al titular sobre la identidad real del fabricante y, si aplica, un BPM emitido a nombre correcto.",
                )
            )
    return hallazgos


def validar_coherencia_campo(
    campo: str,
    etiqueta: str,
    documentos: List[DocumentoModulo1],
    extracciones: List[ExtraccionDocumento],
    contador: List[int],
) -> List[Hallazgo]:
    """Compara un mismo rol (titular, importador, ...) declarado en más de
    un documento del Módulo 1 -- no solo fabricante vs. BPM. Marca
    discrepancia si dos documentos distintos reportan valores distintos
    para el mismo campo."""
    doc_por_id: Dict[str, DocumentoModulo1] = {d.documento_id: d for d in documentos}
    con_valor = [(e, getattr(e, campo)) for e in extracciones]
    con_valor = [(e, v) for e, v in con_valor if v]

    hallazgos: List[Hallazgo] = []
    vistos: Set[Tuple[str, str]] = set()
    for (e1, v1), (e2, v2) in combinations(con_valor, 2):
        if _normalizar(v1) == _normalizar(v2):
            continue
        clave = tuple(sorted([e1.documento_id, e2.documento_id]))
        if clave in vistos:
            continue
        vistos.add(clave)

        doc2 = doc_por_id.get(e2.documento_id)
        ubicacion = (
            _ubicacion(doc2, entidad_responsable=v2, modulo_seccion=f"M1 / Legal — {e2.tipo_documento}")
            if doc2
            else UbicacionExacta(
                documento_id=e2.documento_id,
                modulo_seccion=f"M1 / Legal — {e2.tipo_documento}",
                version="N/A",
                fecha_documento="N/A",
                pagina_folio="N/A",
                entidad_responsable=v2,
            )
        )
        hallazgos.append(
            Hallazgo(
                id_hallazgo=_siguiente_id(contador),
                categoria_riesgo="ALTO",
                respuesta=(
                    f"El {etiqueta} reportado en {e1.tipo_documento} ('{v1}') no coincide "
                    f"con el reportado en {e2.tipo_documento} ('{v2}')."
                ),
                evidencia_citada=f"{e1.tipo_documento}: '{v1}'. {e2.tipo_documento}: '{v2}'.",
                ubicacion_exacta=ubicacion,
                nivel_confianza=0.8,
                contradicciones_detectadas=[
                    f"{etiqueta.capitalize()} distinto entre {e1.tipo_documento} y {e2.tipo_documento}."
                ],
                informacion_faltante=[],
                limitaciones_ia="Comparación textual normalizada; no evalúa variantes de razón social ni errores de digitación menores.",
                accion_sugerida_evaluador=(
                    f"Solicitar aclaración al titular sobre el {etiqueta} correcto y homologar la "
                    "documentación del Módulo 1."
                ),
            )
        )
    return hallazgos


def validar_vigencias(
    documentos: List[DocumentoModulo1],
    extracciones: List[ExtraccionDocumento],
    contador: List[int],
    hoy: Optional[date] = None,
    tipo_producto: str = "SINTESIS_QUIMICA",
) -> List[Hallazgo]:
    hoy = hoy or date.today()
    umbral_dias = UMBRAL_ALERTA_DIAS_POR_TIPO.get(tipo_producto, UMBRAL_ALERTA_DIAS)
    doc_por_id: Dict[str, DocumentoModulo1] = {d.documento_id: d for d in documentos}
    hallazgos: List[Hallazgo] = []

    for e in extracciones:
        if not e.fecha_vigencia:
            continue
        doc = doc_por_id.get(e.documento_id)
        if doc is None:
            continue
        try:
            fecha_vig = datetime.strptime(e.fecha_vigencia, "%Y-%m-%d").date()
        except ValueError:
            continue

        dias = (fecha_vig - hoy).days
        entidad = e.fabricante or e.titular or "N/A"

        if dias < 0:
            riesgo = "ALTO"
            texto = f"El documento {e.tipo_documento} ({doc.documento_id}) está vencido desde hace {abs(dias)} día(s) (venció el {e.fecha_vigencia})."
            accion = f"Solicitar de inmediato la renovación del {e.tipo_documento} al responsable antes de continuar la evaluación."
        elif dias < umbral_dias:
            riesgo = "MEDIO"
            texto = f"El documento {e.tipo_documento} ({doc.documento_id}) está próximo a vencer: quedan {dias} día(s) (vence el {e.fecha_vigencia})."
            accion = f"Notificar al titular sobre la próxima renovación del {e.tipo_documento}."
        else:
            riesgo = "BAJO"
            texto = f"El documento {e.tipo_documento} ({doc.documento_id}) está vigente: quedan {dias} día(s) (vence el {e.fecha_vigencia})."
            accion = "Sin acción requerida por vigencia; continuar con la evaluación normal."

        hallazgos.append(
            Hallazgo(
                id_hallazgo=_siguiente_id(contador),
                categoria_riesgo=riesgo,
                respuesta=texto,
                evidencia_citada=e.cita_textual or f"Fecha de vigencia declarada en el documento: {e.fecha_vigencia}",
                ubicacion_exacta=_ubicacion(doc, entidad_responsable=entidad, modulo_seccion=f"M1 / Legal — {e.tipo_documento}"),
                nivel_confianza=0.9 if e.cita_textual else 0.6,
                contradicciones_detectadas=[],
                informacion_faltante=[],
                limitaciones_ia="La fecha se toma tal como fue extraída del texto del documento; no valida la autenticidad del sello ni de la firma originales.",
                accion_sugerida_evaluador=accion,
            )
        )

    return hallazgos
