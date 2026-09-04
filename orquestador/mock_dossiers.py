"""Datos de expediente simulados para el demo (Hackatón INVIMA del Futuro).

En producción esto vendría de la carga documental real del solicitante.
Para el prototipo, el Orquestador "simula la carga documental" armando
estos payloads y enviándolos a cada agente en el contrato de entrada que
cada uno espera (ver Agente2/schemas.py y Agente3/schemas.py).

Todos los valores aquí son ficticios (caso CORAZILIMAB acordado por el
equipo, ver agente2_reliance/sample_input.json y
agente3_clinico/sample_input.json).
"""
from __future__ import annotations

from typing import Any, Dict, List

DEMO_PRODUCTO_CODIGO = "CRZ-042"
DEMO_PRODUCTO_NOMBRE = "CORAZILIMAB"
DEMO_TITULAR = "Biofarma Andina S.A.S."


def dossier_agente1(
    expediente_id: str, producto_codigo: str, producto_nombre: str, tipo_producto: str = "SINTESIS_QUIMICA"
) -> Dict[str, Any]:
    """Payload para POST /analyze/legal del Agente 1 (ExpedienteLegalInput).

    Documentos del Módulo 1 con 3 problemas deliberados para el demo:
    falta el Poder (completitud), el fabricante del BPM no coincide con
    el del Formulario (coherencia de roles), y el CPP ya venció mientras
    el BPM vence en menos de 90 días (vigencias). Mismo set que
    `Agente1/sample_input.json`.
    """
    return {
        "expediente_id": expediente_id,
        "producto_codigo": producto_codigo,
        "producto_nombre": producto_nombre,
        "tipo_producto": tipo_producto,
        "documentos": [
            {
                "documento_id": "M1-00-01",
                "tipo_documento": "FORMULARIO_SOLICITUD",
                "texto": (
                    f"Solicitud de registro sanitario para {producto_nombre} ({producto_nombre.lower()}), "
                    "concentracion 50 mg/mL, forma farmaceutica solucion inyectable. "
                    f"Titular: {DEMO_TITULAR} Fabricante declarado: Laboratorios PharmaCorp S.A."
                ),
                "version": "v1.0",
                "fecha_documento": "2026-01-10",
                "pagina_folio": "Folio 3",
            },
            {
                "documento_id": "M1-00-05",
                "tipo_documento": "BPM",
                "texto": (
                    "Certificado de Buenas Practicas de Manufactura (BPM). "
                    "Planta: Cali, Colombia. Fabricante: Manufacturas Quimicas del Cauca S.A.S. "
                    "Vigencia hasta: 2026-09-20."
                ),
                "version": "v1.0",
                "fecha_documento": "2025-09-20",
                "pagina_folio": "Folio 45",
            },
            {
                "documento_id": "M1-00-08",
                "tipo_documento": "CPP",
                "texto": (
                    f"Certificado de Producto Farmaceutico (CPP) para {producto_nombre}, emitido por la "
                    f"autoridad sanitaria de origen. Titular: {DEMO_TITULAR} Vigencia hasta: 2026-07-01."
                ),
                "version": "v1.0",
                "fecha_documento": "2024-07-01",
                "pagina_folio": "Folio 60",
            },
        ],
    }


def dossier_agente2(
    expediente_id: str, producto_codigo: str, producto_nombre: str, tipo_producto: str = "SINTESIS_QUIMICA"
) -> Dict[str, Any]:
    """Payload para POST /agente2/analizar (ExpedienteInput)."""
    return {
        "expediente_id": expediente_id,
        "producto_codigo": producto_codigo,
        "producto_nombre": producto_nombre,
        "tipo_producto": tipo_producto,
        "molecula": producto_nombre.lower(),
        "nombre_por_modulo": [
            {"modulo": "M1", "valor": producto_nombre.title(), "documento_id": "M1-01-01", "pagina_folio": "Folio 5"},
            {"modulo": "M3", "valor": producto_nombre.title(), "documento_id": "M3-02-01", "pagina_folio": "Folio 2100"},
            {"modulo": "M8", "valor": f"{producto_nombre.title()} Inyectable", "documento_id": "M8-01-01", "pagina_folio": "Folio 450"},
        ],
        "concentracion_por_modulo": [
            {"modulo": "M1", "valor": "50 mg/mL", "documento_id": "M1-01-02", "pagina_folio": "Folio 6"},
            {"modulo": "M3", "valor": "50 mg/mL", "documento_id": "M3-02-05", "pagina_folio": "Folio 2110"},
            {"modulo": "M8", "valor": "50 mg/mL", "documento_id": "M8-01-01", "pagina_folio": "Folio 451"},
        ],
        "almacenamiento_por_modulo": [
            {"modulo": "M3", "valor": "15-25°C", "documento_id": "M3-02-08", "pagina_folio": "Folio 2151", "entidad_responsable": DEMO_TITULAR},
            {"modulo": "M8", "valor": "2-8°C", "documento_id": "M8-02-01", "pagina_folio": "Folio 450", "entidad_responsable": DEMO_TITULAR},
        ],
    }


