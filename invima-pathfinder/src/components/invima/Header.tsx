import { useAppState } from "@/lib/app-state";
import type { Role } from "@/lib/invima-data";
import { InvimaCrest } from "./shared";
import { Button } from "@/components/ui/button";
import { Building2, Gavel, Microscope, Sparkles } from "lucide-react";
import { cn } from "@/lib/utils";

const ROLES: { id: Role; label: string; short: string; icon: typeof Building2 }[] = [
  { id: "solicitante", label: "Solicitante", short: "Empresa farmacéutica", icon: Building2 },
  { id: "evaluador", label: "Evaluador Técnico", short: "Funcionario INVIMA", icon: Microscope },
  { id: "sala", label: "Sala Especializada", short: "Miembro de Sala", icon: Gavel },
];

export function Header() {
  const { role, setRole } = useAppState();
  const current = ROLES.find((r) => r.id === role)!;

  return (
    <header className="gov-header sticky top-0 z-40 text-navy-foreground shadow-lg">
      <div className="mx-auto flex max-w-[1440px] flex-wrap items-center gap-4 px-5 py-3.5">
        <div className="flex items-center gap-3">
          <InvimaCrest className="border-navy-foreground/30 bg-navy-foreground/10" />
          <div className="leading-tight">
            <p className="font-display text-lg font-extrabold tracking-tight">
              Invima<span className="text-approve">AI</span>
            </p>
            <p className="text-[11px] text-navy-foreground/70">
              Gestión de certificados sanitarios de medicamentos · Colombia
            </p>
          </div>
        </div>

        <div className="ml-auto flex items-center gap-3">
          <div className="hidden items-center gap-1.5 rounded-full border border-navy-foreground/20 bg-navy-foreground/10 px-3 py-1 text-[11px] md:flex">
            <Sparkles className="size-3.5 text-approve" />
            INVAIA activo
          </div>
          <div className="flex rounded-xl border border-navy-foreground/20 bg-navy-foreground/10 p-1">
            {ROLES.map((r) => {
              const Icon = r.icon;
              const active = r.id === role;
              return (
                <Button
                  key={r.id}
                  size="sm"
                  variant="ghost"
                  onClick={() => setRole(r.id)}
                  className={cn(
                    "h-8 gap-2 rounded-lg px-3 text-xs hover:bg-navy-foreground/15 hover:text-navy-foreground",
                    active
                      ? "bg-navy-foreground text-navy shadow-panel hover:bg-navy-foreground hover:text-navy"
                      : "text-navy-foreground/80",
                  )}
                >
                  <Icon className="size-3.5" />
                  <span className="hidden sm:inline">{r.label}</span>
                </Button>
              );
            })}
          </div>
        </div>
      </div>
      <div className="gov-rule h-1 w-full" />
      <div className="mx-auto max-w-[1440px] px-5 py-1.5 text-[11px] text-navy-foreground/70">
        Sesión activa como <span className="font-medium text-navy-foreground">{current.label}</span>{" "}
        · {current.short}
      </div>
    </header>
  );
}
