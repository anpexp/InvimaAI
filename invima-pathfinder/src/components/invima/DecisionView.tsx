import { useState } from "react";
import { useAppState } from "@/lib/app-state";
import type { Dossier } from "@/lib/invima-data";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Separator } from "@/components/ui/separator";
import { ConceptoPill, MatchBadge, SectionTitle, StatusPill, InvimaCrest } from "./shared";
import { Bot, FileCheck2, Lock, Mail, ScrollText } from "lucide-react";
import { toast } from "sonner";

export function DecisionView() {
  const { dossiers } = useAppState();
  const elegibles = dossiers.filter((d) => d.avance === 100);
  const [preliminar, setPreliminar] = useState<Dossier | null>(null);

  return (
    <div className="space-y-6">
      <SectionTitle
        eyebrow="Sala Especializada de Medicamentos y Productos Biológicos"
        title="Panel de decisión"
        description="Acceso restringido. Solo se listan dossiers completamente evaluados con documentación mínima completa."
      />

      <div className="flex items-center gap-2 rounded-lg border border-primary/25 bg-primary/5 px-4 py-2.5 text-sm text-primary">
        <Lock className="size-4" /> {elegibles.length} expedientes habilitados para deliberación de Sala.
      </div>

      {elegibles.map((d) => {
        const completo = d.revisiones.every((r) => r.concepto !== null);
        return (
          <Card key={d.id} className="shadow-panel">
            <CardHeader className="gap-3">
              <div className="flex flex-wrap items-start justify-between gap-4">
                <div>
                  <p className="font-mono text-xs text-muted-foreground">{d.radicado}</p>
                  <h3 className="text-lg font-semibold">{d.producto}</h3>
                  <p className="text-sm text-muted-foreground">
                    {d.solicitante} · {d.principioActivo}
                  </p>
                </div>
                <MatchBadge value={d.similitud} />
              </div>
            </CardHeader>

            <CardContent className="space-y-6">
              <div>
                <p className="mb-2 text-xs font-semibold tracking-widest text-muted-foreground uppercase">
                  Antecedentes históricos
                </p>
                <div className="space-y-2">
                  {d.antecedentes.map((a) => (
                    <div
                      key={a.radicado}
                      className="flex flex-wrap items-start gap-3 rounded-lg border border-border bg-muted/30 p-3"
                    >
                      <div className="min-w-[220px] flex-1">
                        <p className="text-sm font-medium">{a.producto}</p>
                        <p className="font-mono text-xs text-muted-foreground">
                          {a.radicado} · {a.anio} · coincidencia {a.coincidencia}%
                        </p>
                        <p className="mt-1 text-sm text-muted-foreground">{a.motivo}</p>
                      </div>
                      <StatusPill tone={a.dictamen === "Aprobado" ? "aprobado" : "denegado"}>
                        {a.dictamen}
                      </StatusPill>
                    </div>
                  ))}
                </div>
              </div>

              <div className="rounded-lg border border-primary/25 bg-primary/5 p-4">
                <p className="flex items-center gap-2 text-sm font-semibold text-primary">
                  <Bot className="size-4" /> Asistente IA de decisión
                </p>
                <p className="mt-2 text-sm text-muted-foreground">
                  Con base en {d.antecedentes.length} antecedentes comparables ({d.similitud}% de coincidencia) y en
                  la normatividad sanitaria vigente, se sugiere concepto{" "}
                  <span className="font-semibold text-foreground">
                    {d.revisiones.some((r) => r.concepto === "Requiere Ajustes")
                      ? "APROBADO CONDICIONADO a la subsanación de los puntos observados por los grupos evaluadores"
                      : "FAVORABLE para la expedición del registro sanitario"}
                  </span>
                  . {d.alertas.length ? `Se recomienda seguimiento reforzado: ${d.alertas.join(" ")}` : ""}
                </p>
              </div>

              <div>
                <p className="mb-2 text-xs font-semibold tracking-widest text-muted-foreground uppercase">
                  Revisión por grupos
                </p>
                <div className="grid gap-3 md:grid-cols-2">
                  {d.revisiones.map((r) => (
                    <div key={r.grupo} className="rounded-lg border border-border bg-card p-4">
                      <div className="flex items-start justify-between gap-2">
                        <p className="text-sm font-semibold">{r.grupo}</p>
                        <ConceptoPill concepto={r.concepto} />
                      </div>
                      <p className="mt-1 text-xs text-muted-foreground">Responsable: {r.responsable}</p>
                      <p className="mt-2 text-sm text-muted-foreground">
                        {r.observaciones || "Sin observaciones registradas."}
                      </p>
                    </div>
                  ))}
                </div>
              </div>

              <Separator />

              <div className="flex flex-wrap justify-end gap-2">
                <Button
                  variant="outline"
                  className="gap-2"
                  disabled={!completo}
                  onClick={() => setPreliminar(d)}
                >
                  <ScrollText className="size-4" />
                  {completo ? "Ver preliminar de decisión" : "Pendiente revisión de los 4 grupos"}
                </Button>
                <Button
                  className="gap-2"
                  disabled={!completo}
                  onClick={() =>
                    toast.success("Acto administrativo notificado", {
                      description: `El acto administrativo del expediente ${d.radicado} fue enviado al correo registrado de ${d.solicitante}.`,
                    })
                  }
                >
                  <Mail className="size-4" /> Notificar al postulante
                </Button>
              </div>
            </CardContent>
          </Card>
        );
      })}

      <PreliminarModal dossier={preliminar} onClose={() => setPreliminar(null)} />
    </div>
  );
}

