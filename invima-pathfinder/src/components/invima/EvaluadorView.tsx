import { useState } from "react";
import { useAppState } from "@/lib/app-state";
import type { Dossier } from "@/lib/invima-data";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Badge } from "@/components/ui/badge";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { StatusPill, SectionTitle } from "./shared";
import { HallazgosPanel } from "./HallazgosPanel";
import { ConsultaDossier } from "./ConsultaDossier";
import { FileText } from "lucide-react";

export function EvaluadorView() {
  const { dossiers } = useAppState();
  const [open, setOpen] = useState<Dossier | null>(null);

  return (
    <div className="space-y-6">
      <SectionTitle
        eyebrow="Panel de evaluación"
        title="Solicitudes asignadas"
        description="Explore los expedientes radicados, revise los archivos por módulo y solicite investigación de antecedentes a INVAIA."
      />

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {dossiers.map((d) => (
          <Card
            key={d.id}
            className="flex flex-col shadow-panel transition-shadow hover:shadow-raised"
          >
            <CardHeader className="gap-2">
              <div className="flex items-start justify-between gap-2">
                <p className="font-mono text-xs text-muted-foreground">{d.radicado}</p>
                <StatusPill tone={d.fase === "Subsanación" ? "ajustes" : "info"}>
                  {d.fase}
                </StatusPill>
              </div>
              <h3 className="text-base leading-snug font-semibold">{d.producto}</h3>
              <p className="text-sm text-muted-foreground">{d.solicitante}</p>
            </CardHeader>
            <CardContent className="mt-auto space-y-3">
              <div className="flex items-center justify-between text-xs text-muted-foreground">
                <span>Radicado: {d.fechaRadicado}</span>
                <span className="font-semibold text-foreground tabular-nums">{d.avance}%</span>
              </div>
              <Progress value={d.avance} className="h-1.5" />
              <div className="flex flex-wrap gap-1.5">
                {d.tags.map((t) => (
                  <Badge key={t} variant="secondary" className="font-normal">
                    {t}
                  </Badge>
                ))}
              </div>
              <Button variant="outline" className="w-full gap-2" onClick={() => setOpen(d)}>
                <FileText className="size-4" /> Abrir expediente
              </Button>
            </CardContent>
          </Card>
        ))}
      </div>

      <DossierDialog dossier={open} onClose={() => setOpen(null)} />
    </div>
  );
}

function DossierDialog({ dossier, onClose }: { dossier: Dossier | null; onClose: () => void }) {
  return (
    <Dialog
      open={!!dossier}
      onOpenChange={(o) => {
        if (!o) onClose();
      }}
    >
      <DialogContent className="max-h-[88vh] overflow-y-auto sm:max-w-4xl">
        {dossier ? (
          <>
            <DialogHeader>
              <DialogTitle className="pr-8 text-left">{dossier.producto}</DialogTitle>
              <p className="text-left text-sm text-muted-foreground">
                {dossier.radicado} · {dossier.solicitante}
              </p>
            </DialogHeader>

            <Tabs defaultValue="archivos">
              <TabsList>
                <TabsTrigger value="archivos">Archivos por módulo</TabsTrigger>
                <TabsTrigger value="invaia">INVAIA</TabsTrigger>
                <TabsTrigger value="consulta">Consulta</TabsTrigger>
              </TabsList>

              <TabsContent value="archivos" className="space-y-4 pt-4">
                {[...new Set(dossier.archivos.map((a) => a.modulo))].map((mod) => (
                  <div key={mod} className="rounded-lg border border-border">
                    <div className="border-b border-border bg-muted/40 px-3 py-2 font-mono text-xs font-semibold text-primary">
                      {mod}
                    </div>
                    <ul className="divide-y divide-border">
                      {dossier.archivos
                        .filter((a) => a.modulo === mod)
                        .map((a) => (
                          <li
                            key={a.nombre}
                            className="flex items-center gap-3 px-3 py-2.5 text-sm"
                          >
                            <FileText className="size-4 shrink-0 text-muted-foreground" />
                            <span className="flex-1 truncate">{a.nombre}</span>
                            <span className="text-xs text-muted-foreground">{a.paginas} pág.</span>
                          </li>
                        ))}
                    </ul>
                  </div>
                ))}
              </TabsContent>

              <TabsContent value="invaia" className="pt-4">
                <HallazgosPanel expedienteId={dossier.radicado} />
              </TabsContent>

              <TabsContent value="consulta" className="pt-4">
                <ConsultaDossier expedienteId={dossier.radicado} />
              </TabsContent>
            </Tabs>
          </>
        ) : null}
      </DialogContent>
    </Dialog>
  );
}
