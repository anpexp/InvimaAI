import { useMemo, useState } from "react";
import { useAppState } from "@/lib/app-state";
import type { Dossier } from "@/lib/invima-data";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { SectionTitle, StatusPill, MatchBadge, ConceptoPill } from "./shared";
import { ArrowDownUp, ExternalLink, Search } from "lucide-react";

type SortKey = "similitud" | "avance";

export function DossiersTable() {
  const { dossiers } = useAppState();
  const [q, setQ] = useState("");
  const [fase, setFase] = useState("todas");
  const [sort, setSort] = useState<SortKey>("similitud");
  const [dir, setDir] = useState<"asc" | "desc">("desc");
  const [open, setOpen] = useState<Dossier | null>(null);

  const rows = useMemo(() => {
    const term = q.trim().toLowerCase();
    return dossiers
      .filter(
        (d) =>
          (fase === "todas" || d.fase === fase) &&
          (!term ||
            [d.producto, d.solicitante, d.radicado, d.principioActivo, ...d.tags]
              .join(" ")
              .toLowerCase()
              .includes(term)),
      )
      .sort((a, b) => (dir === "desc" ? b[sort] - a[sort] : a[sort] - b[sort]));
  }, [dossiers, q, fase, sort, dir]);

  const toggleSort = (key: SortKey) => {
    if (key === sort) setDir(dir === "desc" ? "asc" : "desc");
    else {
      setSort(key);
      setDir("desc");
    }
  };

  return (
    <div className="space-y-6">
      <SectionTitle
        eyebrow="Tabla maestra"
        title="Dossiers en trámite"
        description="Filtre, busque y ordene los expedientes por probabilidad de similitud o porcentaje de avance."
      />

      <Card className="shadow-panel">
        <CardContent className="space-y-4 py-5">
          <div className="flex flex-wrap gap-3">
            <div className="relative min-w-[240px] flex-1">
              <Search className="absolute top-1/2 left-3 size-4 -translate-y-1/2 text-muted-foreground" />
              <Input
                value={q}
                onChange={(e) => setQ(e.target.value)}
                placeholder="Buscar por producto, solicitante, radicado o etiqueta…"
                className="pl-9"
              />
            </div>
            <Select value={fase} onValueChange={setFase}>
              <SelectTrigger className="w-[220px]">
                <SelectValue placeholder="Estado" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="todas">Todos los estados</SelectItem>
                {["Documentación", "Evaluación Técnica", "Subsanación", "Sala Especializada", "Decisión"].map(
                  (f) => (
                    <SelectItem key={f} value={f}>
                      {f}
                    </SelectItem>
                  ),
                )}
              </SelectContent>
            </Select>
          </div>

          <div className="overflow-x-auto rounded-lg border border-border">
            <Table>
              <TableHeader>
                <TableRow className="bg-muted/50">
                  <TableHead>Radicado</TableHead>
                  <TableHead>Producto</TableHead>
                  <TableHead>Solicitante</TableHead>
                  <TableHead>Estado</TableHead>
                  <TableHead>
                    <button
                      onClick={() => toggleSort("similitud")}
                      className="inline-flex items-center gap-1 hover:text-primary"
                    >
                      Similitud <ArrowDownUp className="size-3.5" />
                    </button>
                  </TableHead>
                  <TableHead className="min-w-[150px]">
                    <button
                      onClick={() => toggleSort("avance")}
                      className="inline-flex items-center gap-1 hover:text-primary"
                    >
                      Avance <ArrowDownUp className="size-3.5" />
                    </button>
                  </TableHead>
                  <TableHead className="text-right">Acciones</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {rows.map((d) => (
                  <TableRow key={d.id}>
                    <TableCell className="font-mono text-xs">{d.radicado}</TableCell>
                    <TableCell className="max-w-[260px]">
                      <p className="truncate font-medium">{d.producto}</p>
                      <p className="truncate text-xs text-muted-foreground">{d.principioActivo}</p>
                    </TableCell>
                    <TableCell className="text-sm">{d.solicitante}</TableCell>
                    <TableCell>
                      <StatusPill tone={d.fase === "Subsanación" ? "ajustes" : "info"}>{d.fase}</StatusPill>
                    </TableCell>
                    <TableCell className="font-semibold tabular-nums">{d.similitud}%</TableCell>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        <Progress value={d.avance} className="h-1.5 w-20" />
                        <span className="text-xs tabular-nums">{d.avance}%</span>
                      </div>
                    </TableCell>
                    <TableCell className="text-right">
                      <Button variant="ghost" size="sm" className="gap-1.5" onClick={() => setOpen(d)}>
                        <ExternalLink className="size-3.5" /> Abrir
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
                {rows.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={7} className="py-10 text-center text-sm text-muted-foreground">
                      No se encontraron expedientes con los criterios seleccionados.
                    </TableCell>
                  </TableRow>
                ) : null}
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>

      <Dialog open={!!open} onOpenChange={(o) => !o && setOpen(null)}>
        <DialogContent className="max-h-[88vh] overflow-y-auto sm:max-w-2xl">
          {open ? (
            <>
              <DialogHeader>
                <DialogTitle className="pr-8 text-left">{open.producto}</DialogTitle>
                <p className="text-left text-sm text-muted-foreground">
                  {open.radicado} · {open.solicitante}
                </p>
              </DialogHeader>
              <div className="flex flex-wrap items-center gap-3">
                <MatchBadge value={open.similitud} />
                <StatusPill tone="info">{open.fase}</StatusPill>
                <StatusPill tone="proceso">Avance {open.avance}%</StatusPill>
              </div>
              <div className="space-y-2">
                <p className="text-xs font-semibold tracking-widest text-muted-foreground uppercase">
                  Conceptos por instancia
                </p>
                {open.revisiones.map((r) => (
                  <div
                    key={r.grupo}
                    className="flex flex-wrap items-center justify-between gap-2 rounded-lg border border-border p-3"
                  >
                    <div>
                      <p className="text-sm font-medium">{r.grupo}</p>
                      <p className="text-xs text-muted-foreground">{r.responsable}</p>
                    </div>
                    <ConceptoPill concepto={r.concepto} />
                  </div>
                ))}
              </div>
              <div className="space-y-2">
                <p className="text-xs font-semibold tracking-widest text-muted-foreground uppercase">
                  Archivos cargados
                </p>
                <ul className="divide-y divide-border rounded-lg border border-border">
                  {open.archivos.map((a) => (
                    <li key={a.nombre} className="flex items-center gap-3 px-3 py-2 text-sm">
                      <span className="font-mono text-xs text-primary">{a.modulo}</span>
                      <span className="flex-1 truncate">{a.nombre}</span>
                      <span className="text-xs text-muted-foreground">{a.paginas} pág.</span>
                    </li>
                  ))}
                </ul>
              </div>
            </>
          ) : null}
        </DialogContent>
      </Dialog>
    </div>
  );
}
