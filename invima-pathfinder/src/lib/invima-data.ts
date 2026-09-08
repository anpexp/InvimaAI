export type Role = "solicitante" | "evaluador" | "sala";

export type SectionStatus = "pendiente" | "proceso" | "aprobado";
export type Concepto = "Aprobado" | "Denegado" | "Requiere Ajustes";

export interface ModuleDef {
  id: string;
  code: string;
  title: string;
  subtitle: string;
  questions: string[];
}

export const MODULES: ModuleDef[] = [
  {
    id: "m12",
    code: "M1 · M2",
    title: "Administración, Legalidad y Síntesis Experta",
    subtitle: "Correspondencia documental, roles, poderes y resúmenes de calidad y clínica",
    questions: [
      "¿Existe correspondencia exacta entre el trámite solicitado, la tarifa pagada, el solicitante y el producto propuesto?",
      "¿Hay coherencia entre los roles involucrados (titular, fabricante, importador) con sus respectivas direcciones, responsabilidades y certificados?",
      "¿Son válidos, auténticos y vigentes los poderes, autorizaciones, contratos, traducciones y apostillas?",
      "¿La composición, forma farmacéutica, indicación, dosis y vía de administración son consistentes con los demás módulos (M2, M3, M5) y con la etiqueta propuesta?",
      "¿Aplica y está debidamente justificada la solicitud de protección de información no divulgada?",
      "¿El resumen general de calidad representa de forma fiel los materiales, el proceso de fabricación, los controles y la estabilidad?",
      "¿Son relevantes para la exposición humana y los riesgos clínicos los resúmenes presentados de farmacología, farmacocinética y toxicología?",
      "¿Es coherente la conclusión sobre el balance beneficio-riesgo con los estudios realizados y la población objetivo?",
    ],
  },
  {
    id: "m3",
    code: "M3",
    title: "Calidad",
    subtitle: "Sustancia activa, proceso de fabricación, métodos analíticos y estabilidad",
    questions: [
      "¿La sustancia activa está inequívocamente identificada y controlada?",
      "¿Los riesgos de origen y la variabilidad de las materias primas y materiales están controlados?",
      "¿El proceso de fabricación propuesto logra reproducir el producto dentro de límites aceptables?",
      "¿Los atributos críticos del producto terminado están claramente definidos y medidos?",
      "¿El método analítico implementado es apto, sensible y reproducible?",
      "¿Los resultados de los datos de los lotes reflejan fielmente el proceso comercial que se propone?",
      "¿La vida útil propuesta, así como el envase y su manejo, están sustentados por estudios de estabilidad?",
      "¿Se encuentran mitigados los riesgos específicos o propios de la plataforma/proceso (como impurezas, nitrosaminas o agentes adventicios)?",
    ],
  },
  {
    id: "m4",
    code: "M4",
    title: "Estudios No Clínicos",
    subtitle: "Diseño experimental, modelos animales, hallazgos toxicológicos y márgenes de seguridad",
    questions: [
      "¿El objetivo y el diseño del estudio permiten responder adecuadamente a las preguntas de eficacia o toxicidad planteadas?",
      "¿Está justificada la elección de la especie o modelo animal para determinar su relevancia biológica y viabilidad de extrapolación?",
      "¿Cómo se conectan los hallazgos de dosis, vía y duración estudiados con la exposición clínica que se tiene prevista para humanos?",
      "¿Los hallazgos identificados, su nivel de severidad y su reversibilidad apoyan la caracterización del riesgo?",
      "¿Existen puntos de referencia claros (como el NOAEL) para contribuir al cálculo de márgenes de seguridad y selección de dosis?",
      "¿Se reportan limitaciones y desviaciones en el estudio para evitar sobreinterpretar evidencia que pueda ser débil o incompleta?",
      "¿Se evidencia un enlace claro entre el riesgo no clínico hallado y su correspondiente vigilancia o resolución en los estudios clínicos?",
    ],
  },
  {
    id: "m5",
    code: "M5",
    title: "Estudios Clínicos",
    subtitle: "Farmacología clínica, eficacia, seguridad, inmunogenicidad y balance beneficio-riesgo",
    questions: [
      "¿La dosis, la frecuencia, la vía de administración y la población propuesta están debidamente sustentadas en la farmacología clínica?",
      "¿El efecto evidenciado en los ensayos clínicos de eficacia es clínicamente relevante y estadísticamente sólido?",
      "¿El perfil de riesgo, incluyendo eventos adversos y discontinuaciones, se encuentra suficientemente caracterizado?",
      "¿La estrategia analítica y el seguimiento implementados logran capturar correctamente el riesgo de inmunogenicidad?",
      "¿La indicación solicitada y el etiquetado pretenden extrapolar datos más allá de la evidencia obtenida en las poblaciones estudiadas?",
      "¿El análisis estadístico presentado respalda la conclusión general sin contener sesgos materiales?",
      "¿La conclusión del balance beneficio-riesgo es coherente tomando en cuenta la magnitud del beneficio, las incertidumbres y el contexto clínico general?",
    ],
  },
  {
    id: "m678",
    code: "M6 · M7 · M8",
    title: "Poscomercialización, PGR y Textos",
    subtitle: "Historia comercial, plan de gestión de riesgo y consistencia de etiquetas e inserto",
    questions: [
      "(M6) ¿Existe coherencia entre las señales y alertas de la historia comercial frente a la etiqueta, contraindicaciones y acciones regulatorias?",
      "(M7) ¿Hay una relación trazable donde el riesgo se traduzca en una evidencia, una actividad, un objetivo y un indicador de efectividad para minimizarlo?",
      "(M8) ¿El nombre, composición, indicación, dosis, advertencias y reacciones adversas presentes en las etiquetas e inserto son completamente consistentes contra lo aprobado en los módulos anteriores?",
    ],
  },
];

