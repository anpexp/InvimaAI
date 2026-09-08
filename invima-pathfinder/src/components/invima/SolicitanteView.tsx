import { useAppState } from "@/lib/app-state";
import { MODULES } from "@/lib/invima-data";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Checkbox } from "@/components/ui/checkbox";
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion";
import { Button } from "@/components/ui/button";
import { StatusPill, SectionTitle } from "./shared";
import { CheckCircle2, CircleDashed, FileUp, Loader2, Send } from "lucide-react";
import { toast } from "sonner";

export function SolicitanteView() {
  const { activeDossierId, dossiers, answers, toggleAnswer, moduleProgress, globalProgress } = useAppState();
  const dossier = dossiers.find((d) => d.id === activeDossierId) ?? dossiers[0]!;
  const global = globalProgress(dossier.id);

  return (
    <div className="space-y-6">
      <SectionTitle
        eyebrow="Módulo del solicitante"
        title="Diligenciamiento del dossier por fases"
        description="Complete las listas de chequeo de cada módulo CTD. El expediente se habilita para radicación cuando todas las secciones estén aprobadas."
      />

      <Card className="shadow-panel">
        <CardHeader className="gap-3">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div>
              <p className="text-xs tracking-widest text-muted-foreground uppercase">{dossier.radicado}</p>
              <h3 className="text-lg font-semibold">{dossier.producto}</h3>
              <p className="text-sm text-muted-foreground">
                {dossier.solicitante} · Radicado el {dossier.fechaRadicado}
              </p>
            </div>
            <div className="min-w-[220px] space-y-2">
              <div className="flex items-baseline justify-between">
                <span className="text-xs text-muted-foreground">Progreso global</span>
                <span className="font-display text-2xl font-bold tabular-nums text-primary">{global}%</span>
              </div>
              <Progress value={global} className="h-2" />
            </div>
          </div>
        </CardHeader>
        <CardContent className="flex flex-wrap gap-2">
          {MODULES.map((m) => {
            const p = moduleProgress(dossier.id, m.id);
            const tone = p === 100 ? "aprobado" : p > 0 ? "proceso" : "pendiente";
            const label = p === 100 ? "Aprobado" : p > 0 ? "En proceso" : "Pendiente";
            return (
              <StatusPill key={m.id} tone={tone}>
                {p === 100 ? (
                  <CheckCircle2 className="size-3.5" />
                ) : p > 0 ? (
                  <Loader2 className="size-3.5" />
                ) : (
                  <CircleDashed className="size-3.5" />
                )}
                {m.code} · {label} ({p}%)
              </StatusPill>
            );
          })}
        </CardContent>
      </Card>

      <Accordion type="multiple" defaultValue={["m12"]} className="space-y-3">
        {MODULES.map((m) => {
          const p = moduleProgress(dossier.id, m.id);
          return (
            <AccordionItem
              key={m.id}
              value={m.id}
              className="overflow-hidden rounded-xl border border-border bg-card shadow-panel"
            >
              <AccordionTrigger className="px-5 py-4 hover:no-underline">
                <div className="flex w-full flex-wrap items-center gap-4 pr-3 text-left">
                  <span className="rounded-md bg-primary/10 px-2 py-1 font-mono text-xs font-semibold text-primary">
                    {m.code}
                  </span>
                  <div className="min-w-[200px] flex-1">
                    <p className="font-medium">{m.title}</p>
                    <p className="text-xs text-muted-foreground">{m.subtitle}</p>
                  </div>
                  <div className="flex items-center gap-3">
                    <Progress value={p} className="h-1.5 w-24" />
                    <StatusPill tone={p === 100 ? "aprobado" : p > 0 ? "proceso" : "pendiente"}>
                      {p}%
                    </StatusPill>
                  </div>
                </div>
              </AccordionTrigger>
              <AccordionContent className="border-t border-border bg-muted/30 px-5 py-4">
                <ul className="space-y-2">
                  {m.questions.map((q, i) => {
                    const key = `${dossier.id}:${m.id}:${i}`;
                    const checked = !!answers[key];
                    return (
                      <li
                        key={key}
                        className="flex items-start gap-3 rounded-lg border border-border bg-card p-3"
                      >
                        <Checkbox
                          id={key}
                          checked={checked}
                          onCheckedChange={() => toggleAnswer(key)}
                          className="mt-0.5"
                        />
                        <label htmlFor={key} className="flex-1 cursor-pointer text-sm leading-relaxed">
                          {q}
                        </label>
                        <StatusPill tone={checked ? "aprobado" : "pendiente"}>
                          {checked ? "Diligenciado" : "Pendiente"}
                        </StatusPill>
                      </li>
                    );
                  })}
                </ul>
                <div className="mt-4 flex flex-wrap gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    className="gap-2"
                    onClick={() => toast.success(`Soporte cargado en ${m.code}`)}
                  >
                    <FileUp className="size-4" /> Cargar soporte documental
                  </Button>
                </div>
              </AccordionContent>
            </AccordionItem>
          );
        })}
      </Accordion>

      <div className="flex justify-end">
        <Button
          className="gap-2"
          disabled={global < 100}
          onClick={() => toast.success("Dossier radicado ante el INVIMA para evaluación técnica.")}
        >
          <Send className="size-4" />
          {global < 100 ? `Complete el dossier (${global}%)` : "Radicar dossier"}
        </Button>
      </div>
    </div>
  );
}
