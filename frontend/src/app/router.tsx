import { createBrowserRouter } from "react-router-dom";
import { AppShell } from "./shell/AppShell";
import { HomePage } from "./pages/HomePage";
import { ModulePage } from "./pages/ModulePage";
import { NewProjectPlaceholder } from "./pages/NewProjectPlaceholder";
import { ProjectPlaceholder } from "./pages/ProjectPlaceholder";
import { NotFound } from "./pages/NotFound";
import { availableModules } from "./modules/registry";

/**
 * Routing per ARCHITECTURE.md §16.2: /{module-slug}/{project-slug}/{view}.
 *
 * The shell (agent C) owns the homepage (1a), the module page (1c), and the
 * route skeleton. The generate flow (1d/1e) and the rendered plan (1f + the
 * four sections) are built by mechanic-ui (agent D) — C mounts placeholders at
 * `…/new` and `…/:projectSlug/:view` now; D swaps them in when it integrates
 * against the shell. Routes are generated from the module registry, so a new
 * module is a registry row, not a router edit (§15).
 */
export const router = createBrowserRouter(
  [
    {
      element: <AppShell />,
      children: [
        { index: true, element: <HomePage /> },
        ...availableModules.flatMap((m) => [
          { path: m.routeSlug, element: <ModulePage moduleSlug={m.slug} /> },
          { path: `${m.routeSlug}/new`, element: <NewProjectPlaceholder moduleSlug={m.slug} /> },
          { path: `${m.routeSlug}/:projectSlug/:view?`, element: <ProjectPlaceholder /> },
        ]),
        { path: "*", element: <NotFound /> },
      ],
    },
  ],
  // Opt into the v7 routing behavior now so the upgrade is a no-op later.
  // (v7_startTransition is a RouterProvider prop — see App.tsx.)
  { future: { v7_relativeSplatPath: true } },
);