export interface GroupReview {
  grupo: string;
  responsable: string;
  concepto: Concepto | null;
  observaciones: string;
}

export interface Antecedente {
  radicado: string;
  producto: string;
  anio: number;
  coincidencia: number;
  dictamen: "Aprobado" | "Denegado";
  motivo: string;
}

export interface Dossier {
  id: string;
  radicado: string;
  producto: string;
  principioActivo: string;
  solicitante: string;
  fechaRadicado: string;
  fase: "Documentación" | "Evaluación Técnica" | "Subsanación" | "Sala Especializada" | "Decisión";
  avance: number;
  similitud: number;
  tags: string[];
  archivos: { modulo: string; nombre: string; paginas: number }[];
  antecedentes: Antecedente[];
  revisiones: GroupReview[];
  alertas: string[];
}

const rev = (
  responsables: [string, string, string, string],
  conceptos: (Concepto | null)[],
  obs: string[],
): GroupReview[] =>
  ["Evaluación del Grupo Técnico", "Grupo de Farmacovigilancia", "Grupo de Registros Sanitarios", "Equipo de Apoyo a Salas"].map(
    (grupo, i) => ({
      grupo,
      responsable: responsables[i] ?? "",
      concepto: conceptos[i] ?? null,
      observaciones: obs[i] ?? "",
    }),
  );

