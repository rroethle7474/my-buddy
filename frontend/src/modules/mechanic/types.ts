// Mechanic module types — aliased from the generated OpenAPI contract.
//
// `frontend/src/api/schema.d.ts` is generated (never hand-edited, COORDINATION.md
// §6). We alias the schemas we render off so components import a stable local
// name; if the contract moves, regen the schema and these aliases follow.
//
// The read view renders off the HYDRATED project (`GET /projects/{id}` →
// ProjectRead), which carries the spec §6 fields plus runtime state (checked /
// completed / note / owned / acquire).

import type { components } from "../../api/schema";

export type ProjectRead = components["schemas"]["ProjectRead"];
export type MaterialRead = components["schemas"]["MaterialRead"];
export type ToolRead = components["schemas"]["ToolRead"];
export type StepRead = components["schemas"]["StepRead"];
export type ResearchTopicRead = components["schemas"]["ResearchTopicRead"];
export type ResearchResource = components["schemas"]["ResearchResource"];
export type PhotoRead = components["schemas"]["PhotoRead"];
export type RetrospectiveRead = components["schemas"]["RetrospectiveRead"];

export type Difficulty = components["schemas"]["Difficulty"];
export type TimeBudget = components["schemas"]["TimeBudget"];
export type ProjectStatus = components["schemas"]["ProjectStatus"];

// The four rendered sections (§16.3). Values double as anchor ids / nav keys.
export type SectionKey = "shopping" | "tools" | "tutorial" | "research";
