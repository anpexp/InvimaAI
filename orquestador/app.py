"""Dashboard Personalizado — Hackatón INVIMA del Futuro.

Regla de negocio inquebrantable: este panel NO reemplaza al evaluador ni
su responsabilidad. Cada hallazgo debe ser aprobado, modificado o
rechazado explícitamente por un humano antes de entrar al informe final
(Human-in-the-Loop). El texto que llega de los agentes se renderiza
siempre como texto plano (sin `unsafe_allow_html` sobre contenido de
agentes/dossiers) para no interpretar como marcado nada que venga de un
documento cargado.
"""
from __future__ import annotations

import os
from typing import Optional

import requests
import streamlit as st

ORQUESTADOR_URL = os.getenv("ORQUESTADOR_URL", "http://localhost:8080")

ROLES = {
    "LEGAL": {
        "agente": "AGENTE_1_LEGAL",
        "etiqueta": "⚖️ Legal",
        "foco": "vigencia de poderes, correspondencia trámite/solicitante y Módulo 1",
    },
    "CALIDAD": {
        "agente": "AGENTE_2_RELIANCE",
        "etiqueta": "🧪 Calidad / Farmacéutico",
        "foco": "consistencia entre módulos (M1/M3/M8) y antecedentes de reliance",
    },
    "CLINICO": {
        "agente": "AGENTE_3_CLINICO",
        "etiqueta": "🩺 Clínico / Farmacológico",
        "foco": "estudios clínicos y soporte de eficacia del Módulo 2",
    },
}

RIESGO_COLOR = {"BAJO": "#10B981", "MEDIO": "#F59E0B", "ALTO": "#EF4444"}
ESTADO_COLOR = {"PENDIENTE": "#6B7280", "APROBADO": "#10B981", "MODIFICADO": "#3B82F6", "RECHAZADO": "#EF4444"}

st.set_page_config(page_title="INVIMA · Orquestador HITL", layout="wide", page_icon="🧭")


# --------------------------------------------------------------------------
# Estado de sesión
# --------------------------------------------------------------------------
st.session_state.setdefault("expediente_id", "2026-REG-CRZ-001784")
st.session_state.setdefault("hallazgos", [])
st.session_state.setdefault("estados_agentes", [])
st.session_state.setdefault("antecedentes_historicos", [])
st.session_state.setdefault("resumen_expediente", None)
st.session_state.setdefault("matriz_cargada", False)
st.session_state.setdefault("ultimo_rol", None)
st.session_state.setdefault("editando", None)  # clave del hallazgo en edición
st.session_state.setdefault("historial_consultas", {})  # expediente_id -> [respuestas]

PRIORIDAD_COLOR = {"ALTA": "#EF4444", "MEDIA": "#F59E0B", "BAJA": "#10B981"}


def badge(texto: str, color: str) -> str:
    return f"<span style='background:{color};color:white;padding:2px 10px;border-radius:12px;font-size:0.8em;margin-right:6px;white-space:nowrap;'>{texto}</span>"