export const DOSSIERS: Dossier[] = [
  {
    id: "d1",
    radicado: "INV-2026-004521",
    producto: "Onbrelizumab 150 mg/mL Solución Inyectable",
    principioActivo: "Onbrelizumab",
    solicitante: "BioAndina Pharma S.A.S.",
    fechaRadicado: "2026-03-14",
    fase: "Sala Especializada",
    avance: 100,
    similitud: 92,
    tags: ["Biotecnológico", "Anticuerpo monoclonal", "Artritis reumatoide", "Nuevo"],
    archivos: [
      { modulo: "M1 · M2", nombre: "01_Formato_unico_tramite.pdf", paginas: 24 },
      { modulo: "M1 · M2", nombre: "02_Poder_apostillado.pdf", paginas: 9 },
      { modulo: "M3", nombre: "03_Calidad_sustancia_activa.pdf", paginas: 312 },
      { modulo: "M3", nombre: "04_Estabilidad_lotes_comerciales.xlsx", paginas: 48 },
      { modulo: "M4", nombre: "05_Toxicologia_no_clinica.pdf", paginas: 187 },
      { modulo: "M5", nombre: "06_Ensayo_fase_III_ONB-301.pdf", paginas: 640 },
      { modulo: "M6 · M7 · M8", nombre: "07_PGR_y_textos_etiqueta.pdf", paginas: 76 },
    ],
    antecedentes: [
      {
        radicado: "INV-2023-001188",
        producto: "Adalimumab biosimilar 40 mg",
        anio: 2023,
        coincidencia: 88,
        dictamen: "Aprobado",
        motivo:
          "Comparabilidad analítica y clínica demostrada; PGR con plan de inmunogenicidad a 24 meses aceptado por la Sala.",
      },
      {
        radicado: "INV-2021-000734",
        producto: "Tocilizumab 162 mg/0.9 mL",
        anio: 2021,
        coincidencia: 74,
        dictamen: "Aprobado",
        motivo: "Perfil beneficio-riesgo favorable con restricción de indicación a población adulta.",
      },
      {
        radicado: "INV-2022-002903",
        producto: "Anticuerpo anti-IL6 (solicitud retirada de referencia)",
        anio: 2022,
        coincidencia: 61,
        dictamen: "Denegado",
        motivo:
          "Datos de estabilidad insuficientes para la vida útil propuesta y ausencia de validación del método de detección de anticuerpos neutralizantes.",
      },
    ],
    revisiones: rev(
      ["Q.F. Laura Restrepo M.", "Dra. Camila Ordóñez P.", "Abg. Juan D. Peláez", "Ing. Marcela Ruiz T."],
      ["Aprobado", "Requiere Ajustes", "Aprobado", "Aprobado"],
      [
        "Calidad, no clínico y clínico consistentes. Márgenes de seguridad adecuados (NOAEL 30 mg/kg).",
        "Se solicita fortalecer el indicador de efectividad para la minimización del riesgo de infecciones graves en el PGR.",
        "Documentación legal completa, poderes y apostillas vigentes.",
        "Expediente completo y trazable; apto para presentación en Sala.",
      ],
    ),
    alertas: [
      "Riesgo de inmunogenicidad reportado en antecedentes de la misma clase terapéutica.",
      "Señal de infecciones oportunistas en farmacovigilancia internacional (2024).",
    ],
  },
  {
    id: "d2",
    radicado: "INV-2026-004618",
    producto: "Metformina/Dapagliflozina 1000/10 mg Tableta LP",
    principioActivo: "Metformina + Dapagliflozina",
    solicitante: "Laboratorios Tequendama Ltda.",
    fechaRadicado: "2026-04-02",
    fase: "Evaluación Técnica",
    avance: 68,
    similitud: 84,
    tags: ["Sintético", "Combinación fija", "Diabetes tipo 2"],
    archivos: [
      { modulo: "M1 · M2", nombre: "01_Tarifa_y_formato.pdf", paginas: 18 },
      { modulo: "M3", nombre: "02_Calidad_producto_terminado.pdf", paginas: 210 },
      { modulo: "M3", nombre: "03_Nitrosaminas_evaluacion_riesgo.pdf", paginas: 33 },
      { modulo: "M5", nombre: "04_Bioequivalencia_BE-2025.pdf", paginas: 121 },
    ],
    antecedentes: [
      {
        radicado: "INV-2024-003310",
        producto: "Metformina/Empagliflozina 1000/12.5 mg",
        anio: 2024,
        coincidencia: 90,
        dictamen: "Aprobado",
        motivo: "Bioequivalencia demostrada frente a comparador y control de nitrosaminas satisfactorio.",
      },
      {
        radicado: "INV-2023-002011",
        producto: "Metformina LP 1000 mg (genérico)",
        anio: 2023,
        coincidencia: 66,
        dictamen: "Denegado",
        motivo: "Niveles de NDMA por encima del límite de ingesta diaria aceptable en lotes de estabilidad.",
      },
    ],
    revisiones: rev(
      ["Q.F. Andrés Villamil", "Dra. Paula Serrano", "Abg. Juan D. Peláez", "Ing. Marcela Ruiz T."],
      ["Requiere Ajustes", null, "Aprobado", null],
      [
        "Pendiente ampliar datos de tres lotes a escala comercial.",
        "",
        "Sin observaciones legales.",
        "",
      ],
    ),
    alertas: ["Antecedente de rechazo por nitrosaminas en el mismo principio activo."],
  },
  {
    id: "d3",
    radicado: "INV-2026-004702",
    producto: "Vacuna Recombinante VRS-Ad26 Suspensión",
    principioActivo: "Antígeno F estabilizado VRS",
    solicitante: "Inmunova Colombia S.A.",
    fechaRadicado: "2026-04-19",
    fase: "Documentación",
    avance: 31,
    similitud: 57,
    tags: ["Vacuna", "Biológico", "Población adulta mayor"],
    archivos: [
      { modulo: "M1 · M2", nombre: "01_Solicitud_registro.pdf", paginas: 15 },
      { modulo: "M3", nombre: "02_Banco_celular_maestro.pdf", paginas: 96 },
    ],
    antecedentes: [
      {
        radicado: "INV-2022-001450",
        producto: "Vacuna recombinante adyuvada Herpes Zóster",
        anio: 2022,
        coincidencia: 63,
        dictamen: "Aprobado",
        motivo: "Eficacia consistente en mayores de 60 años y control de agentes adventicios demostrado.",
      },
    ],
    revisiones: rev(
      ["Q.F. Laura Restrepo M.", "Dra. Camila Ordóñez P.", "Abg. Sofía Cárdenas", "Ing. Marcela Ruiz T."],
      [null, null, null, null],
      ["", "", "", ""],
    ),
    alertas: ["Documentación mínima incompleta: faltan módulos 4 y 5."],
  },
  {
    id: "d4",
    radicado: "INV-2026-004388",
    producto: "Rivaroxabán 20 mg Tableta Recubierta",
    principioActivo: "Rivaroxabán",
    solicitante: "Genfarma Andina S.A.S.",
    fechaRadicado: "2026-02-27",
    fase: "Subsanación",
    avance: 54,
    similitud: 79,
    tags: ["Sintético", "Genérico", "Anticoagulante"],
    archivos: [
      { modulo: "M1 · M2", nombre: "01_Certificado_CPP.pdf", paginas: 6 },
      { modulo: "M3", nombre: "02_Perfil_disolucion.pdf", paginas: 44 },
      { modulo: "M5", nombre: "03_Estudio_BE.pdf", paginas: 88 },
    ],
    antecedentes: [
      {
        radicado: "INV-2021-000912",
        producto: "Rivaroxabán 15 mg (genérico)",
        anio: 2021,
        coincidencia: 81,
        dictamen: "Aprobado",
        motivo: "Bioequivalencia con IC 90% dentro del rango 80-125%.",
      },
      {
        radicado: "INV-2024-003877",
        producto: "Apixabán 5 mg (genérico)",
        anio: 2024,
        coincidencia: 58,
        dictamen: "Denegado",
        motivo: "Inconsistencias entre el inserto propuesto y las contraindicaciones aprobadas del innovador.",
      },
    ],
    revisiones: rev(
      ["Q.F. Andrés Villamil", "Dra. Paula Serrano", "Abg. Sofía Cárdenas", "Ing. Marcela Ruiz T."],
      ["Requiere Ajustes", "Aprobado", "Requiere Ajustes", null],
      [
        "Perfil de disolución incompleto en medio pH 6.8.",
        "PGR estándar de clase aceptado.",
        "Debe actualizar el CPP con vigencia menor a dos años.",
        "",
      ],
    ),
    alertas: ["Requerimiento de subsanación notificado el 2026-04-08."],
  },
  {
    id: "d5",
    radicado: "INV-2026-004195",
    producto: "Insulina Glargina Biosimilar 100 UI/mL",
    principioActivo: "Insulina glargina",
    solicitante: "BioAndina Pharma S.A.S.",
    fechaRadicado: "2026-01-30",
    fase: "Decisión",
    avance: 100,
    similitud: 95,
    tags: ["Biosimilar", "Diabetes", "Vía comparabilidad"],
    archivos: [
      { modulo: "M1 · M2", nombre: "01_Comparabilidad_resumen.pdf", paginas: 40 },
      { modulo: "M3", nombre: "02_Caracterizacion_analitica.pdf", paginas: 288 },
      { modulo: "M4", nombre: "03_No_clinico_comparativo.pdf", paginas: 102 },
      { modulo: "M5", nombre: "04_Clinico_PK_PD_clamp.pdf", paginas: 233 },
      { modulo: "M6 · M7 · M8", nombre: "05_Textos_e_inserto.pdf", paginas: 51 },
    ],
    antecedentes: [
      {
        radicado: "INV-2020-000341",
        producto: "Insulina glargina biosimilar (otro titular)",
        anio: 2020,
        coincidencia: 95,
        dictamen: "Aprobado",
        motivo: "Comparabilidad fisicoquímica, PK/PD por clamp euglucémico e inmunogenicidad equivalentes.",
      },
      {
        radicado: "INV-2019-000205",
        producto: "Insulina humana rDNA 100 UI/mL",
        anio: 2019,
        coincidencia: 70,
        dictamen: "Aprobado",
        motivo: "Cumplimiento de estándares de calidad y estabilidad en cadena de frío.",
      },
    ],
    revisiones: rev(
      ["Q.F. Laura Restrepo M.", "Dra. Camila Ordóñez P.", "Abg. Juan D. Peláez", "Ing. Marcela Ruiz T."],
      ["Aprobado", "Aprobado", "Aprobado", "Aprobado"],
      [
        "Comparabilidad demostrada en los tres niveles de evidencia.",
        "PGR con seguimiento de hipoglucemias e inmunogenicidad adecuado.",
        "Expediente legal conforme al Decreto 677 de 1995 y normas concordantes.",
        "Documentación mínima completa y verificada.",
      ],
    ),
    alertas: [],
  },
  {
    id: "d6",
    radicado: "INV-2026-004760",
    producto: "Ácido Zoledrónico 5 mg/100 mL Solución para Infusión",
    principioActivo: "Ácido zoledrónico",
    solicitante: "Farmacéutica del Caribe S.A.",
    fechaRadicado: "2026-04-25",
    fase: "Documentación",
    avance: 22,
    similitud: 48,
    tags: ["Sintético", "Osteoporosis", "Uso hospitalario"],
    archivos: [{ modulo: "M1 · M2", nombre: "01_Radicado_inicial.pdf", paginas: 11 }],
    antecedentes: [
      {
        radicado: "INV-2022-001760",
        producto: "Ácido zoledrónico 4 mg/5 mL",
        anio: 2022,
        coincidencia: 72,
        dictamen: "Aprobado",
        motivo: "Equivalencia farmacéutica y esterilidad demostradas.",
      },
    ],
    revisiones: rev(
      ["Q.F. Andrés Villamil", "Dra. Paula Serrano", "Abg. Sofía Cárdenas", "Ing. Marcela Ruiz T."],
      [null, null, null, null],
      ["", "", "", ""],
    ),
    alertas: ["Pendiente de documentación: módulos 3, 4 y 5 no cargados."],
  },
];

export const conceptoTone = (c: Concepto | null) =>
  c === "Aprobado" ? "aprobado" : c === "Denegado" ? "denegado" : c === "Requiere Ajustes" ? "ajustes" : "pendiente";
