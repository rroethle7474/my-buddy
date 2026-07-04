// My Buddy design tokens (ARCHITECTURE.md §16.1).
//
// Lifted from the "Buddy" mascot palette — a warm-neutral canvas with the
// doll's colors as accents. Do NOT invent new colors or type choices; every
// UI value here derives from §16.1. The CSS custom properties in `styles.css`
// mirror these; this module exists for the few places JS needs a token value
// (e.g. difficulty/status badge colors computed at render time).

export const color = {
  // Canvas / surfaces
  white: "#ffffff",
  surface1: "#f7f7f3",
  surface2: "#f5f5f1",
  surface3: "#f0f0eb",
  surface4: "#eaeae4",
  // Borders / dividers
  border: "#e6e6e0",
  border2: "#e4e4de",
  border3: "#e0e0d9",
  // Ink
  ink: "#1b1b19",
  inkMax: "#141414",
  muted: "#54544e",
  muted2: "#7a7a72",
  muted3: "#83837b",
  muted4: "#8a8a82",
  faint: "#b4b4ac",
  faint2: "#c4c4bc",
  // Red — primary action
  red: "#de3b2c",
  redTint: "#fbecea",
  redHover: "#e5675c",
  // Blue — module accent, links, secondary
  blue: "#2e7cc2",
  blueTint: "#eaf2fb",
  // Green — success / "ready"
  green: "#2e8b57",
  greenInk: "#256f49",
  greenTint: "#e7f3ec",
  greenTint2: "#cde7d8",
  // Gold — highlights / badges
  gold: "#edc24c",
  goldInk: "#b9891a",
  goldTint: "#fbf3dc",
} as const;

// Difficulty label → accent (user-facing labels from setup, §6/§16 mock 1d).
export const difficultyAccent: Record<
  string,
  { fg: string; bg: string; label: string }
> = {
  beginner: { fg: color.green, bg: color.greenTint, label: "Beginner" },
  handy: { fg: color.blue, bg: color.blueTint, label: "Handy" },
  pro: { fg: color.goldInk, bg: color.goldTint, label: "Pro" },
};

// Project status → badge (§5 projects.status).
export const statusBadge: Record<
  string,
  { fg: string; bg: string; label: string }
> = {
  planning: { fg: color.goldInk, bg: color.goldTint, label: "Planning" },
  active: { fg: color.blue, bg: color.blueTint, label: "In progress" },
  complete: { fg: color.green, bg: color.greenTint, label: "Done" },
};

// Time budget → human label (§6).
export const timeBudgetLabel: Record<string, string> = {
  afternoon: "An afternoon",
  weekend: "A weekend",
  "multi-weekend": "Multiple weekends",
};
