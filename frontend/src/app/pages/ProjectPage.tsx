import { useParams } from "react-router-dom";
import { ProjectDocsScreen } from "../../modules/mechanic";

/**
 * Route mount for a project's rendered plan — the 1f docs view and the four
 * interactive sections (cart / tools / tutorial / research) + journal. The route
 * shape is §16.2: /{module-slug}/{project-slug}/{view}. Thin adapter over the
 * mechanic module screen (agent D, tasks D1/D2/D3) — replaces the placeholder.
 */
export function ProjectPage({ moduleSlug }: { moduleSlug: string }) {
  const { projectSlug } = useParams();
  return <ProjectDocsScreen moduleSlug={moduleSlug} projectSlug={projectSlug} />;
}
