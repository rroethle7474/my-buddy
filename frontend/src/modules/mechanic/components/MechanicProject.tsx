// MechanicProject — the mechanic module's read view (mock 1f, reframed per
// §16.3 to the four interactive sections rather than the mock's placeholder
// document grid). Composes: an optional "plan is ready" banner, the project
// header, a top-level safety caution for load-bearing builds (§16.4), the
// sticky section nav, and the four sections + journal notes.
//
// Data comes in via `useMechanicProject` (mocked now; live TanStack Query on D3).
// This component is what C's shell mounts at /{module}/{slug}/docs — it renders
// its own content only; the shell provides the surrounding chrome/breadcrumb.

import type { MechanicProjectApi } from "../hooks/useMechanicProject";
import type { SectionKey } from "../types";
import { money } from "../format";
import { color, difficultyAccent, statusBadge, timeBudgetLabel } from "../tokens";
import { Badge, Chip } from "./ui";
import { SectionNav } from "./SectionNav";
import { ShoppingCartSection } from "./ShoppingCartSection";
import { ToolListSection } from "./ToolListSection";
import { TutorialSection } from "./TutorialSection";
import { ResearchSection } from "./ResearchSection";
import { SafetyDisclaimer } from "./SafetyDisclaimer";
import { PlanReadyBanner } from "./PlanReadyBanner";

/** Heuristic (§16.4): does this build bear weight / involve structural,
 *  electrical, or power-tool hazard? If so we surface an emphasized caution. */
function looksHazardous(text: string): boolean {
  return /\b(load|weight|weigh|bear|structur|anchor|electr|wiring|voltage|ladder|power tool|blade|300\s?lb|pull-?up)\b/i.test(
    text,
  );
}

export function MechanicProject({
  api,
  showReadyBanner = false,
  onDownloadAll,
}: {
  api: MechanicProjectApi;
  showReadyBanner?: boolean;
  onDownloadAll?: () => void;
}) {
  const { project } = api;
  const diff = difficultyAccent[project.difficulty];
  const status = statusBadge[project.status];

  const hazardText =
    project.summary + " " + project.steps.map((s) => s.safety_note).join(" ");
  const hazardous = looksHazardous(hazardText);

  const stepsDone = project.steps.filter((s) => s.completed).length;
  const cartLeft = project.materials.filter((m) => !m.checked).length;
  const toGet = project.tools.filter((t) => t.acquire).length;

  const navItems: { key: SectionKey; label: string; count?: string }[] = [
    { key: "shopping", label: "Shopping", count: cartLeft ? String(cartLeft) : undefined },
    { key: "tools", label: "Tools", count: toGet ? String(toGet) : undefined },
    {
      key: "tutorial",
      label: "Tutorial",
      count: `${stepsDone}/${project.steps.length}`,
    },
    { key: "research", label: "Research" },
  ];

  const download = onDownloadAll ?? (() => window.print());

  return (
    <div className="mech">
      <div className="mech-doc">
        {showReadyBanner && <PlanReadyBanner onDownloadAll={download} />}

        <header className="mech-header">
          <span className="mech-eyebrow">My Mechanic</span>
          <h1 className="mech-h1" style={{ marginTop: 8 }}>
            {project.name}
          </h1>

          <div className="mech-facts">
            {diff && (
              <Badge fg={diff.fg} bg={diff.bg}>
                {diff.label}
              </Badge>
            )}
            <Chip>⏱ {timeBudgetLabel[project.time_budget] ?? project.time_budget}</Chip>
            <Chip>💵 about {money(project.estimated_cost_usd)}</Chip>
            {status && (
              <Badge fg={status.fg} bg={status.bg}>
                {status.label}
              </Badge>
            )}
          </div>

          <p className="mech-lead">{project.summary}</p>

          {project.workspace_required && (
            <p className="mech-lead" style={{ fontSize: 14, marginTop: 12 }}>
              <strong style={{ color: color.ink }}>You'll need: </strong>
              {project.workspace_required}
            </p>
          )}

          {project.skill_focus.length > 0 && (
            <div className="mech-focus">
              {project.skill_focus.map((s) => (
                <Chip key={s} outline>
                  {s}
                </Chip>
              ))}
            </div>
          )}
        </header>

        {hazardous && (
          <div className="mech-safety-note" role="note" style={{ marginTop: 18 }}>
            <span className="mech-safety-note__icon" aria-hidden="true">
              ⚠️
            </span>
            <div className="mech-safety-note__body">
              <strong>This build bears weight.</strong> Read every step's safety
              note, and run the test routine at the end before you trust it with
              your full body weight.
            </div>
          </div>
        )}

        <SectionNav items={navItems} />

        <ShoppingCartSection
          materials={project.materials}
          onToggle={api.toggleMaterial}
        />
        <ToolListSection
          tools={project.tools}
          onToggle={api.toggleTool}
          onOwn={(id) => api.setToolOwned(id, true)}
        />
        <TutorialSection
          steps={project.steps}
          onToggle={api.toggleStep}
          onNote={api.setStepNote}
        />
        <ResearchSection topics={project.research_topics} />

        <SafetyDisclaimer />
      </div>
    </div>
  );
}
