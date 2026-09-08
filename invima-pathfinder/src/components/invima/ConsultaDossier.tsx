import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { StatusPill } from "./shared";
import { Loader2, MessageCircleQuestion, Quote, Sparkles } from "lucide-react";
import {
  consultarDossier,
  type CitaDocumental,
  type ConsultaDossierResponse,
} from "@/lib/orquestador-api";

const PREGUNTAS_SUGERIDAS = [
  "¿Cuándo vence el certificado BPM?",
  "¿Qué condición de almacenamiento reporta el Módulo 8?",
  "¿Cuántos pacientes tuvo el estudio pivotal?",
];

/** Barra de consulta libre sobre el dossier: pregunta en lenguaje
 * natural, respondida citando el documento_id y folio EXACTOS del
 * expediente simulado -- nunca una referencia inventada (ver
 * orquestador/consulta_dossier.py). No reemplaza al evaluador: es una
 * ayuda de lectura, no una decisión. */
export function ConsultaDossier({ expedienteId }: { expedienteId: string }) {
  const [pregunta, setPregunta] = useState("");
  const [historial, setHistorial] = useState<ConsultaDossierResponse[]>([]);

  const consultaMutation = useMutation({
    mutationFn: (p: string) => consultarDossier(expedienteId, "BIOLOGICO", p),
    onSuccess: (data) => setHistorial((prev) => [data, ...prev]),
  });

  const enviar = () => {
    const p = pregunta.trim();
    if (!p || consultaMutation.isPending) return;
    consultaMutation.mutate(p);
    setPregunta("");
  };

  return (
    <div className="space-y-4">
      <div className="rounded-lg border border-primary/25 bg-primary/5 p-4">
        <p className="flex items-center gap-2 text-sm font-medium">
          <MessageCircleQuestion className="size-4 text-primary" /> Pregúntele al dossier
        </p>
        <p className="mt-1 text-xs text-muted-foreground">
          Respuestas generadas citando el documento y folio exactos del expediente simulado — nunca
          inventa una referencia. No reemplaza la lectura completa por el evaluador.
        </p>
        <div className="mt-3 flex gap-2">
          <Input
            value={pregunta}
            onChange={(e) => setPregunta(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") enviar();
            }}
            placeholder="Ej.: ¿el fabricante del BPM coincide con el del formulario?"
            disabled={consultaMutation.isPending}
          />
          <Button
            onClick={enviar}
            disabled={consultaMutation.isPending || !pregunta.trim()}
            className="gap-2"
          >
            {consultaMutation.isPending ? (
              <Loader2 className="size-4 animate-spin" />
            ) : (
              <Sparkles className="size-4" />
            )}
            Preguntar
          </Button>
        </div>
        <div className="mt-2 flex flex-wrap gap-1.5">
          {PREGUNTAS_SUGERIDAS.map((p) => (
            <button
              key={p}
              type="button"
              onClick={() => !consultaMutation.isPending && consultaMutation.mutate(p)}
              className="rounded-full border border-border bg-card px-2.5 py-1 text-xs text-muted-foreground transition-colors hover:bg-accent hover:text-accent-foreground disabled:pointer-events-none"
              disabled={consultaMutation.isPending}
            >
              {p}
            </button>
          ))}
        </div>
      </div>

      {consultaMutation.isError ? (
        <Alert variant="destructive">
          <AlertDescription>
            No se pudo consultar al Orquestador ({(consultaMutation.error as Error).message}).
          </AlertDescription>
        </Alert>
      ) : null}

      {historial.length === 0 && !consultaMutation.isPending ? (
        <p className="text-sm text-muted-foreground">
          Escriba una pregunta sobre el expediente o elija una sugerida arriba.
        </p>
      ) : null}

      <div className="space-y-3">
        {historial.map((item, i) => (
          <RespuestaConsulta key={`${item.pregunta}-${i}`} item={item} />
        ))}
      </div>
    </div>
  );
}

function RespuestaConsulta({ item }: { item: ConsultaDossierResponse }) {
  return (
    <div className="space-y-2.5 rounded-lg border border-border bg-card p-4 shadow-panel">
      <p className="text-sm font-semibold">{item.pregunta}</p>

      <div className="flex items-center gap-2">
        <StatusPill tone={item.modo === "gemini" ? "info" : "pendiente"}>
          {item.modo === "gemini" ? "Gemini" : "Heurístico (sin Gemini)"}
        </StatusPill>
      </div>

      <p className="whitespace-pre-line text-sm text-muted-foreground">{item.respuesta}</p>

      {item.citas.length > 0 ? (
        <div className="space-y-1.5 border-t border-border pt-2.5">
          <p className="flex items-center gap-1.5 text-xs font-semibold text-foreground">
            <Quote className="size-3.5" /> Citas del documento real
          </p>
          {item.citas.map((c: CitaDocumental, i: number) => (
            <div
              key={`${c.documento_id}-${i}`}
              className="rounded-md border border-sky-500/30 bg-sky-500/5 p-2 text-xs"
            >
              <p className="font-mono text-[11px] text-muted-foreground">
                {c.documento_id} · {c.modulo_seccion} · {c.pagina_folio}
              </p>
              <p className="mt-0.5">{c.fragmento_citado}</p>
            </div>
          ))}
        </div>
      ) : null}

      <p className="text-[11px] text-muted-foreground italic">{item.limitaciones_ia}</p>
    </div>
  );
}
