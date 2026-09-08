/**
 * Cliente del Orquestador Principal (INVIMA del Futuro). Los tipos de
 * abajo reflejan EXACTAMENTE el contrato de salida que exponen los 3
 * agentes y el orquestador (ver orquestador/models.py) — no renombrar
 * campos sin actualizar también el backend.
 */

export type CategoriaRiesgo = "BAJO" | "MEDIO" | "ALTO";
export type EstadoRevision = "PENDIENTE" | "APROBADO" | "MODIFICADO" | "RECHAZADO";
export type RolEvaluador = "LEGAL" | "CALIDAD" | "CLINICO";
export type TipoProducto = "SINTESIS_QUIMICA" | "BIOLOGICO" | "VACUNA";
export type DecisionHITL = "APROBAR" | "MODIFICAR" | "RECHAZAR";

export interface UbicacionExacta {
  documento_id: string;
  modulo_seccion: string;
  version: string;
  fecha_documento: string;
  pagina_folio: string;
  entidad_responsable: string;
}

export interface HallazgoConsolidado {
  id_hallazgo: string;
  categoria_riesgo: CategoriaRiesgo;
  respuesta: string;
  evidencia_citada: string;
  ubicacion_exacta: UbicacionExacta;
  nivel_confianza: number;
  contradicciones_detectadas: string[];
  informacion_faltante: string[];
  limitaciones_ia: string;
  accion_sugerida_evaluador: string;
  agente_origen: string;
  expediente_id: string;
  producto_codigo: string;
  producto_nombre: string;
  estado_revision: EstadoRevision;
  respuesta_modificada: string | null;
  comentario_evaluador: string | null;
  revisado_por_rol: string | null;
  revisado_en: string | null;
}

export interface AgenteEstado {
  agente_origen: string;
  ok: boolean;
  detalle: string;
  num_hallazgos: number;
}

export type PrioridadTramite = "ALTA" | "MEDIA" | "BAJA";

/** Un expediente anterior relacionado (mismo producto o misma entidad
 * responsable) — resultado de la Memoria Transversal. */
export interface AntecedenteHistorico {
  expediente_id: string;
  producto_codigo: string;
  producto_nombre: string;
  fecha_analisis: string;
  categoria_riesgo_maxima: CategoriaRiesgo;
  num_hallazgos_alto: number;
  entidades_responsables: string[];
  resumen: string;
}

/** Clasificación/priorización del trámite + detección de incompletos. */
export interface ResumenExpediente {
  expediente_id: string;
  producto_codigo: string;
  producto_nombre: string;
  fecha_analisis: string;
  categoria_riesgo_maxima: CategoriaRiesgo;
  num_hallazgos_alto: number;
  num_hallazgos: number;
  expediente_completo: boolean;
  informacion_faltante: string[];
  prioridad: PrioridadTramite;
  agentes_disponibles: string[];
  agentes_no_disponibles: string[];
}

export interface OrquestacionResponse {
  expediente_id: string;
  tipo_producto: TipoProducto;
  rol_evaluador: RolEvaluador;
  estados_agentes: AgenteEstado[];
  hallazgos: HallazgoConsolidado[];
  antecedentes_historicos: AntecedenteHistorico[];
  resumen_expediente: ResumenExpediente | null;
}

// Vite solo expone al cliente las variables prefijadas con VITE_.
// (bracket notation: tsconfig tiene noPropertyAccessFromIndexSignature)
export const ORQUESTADOR_URL: string =
  (import.meta.env["VITE_ORQUESTADOR_URL"] as string | undefined) ?? "http://localhost:8080";

async function parseOrThrow<T>(resp: Response): Promise<T> {
  if (!resp.ok) {
    const detalle = await resp.text().catch(() => "");
    throw new Error(`Orquestador respondió ${resp.status}: ${detalle || resp.statusText}`);
  }
  return (await resp.json()) as T;
}

/** Dispara la orquestación completa (simula la carga documental y llama a
 * los 3 agentes). El rol solo determina qué subconjunto trae la respuesta
 * inmediata — el backend igual procesa y consolida los 3 agentes. */
