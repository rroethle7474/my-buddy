import { useParams } from "react-router-dom";
import { Button } from "../components/Button";
import { Placeholder } from "../components/Placeholder";

/**
 * Route mount point for a project's rendered plan — the 1f docs view and the
 * four interactive sections (cart / tools / tutorial / research) + journal.
 * mechanic-ui (agent D, tasks D1/D3) replaces this with the real views. The
 * route shape is §16.2: /{module-slug}/{project-slug}/{view}.
 */
export function ProjectPlaceholder() {
  const { projectSlug } = useParams();
  const pretty = projectSlug?.replace(/-/g, " ") ?? "your project";
  return (
    <Placeholder
      title="Your plan is on its way"
      body={`The shopping cart, tool list, step-by-step tutorial, and research for “${pretty}” will show up here once the mechanic views are wired in.`}
    >
      <Button to="/" variant="secondary">
        ← Back to home
      </Button>
    </Placeholder>
  );
}