function PreliminarModal({ dossier, onClose }: { dossier: Dossier | null; onClose: () => void }) {
  const resolucion = dossier
    ? dossier.revisiones.every((r) => r.concepto === "Aprobado")
      ? "CONCEDER"
      : dossier.revisiones.some((r) => r.concepto === "Denegado")
        ? "NEGAR"
        : "CONCEDER CONDICIONADO"
    : "";

  return (
    <Dialog open={!!dossier} onOpenChange={(o) => !o && onClose()}>
      <DialogContent className="max-h-[88vh] overflow-y-auto sm:max-w-3xl">
        <DialogHeader className="sr-only">
          <DialogTitle>Preliminar de decisión</DialogTitle>
        </DialogHeader>
        {dossier ? (
          <div className="rounded-md border border-border bg-card p-8 font-sans shadow-panel">
            <div className="flex items-start gap-4 border-b-2 border-navy pb-4">
              <InvimaCrest className="size-14" />
              <div className="leading-tight">
                <p className="font-display text-base font-bold text-navy">
                  INSTITUTO NACIONAL DE VIGILANCIA DE MEDICAMENTOS Y ALIMENTOS
                </p>
                <p className="text-xs text-muted-foreground">
                  INVIMA · Ministerio de Salud y Protección Social · República de Colombia
                </p>
                <p className="text-xs text-muted-foreground">
                  Sala Especializada de Medicamentos y Productos Biológicos
                </p>
              </div>
            </div>

            <div className="mt-6 text-center">
              <p className="font-display text-sm font-bold tracking-wide">
                ACTA PRELIMINAR DE DECISIÓN No. {dossier.radicado.replace("INV-", "SEMPB-")}
              </p>
              <p className="text-xs text-muted-foreground">
                Por la cual se emite concepto sobre la solicitud de certificado sanitario para comercialización
              </p>
            </div>

            <div className="mt-6 space-y-1 text-sm">
              <p>
                <span className="font-semibold">Producto:</span> {dossier.producto}
              </p>
              <p>
                <span className="font-semibold">Principio activo:</span> {dossier.principioActivo}
              </p>
              <p>
                <span className="font-semibold">Solicitante:</span> {dossier.solicitante}
              </p>
              <p>
                <span className="font-semibold">Fecha de radicado:</span> {dossier.fechaRadicado}
              </p>
              <p>
                <span className="font-semibold">Coincidencia con antecedentes:</span> {dossier.similitud}%
              </p>
            </div>

            <p className="mt-6 text-sm font-semibold">RESUMEN DE CONCEPTOS</p>
            <table className="mt-2 w-full border-collapse text-sm">
              <thead>
                <tr className="bg-muted/60 text-left">
                  <th className="border border-border px-3 py-2 font-semibold">Instancia</th>
                  <th className="border border-border px-3 py-2 font-semibold">Responsable</th>
                  <th className="border border-border px-3 py-2 font-semibold">Concepto</th>
                </tr>
              </thead>
              <tbody>
                {dossier.revisiones.map((r) => (
                  <tr key={r.grupo}>
                    <td className="border border-border px-3 py-2">{r.grupo}</td>
                    <td className="border border-border px-3 py-2">{r.responsable}</td>
                    <td className="border border-border px-3 py-2">{r.concepto}</td>
                  </tr>
                ))}
              </tbody>
            </table>

            <p className="mt-6 text-sm font-semibold">RESOLUCIÓN</p>
            <p className="mt-2 text-sm leading-relaxed">
              La Sala Especializada de Medicamentos y Productos Biológicos, revisada la documentación de los módulos
              M1 a M8 y los conceptos de las instancias evaluadoras, recomienda{" "}
              <span className="font-semibold">{resolucion}</span> el certificado sanitario solicitado para el
              producto de la referencia
              {resolucion === "CONCEDER CONDICIONADO"
                ? ", sujeto a la subsanación de las observaciones consignadas por los grupos evaluadores dentro del término legal."
                : "."}
            </p>

            <div className="mt-10 flex justify-between gap-8 text-xs">
              <div className="flex-1 border-t border-foreground/40 pt-2 text-center">
                Secretaría Técnica de la Sala
              </div>
              <div className="flex-1 border-t border-foreground/40 pt-2 text-center">Presidente de la Sala</div>
            </div>

            <div className="mt-6 flex items-center justify-center gap-2 text-[11px] text-muted-foreground">
              <FileCheck2 className="size-3.5" /> Documento preliminar generado por InvimaAI · sin valor legal hasta
              su firma
            </div>
          </div>
        ) : null}
      </DialogContent>
    </Dialog>
  );
}
