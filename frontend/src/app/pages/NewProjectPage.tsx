import { NewProjectFlow } from "../../modules/mechanic";

/**
 * Route mount for the generate-via-chat flow (setup 1d → chat 1e). The screens
 * live in the mechanic module (agent D, task D2); this is the shell's thin
 * adapter at /{module}/new (replaces the earlier placeholder).
 */
export function NewProjectPage({ moduleSlug }: { moduleSlug: string }) {
  return <NewProjectFlow moduleSlug={moduleSlug} />;
}
