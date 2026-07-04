// useMechanicProject — the data seam for the mechanic sections.
//
// LIVE (TASKS D3): mutations update local state + the shared TanStack query cache
// optimistically (instant UI), then PATCH the §11 item-state endpoints and
// reconcile each entity from the server's response. On failure the one changed
// entity is rolled back and a transient error is surfaced. The MechanicProjectApi
// interface is unchanged from the D1 scaffold, so no section component changed:
//
//   PATCH /projects/{id}/materials/{mid}  { checked }         → toggleMaterial
//   PATCH /projects/{id}/tools/{tid}      { checked | owned }  → toggleTool / setToolOwned
//   PATCH /projects/{id}/steps/{sid}      { completed | note } → toggleStep / setStepNote
//
// Preview mode: when called WITHOUT `options` (the dev fixture preview, which has
// no live project or backend) mutations stay local-only, so the read view is still
// demoable end-to-end offline.

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import type { ProjectRead, RetrospectiveUpsert } from "../types";
import {
  patchMaterial,
  patchStep,
  patchTool,
  upsertRetrospective,
} from "../api/projects";

export interface MechanicProjectApi {
  project: ProjectRead;
  /** Toggle a shopping-cart (material) checkbox. */
  toggleMaterial: (materialId: number, checked: boolean) => void;
  /** Toggle a tool's "have it / packed it" checkbox. */
  toggleTool: (toolId: number, checked: boolean) => void;
  /** Move a tool between the owned and to-acquire buckets (shop diff, §8). */
  setToolOwned: (toolId: number, owned: boolean) => void;
  /** Mark a tutorial step complete / incomplete. */
  toggleStep: (stepId: number, completed: boolean) => void;
  /** Save a per-step journal note ("where I got stuck"). */
  setStepNote: (stepId: number, note: string) => void;
  /** Upsert the end-of-project retrospective (§5). Resolves on save, rejects on
   *  failure so the form can show its own pending/saved/failed state. */
  saveRetrospective: (draft: RetrospectiveUpsert) => Promise<void>;
  /** A recent change failed to save and was rolled back (null when all is well). */
  error: string | null;
  /** Dismiss the current error toast. */
  clearError: () => void;
}

export interface UseMechanicProjectOptions {
  /** Query-cache coordinates of the live project — must match `useProjectBySlug`'s
   *  key `["project", moduleSlug, projectSlug]`. When provided, mutations persist
   *  via PATCH and update that cache entry; when omitted, they stay local-only. */
  moduleSlug: string;
  projectSlug: string | undefined;
}

const SAVE_FAILED =
  "Couldn't save that change — check your connection and try again.";

