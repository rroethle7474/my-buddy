// Docs (1f) — the rendered plan. Resolves the project from the URL slug, renders
// the four sections (MechanicProject), and — right after generation ONLY — fires
// the research refresh (§7.2) with a loading state on the research section, so
// the user never has to know research is a second pass (02:40Z DECISION).
// Revisits with empty resources get an explicit "Find resources" action instead:
// every refresh runs real (billed) web searches, so a page load must never
// re-spend silently, and a failed refresh must surface a retry, not spin forever.

import { useCallback, useEffect, useRef } from "react";
import { useLocation } from "react-router-dom";
import { useQueryClient } from "@tanstack/react-query";
import type { ProjectRead } from "../types";
import { useMechanicProject } from "../hooks/useMechanicProject";
import { useProjectBySlug, useResearchRefresh } from "../api/projects";
import { MechanicProject } from "../components/MechanicProject";

export function ProjectDocsScreen({
  moduleSlug,
  projectSlug,
}: {
  moduleSlug: string;
  projectSlug: string | undefined;
}) {
  const location = useLocation();
  const navState = (location.state ?? null) as
    | { project?: ProjectRead; justCreated?: boolean }
    | null;

  const query = useProjectBySlug(moduleSlug, projectSlug, navState?.project);

  if (query.isLoading && !query.data) {
    return (
      <div className="mech">
        <div className="mech-doc mech-load">
          <div className="mech-spinner mech-spinner--lg" aria-hidden="true" />
          <p className="mech-lead">Loading your plan…</p>
        </div>
      </div>
    );
  }

  if (query.isError || !query.data) {
    return (
      <div className="mech">
        <div className="mech-doc mech-load">
          <div className="mech-load__emoji" aria-hidden="true">😕</div>
          <p className="mech-h2">We couldn't open that plan</p>
          <p className="mech-lead">
            {query.error instanceof Error
              ? query.error.message
              : "It may have been removed, or you're offline."}
          </p>
        </div>
      </div>
    );
  }

  return (
    <ProjectDocs
      project={query.data}
      justCreated={Boolean(navState?.justCreated)}
      moduleSlug={moduleSlug}
      projectSlug={projectSlug}
    />
  );
}

/** Inner view — receives a guaranteed project so the hooks below are unconditional. */
function ProjectDocs({
  project,
  justCreated,
  moduleSlug,
  projectSlug,
}: {
  project: ProjectRead;
  justCreated: boolean;
  moduleSlug: string;
  projectSlug: string | undefined;
}) {
  const qc = useQueryClient();
  const refresh = useResearchRefresh();
  const fired = useRef(false);
  const api = useMechanicProject(project, { moduleSlug, projectSlug });

  const { mutate: refreshMutate } = refresh;
  const runRefresh = useCallback(() => {
    refreshMutate(project.id, {
      onSuccess: (topics) => {
        // Merge into the cached project so the read view (and later revisits)
        // show the filled resources without a re-fetch.
        qc.setQueryData(
          ["project", moduleSlug, projectSlug],
          (old: ProjectRead | undefined) =>
            old ? { ...old, research_topics: topics } : old,
        );
      },
    });
  }, [refreshMutate, project.id, moduleSlug, projectSlug, qc]);

  // Auto-fire only on the just-generated visit; anything else goes through the
  // research section's explicit "Find resources" / "Try again" action.
  // `justCreated` rides in history state, which SURVIVES page reloads — so it
  // must be consumed on first use (and skipped when resources already landed),
  // or every reload of this history entry re-fires a billed search pass.
  const unfilled =
    project.research_topics.length > 0 &&
    project.research_topics.every((t) => t.resources.length === 0);
  useEffect(() => {
    if (!justCreated || fired.current) return;
    fired.current = true;
    if (unfilled) runRefresh();
    const h = window.history;
    h.replaceState(
      { ...h.state, usr: { ...(h.state?.usr ?? {}), justCreated: false } },
      "",
    );
  }, [justCreated, unfilled, runRefresh]);

  return (
    <MechanicProject
      api={api}
      showReadyBanner={justCreated}
      researchLoading={refresh.isPending}
      researchError={refresh.isError}
      onResearchRefresh={runRefresh}
    />
  );
}
