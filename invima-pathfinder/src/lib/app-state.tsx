import { createContext, useContext, useMemo, useState, type ReactNode } from "react";
import { DOSSIERS, MODULES, type Dossier, type Role } from "./invima-data";

type Answers = Record<string, boolean>; // key: `${dossierId}:${moduleId}:${index}`

interface AppState {
  role: Role;
  setRole: (r: Role) => void;
  dossiers: Dossier[];
  activeDossierId: string;
  setActiveDossierId: (id: string) => void;
  answers: Answers;
  toggleAnswer: (key: string) => void;
  moduleProgress: (dossierId: string, moduleId: string) => number;
  globalProgress: (dossierId: string) => number;
}

const Ctx = createContext<AppState | null>(null);

export function AppStateProvider({ children }: { children: ReactNode }) {
  const [role, setRole] = useState<Role>("solicitante");
  const [activeDossierId, setActiveDossierId] = useState<string>(DOSSIERS[0]!.id);
  const [answers, setAnswers] = useState<Answers>(() => {
    const seed: Answers = {};
    // Pre-diligenciamiento parcial del dossier del solicitante
    MODULES.slice(0, 2).forEach((m) =>
      m.questions.forEach((_, i) => {
        if (i < m.questions.length - 2) seed[`d1:${m.id}:${i}`] = true;
      }),
    );
    return seed;
  });

  const value = useMemo<AppState>(() => {
    const moduleProgress = (dossierId: string, moduleId: string) => {
      const mod = MODULES.find((m) => m.id === moduleId);
      if (!mod) return 0;
      const done = mod.questions.filter((_, i) => answers[`${dossierId}:${moduleId}:${i}`]).length;
      return Math.round((done / mod.questions.length) * 100);
    };
    const globalProgress = (dossierId: string) => {
      const total = MODULES.reduce((a, m) => a + m.questions.length, 0);
      const done = MODULES.reduce(
        (a, m) => a + m.questions.filter((_, i) => answers[`${dossierId}:${m.id}:${i}`]).length,
        0,
      );
      return Math.round((done / total) * 100);
    };
    return {
      role,
      setRole,
      dossiers: DOSSIERS,
      activeDossierId,
      setActiveDossierId,
      answers,
      toggleAnswer: (key: string) => setAnswers((prev) => ({ ...prev, [key]: !prev[key] })),
      moduleProgress,
      globalProgress,
    };
  }, [role, activeDossierId, answers]);

  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}

export function useAppState() {
  const ctx = useContext(Ctx);
  if (!ctx) throw new Error("useAppState must be used within AppStateProvider");
  return ctx;
}
