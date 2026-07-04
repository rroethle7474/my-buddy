import { useQuery } from "@tanstack/react-query";
import type { components } from "./schema";
import { api } from "./client";

// Handy aliases for the generated DTOs the shell renders (§5/§11).
export type ProjectSummary = components["schemas"]["ProjectSummary"];
export type ProjectRead = components["schemas"]["ProjectRead"];
export type ModuleRead = components["schemas"]["ModuleRead"];
export type ProjectStatus = components["schemas"]["ProjectStatus"];

export interface ProjectFilters {
  /** DB/API module slug, e.g. "mechanic" (§11 GET /projects?module=). */
  module?: string;
  status?: ProjectStatus;
}

/** GET /projects — the 1a "Your projects" grid and the 1c module list. */
export function useProjects(filters: ProjectFilters = {}) {
  return useQuery({
    queryKey: ["projects", filters],
    queryFn: async () => {
      const { data, error } = await api.GET("/projects", {
        params: { query: { module: filters.module, status: filters.status } },
      });
      if (error) throw new Error("Could not load your projects.");
      return data;
    },
  });
}

/** GET /modules — the module registry, live from the backend. */
export function useModules() {
  return useQuery({
    queryKey: ["modules"],
    queryFn: async () => {
      const { data, error } = await api.GET("/modules");
      if (error) throw new Error("Could not load modules.");
      return data;
    },
  });
}

/** GET /modules/{slug} — one module's detail (drives the 1c hero). */
export function useModule(slug: string) {
  return useQuery({
    queryKey: ["module", slug],
    queryFn: async () => {
      const { data, error } = await api.GET("/modules/{slug}", {
        params: { path: { slug } },
      });
      if (error) throw new Error("Could not load this module.");
      return data;
    },
    enabled: Boolean(slug),
  });
}
