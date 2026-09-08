import { cn } from "@/lib/utils";
import type { Concepto } from "@/lib/invima-data";
import { ShieldCheck } from "lucide-react";

export function StatusPill({
  tone,
  children,
  className,
}: {
  tone: "aprobado" | "denegado" | "ajustes" | "pendiente" | "proceso" | "info";
  children: React.ReactNode;
  className?: string;
}) {
  const tones: Record<string, string> = {
    aprobado: "bg-approve-soft text-approve-foreground border-approve/40",
    denegado: "bg-deny-soft text-deny border-deny/40",
    ajustes: "bg-warn-soft text-warn-foreground border-warn/50",
    pendiente: "bg-muted text-muted-foreground border-border",
    proceso: "bg-accent text-accent-foreground border-primary/25",
    info: "bg-primary/10 text-primary border-primary/25",
  };
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-xs font-semibold whitespace-nowrap",
        tones[tone],
        className,
      )}
    >
      {children}
    </span>
  );
}

export function ConceptoPill({ concepto }: { concepto: Concepto | null }) {
  if (!concepto) return <StatusPill tone="pendiente">Sin concepto</StatusPill>;
  const tone =
    concepto === "Aprobado" ? "aprobado" : concepto === "Denegado" ? "denegado" : "ajustes";
  return <StatusPill tone={tone}>{concepto}</StatusPill>;
}

export function MatchBadge({ value, className }: { value: number; className?: string }) {
  const tone = value >= 85 ? "text-approve" : value >= 65 ? "text-warn" : "text-muted-foreground";
  return (
    <div
      className={cn(
        "inline-flex items-center gap-2 rounded-xl border border-border/60 bg-card px-3 py-1.5 shadow-panel",
        className,
      )}
    >
      <span className="text-[10px] font-semibold tracking-widest text-muted-foreground uppercase">
        Coincidencia
      </span>
      <span className={cn("font-display text-lg leading-none font-bold tabular-nums", tone)}>
        {value}%
      </span>
    </div>
  );
}

export function InvimaCrest({ className }: { className?: string }) {
  return (
    <div
      className={cn(
        "flex size-10 items-center justify-center rounded-xl border border-navy-foreground/25 bg-gradient-to-br from-navy to-primary text-navy-foreground shadow-panel",
        className,
      )}
    >
      <ShieldCheck className="size-5" strokeWidth={2.2} />
    </div>
  );
}

export function SectionTitle({
  eyebrow,
  title,
  description,
}: {
  eyebrow?: string;
  title: string;
  description?: string;
}) {
  return (
    <div className="space-y-1.5">
      {eyebrow ? (
        <p className="text-[11px] font-semibold tracking-[0.18em] text-primary uppercase">
          {eyebrow}
        </p>
      ) : null}
      <h2 className="text-2xl font-bold tracking-tight">{title}</h2>
      {description ? <p className="text-sm text-muted-foreground">{description}</p> : null}
    </div>
  );
}
