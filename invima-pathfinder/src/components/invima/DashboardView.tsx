import { useAppState } from "@/lib/app-state";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { SectionTitle, StatusPill } from "./shared";
import { Progress } from "@/components/ui/progress";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { CalendarClock, FileStack, FileWarning, Inbox, RefreshCcw } from "lucide-react";

export function DashboardView() {
  const { dossiers } = useAppState();

  const fases = ["Documentación", "Evaluación Técnica", "Subsanación", "Sala Especializada", "Decisión"];
  const porFase = fases.map((f) => ({ fase: f, total: dossiers.filter((d) => d.fase === f).length }));
  const pendDoc = dossiers.filter((d) => d.fase === "Documentación").length;
  const pendSub = dossiers.filter((d) => d.fase === "Subsanación").length;
  const proxSala = dossiers.filter((d) => d.fase === "Sala Especializada" || d.fase === "Decisión");

  const kpis = [
    { label: "Solicitudes recibidas", value: dossiers.length, icon: Inbox, tone: "text-primary" },
    { label: "Pendientes de documentación", value: pendDoc, icon: FileWarning, tone: "text-warn" },
    { label: "Pendientes de subsanación", value: pendSub, icon: RefreshCcw, tone: "text-deny" },
    { label: "Próximos a Sala Especializada", value: proxSala.length, icon: CalendarClock, tone: "text-approve" },
  ];

  const colors = ["var(--color-primary)", "var(--color-warn)", "var(--color-deny)", "var(--color-approve)", "var(--color-chart-5)"];

  return (
    <div className="space-y-6">
      <SectionTitle
        eyebrow="Dashboard global"
        title="Estado general del proceso"
        description="Indicadores consolidados de las solicitudes de certificado sanitario en trámite."
      />

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {kpis.map((k) => {
          const Icon = k.icon;
          return (
            <Card key={k.label} className="shadow-panel">
              <CardContent className="flex items-center gap-4 py-5">
                <div className="flex size-11 items-center justify-center rounded-lg bg-muted">
                  <Icon className={`size-5 ${k.tone}`} />
                </div>
                <div>
                  <p className="font-display text-3xl leading-none font-bold tabular-nums">{k.value}</p>
                  <p className="mt-1 text-xs text-muted-foreground">{k.label}</p>
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card className="shadow-panel">
          <CardHeader>
            <p className="text-sm font-semibold">Distribución por fase del proceso</p>
          </CardHeader>
          <CardContent className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={porFase} margin={{ left: -20, bottom: 30 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" vertical={false} />
                <XAxis
                  dataKey="fase"
                  tick={{ fontSize: 11, fill: "var(--color-muted-foreground)" }}
                  angle={-18}
                  textAnchor="end"
                  interval={0}
                />
                <YAxis allowDecimals={false} tick={{ fontSize: 11, fill: "var(--color-muted-foreground)" }} />
                <Tooltip
                  contentStyle={{
                    background: "var(--color-card)",
                    border: "1px solid var(--color-border)",
                    borderRadius: 8,
                    fontSize: 12,
                  }}
                />
                <Bar dataKey="total" radius={[6, 6, 0, 0]}>
                  {porFase.map((_, i) => (
                    <Cell key={i} fill={colors[i % colors.length]} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        <Card className="shadow-panel">
          <CardHeader>
            <p className="text-sm font-semibold">Participación por fase</p>
          </CardHeader>
          <CardContent className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={porFase.filter((f) => f.total > 0)}
                  dataKey="total"
                  nameKey="fase"
                  innerRadius={55}
                  outerRadius={95}
                  paddingAngle={3}
                >
                  {porFase
                    .filter((f) => f.total > 0)
                    .map((_, i) => (
                      <Cell key={i} fill={colors[i % colors.length]} />
                    ))}
                </Pie>
                <Tooltip
                  contentStyle={{
                    background: "var(--color-card)",
                    border: "1px solid var(--color-border)",
                    borderRadius: 8,
                    fontSize: 12,
                  }}
                />
              </PieChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      <Card className="shadow-panel">
        <CardHeader className="flex-row items-center gap-2">
          <FileStack className="size-4 text-primary" />
          <p className="text-sm font-semibold">
            Próximos a presentar a la Sala Especializada de Medicamentos y Productos Biológicos
          </p>
        </CardHeader>
        <CardContent className="space-y-3">
          {proxSala.map((d) => (
            <div key={d.id} className="flex flex-wrap items-center gap-4 rounded-lg border border-border p-3">
              <div className="min-w-[220px] flex-1">
                <p className="text-sm font-medium">{d.producto}</p>
                <p className="font-mono text-xs text-muted-foreground">
                  {d.radicado} · {d.solicitante}
                </p>
              </div>
              <Progress value={d.avance} className="h-1.5 w-32" />
              <StatusPill tone="aprobado">{d.fase}</StatusPill>
            </div>
          ))}
        </CardContent>
      </Card>
    </div>
  );
}
