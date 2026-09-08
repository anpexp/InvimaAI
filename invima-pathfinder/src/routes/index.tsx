import { createFileRoute } from "@tanstack/react-router";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Toaster } from "@/components/ui/sonner";
import { AppStateProvider, useAppState } from "@/lib/app-state";
import { Header } from "@/components/invima/Header";
import { DashboardView } from "@/components/invima/DashboardView";
import { SolicitanteView } from "@/components/invima/SolicitanteView";
import { EvaluadorView } from "@/components/invima/EvaluadorView";
import { DecisionView } from "@/components/invima/DecisionView";
import { DossiersTable } from "@/components/invima/DossiersTable";
import { LayoutDashboard, FileEdit, ClipboardCheck, Gavel, Table2 } from "lucide-react";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "InvimaAI · Certificados sanitarios de medicamentos" },
      {
        name: "description",
        content:
          "Entorno de trabajo institucional para la gestión, evaluación y decisión de solicitudes de certificados sanitarios de medicamentos en Colombia.",
      },
      { property: "og:title", content: "InvimaAI · Certificados sanitarios de medicamentos" },
      {
        property: "og:description",
        content:
          "Dossiers por módulos CTD, panel de evaluación con el agente INVAIA y panel de decisión de la Sala Especializada.",
      },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: () => (
    <AppStateProvider>
      <InvimaApp />
    </AppStateProvider>
  ),
});

function InvimaApp() {
  const { role } = useAppState();

  return (
    <div className="min-h-screen bg-background">
      <Header />
      <main className="mx-auto max-w-[1440px] px-5 py-6">
        <Tabs key={role} defaultValue={role === "sala" ? "decision" : role === "evaluador" ? "evaluacion" : "solicitud"}>
          <TabsList className="mb-6 h-auto flex-wrap">
            <TabsTrigger value="dashboard" className="gap-2">
              <LayoutDashboard className="size-4" /> Dashboard
            </TabsTrigger>
            {role === "solicitante" ? (
              <TabsTrigger value="solicitud" className="gap-2">
                <FileEdit className="size-4" /> Mi dossier
              </TabsTrigger>
            ) : null}
            {role === "evaluador" ? (
              <TabsTrigger value="evaluacion" className="gap-2">
                <ClipboardCheck className="size-4" /> Evaluación
              </TabsTrigger>
            ) : null}
            {role === "sala" ? (
              <TabsTrigger value="decision" className="gap-2">
                <Gavel className="size-4" /> Panel de decisión
              </TabsTrigger>
            ) : null}
            <TabsTrigger value="tabla" className="gap-2">
              <Table2 className="size-4" /> Tabla maestra
            </TabsTrigger>
          </TabsList>

          <TabsContent value="dashboard">
            <DashboardView />
          </TabsContent>
          {role === "solicitante" ? (
            <TabsContent value="solicitud">
              <SolicitanteView />
            </TabsContent>
          ) : null}
          {role === "evaluador" ? (
            <TabsContent value="evaluacion">
              <EvaluadorView />
            </TabsContent>
          ) : null}
          {role === "sala" ? (
            <TabsContent value="decision">
              <DecisionView />
            </TabsContent>
          ) : null}
          <TabsContent value="tabla">
            <DossiersTable />
          </TabsContent>
        </Tabs>
      </main>
      <footer className="border-t border-border py-6 text-center text-xs text-muted-foreground">
        InvimaAI · Prototipo institucional de gestión de certificados sanitarios · Datos simulados
      </footer>
      <Toaster position="top-right" richColors />
    </div>
  );
}