export async function analizarExpediente(
  expedienteId: string,
  tipoProducto: TipoProducto,
  rolEvaluador: RolEvaluador,
): Promise<OrquestacionResponse> {
  const resp = await fetch(`${ORQUESTADOR_URL}/orquestador/analizar`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      expediente_id: expedienteId,
      tipo_producto: tipoProducto,
      rol_evaluador: rolEvaluador,
    }),
  });
  return parseOrThrow<OrquestacionResponse>(resp);
}

/** Relee la matriz temporal ya consolidada, sin volver a llamar a los
 * agentes. Sin `rolEvaluador`, trae los hallazgos de los 3 agentes. */
export async function obtenerMatriz(
  expedienteId: string,
  rolEvaluador?: RolEvaluador,
): Promise<HallazgoConsolidado[]> {
  const url = new URL(`${ORQUESTADOR_URL}/orquestador/matriz/${encodeURIComponent(expedienteId)}`);
  if (rolEvaluador) url.searchParams.set("rol_evaluador", rolEvaluador);
  const resp = await fetch(url);
  return parseOrThrow<HallazgoConsolidado[]>(resp);
}

/** Autoridad humana: aprueba, modifica o rechaza un hallazgo puntual. */
export async function registrarDecision(params: {
  expedienteId: string;
  idHallazgo: string;
  agenteOrigen: string;
  decision: DecisionHITL;
  rolEvaluador: RolEvaluador;
  respuestaModificada?: string;
  comentarioEvaluador?: string;
}): Promise<HallazgoConsolidado> {
  const resp = await fetch(`${ORQUESTADOR_URL}/orquestador/hallazgo/decision`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      expediente_id: params.expedienteId,
      id_hallazgo: params.idHallazgo,
      agente_origen: params.agenteOrigen,
      decision: params.decision,
      rol_evaluador: params.rolEvaluador,
      respuesta_modificada: params.respuestaModificada ?? null,
      comentario_evaluador: params.comentarioEvaluador ?? null,
    }),
  });
  return parseOrThrow<HallazgoConsolidado>(resp);
}

/** Solo los hallazgos aprobados o modificados por un humano. */
export async function obtenerInforme(expedienteId: string): Promise<HallazgoConsolidado[]> {
  const resp = await fetch(
    `${ORQUESTADOR_URL}/orquestador/informe/${encodeURIComponent(expedienteId)}`,
  );
  return parseOrThrow<HallazgoConsolidado[]>(resp);
}

/** Panel de trámites: clasifica y prioriza todos los expedientes ya
 * procesados en esta ejecución del Orquestador. */
export async function obtenerPanel(): Promise<ResumenExpediente[]> {
  const resp = await fetch(`${ORQUESTADOR_URL}/orquestador/panel`);
  return parseOrThrow<ResumenExpediente[]>(resp);
}

/** Una cita al documento REAL del dossier (nunca inventada). */
export interface CitaDocumental {
  documento_id: string;
  modulo_seccion: string;
  pagina_folio: string;
  fragmento_citado: string;
}

export interface ConsultaDossierResponse {
  expediente_id: string;
  pregunta: string;
  respuesta: string;
  citas: CitaDocumental[];
  modo: "gemini" | "heuristico";
  limitaciones_ia: string;
}

/** Barra de consulta del dossier: pregunta libre en lenguaje natural,
 * respondida citando el documento_id y folio exactos del expediente
 * (con Gemini si hay GEMINI_API_KEY en el Orquestador; si no, con un
 * buscador heurístico por palabras clave). */
export async function consultarDossier(
  expedienteId: string,
  tipoProducto: TipoProducto,
  pregunta: string,
): Promise<ConsultaDossierResponse> {
  const resp = await fetch(`${ORQUESTADOR_URL}/orquestador/consultar`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ expediente_id: expedienteId, tipo_producto: tipoProducto, pregunta }),
  });
  return parseOrThrow<ConsultaDossierResponse>(resp);
}
