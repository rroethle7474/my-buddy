// Project data layer for the mechanic flow — import (create from spec), fetch a
// hydrated project by its URL slug, and the research refresh (§7.2). Built on the
// shared openapi-fetch client; the shell's src/api/hooks.ts owns the list/module
// reads, we add the project-detail + write paths D2/D3 need.

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "../../../api/client";
import type { components } from "../../../api/schema";
import type {
  MaterialRead,
  ProjectRead,
  ResearchTopicRead,
  RetrospectiveRead,
  RetrospectiveUpsert,
  StepRead,
  ToolRead,
} from "../types";

type ProjectSpec = components["schemas"]["ProjectSpec"];
type MaterialUpdate = components["schemas"]["MaterialUpdate"];
type ToolUpdate = components["schemas"]["ToolUpdate"];
type StepUpdate = components["schemas"]["StepUpdate"];

// --- Item-state PATCHes (§11, offline-queued-friendly). Each returns the single
// updated entity (the exact delta), so the caller reconciles its cache by id
// without re-fetching the whole project. Used by useMechanicProject (D3). ---

/** PATCH /projects/{id}/materials/{mid} — toggle a shopping-cart checkbox. */
export async function patchMaterial(
  projectId: number,
  materialId: number,
  body: MaterialUpdate,
): Promise<MaterialRead> {
  const { data, error } = await api.PATCH(
    "/projects/{project_id}/materials/{material_id}",
    { params: { path: { project_id: projectId, material_id: materialId } }, body },
  );
  if (error || !data) throw new Error("Could not save that change.");
  return data;
}

/** PATCH /projects/{id}/tools/{tid} — toggle `checked` and/or move buckets (`owned`). */
export async function patchTool(
  projectId: number,
  toolId: number,
  body: ToolUpdate,
): Promise<ToolRead> {
  const { data, error } = await api.PATCH(
    "/projects/{project_id}/tools/{tool_id}",
    { params: { path: { project_id: projectId, tool_id: toolId } }, body },
  );
  if (error || !data) throw new Error("Could not save that change.");
  return data;
}

/** PATCH /projects/{id}/steps/{sid} — toggle `completed` / save the journal `note`. */
export async function patchStep(
  projectId: number,
  stepId: number,
  body: StepUpdate,
): Promise<StepRead> {
  const { data, error } = await api.PATCH(
    "/projects/{project_id}/steps/{step_id}",
    { params: { path: { project_id: projectId, step_id: stepId } }, body },
  );
  if (error || !data) throw new Error("Could not save that change.");
  return data;
}

/** PATCH /projects/{id}/retrospective — upsert the end-of-project reflection (§5). */
export async function upsertRetrospective(
  projectId: number,
  body: RetrospectiveUpsert,
): Promise<RetrospectiveRead> {
  const { data, error } = await api.PATCH(
    "/projects/{project_id}/retrospective",
    { params: { path: { project_id: projectId } }, body },
  );
  if (error || !data) throw new Error("Could not save your retrospective.");
  return data;
}

/** POST /projects — the import path: validate + persist + run the shop diff (§8),
 *  returning the hydrated project. Invalidates the projects list so the new build
 *  shows up in the 1a/1c grids. */
export function useCreateProject() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (spec: ProjectSpec): Promise<ProjectRead> => {
      const { data, error } = await api.POST("/projects", { body: spec });
      if (error || !data) throw new Error("Could not save your plan. Please try again.");
      return data;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["projects"] });
    },
  });
}

/** Resolve `{module}/{project-slug}` → hydrated project. The route is slug-based
 *  (§16.2) but GET /projects/{id} is id-based, so we list by module, match the
 *  slug, then fetch the detail. `seed` (the just-created ProjectRead) renders the
 *  docs instantly after generation while the query settles. */
export function useProjectBySlug(
  moduleSlug: string,
  projectSlug: string | undefined,
  seed?: ProjectRead,
) {
  return useQuery({
    queryKey: ["project", moduleSlug, projectSlug],
    enabled: Boolean(moduleSlug && projectSlug),
    initialData: seed,
    queryFn: async (): Promise<ProjectRead> => {
      const { data: list, error } = await api.GET("/projects", {
        params: { query: { module: moduleSlug } },
      });
      if (error || !list) throw new Error("Could not load your projects.");
      const row = list.find((p) => p.slug === projectSlug);
      if (!row) throw new Error("We couldn't find that project.");
      const { data, error: detailError } = await api.GET("/projects/{project_id}", {
        params: { path: { project_id: row.id } },
      });
      if (detailError || !data) throw new Error("Could not load this project.");
      return data;
    },
  });
}

/** POST /projects/{id}/research/refresh — fill each topic's `resources[]` via web
 *  search (§7.2). Fired right after create (02:40Z DECISION); returns the topics. */
export function useResearchRefresh() {
  return useMutation({
    mutationFn: async (projectId: number): Promise<ResearchTopicRead[]> => {
      const { data, error } = await api.POST(
        "/projects/{project_id}/research/refresh",
        { params: { path: { project_id: projectId } } },
      );
      if (error || !data) throw new Error("Could not fetch research resources.");
      return data;
    },
  });
}
