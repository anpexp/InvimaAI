import { useEffect, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Textarea } from "@/components/ui/textarea";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { StatusPill } from "./shared";
import { AlertTriangle, Bot, Check, Clock, Loader2, MapPin, Pencil, Search, X } from "lucide-react";
import {
  analizarExpediente,
  obtenerMatriz,
  registrarDecision,
  type AntecedenteHistorico,
  type CategoriaRiesgo,
  type DecisionHITL,
  type EstadoRevision,
  type HallazgoConsolidado,
  type PrioridadTramite,
  type ResumenExpediente,
  type RolEvaluador,
} from "@/lib/orquestador-api";

const RIESGO_TONE: Record<CategoriaRiesgo, "aprobado" | "ajustes" | "denegado"> = {
  BAJO: "aprobado",
  MEDIO: "ajustes",
  ALTO: "denegado",
};

const ESTADO_TONE: Record<EstadoRevision, "pendiente" | "aprobado" | "info" | "denegado"> = {
  PENDIENTE: "pendiente",
  APROBADO: "aprobado",
  MODIFICADO: "info",
  RECHAZADO: "denegado",
};

const PRIORIDAD_TONE: Record<PrioridadTramite, "denegado" | "ajustes" | "aprobado"> = {
  ALTA: "denegado",
  MEDIA: "ajustes",
  BAJA: "aprobado",
};

// Vista personalizada por rol: cada especialidad SOLO ve los hallazgos de
// su agente — igual que el dashboard Streamlit (rol_evaluador filtra en
// el backend). Antes este panel mostraba los 3 agentes a la vez.
const ESPECIALIDADES: { rol: RolEvaluador; etiqueta: string; agente: string }[] = [
  { rol: "LEGAL", etiqueta: "⚖️ Legal", agente: "AGENTE_1_LEGAL" },
  { rol: "CALIDAD", etiqueta: "🧪 Calidad / Farmacéutico", agente: "AGENTE_2_RELIANCE" },
  { rol: "CLINICO", etiqueta: "🩺 Clínico / Farmacológico", agente: "AGENTE_3_CLINICO" },
];

/** Panel que reemplaza la simulación anterior de "INVAIA": llama de verdad
 * al Orquestador (Agentes 1, 2 y 3) y renderiza su matriz de hallazgos con
 * el flujo Human-in-the-Loop, filtrada por especialidad. Este panel NO
 * reemplaza al evaluador ni su responsabilidad — la IA asiste, el humano
 * aprueba. */
