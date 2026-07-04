// Fixture: a fully hydrated project (§6 spec + runtime state), shaped exactly
// like `GET /projects/{id}` → ProjectRead. This is D1's scaffold-ahead stand-in
// for the live endpoint (TASKS D1); D3 swaps the mocked hook for the real query,
// and this file can stay as a test/Storybook seed.
//
// Content mirrors the approved mock 1e/1f narrative: a no-drill, leverage-mount
// doorway pull-up bar sized to a 32" opening, rated 300 lb. It is deliberately
// load-bearing so the safety treatment (§16.4) has something real to render.

import type { ProjectRead } from "../types";

export const doorwayPullUpBar: ProjectRead = {
  id: 1,
  user_id: 1,
  module_id: 1,
  name: "Doorway Pull-Up Bar",
  slug: "doorway-pull-up-bar",
  skill_focus: ["measuring", "leverage & load", "no-drill mounting"],
  difficulty: "handy",
  time_budget: "afternoon",
  estimated_cost_usd: 58,
  summary:
    "A no-drill pull-up bar that braces itself in a hallway doorway using leverage — the harder you pull down, the tighter it grips the wall above the frame. You'll learn to measure an opening precisely, reason about how leverage turns your weight into holding force, and pressure-test a build before you trust it. Finished, it holds up to 300 lb and pops out in seconds when you want the doorway back.",
  workspace_required:
    "A trimmed doorway 24–36\" wide with solid wall above the frame, plus a few feet of floor to lay parts out. No permanent wall damage.",
  status: "complete",
  spec_version: "1.0",
  created_at: "2026-07-03T21:40:00Z",

  materials: [
    {
      id: 101,
      project_id: 1,
      name: "Leverage-mount pull-up bar, 1.25\" steel tube",
      quantity: 1,
      unit: "bar",
      est_cost_usd: 34,
      where_to_find: "Sporting-goods store or online; look for \"doorway pull-up bar, no screws\"",
      notes: "Get one rated to at least 300 lb and adjustable to fit a 24–36\" opening.",
      checked: false,
    },
    {
      id: 102,
      project_id: 1,
      name: "High-density foam pipe insulation, 1.25\" ID",
      quantity: 1,
      unit: "length",
      est_cost_usd: 4,
      where_to_find: "Hardware store, plumbing aisle",
      notes: "Slips over the bar as a grip so your hands don't slide on bare steel.",
      checked: false,
    },
    {
      id: 103,
      project_id: 1,
      name: "Adhesive felt pads, 2\" (for the wall pads)",
      quantity: 4,
      unit: "pad",
      est_cost_usd: 5,
      where_to_find: "Hardware store, furniture-protection aisle",
      notes: "Protect the paint where the bar's brackets press against the wall.",
      checked: false,
    },
    {
      id: 104,
      project_id: 1,
      name: "Painter's tape",
      quantity: 1,
      unit: "roll",
      est_cost_usd: 6,
      where_to_find: "Hardware or paint aisle",
      notes: "Mark your measurements without marking the trim.",
      checked: false,
    },
    {
      id: 105,
      project_id: 1,
      name: "Non-marring shims (thin plywood or plastic)",
      quantity: 1,
      unit: "pack",
      est_cost_usd: 9,
      where_to_find: "Hardware store, near door hardware",
      notes: "Only if your trim is uneven — takes up small gaps so the bar sits square.",
      checked: false,
    },
  ],

  tools: [
    {
      id: 201,
      project_id: 1,
      name: "Tape measure",
      essential: true,
      est_cost_usd: 0,
      notes: "For the doorway width and the mounting height.",
      alternatives: "A folding ruler works; avoid a fabric sewing tape — it stretches.",
      owned: true,
      acquire: false,
      checked: false,
    },
    {
      id: 202,
      project_id: 1,
      name: "Pencil",
      essential: true,
      est_cost_usd: 0,
      notes: "Mark on the painter's tape, not the trim.",
      alternatives: "Any washable marker.",
      owned: true,
      acquire: false,
      checked: false,
    },
    {
      id: 203,
      project_id: 1,
      name: "Bubble level (or a phone level app)",
      essential: true,
      est_cost_usd: 0,
      notes: "The bar must sit dead level or the load pulls unevenly.",
      alternatives: "Most phones have a built-in level in the compass/measure app.",
      owned: true,
      acquire: false,
      checked: false,
    },
    {
      id: 204,
      project_id: 1,
      name: "Adjustable wrench",
      essential: true,
      est_cost_usd: 14,
      notes: "To snug the bar's width-adjustment collar. Don't over-tighten.",
      alternatives: "The bar sometimes ships with a hex key that fits — check the box first.",
      owned: false,
      acquire: true,
      checked: false,
    },
    {
      id: 205,
      project_id: 1,
      name: "Utility knife",
      essential: false,
      est_cost_usd: 8,
      notes: "To cut the foam grip to length.",
      alternatives: "Sturdy scissors will cut foam pipe insulation fine.",
      owned: false,
      acquire: true,
      checked: false,
    },
  ],

  steps: [
    {
      id: 301,
      project_id: 1,
      order: 1,
      title: "Measure the doorway opening",
      instruction:
        "Stretch the tape measure across the inside of the door frame at the height you'll mount the bar (usually near the top). Measure the clear width between the two trimmed sides — the actual gap, not the outer edges of the moulding. Write it down. Measure again a few inches higher and lower; if the numbers differ, the frame isn't square, so use the smallest one.",
      safety_note:
        "Confirm the opening is within the bar's rated range (typically 24–36\"). A bar that's near the end of its adjustment grips with less margin — stay in the middle of the range if you can.",
      est_time_minutes: 10,
      tools_used: ["Tape measure", "Pencil"],
      materials_used: ["Painter's tape"],
      completed: false,
      note: null,
    },
    {
      id: 302,
      project_id: 1,
      order: 2,
      title: "Check the wall above the frame",
      instruction:
        "A leverage bar pushes against the wall above the door, so that wall does the real work. Press firmly with your palm across the area a hand's-width above the frame. It should feel solid, not hollow or crumbly. Knock lightly — a dull, dense sound is good; a drum-like echo over a large area means weak drywall with no backing.",
      safety_note:
        "If the wall flexes, sounds hollow, or is cracked/damaged, STOP — this mount is not safe there. A leverage bar can punch through weak drywall under load. Pick a different, solid doorway.",
      est_time_minutes: 10,
      tools_used: [],
      materials_used: [],
      completed: false,
      note: null,
    },
    {
      id: 303,
      project_id: 1,
      order: 3,
      title: "Fit the foam grip",
      instruction:
        "Slide the foam pipe insulation over the middle section of the bar where your hands will go. Hold it against the bar, mark where it should end, and cut it to length with the utility knife or scissors. Leave the width-adjustment collar exposed so you can still turn it.",
      safety_note:
        "Cut away from your body on a stable surface. Foam is soft but a utility knife will still bite — keep fingers behind the blade.",
      est_time_minutes: 10,
      tools_used: ["Utility knife"],
      materials_used: ["High-density foam pipe insulation, 1.25\" ID"],
      completed: false,
      note: null,
    },
    {
      id: 304,
      project_id: 1,
      order: 4,
      title: "Set the bar's width",
      instruction:
        "Loosen the adjustment collar and extend the bar until it's a touch wider than your smallest doorway measurement — a snug interference fit. Stick a felt pad on each wall bracket where it will contact the paint. If your trim is uneven, add a thin shim behind a bracket so the bar sits flat against the wall, not the moulding.",
      safety_note:
        "The brackets must bear on the flat wall above the frame, not on the rounded edge of the trim. Bearing on trim alone can crack it and gives a much weaker hold.",
      est_time_minutes: 10,
      tools_used: ["Adjustable wrench"],
      materials_used: [
        "Adhesive felt pads, 2\" (for the wall pads)",
        "Non-marring shims (thin plywood or plastic)",
      ],
      completed: false,
      note: null,
    },
    {
      id: 305,
      project_id: 1,
      order: 5,
      title: "Mount it and level it",
      instruction:
        "Lift the bar into the opening and let the upper brackets rest against the wall above the frame while the lower hooks catch the near side of the trim. Rest your level on the bar and adjust until the bubble is centered. Snug the collar with the wrench just until it stops turning easily — firm, not forced.",
      safety_note:
        "A bar that isn't level loads one side harder than the other and can slip. Re-check the bubble after tightening — tightening can nudge it out of level.",
      est_time_minutes: 10,
      tools_used: ["Bubble level (or a phone level app)", "Adjustable wrench"],
      materials_used: [],
      completed: false,
      note: null,
    },
    {
      id: 306,
      project_id: 1,
      order: 6,
      title: "Pressure-test before you trust it",
      instruction:
        "With the bar mounted, do the test routine in order: (1) hang your hands on it and press DOWN hard without lifting your feet; (2) pull down with about half your weight, feet still on the floor; (3) only then lift your feet for a moment, staying low so you can stand instantly if anything shifts. Watch the wall contact points the whole time — they should not move, dent, or creak.",
      safety_note:
        "Keep your feet under you and never test over stairs or a hard edge. If you see any movement at the wall, hear cracking, or the bar shifts — come down immediately and re-check steps 2, 4, and 5. Do not do a full pull-up until it passes every stage with zero movement.",
      est_time_minutes: 10,
      tools_used: [],
      materials_used: [],
      completed: false,
      note: null,
    },
    {
      id: 307,
      project_id: 1,
      order: 7,
      title: "Set your before-each-use habit",
      instruction:
        "A leverage bar can loosen over days of use and temperature swings. Before every session, give it the same quick check: press down hard from a standing position and glance at the wall contacts. Decide your rule now — e.g. \"press-test every time, full re-level once a week\" — and stick to it.",
      safety_note:
        "Re-run the full step-6 pressure test any time the bar has been removed and re-hung, or if anything about the fit feels different.",
      est_time_minutes: 5,
      tools_used: [],
      materials_used: [],
      completed: false,
      note: null,
    },
  ],

  research_topics: [
    {
      id: 401,
      project_id: 1,
      topic: "How a leverage (no-screw) doorway bar actually holds",
      why: "Understanding that your downward pull is what creates the grip tells you why the wall above the frame — not the trim — must be solid, and why a level fit matters.",
      resources: [
        {
          title: "How leverage-mount pull-up bars work (short explainer)",
          url: "https://www.youtube.com/results?search_query=how+leverage+doorway+pull+up+bar+works",
          type: "video",
        },
      ],
    },
    {
      id: 402,
      project_id: 1,
      topic: "Telling solid wall from weak drywall by feel and sound",
      why: "The whole mount depends on the wall above the frame being strong. Knowing the knock-and-press test keeps you from trusting a wall that will fail under load.",
      resources: [
        {
          title: "Drywall vs. solid backing — the knock test",
          url: "https://www.youtube.com/results?search_query=how+to+tell+if+drywall+is+solid+knock+test",
          type: "video",
        },
      ],
    },
    {
      id: 403,
      project_id: 1,
      topic: "Reading a tape measure to the sixteenth",
      why: "A snug interference fit lives or dies on an accurate width measurement. A quick refresher on reading the small marks pays off on the very first step.",
      resources: [
        {
          title: "How to read a tape measure (beginner guide)",
          url: "https://www.youtube.com/results?search_query=how+to+read+a+tape+measure+for+beginners",
          type: "video",
        },
      ],
    },
  ],

  photos: [],
  retrospective: null,
};
