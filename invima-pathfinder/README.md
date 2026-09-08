# Med-Cert AI

Crea una aplicación web moderna, profesional e institucional llamada **InvimaAI**, un entorno de trabajo integral para la gestión de solicitudes de certificados sanitarios de medicamentos para comercialización en Colombia.

### 🎨 Estilo y Diseño

- **Paleta de colores:** Azul institucional gubernamental (#0F2C59 / #1E3A8A), verde de aprobación (#10B981), ámbar para advertencias (#F59E0B) y rojo para denegaciones (#EF4444).

- **Tipografía y UI:** Limpia, tipo dashboard gubernamental de alta tecnología. Uso de Shadcn UI, Tailwind CSS, Lucide Icons, badges de estado, modales interactivos y pestañas claras.

---

### 👥 Arquitectura de Roles y Navegación

La aplicación debe contar con un selector de rol rápido en el encabezado (Header) para alternar entre:

1. **Solicitante** (Empresa farmacéutica)

2. **Evaluador Técnico** (Funcionario INVIMA)

3. **Miembro de la Sala Especializada** (Acceso exclusivo al panel de Decisión)

---

### 📁 1. Módulo de Solicitante (Diligenciamiento por Fases)

Vista de formulario por fases con barra de progreso global y banderas de estado por sección (Pendiente, En Proceso, Aprobado). El dossier se divide en 5 módulos interactivos con listas de chequeo/preguntas a diligenciar:

#### **Módulo 1 y 2: Administración, Legalidad y Síntesis Experta**

* ¿Existe correspondencia exacta entre el trámite solicitado, la tarifa pagada, el solicitante y el producto propuesto?

* ¿Hay coherencia entre los roles involucrados (titular, fabricante, importador) con sus respectivas direcciones, responsabilidades y certificados?

* ¿Son válidos, auténticos y vigentes los poderes, autorizaciones, contratos, traducciones y apostillas?

* ¿La composición, forma farmacéutica, indicación, dosis y vía de administración son consistentes con los demás módulos (M2, M3, M5) y con la etiqueta propuesta?

* ¿Aplica y está debidamente justificada la solicitud de protección de información no divulgada?

* ¿El resumen general de calidad representa de forma fiel los materiales, el proceso de fabricación, los controles y la estabilidad?

* ¿Son relevantes para la exposición humana y los riesgos clínicos los resúmenes presentados de farmacología, farmacocinética y toxicología?

* ¿Es coherente la conclusión sobre el balance beneficio-riesgo con los estudios realizados y la población objetivo?

#### **Módulo 3: Calidad**

* ¿La sustancia activa está inequívocamente identificada y controlada?

* ¿Los riesgos de origen y la variabilidad de las materias primas y materiales están controlados?

* ¿El proceso de fabricación propuesto logra reproducir el producto dentro de límites aceptables?

* ¿Los atributos críticos del producto terminado están claramente definidos y medidos?

* ¿El método analítico implementado es apto, sensible y reproducible?

* ¿Los resultados de los datos de los lotes reflejan fielmente el proceso comercial que se propone?

* ¿La vida útil propuesta, así como el envase y su manejo, están sustentados por estudios de estabilidad?

* ¿Se encuentran mitigados los riesgos específicos o propios de la plataforma/proceso (como impurezas, nitrosaminas o agentes adventicios)?

#### **Módulo 4: Estudios No Clínicos**

* ¿El objetivo y el diseño del estudio permiten responder adecuadamente a las preguntas de eficacia o toxicidad planteadas?

* ¿Está justificada la elección de la especie o modelo animal para determinar su relevancia biológica y viabilidad de extrapolación?

* ¿Cómo se conectan los hallazgos de dosis, vía y duración estudiados con la exposición clínica que se tiene prevista para humanos?

* ¿Los hallazgos identificados, su nivel de severidad y su reversibilidad apoyan la caracterización del riesgo?

* ¿Existen puntos de referencia claros (como el NOAEL) para contribuir al cálculo de márgenes de seguridad y selección de dosis?

* ¿Se reportan limitaciones y desviaciones en el estudio para evitar sobreinterpretar evidencia que pueda ser débil o incompleta?

* ¿Se evidencia un enlace claro entre el riesgo no clínico hallado y su correspondiente vigilancia o resolución en los estudios clínicos?

#### **Módulo 5: Estudios Clínicos**

* ¿La dosis, la frecuencia, la vía de administración y la población propuesta están debidamente sustentadas en la farmacología clínica?

* ¿El efecto evidenciado en los ensayos clínicos de eficacia es clínicamente relevante y estadísticamente sólido?

* ¿El perfil de riesgo, incluyendo eventos adversos y discontinuaciones, se encuentra suficientemente caracterizado?

* ¿La estrategia analítica y el seguimiento implementados logran capturar correctamente el riesgo de inmunogenicidad?

* ¿La indicación solicitada y el etiquetado pretenden extrapolar datos más allá de la evidencia obtenida en las poblaciones estudiadas?

* ¿El análisis estadístico presentado respalda la conclusión general sin contener sesgos materiales?

* ¿La conclusión del balance beneficio-riesgo es coherente tomando en cuenta la magnitud del beneficio, las incertidumbres y el contexto clínico general?

#### **Módulo 5 Extensiones: Poscomercialización, PGR y Textos (M6, M7, M8)**

* (M6) ¿Existe coherencia entre las señales y alertas de la historia comercial frente a la etiqueta, contraindicaciones y acciones regulatorias?

* (M7) ¿Hay una relación trazable donde el riesgo se traduzca en una evidencia, una actividad, un objetivo y un indicador de efectividad para minimizarlo?

* (M8) ¿El nombre, composición, indicación, dosis, advertencias y reacciones adversas presentes en las etiquetas e inserto son completamente consistentes contra lo aprobado en los módulos anteriores?

---

### 🔍 2. Panel de Evaluación (Rol Evaluador)

- Vista en formato de **Cards de Solicitudes**. Cada card muestra: Nombre del producto, Solicitante, Fecha de radicado, Porcentaje de avance y Tags.

- **Detalle de la Solicitud:** Al abrir una card, permite explorar los archivos cargados por módulo.

- **Agente IA Integrado (INVAIA):** Botón *"Solicitar investigación a INVAIA"*. Al activarlo, simula una búsqueda en base de datos de antecedentes por etiquetas y palabras clave, mostrando:

  - Dossiers similares encontrados.

  - Porcentaje de coincidencia.

  - Conclusiones y alertas detectadas en antecedentes.

---

### ⚖️ 3. Panel de Decisión (Exclusivo Sala Especializada de Medicamentos)

*Restringido solo para el rol de miembro de la Sala Especializada.* Muestra únicamente dossiers completamente evaluados con documentación mínima completa.

- **Métricas de Coincidencia:** Badge destacado con `% de Coincidencia` con otros dossiers y antecedentes.

- **Antecedentes Históricos:** Sección que despliega solicitudes similares previa con su dictamen (*Aprobado / Denegado*) y el motivo o justificación técnica de dicha decisión.

- **Asistente IA de Decisión:** Agente simulado que emite un concepto/opinión técnica sugerida basada en los antecedentes y regulaciones vigentes.

- **Estructura de Revisión en 3 Grupos + Evaluación Técnica:**

  Cada dossier debe mostrar la evaluación de 4 entidades/responsables con su concepto (`Aprobado`, `Denegado`, `Requiere Ajustes`), persona responsable y observaciones:

  1. *Evaluación del Grupo Técnico*

  2. *Grupo de Farmacovigilancia*

  3. *Grupo de Registros Sanitarios*

  4. *Equipo de Apoyo a Salas*

- **Acciones Finales:**

  - Botón **"Ver preliminar de decisión"**: Se habilita únicamente cuando los 3 grupos + grupo técnico han completado su revisión. Abre un modal que simula un **documento PDF oficial gubernamental** formateado con el escudo, membrete del INVIMA, resumen de los 4 conceptos y la resolución final.

  - Botón **"Notificar al postulante"**: Dispara un Toast/Notificación del sistema indicando que el acto administrativo ha sido enviado al correo del solicitante.

---

### 📊 4. Dashboard Global de Estado

Un panel general con KPIs y gráficos resumidos:

- **Total de solicitudes recibidas**

- **Distribución por fase actual del proceso**

- **Solicitudes pendientes de documentación**

- **Solicitudes pendientes de subsanación**

- **Próximos a presentar a la Sala Especializada de Medicamentos y Productos Biológicos**

---

### 📋 5. Tabla Maestra de Dossiers

Tabla completa tipo Data-Table con capacidades de:

- Filtro por estado y buscador general.

- Ordenamiento dinámico por **Probabilidad de similitud** y **Porcentaje de avance del proceso**.

- Acciones rápidas para abrir el expediente completo.

This project was built with [Lovable](https://lovable.dev).

**Live app**: https://invima-pathfinder.lovable.app

## Build with Lovable

Continue developing this project in the [Lovable editor](https://lovable.dev/projects/310cff62-0c2a-4c9d-9dd3-2b5c42c769ee).

- **Ship faster**: describe what you want to build and Lovable handles the code.
- **Stay in sync**: every change made in Lovable is committed straight to this repository.
- **Full ownership**: this code is yours. Push to `main` on GitHub and your changes sync back into Lovable, ready for your next prompt.

## Development

Prefer working locally? You need Node.js and npm — [install with nvm](https://github.com/nvm-sh/nvm#installing-and-updating).

```sh
git clone <this-repository-url>
cd <repository-name>
npm i
npm run dev
```