export function HallazgosPanel({ expedienteId }: { expedienteId: string }) {
  const queryClient = useQueryClient();
  const [especialidad, setEspecialidad] = useState<RolEvaluador>("LEGAL");
  const [yaEjecutado, setYaEjecutado] = useState(false);
  const [resumenExpediente, setResumenExpediente] = useState<ResumenExpediente | null>(null);
  const [antecedentes, setAntecedentes] = useState<AntecedenteHistorico[]>([]);

  const matrizKey = ["orquestador-matriz", expedienteId, especialidad];
  const matrizQuery = useQuery({
    queryKey: matrizKey,
    queryFn: () => obtenerMatriz(expedienteId, especialidad),
    enabled: false,
  });

  // Cambiar de especialidad relee la matriz ya consolidada (sin volver a
  // llamar a los agentes) — igual que el dashboard Streamlit.
  useEffect(() => {
    if (yaEjecutado) matrizQuery.refetch();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [especialidad, yaEjecutado]);

  const analizarMutation = useMutation({
    mutationFn: () => analizarExpediente(expedienteId, "BIOLOGICO", especialidad),
    onSuccess: (data) => {
      queryClient.setQueryData(matrizKey, data.hallazgos);
      setResumenExpediente(data.resumen_expediente);
      setAntecedentes(data.antecedentes_historicos);
      setYaEjecutado(true);
    },
  });

  const decisionMutation = useMutation({
    mutationFn: registrarDecision,
    onSuccess: (actualizado) => {
      queryClient.setQueryData<HallazgoConsolidado[]>(matrizKey, (prev) =>
        (prev ?? []).map((h) =>
          h.agente_origen === actualizado.agente_origen && h.id_hallazgo === actualizado.id_hallazgo
            ? actualizado
            : h,
        ),
      );
    },
  });

  const hallazgos = matrizQuery.data ?? [];
  const cargando = analizarMutation.isPending || matrizQuery.isFetching;
  const especialidadActual = ESPECIALIDADES.find((e) => e.rol === especialidad)!;

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-center justify-between gap-3 rounded-lg border border-primary/25 bg-primary/5 p-4">
        <div className="flex items-center gap-3">
          <Bot className="size-5 text-primary" />
          <div>
            <p className="text-sm font-medium">Orquestador Principal · Agentes 1, 2 y 3</p>
            <p className="text-xs text-muted-foreground">
              Simula la carga documental del expediente {expedienteId} y consolida los hallazgos de
              los 3 agentes.
            </p>
          </div>
        </div>
        <Button onClick={() => analizarMutation.mutate()} disabled={cargando} className="gap-2">
          {cargando ? <Loader2 className="size-4 animate-spin" /> : <Search className="size-4" />}
          Ejecutar orquestación
        </Button>
      </div>

      <div className="flex flex-wrap items-center gap-2">
        <span className="text-xs font-medium text-muted-foreground">Vista por especialidad:</span>
        {ESPECIALIDADES.map((e) => (
          <Button
            key={e.rol}
            size="sm"
            variant={e.rol === especialidad ? "default" : "outline"}
            onClick={() => setEspecialidad(e.rol)}
          >
            {e.etiqueta}
          </Button>
        ))}
      </div>

      {analizarMutation.isError ? (
        <Alert variant="destructive">
          <AlertDescription>
            No se pudo contactar al Orquestador ({(analizarMutation.error as Error).message}).
            Verifique que esté corriendo (ver <code>orquestador/README.md</code>).
          </AlertDescription>
        </Alert>
      ) : null}
      {matrizQuery.isError ? (
        <Alert variant="destructive">
          <AlertDescription>
            No se pudo leer la matriz del expediente ({(matrizQuery.error as Error).message}).
          </AlertDescription>
        </Alert>
      ) : null}

      {resumenExpediente ? (
        <div className="flex flex-wrap items-center gap-2 rounded-lg border border-border bg-muted/30 p-3">
          <StatusPill tone={PRIORIDAD_TONE[resumenExpediente.prioridad]}>
            Prioridad {resumenExpediente.prioridad}
          </StatusPill>
          <StatusPill tone={resumenExpediente.expediente_completo ? "aprobado" : "denegado"}>
            {resumenExpediente.expediente_completo
              ? "Expediente completo"
              : "Expediente incompleto"}
          </StatusPill>
          <span className="text-xs text-muted-foreground">
            {resumenExpediente.num_hallazgos_alto} hallazgo(s) ALTO de{" "}
            {resumenExpediente.num_hallazgos} totales
          </span>
          {resumenExpediente.agentes_no_disponibles.length ? (
            <span className="text-xs text-deny">
              Agentes no disponibles: {resumenExpediente.agentes_no_disponibles.join(", ")}
            </span>
          ) : null}
        </div>
      ) : null}

      {antecedentes.length ? (
        <div className="space-y-2 rounded-lg border border-border p-3">
          <p className="flex items-center gap-1.5 text-xs font-semibold text-foreground">
            <Clock className="size-3.5" /> Memoria transversal — {antecedentes.length}{" "}
            antecedente(s) relacionado(s)
          </p>
          {antecedentes.map((a) => (
            <p key={a.expediente_id} className="text-xs text-muted-foreground">
              <StatusPill tone={RIESGO_TONE[a.categoria_riesgo_maxima]} className="mr-1.5">
                {a.categoria_riesgo_maxima}
              </StatusPill>
              <span className="font-mono">{a.expediente_id}</span> ({a.fecha_analisis.slice(0, 10)})
              — {a.resumen}
            </p>
          ))}
        </div>
      ) : null}

      {!yaEjecutado ? (
        <p className="text-sm text-muted-foreground">
          Pulse «Ejecutar orquestación» para traer los hallazgos reales de los Agentes 1, 2 y 3
          sobre este expediente.
        </p>
      ) : null}

      {yaEjecutado && !cargando && hallazgos.length === 0 ? (
        <p className="text-sm text-muted-foreground">
          No hay hallazgos de {especialidadActual.agente} para este expediente.
        </p>
      ) : null}

      {yaEjecutado && hallazgos.length > 0 ? (
        <div className="space-y-3">
          {hallazgos.map((h) => (
            <HallazgoCard
              key={`${h.agente_origen}:${h.id_hallazgo}`}
              hallazgo={h}
              pendiente={decisionMutation.isPending}
              onDecidir={(decision, extra) =>
                decisionMutation.mutate({
                  expedienteId,
                  idHallazgo: h.id_hallazgo,
                  agenteOrigen: h.agente_origen,
                  decision,
                  rolEvaluador: especialidad,
                  ...extra,
                })
              }
            />
          ))}
        </div>
      ) : null}
    </div>
  );
}

