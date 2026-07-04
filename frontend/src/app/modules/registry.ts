/**
 * The module registry (ARCHITECTURE.md §15: the shell + registry make adding a
 * module "a new `modules` row + a new `frontend/src/modules/<name>` folder, not
 * a fork"). The shell reads this to build the nav and the routes; the mechanic
 * screens themselves are owned by mechanic-ui (agent D).
 *
 * Two slugs, deliberately separate:
 *  - `slug`      — the DB/API slug ("mechanic") used for GET /modules/{slug}
 *                  and GET /projects?module= (§5/§11).
 *  - `routeSlug` — the URL segment ("my-mechanic") from the mock URLs (§16.2,
 *                  e.g. /my-mechanic/doorway-pull-up-bar/docs).
 */
export type ModuleStatus = "available" | "coming-soon";

export interface ModuleDef {
  slug: string;
  routeSlug: string;
  /** Display name, e.g. "My Mechanic". */
  name: string;
  /** Emoji glyph for the module (nav mark / project card headers). */
  glyph: string;
  /** Module-page hero copy (1c). */
  tagline: string;
  /** Accent color token (module chip + links). Mechanic = blue (§16.1). */
  accent: string;
  accentTint: string;
  /** Gradient partner for card headers. */
  accentTint2: string;
  status: ModuleStatus;
}

export const modules: ModuleDef[] = [
  {
    slug: "mechanic",
    routeSlug: "my-mechanic",
    name: "My Mechanic",
    glyph: "🔧",
    tagline:
      "Your workshop buddy for small builds and fixes around the house. Start something new, or pick up where you left off.",
    accent: "var(--blue)",
    accentTint: "var(--blue-tint)",
    accentTint2: "var(--blue-tint-2)",
    status: "available",
  },
  {
    slug: "garden",
    routeSlug: "my-garden",
    name: "My Garden",
    glyph: "🌱",
    tagline: "Grow-it-yourself projects for the yard and windowsill.",
    accent: "var(--green)",
    accentTint: "var(--green-tint)",
    accentTint2: "var(--green-tint-2)",
    status: "coming-soon",
  },
  {
    slug: "kitchen",
    routeSlug: "my-kitchen",
    name: "My Kitchen",
    glyph: "🍳",
    tagline: "Cook-along builds for confidence in the kitchen.",
    accent: "var(--gold-ink)",
    accentTint: "var(--gold-tint)",
    accentTint2: "var(--gold-tint)",
    status: "coming-soon",
  },
];

export const availableModules = modules.filter((m) => m.status === "available");

export const moduleBySlug = (slug: string): ModuleDef | undefined =>
  modules.find((m) => m.slug === slug);

export const moduleByRouteSlug = (routeSlug: string): ModuleDef | undefined =>
  modules.find((m) => m.routeSlug === routeSlug);

/** Path helper so links stay consistent with §16.2's URL shape. */
export const projectPath = (m: ModuleDef, projectSlug: string, view = "docs") =>
  `/${m.routeSlug}/${projectSlug}/${view}`;

export const newProjectPath = (m: ModuleDef) => `/${m.routeSlug}/new`;
