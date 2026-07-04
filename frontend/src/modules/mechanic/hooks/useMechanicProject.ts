// useMechanicProject — the data seam for the mechanic sections.
//
// SCAFFOLD-AHEAD (TASKS D1): this hook holds the hydrated project in local React
// state and applies mutations optimistically in-memory. The mutation function
// SHAPES match the live PATCH endpoints (§11) so D3 swaps the internals for
// TanStack Query `useQuery` + `useMutation` (optimistic update → PATCH → invalidate)
// without touching a single component:
//
//   PATCH /projects/{id}/materials/{mid}  { checked }          → toggleMaterial
//   PATCH /projects/{id}/tools/{tid}      { checked, owned }    → toggleTool / setToolOwned
//   PATCH /projects/{id}/steps/{sid}      { completed, note }   → toggleStep / setStepNote
//
// Until then it's fully interactive against the fixture, so the read view is
// demoable end-to-end offline.

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import type { ProjectRead } from "../types";

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
}

export function useMechanicProject(initial: ProjectRead): MechanicProjectApi {
  const [project, setProject] = useState<ProjectRead>(initial);

  // Re-sync when the caller hands us a new project object (live load settling, or
  // the research refresh merging in). A stable `initial` (e.g. the D1 fixture) never
  // triggers this, so local toggles persist in the preview. D3 replaces the local
  // mutations with server-backed ones.
  const seen = useRef(initial);
  useEffect(() => {
    if (initial !== seen.current) {
      seen.current = initial;
      setProject(initial);
    }
  }, [initial]);

  const toggleMaterial = useCallback((materialId: number, checked: boolean) => {
    setProject((p) => ({
      ...p,
      materials: p.materials.map((m) =>
        m.id === materialId ? { ...m, checked } : m,
      ),
    }));
  }, []);

  const toggleTool = useCallback((toolId: number, checked: boolean) => {
    setProject((p) => ({
      ...p,
      tools: p.tools.map((t) => (t.id === toolId ? { ...t, checked } : t)),
    }));
  }, []);

  const setToolOwned = useCallback((toolId: number, owned: boolean) => {
    setProject((p) => ({
      ...p,
      tools: p.tools.map((t) =>
        t.id === toolId ? { ...t, owned, acquire: !owned } : t,
      ),
    }));
  }, []);

  const toggleStep = useCallback((stepId: number, completed: boolean) => {
    setProject((p) => ({
      ...p,
      steps: p.steps.map((s) => (s.id === stepId ? { ...s, completed } : s)),
    }));
  }, []);

  const setStepNote = useCallback((stepId: number, note: string) => {
    setProject((p) => ({
      ...p,
      steps: p.steps.map((s) =>
        s.id === stepId ? { ...s, note: note.trim() ? note : null } : s,
      ),
    }));
  }, []);

  return useMemo(
    () => ({
      project,
      toggleMaterial,
      toggleTool,
      setToolOwned,
      toggleStep,
      setStepNote,
    }),
    [project, toggleMaterial, toggleTool, setToolOwned, toggleStep, setStepNote],
  );
}