function HallazgoCard({
  hallazgo,
  pendiente,
  onDecidir,
}: {
  hallazgo: HallazgoConsolidado;
  pendiente: boolean;
  onDecidir: (
    decision: DecisionHITL,
    extra?: { respuestaModificada?: string; comentarioEvaluador?: string },
  ) => void;
}) {
  const [editando, setEditando] = useState(false);
  const respuestaMostrada = hallazgo.respuesta_modificada ?? hallazgo.respuesta;
  const [borrador, setBorrador] = useState(respuestaMostrada);
  const u = hallazgo.ubicacion_exacta;
  const tieneAlertas =
    hallazgo.contradicciones_detectadas.length > 0 || hallazgo.informacion_faltante.length > 0;

  return (
    <Card className="shadow-panel">
      <CardHeader className="gap-2 pb-3">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <p className="font-mono text-xs text-muted-foreground">{hallazgo.id_hallazgo}</p>
          <div className="flex flex-wrap items-center gap-1.5">
            <StatusPill tone={RIESGO_TONE[hallazgo.categoria_riesgo]}>
              Riesgo {hallazgo.categoria_riesgo}
            </StatusPill>
            <StatusPill tone={ESTADO_TONE[hallazgo.estado_revision]}>
              {hallazgo.estado_revision}
            </StatusPill>
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        <section className="space-y-1.5">
          <span className="inline-flex items-center gap-1 rounded-full border border-sky-500/30 bg-sky-500/10 px-2 py-0.5 text-[11px] font-semibold text-sky-700 dark:text-sky-300">
            DATO EXTRAÍDO
          </span>
          <p className="rounded-md border border-border bg-muted/30 p-2.5 text-sm">
            {hallazgo.evidencia_citada}
          </p>
          <p className="flex flex-wrap items-center gap-1.5 text-xs text-muted-foreground">
            <MapPin className="size-3.5 shrink-0" />
            {u.modulo_seccion} · Doc: {u.documento_id} · Versión: {u.version} · Folio:{" "}
            {u.pagina_folio} · {u.fecha_documento} · {u.entidad_responsable}
          </p>
        </section>

        <section className="space-y-1.5">
          <span className="inline-flex items-center gap-1 rounded-full border border-violet-500/30 bg-violet-500/10 px-2 py-0.5 text-[11px] font-semibold text-violet-700 dark:text-violet-300">
            IA · INFERENCIA
          </span>
          <p className="text-sm">{respuestaMostrada}</p>
          {hallazgo.respuesta_modificada ? (
            <p className="text-xs italic text-muted-foreground">
              Versión modificada por el evaluador.
            </p>
          ) : null}
          <div className="space-y-1">
            <div className="flex items-center justify-between text-xs text-muted-foreground">
              <span>Nivel de confianza</span>
              <span className="font-medium text-foreground tabular-nums">
                {Math.round(hallazgo.nivel_confianza * 100)}%
              </span>
            </div>
            <Progress value={hallazgo.nivel_confianza * 100} className="h-1.5" />
          </div>
          <p className="text-sm">
            <span className="font-semibold">Acción sugerida al evaluador: </span>
            {hallazgo.accion_sugerida_evaluador}
          </p>
        </section>

        {tieneAlertas ? (
          <div className="rounded-lg border border-warn/40 bg-warn-soft p-3 text-sm text-warn-foreground">
            {hallazgo.contradicciones_detectadas.length ? (
              <>
                <p className="flex items-center gap-1.5 font-semibold">
                  <AlertTriangle className="size-3.5" /> Contradicciones detectadas
                </p>
                <ul className="mt-1 list-disc space-y-0.5 pl-5">
                  {hallazgo.contradicciones_detectadas.map((c) => (
                    <li key={c}>{c}</li>
                  ))}
                </ul>
              </>
            ) : null}
            {hallazgo.informacion_faltante.length ? (
              <>
                <p className="mt-2 flex items-center gap-1.5 font-semibold">
                  <AlertTriangle className="size-3.5" /> Información faltante
                </p>
                <ul className="mt-1 list-disc space-y-0.5 pl-5">
                  {hallazgo.informacion_faltante.map((c) => (
                    <li key={c}>{c}</li>
                  ))}
                </ul>
              </>
            ) : null}
          </div>
        ) : null}

        <p className="text-xs text-muted-foreground">
          ⚠️ Limitaciones de la IA: {hallazgo.limitaciones_ia}
        </p>

        {hallazgo.comentario_evaluador ? (
          <p className="text-xs text-muted-foreground">
            🗒️ Comentario del evaluador ({hallazgo.revisado_por_rol}):{" "}
            {hallazgo.comentario_evaluador}
          </p>
        ) : null}

        <div className="flex flex-wrap gap-2 pt-1">
          <Button
            size="sm"
            variant="outline"
            disabled={pendiente}
            className="gap-1.5 border-approve/40 text-approve hover:bg-approve-soft"
            onClick={() => onDecidir("APROBAR")}
          >
            <Check className="size-3.5" /> Aprobar y agregar al informe
          </Button>
          <Button
            size="sm"
            variant="outline"
            disabled={pendiente}
            className="gap-1.5"
            onClick={() => setEditando((v) => !v)}
          >
            <Pencil className="size-3.5" /> Modificar recomendación
          </Button>
          <Button
            size="sm"
            variant="outline"
            disabled={pendiente}
            className="gap-1.5 border-deny/40 text-deny hover:bg-deny-soft"
            onClick={() => onDecidir("RECHAZAR")}
          >
            <X className="size-3.5" /> Rechazar por alucinación
          </Button>
        </div>

        {editando ? (
          <div className="space-y-2 rounded-lg border border-border bg-muted/30 p-3">
            <Textarea value={borrador} onChange={(e) => setBorrador(e.target.value)} rows={3} />
            <div className="flex justify-end gap-2">
              <Button size="sm" variant="ghost" onClick={() => setEditando(false)}>
                Cancelar
              </Button>
              <Button
                size="sm"
                disabled={pendiente}
                onClick={() => {
                  onDecidir("MODIFICAR", { respuestaModificada: borrador });
                  setEditando(false);
                }}
              >
                Guardar modificación
              </Button>
            </div>
          </div>
        ) : null}
      </CardContent>
    </Card>
  );
}