def dossier_agente3(
    expediente_id: str, producto_codigo: str, producto_nombre: str, tipo_producto: str = "SINTESIS_QUIMICA"
) -> Dict[str, Any]:
    """Payload para POST /agente3/analizar (ExpedienteClinicoInput)."""
    return {
        "expediente_id": expediente_id,
        "producto_codigo": producto_codigo,
        "producto_nombre": producto_nombre,
        "tipo_producto": tipo_producto,
        "afirmaciones_modulo2": [
            {
                "id": "AF-001",
                "texto": "El estudio pivotal demostró reducción significativa de eventos cardiovasculares mayores frente a placebo.",
                "documento_id": "M2-01-01",
                "pagina_folio": "Folio 30",
            },
            {
                "id": "AF-002",
                "texto": "El producto demostró superioridad frente al tratamiento estándar en población pediátrica menor de 12 años.",
                "documento_id": "M2-01-02",
                "pagina_folio": "Folio 31",
            },
        ],
        "evidencia_primaria": [
            {
                "id": "EV-001",
                "modulo": "M3",
                "texto": "Estudio fase III, aleatorizado, doble ciego, 812 pacientes adultos, comparador placebo. Se observó reducción significativa de eventos cardiovasculares mayores (HR 0.72, IC95% 0.58-0.89).",
                "documento_id": "M3-05-01",
                "pagina_folio": "Folio 2200",
                "entidad_responsable": DEMO_TITULAR,
            },
            {
                "id": "EV-002",
                "modulo": "M4",
                "texto": "Estudios preclínicos en modelo animal de toxicidad crónica, sin hallazgos relevantes a dosis terapéuticas.",
                "documento_id": "M4-01-01",
                "pagina_folio": "Folio 1800",
                "entidad_responsable": DEMO_TITULAR,
            },
        ],
    }


def hallazgos_agente1_legal_mock(producto_nombre: str, titular: str = DEMO_TITULAR) -> List[Dict[str, Any]]:
    """Hallazgos simulados del Agente 1 (Legal / Módulo 1).

    No existe todavía un microservicio real para el Agente 1 en este
    repositorio: la carpeta `Agente1/` contiene, en realidad, una
    implementación alterna del Agente 3 Clínico (mismo README dice
    "INVIMA Agente 3"), no un agente legal. Mientras el equipo conecta un
    servicio real (ver AGENTE1_URL en orchestrator.py), estos hallazgos
    fijos permiten demostrar el flujo HITL completo para el rol LEGAL.
    """
    return [
        {
            "id_hallazgo": "HLZ-001",
            "categoria_riesgo": "BAJO",
            "respuesta": (
                f"Los poderes de representación del apoderado que radica el trámite de {producto_nombre} "
                "(Módulo 1) están vigentes y correctamente apostillados."
            ),
            "evidencia_citada": "Poder General No. PA-2026-0451, otorgado 2026-01-15, vigencia 2 años, apostilla de La Haya verificada.",
            "ubicacion_exacta": {
                "documento_id": "M1-00-03",
                "modulo_seccion": "M1 - Poderes y representación legal",
                "version": "v1.0",
                "fecha_documento": "2026-01-15",
                "pagina_folio": "Folio 12",
                "entidad_responsable": titular,
            },
            "nivel_confianza": 0.93,
            "contradicciones_detectadas": [],
            "informacion_faltante": [],
            "limitaciones_ia": "Verificación basada en los metadatos declarados del documento digitalizado; no reemplaza la validación notarial ni la confirmación ante la autoridad apostillante.",
            "accion_sugerida_evaluador": "Aceptar como válido salvo que el caso amerite verificación adicional ante la entidad emisora.",
        },
        {
            "id_hallazgo": "HLZ-002",
            "categoria_riesgo": "MEDIO",
            "respuesta": (
                "El nombre del titular declarado en la carta de solicitud del Módulo 1 no coincide "
                "textualmente con la razón social reportada en el certificado de existencia y representación legal."
            ),
            "evidencia_citada": (
                f"Carta de solicitud (folio 3): titular '{titular}'. "
                f"Certificado de Cámara de Comercio (folio 4): '{titular} BIC'."
            ),
            "ubicacion_exacta": {
                "documento_id": "M1-00-01",
                "modulo_seccion": "M1 - Correspondencia trámite / solicitante",
                "version": "v1.0",
                "fecha_documento": "2026-01-10",
                "pagina_folio": "Folio 3-4",
                "entidad_responsable": titular,
            },
            "nivel_confianza": 0.78,
            "contradicciones_detectadas": [
                "Diferencia en razón social entre la carta de solicitud y el certificado de existencia y representación legal.",
            ],
            "informacion_faltante": [],
            "limitaciones_ia": "La diferencia puede deberse a una actualización de denominación (p. ej. sigla BIC) no reflejada aún en todos los soportes; el agente no puede confirmar cuál versión es la vigente.",
            "accion_sugerida_evaluador": "Solicitar al titular un certificado de existencia y representación legal actualizado que unifique la razón social en todos los soportes del Módulo 1.",
        },
        {
            "id_hallazgo": "HLZ-003",
            "categoria_riesgo": "ALTO",
            "respuesta": "No se encontró, dentro de los documentos indexados del Módulo 1, el soporte de pago de la tarifa correspondiente a este trámite.",
            "evidencia_citada": "Búsqueda en el índice documental del Módulo 1 no arroja recibo ni consignación asociados al radicado.",
            "ubicacion_exacta": {
                "documento_id": "NO_ENCONTRADO",
                "modulo_seccion": "M1 - Tarifas",
                "version": "N/A",
                "fecha_documento": "N/A",
                "pagina_folio": "N/A",
                "entidad_responsable": titular,
            },
            "nivel_confianza": 0.65,
            "contradicciones_detectadas": [],
            "informacion_faltante": ["Soporte de pago de la tarifa del trámite."],
            "limitaciones_ia": "La ausencia de un soporte en el índice digital no garantiza su ausencia en el expediente físico o en el sistema de radicación; puede deberse a un error de digitalización.",
            "accion_sugerida_evaluador": "Verificar en el sistema de radicación oficial si el pago fue recibido antes de continuar con el trámite.",
        },
    ]
