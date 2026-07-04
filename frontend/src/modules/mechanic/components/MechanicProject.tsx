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
import { PhotosSection } from "./PhotosSection";
import { RetrospectiveSection } from "./RetrospectiveSection";
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
  researchLoading = false,
  researchError = false,
  onResearchRefresh,
  onDownloadAll,
}: {
  api: MechanicProjectApi;
  showReadyBanner?: boolean;
  /** The research refresh (§7.2) is in flight — the research section shows a
   *  gathering state until resources land (02:40Z DECISION). */
  researchLoading?: boolean;
  /** The last refresh failed — the research section offers a retry. */
  researchError?: boolean;
  /** Fire (or re-fire) the research refresh; rendered as an explicit action. */
  onResearchRefresh?: () => void;
  onDownloadAll?: () => void;
}) {
  const { project, error, clearError } = api;
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
    {
      key: "photos",
      label: "Photos",
      count: project.photos.length ? String(project.photos.length) : undefined,
    },
    { key: "retrospective", label: "Retrospective" },
  ];

  // Default "Download all" (D5): client-side print → the user picks "Save as
  // PDF". The @media print stylesheet (styles.css) produces the clean copy.
  // The shell may inject its own handler; otherwise we briefly set the document
  // title so the default PDF filename is the project name, then restore it.
  const download =
    onDownloadAll ??
    (() => {
      const prevTitle = document.title;
      document.title = project.name;
      const restore = () => {
        document.title = prevTitle;
        window.removeEventListener("afterprint", restore);
      };
      window.addEventListener("afterprint", restore);
      window.print();
    });

  return (
    <div className="mech">
      <div className="mech-doc">
        {showReadyBanner && <PlanReadyBanner onDownloadAll={download} />}

        <header className="mech-header">
          <div className="mech-header__top">
            <div>
              <span className="mech-eyebrow">My Mechanic</span>
              <h1 className="mech-h1" style={{ marginTop: 8 }}>
                {project.name}
              </h1>
            </div>
            <div className="mech-header__actions">
              <button
                type="button"
                className="mech-btn mech-btn--ghost mech-btn--sm"
                onClick={download}
              >
                ↓ Download all
              </button>
            </div>
          </div>

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
        <ResearchSection
          topics={project.research_topics}
          loading={researchLoading}
          error={researchError}
          onRefresh={onResearchRefresh}
        />
        <PhotosSection
          photos={project.photos}
          onUpload={api.uploadPhoto}
          onDelete={api.deletePhoto}
        />
        <RetrospectiveSection
          retrospective={project.retrospective ?? null}
          onSave={api.saveRetrospective}
        />

        <SafetyDisclaimer />
      </div>

      {error && (
        <div className="mech-toast" role="alert">
          <span>{error}</span>
          <button
            type="button"
            className="mech-toast__close"
            onClick={clearError}
            aria-label="Dismiss"
          >
            ✕
          </button>
        </div>
      )}
    </div>
  );
}
