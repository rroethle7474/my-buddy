// Public surface of the mechanic module (D — ARCHITECTURE.md §13).
//
// The shell (C) mounts `MechanicProject` at /{module-slug}/{project-slug}/{view}
// (§16.2) and feeds it a hydrated project via `useMechanicProject`. On D3 the
// hook swaps its in-memory internals for live TanStack Query; nothing else here
// changes. `import "./styles.css"` here so any consumer of the module gets the
// scoped styles without a separate import.

import "./styles.css";
import "./generate.css";

export { MechanicProject } from "./components/MechanicProject";
export { useMechanicProject } from "./hooks/useMechanicProject";
export type { MechanicProjectApi } from "./hooks/useMechanicProject";
export { doorwayPullUpBar } from "./fixtures/doorwayPullUpBar";

// D2 — the generate-via-chat flow (1d/1e) and the docs (1f) route screen.
export { NewProjectFlow } from "./screens/NewProjectFlow";
export { ProjectDocsScreen } from "./screens/ProjectDocsScreen";
export type {
  ProjectRead,
  MaterialRead,
  ToolRead,
  StepRead,
  ResearchTopicRead,
  SectionKey,
} from "./types";
