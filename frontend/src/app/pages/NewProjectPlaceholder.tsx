import { moduleBySlug } from "../modules/registry";
import { Button } from "../components/Button";
import { Placeholder } from "../components/Placeholder";

/**
 * Route mount point for the generate-via-chat flow (setup 1d → chat 1e).
 * mechanic-ui (agent D, task D2) replaces this with the real stepper once it
 * integrates against the shell. Until then this keeps the route navigable and
 * on-brand.
 */
export function NewProjectPlaceholder({ moduleSlug }: { moduleSlug: string }) {
  const module = moduleBySlug(moduleSlug);
  return (
    <Placeholder
      title="Let's plan your build"
      body={`The guided setup and chat for ${module?.name ?? "this module"} are on their way. Soon you'll describe what you want to make and My Buddy will design it with you.`}
    >
      <Button to={module ? `/${module.routeSlug}` : "/"} variant="secondary">
        ← Back to {module?.name ?? "module"}
      </Button>
    </Placeholder>
  );
}