export function useMechanicProject(
  initial: ProjectRead,
  options?: UseMechanicProjectOptions,
): MechanicProjectApi {
  const qc = useQueryClient();
  const live = options != null;
  const [project, setProject] = useState<ProjectRead>(initial);
  const [error, setError] = useState<string | null>(null);

  // Latest committed project, read inside handlers so rollback snapshots don't
  // capture a stale closure.
  const projectRef = useRef(project);
  useEffect(() => {
    projectRef.current = project;
  }, [project]);

  // Re-sync when the caller hands us a new project object (live load settling, the
  // research refresh merging in, or our own cache writes flowing back). A stable
  // `initial` (the fixture) never triggers this, so preview toggles persist.
  const seen = useRef(initial);
  useEffect(() => {
    if (initial !== seen.current) {
      seen.current = initial;
      setProject(initial);
    }
  }, [initial]);

  const queryKey = useMemo(
    () => ["project", options?.moduleSlug, options?.projectSlug] as const,
    [options?.moduleSlug, options?.projectSlug],
  );

  // Apply an updater to local state (instant, optimistic) and — in live mode — to
  // the shared query cache, so the docs view and any later revisit read the same.
  const applyBoth = useCallback(
    (updater: (p: ProjectRead) => ProjectRead) => {
      setProject(updater);
      if (live) {
        qc.setQueryData<ProjectRead>(queryKey, (old) => (old ? updater(old) : old));
      }
    },
    [live, qc, queryKey],
  );

  const clearError = useCallback(() => setError(null), []);

  // Auto-dismiss the transient error toast.
  useEffect(() => {
    if (!error) return;
    const t = setTimeout(() => setError(null), 4500);
    return () => clearTimeout(t);
  }, [error]);

  const toggleMaterial = useCallback(
    (materialId: number, checked: boolean) => {
      const prev = projectRef.current.materials.find((m) => m.id === materialId);
      applyBoth((p) => ({
        ...p,
        materials: p.materials.map((m) =>
          m.id === materialId ? { ...m, checked } : m,
        ),
      }));
      if (!live) return;
      patchMaterial(projectRef.current.id, materialId, { checked })
        .then((updated) =>
          applyBoth((p) => ({
            ...p,
            materials: p.materials.map((m) => (m.id === materialId ? updated : m)),
          })),
        )
        .catch(() => {
          if (prev) {
            applyBoth((p) => ({
              ...p,
              materials: p.materials.map((m) => (m.id === materialId ? prev : m)),
            }));
          }
          setError(SAVE_FAILED);
        });
    },
    [applyBoth, live],
  );

  const toggleTool = useCallback(
    (toolId: number, checked: boolean) => {
      const prev = projectRef.current.tools.find((t) => t.id === toolId);
      applyBoth((p) => ({
        ...p,
        tools: p.tools.map((t) => (t.id === toolId ? { ...t, checked } : t)),
      }));
      if (!live) return;
      patchTool(projectRef.current.id, toolId, { checked })
        .then((updated) =>
          applyBoth((p) => ({
            ...p,
            tools: p.tools.map((t) => (t.id === toolId ? updated : t)),
          })),
        )
        .catch(() => {
          if (prev) {
            applyBoth((p) => ({
              ...p,
              tools: p.tools.map((t) => (t.id === toolId ? prev : t)),
            }));
          }
          setError(SAVE_FAILED);
        });
    },
    [applyBoth, live],
  );

  const setToolOwned = useCallback(
    (toolId: number, owned: boolean) => {
      const prev = projectRef.current.tools.find((t) => t.id === toolId);
      applyBoth((p) => ({
        ...p,
        tools: p.tools.map((t) =>
          t.id === toolId ? { ...t, owned, acquire: !owned } : t,
        ),
      }));
      if (!live) return;
      patchTool(projectRef.current.id, toolId, { owned })
        .then((updated) =>
          applyBoth((p) => ({
            ...p,
            tools: p.tools.map((t) => (t.id === toolId ? updated : t)),
          })),
        )
        .catch(() => {
          if (prev) {
            applyBoth((p) => ({
              ...p,
              tools: p.tools.map((t) => (t.id === toolId ? prev : t)),
            }));
          }
          setError(SAVE_FAILED);
        });
    },
    [applyBoth, live],
  );

  const toggleStep = useCallback(
    (stepId: number, completed: boolean) => {
      const prev = projectRef.current.steps.find((s) => s.id === stepId);
      applyBoth((p) => ({
        ...p,
        steps: p.steps.map((s) => (s.id === stepId ? { ...s, completed } : s)),
      }));
      if (!live) return;
      patchStep(projectRef.current.id, stepId, { completed })
        .then((updated) =>
          applyBoth((p) => ({
            ...p,
            steps: p.steps.map((s) => (s.id === stepId ? updated : s)),
          })),
        )
        .catch(() => {
          if (prev) {
            applyBoth((p) => ({
              ...p,
              steps: p.steps.map((s) => (s.id === stepId ? prev : s)),
            }));
          }
          setError(SAVE_FAILED);
        });
    },
    [applyBoth, live],
  );

  const setStepNote = useCallback(
    (stepId: number, note: string) => {
      const value = note.trim() ? note : null;
      const prev = projectRef.current.steps.find((s) => s.id === stepId);
      applyBoth((p) => ({
        ...p,
        steps: p.steps.map((s) => (s.id === stepId ? { ...s, note: value } : s)),
      }));
      if (!live) return;
      patchStep(projectRef.current.id, stepId, { note: value })
        .then((updated) =>
          applyBoth((p) => ({
            ...p,
            steps: p.steps.map((s) => (s.id === stepId ? updated : s)),
          })),
        )
        .catch(() => {
          if (prev) {
            applyBoth((p) => ({
              ...p,
              steps: p.steps.map((s) => (s.id === stepId ? prev : s)),
            }));
          }
          setError(SAVE_FAILED);
        });
    },
    [applyBoth, live],
  );

  const saveRetrospective = useCallback(
    async (draft: RetrospectiveUpsert) => {
      if (!live) {
        applyBoth((p) => ({
          ...p,
          retrospective: {
            id: p.retrospective?.id ?? 0,
            project_id: p.id,
            created_at: p.retrospective?.created_at ?? new Date().toISOString(),
            ...draft,
          },
        }));
        return;
      }
      try {
        const updated = await upsertRetrospective(projectRef.current.id, draft);
        applyBoth((p) => ({ ...p, retrospective: updated }));
      } catch {
        setError("Couldn't save your retrospective — check your connection and try again.");
        throw new Error(SAVE_FAILED);
      }
    },
    [applyBoth, live],
  );

  return useMemo(
    () => ({
      project,
      toggleMaterial,
      toggleTool,
      setToolOwned,
      toggleStep,
      setStepNote,
      saveRetrospective,
      error,
      clearError,
    }),
    [
      project,
      toggleMaterial,
      toggleTool,
      setToolOwned,
      toggleStep,
      setStepNote,
      saveRetrospective,
      error,
      clearError,
    ],
  );
}