def llamar_orquestador(expediente_id: str, tipo_producto: str, rol_evaluador: str) -> None:
    try:
        resp = requests.post(
            f"{ORQUESTADOR_URL}/orquestador/analizar",
            json={"expediente_id": expediente_id, "tipo_producto": tipo_producto, "rol_evaluador": rol_evaluador},
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        st.session_state.hallazgos = data["hallazgos"]
        st.session_state.estados_agentes = data["estados_agentes"]
        st.session_state.antecedentes_historicos = data.get("antecedentes_historicos", [])
        st.session_state.resumen_expediente = data.get("resumen_expediente")
        st.session_state.matriz_cargada = True
        st.session_state.ultimo_rol = rol_evaluador
    except requests.RequestException as exc:
        st.error(f"No se pudo contactar al Orquestador en {ORQUESTADOR_URL}: {exc}")


def consultar_dossier(expediente_id: str, tipo_producto: str, pregunta: str) -> None:
    try:
        resp = requests.post(
            f"{ORQUESTADOR_URL}/orquestador/consultar",
            json={"expediente_id": expediente_id, "tipo_producto": tipo_producto, "pregunta": pregunta},
            timeout=30,
        )
        resp.raise_for_status()
        # Historial por expediente: preguntas de un expediente anterior no
        # deben quedar "flotando" cuando se cambia a otro expediente_id.
        st.session_state.historial_consultas.setdefault(expediente_id, []).insert(0, resp.json())
    except requests.RequestException as exc:
        st.error(f"No se pudo consultar el dossier: {exc}")


def refrescar_matriz(expediente_id: str, rol_evaluador: str) -> None:
    try:
        resp = requests.get(
            f"{ORQUESTADOR_URL}/orquestador/matriz/{expediente_id}",
            params={"rol_evaluador": rol_evaluador},
            timeout=15,
        )
        resp.raise_for_status()
        st.session_state.hallazgos = resp.json()
        st.session_state.ultimo_rol = rol_evaluador
    except requests.RequestException as exc:
        st.error(f"No se pudo refrescar la matriz: {exc}")


def enviar_decision(
    hallazgo: dict,
    decision: str,
    rol_evaluador: str,
    respuesta_modificada: Optional[str] = None,
    comentario: Optional[str] = None,
) -> None:
    try:
        resp = requests.post(
            f"{ORQUESTADOR_URL}/orquestador/hallazgo/decision",
            json={
                "expediente_id": hallazgo["expediente_id"],
                "id_hallazgo": hallazgo["id_hallazgo"],
                "agente_origen": hallazgo["agente_origen"],
                "decision": decision,
                "rol_evaluador": rol_evaluador,
                "respuesta_modificada": respuesta_modificada,
                "comentario_evaluador": comentario,
            },
            timeout=15,
        )
        resp.raise_for_status()
        st.session_state.editando = None
    except requests.RequestException as exc:
        st.error(f"No se pudo registrar la decisión: {exc}")
        return


# --------------------------------------------------------------------------
# Sidebar: selector de rol + parámetros del expediente
# --------------------------------------------------------------------------
with st.sidebar:
    st.title("🧭 Panel del Evaluador")
    rol_evaluador = st.selectbox(
        "Rol del evaluador", options=list(ROLES.keys()), format_func=lambda r: ROLES[r]["etiqueta"]
    )
    st.caption(f"Este rol solo ve hallazgos de **{ROLES[rol_evaluador]['agente']}** — {ROLES[rol_evaluador]['foco']}.")

    expediente_id = st.text_input("ID de expediente", value=st.session_state.expediente_id)
    tipo_producto = st.selectbox("Tipo de producto", options=["SINTESIS_QUIMICA", "BIOLOGICO", "VACUNA"])

    if st.button("🚀 Ejecutar orquestación (simular carga documental)", use_container_width=True):
        st.session_state.expediente_id = expediente_id
        llamar_orquestador(expediente_id, tipo_producto, rol_evaluador)

    if st.session_state.estados_agentes:
        st.divider()
        st.caption("Estado de los agentes en la última ejecución")
        for estado in st.session_state.estados_agentes:
            if estado["ok"]:
                st.caption(f"🟢 {estado['agente_origen']} — {estado['num_hallazgos']} hallazgo(s)")
            else:
                st.caption(f"🔴 {estado['agente_origen']} — no disponible")

    st.divider()
    with st.expander("📋 Panel de trámites (clasificar y priorizar)"):
        try:
            resp_panel = requests.get(f"{ORQUESTADOR_URL}/orquestador/panel", timeout=15)
            resp_panel.raise_for_status()
            panel = resp_panel.json()
            if not panel:
                st.caption("Aún no se ha procesado ningún expediente en esta sesión del Orquestador.")
            for fila in panel:
                color = PRIORIDAD_COLOR.get(fila["prioridad"], "#6B7280")
                marca_incompleto = "" if fila["expediente_completo"] else " · ⚠️ incompleto"
                st.markdown(
                    badge(fila["prioridad"], color) + f"**{fila['expediente_id']}**{marca_incompleto}",
                    unsafe_allow_html=True,
                )
        except requests.RequestException:
            st.caption("Panel no disponible (¿el Orquestador está corriendo?).")

    st.divider()
    st.markdown(badge("DATO EXTRAÍDO", "#2563EB") + " texto citado literalmente del expediente.", unsafe_allow_html=True)
    st.markdown(badge("IA · INFERENCIA", "#7C3AED") + " interpretación/recomendación — requiere aprobación humana.", unsafe_allow_html=True)
    st.caption("⚠️ Este prototipo NO reemplaza al evaluador ni su responsabilidad. La IA asiste; el humano decide y aprueba.")

expediente_id = st.session_state.expediente_id

# Si cambia el rol y ya hay una matriz cargada para este expediente, refrescar
# la vista sin volver a llamar a los agentes.
if st.session_state.matriz_cargada and st.session_state.ultimo_rol != rol_evaluador:
    refrescar_matriz(expediente_id, rol_evaluador)


# --------------------------------------------------------------------------
# Cuerpo principal
# --------------------------------------------------------------------------
st.title("Orquestador Principal · Dashboard Personalizado")
st.caption(f"Expediente **{expediente_id}** — Vista: {ROLES[rol_evaluador]['etiqueta']}")

if not st.session_state.matriz_cargada:
    st.info("Ejecute la orquestación desde la barra lateral para simular la carga documental y traer los hallazgos del expediente.")
elif not st.session_state.hallazgos:
    st.success(f"No hay hallazgos de {ROLES[rol_evaluador]['agente']} para este expediente.")

resumen = st.session_state.resumen_expediente
if resumen:
    col_r1, col_r2, col_r3 = st.columns(3)
    col_r1.markdown(
        badge(f"Prioridad {resumen['prioridad']}", PRIORIDAD_COLOR.get(resumen["prioridad"], "#6B7280")),
        unsafe_allow_html=True,
    )
    col_r2.markdown(
        badge("✅ Completo", "#10B981") if resumen["expediente_completo"] else badge("⚠️ Incompleto", "#EF4444"),
        unsafe_allow_html=True,
    )
    col_r3.caption(f"{resumen['num_hallazgos_alto']} hallazgo(s) de riesgo ALTO de {resumen['num_hallazgos']} totales")
    if resumen["informacion_faltante"]:
        st.warning("**Expediente incompleto — información faltante (todos los agentes):**\n" + "\n".join(f"- {x}" for x in resumen["informacion_faltante"]))
    if resumen["agentes_no_disponibles"]:
        st.error(f"Agentes no disponibles en el último análisis: {', '.join(resumen['agentes_no_disponibles'])}")

antecedentes = st.session_state.antecedentes_historicos
if antecedentes:
    with st.expander(f"🕘 Memoria transversal — {len(antecedentes)} antecedente(s) relacionado(s)", expanded=False):
        st.caption("Otros expedientes ya evaluados para el mismo producto o entidad responsable.")
        for a in antecedentes:
            st.markdown(
                badge(a["categoria_riesgo_maxima"], RIESGO_COLOR.get(a["categoria_riesgo_maxima"], "#6B7280"))
                + f"**{a['expediente_id']}** ({a['fecha_analisis'][:10]}) — {a['resumen']}",
                unsafe_allow_html=True,
            )

for hallazgo in st.session_state.hallazgos:
    riesgo = hallazgo["categoria_riesgo"]
    estado = hallazgo["estado_revision"]
    clave_unica = f"{hallazgo['agente_origen']}_{hallazgo['id_hallazgo']}"

    with st.container(border=True):
        col_titulo, col_badges = st.columns([3, 2])
        with col_titulo:
            st.markdown(f"#### {hallazgo['id_hallazgo']}")
        with col_badges:
            st.markdown(
                badge(f"Riesgo {riesgo}", RIESGO_COLOR.get(riesgo, "#6B7280"))
                + badge(estado, ESTADO_COLOR.get(estado, "#6B7280")),
                unsafe_allow_html=True,
            )

        # --- DATO EXTRAÍDO ---
        st.markdown(badge("DATO EXTRAÍDO", "#2563EB"), unsafe_allow_html=True)
        st.text_area(
            "Evidencia citada",
            value=hallazgo["evidencia_citada"],
            height=70,
            disabled=True,
            key=f"ev_{clave_unica}",
            label_visibility="visible",
        )
        ubic = hallazgo["ubicacion_exacta"]
        st.caption(
            f"📍 Ubicación exacta — Módulo/Sección: **{ubic['modulo_seccion']}** · "
            f"Documento: **{ubic['documento_id']}** · Versión: **{ubic['version']}** · "
            f"Folio: **{ubic['pagina_folio']}** · Fecha: {ubic['fecha_documento']} · "
            f"Responsable: {ubic['entidad_responsable']}"
        )

        # --- INFERENCIA / RECOMENDACIÓN DE LA IA ---
        st.markdown(badge("IA · INFERENCIA", "#7C3AED"), unsafe_allow_html=True)
        respuesta_mostrada = hallazgo.get("respuesta_modificada") or hallazgo["respuesta"]
        if hallazgo.get("respuesta_modificada"):
            st.caption("✏️ Mostrando la versión modificada por el evaluador.")
        st.markdown(f"**Respuesta:** {respuesta_mostrada}")
        st.progress(min(max(hallazgo["nivel_confianza"], 0.0), 1.0), text=f"Nivel de confianza: {hallazgo['nivel_confianza']:.0%}")
        st.markdown(f"**➡️ Acción sugerida al evaluador:** {hallazgo['accion_sugerida_evaluador']}")

        if hallazgo.get("contradicciones_detectadas"):
            st.warning("**Contradicciones detectadas:**\n" + "\n".join(f"- {c}" for c in hallazgo["contradicciones_detectadas"]))
        if hallazgo.get("informacion_faltante"):
            st.warning("**Información faltante:**\n" + "\n".join(f"- {c}" for c in hallazgo["informacion_faltante"]))

        st.markdown(f"⚠️ **Limitaciones de la IA:** _{hallazgo['limitaciones_ia']}_")

        if hallazgo.get("comentario_evaluador"):
            st.caption(f"🗒️ Comentario del evaluador ({hallazgo.get('revisado_por_rol', '')}): {hallazgo['comentario_evaluador']}")

        # --- Acciones Human-in-the-Loop ---
        c1, c2, c3 = st.columns(3)
        if c1.button("✅ Aprobar y agregar al informe", key=f"aprobar_{clave_unica}", use_container_width=True):
            enviar_decision(hallazgo, "APROBAR", rol_evaluador)
            refrescar_matriz(expediente_id, rol_evaluador)
            st.rerun()
        if c2.button("📝 Modificar recomendación", key=f"modbtn_{clave_unica}", use_container_width=True):
            st.session_state.editando = clave_unica
        if c3.button("❌ Rechazar por alucinación", key=f"rechazar_{clave_unica}", use_container_width=True):
            enviar_decision(hallazgo, "RECHAZAR", rol_evaluador)
            refrescar_matriz(expediente_id, rol_evaluador)
            st.rerun()

        if st.session_state.editando == clave_unica:
            with st.form(key=f"form_{clave_unica}"):
                nueva_respuesta = st.text_area("Nueva recomendación (reemplaza la de la IA)", value=respuesta_mostrada)
                comentario = st.text_input("Motivo de la modificación (opcional)")
                if st.form_submit_button("Guardar modificación"):
                    enviar_decision(hallazgo, "MODIFICAR", rol_evaluador, respuesta_modificada=nueva_respuesta, comentario=comentario)
                    refrescar_matriz(expediente_id, rol_evaluador)
                    st.rerun()

st.divider()
if not st.session_state.matriz_cargada:
    st.caption("🔎 La consulta libre del dossier estará disponible aquí una vez ejecute la orquestación.")
else:
    st.subheader(f"🔎 Pregúntele al dossier — Expediente {expediente_id}")
    st.caption(
        "Respuestas citando el documento y folio EXACTOS de ESTE expediente — nunca "
        "inventa una referencia. No reemplaza la lectura completa del expediente por el evaluador."
    )
    with st.form("form_consulta", clear_on_submit=True):
        pregunta_form = st.text_input(
            "Pregunta sobre el expediente",
            placeholder="Ej.: ¿el fabricante del BPM coincide con el del formulario?",
            label_visibility="collapsed",
        )
        enviado = st.form_submit_button("Preguntar")
    if enviado and pregunta_form.strip():
        consultar_dossier(expediente_id, tipo_producto, pregunta_form.strip())
        st.rerun()

    historial_expediente = st.session_state.historial_consultas.get(expediente_id, [])
    if not historial_expediente:
        st.caption("Aún no hay preguntas para este expediente.")
    for item in historial_expediente:
        with st.container(border=True):
            st.markdown(f"**{item['pregunta']}**")
            st.markdown(
                badge("Gemini" if item["modo"] == "gemini" else "Heurístico (sin Gemini)", "#3B82F6" if item["modo"] == "gemini" else "#6B7280"),
                unsafe_allow_html=True,
            )
            st.markdown(item["respuesta"])
            if item["citas"]:
                st.caption("Citas del documento real:")
                for c in item["citas"]:
                    st.markdown(f"> `{c['documento_id']} · {c['modulo_seccion']} · {c['pagina_folio']}`\n>\n> {c['fragmento_citado']}")
            st.caption(item["limitaciones_ia"])

st.divider()
with st.expander("📄 Informe final del expediente (hallazgos aprobados o modificados por el evaluador)"):
    try:
        resp = requests.get(f"{ORQUESTADOR_URL}/orquestador/informe/{expediente_id}", timeout=15)
        resp.raise_for_status()
        informe = resp.json()
        if not informe:
            st.caption("Aún no hay hallazgos aprobados ni modificados para este expediente.")
        for h in informe:
            texto = h.get("respuesta_modificada") or h["respuesta"]
            st.markdown(f"- **[{h['agente_origen']}] {h['id_hallazgo']}** ({h['estado_revision']}): {texto}")
    except requests.RequestException:
        st.caption("Informe no disponible (¿el Orquestador está corriendo?).")
