// Retrospective (§5) — the end-of-project reflection, the last piece of the
// learning journal. One per project: what went well, what you'd do differently,
// and the skills you practiced. Upserts via PATCH …/retrospective; the form is
// always editable and pre-fills from any saved reflection.

import { useEffect, useState } from "react";
import type { RetrospectiveRead, RetrospectiveUpsert } from "../types";
import { color } from "../tokens";
import { Chip, SectionHead } from "./ui";

function splitSkills(text: string): string[] {
  return text
    .split(",")
    .map((s) => s.trim())
    .filter(Boolean);
}

export function RetrospectiveSection({
  retrospective,
  onSave,
}: {
  retrospective: RetrospectiveRead | null;
  /** Upsert the reflection; resolves on save, rejects on failure. */
  onSave: (draft: RetrospectiveUpsert) => Promise<void>;
}) {
  const savedSkills = retrospective?.skills_practiced ?? [];
  const [wentWell, setWentWell] = useState(retrospective?.what_went_well ?? "");
  const [differently, setDifferently] = useState(
    retrospective?.what_i_would_do_differently ?? "",
  );
  const [skillsText, setSkillsText] = useState(savedSkills.join(", "));
  const [saving, setSaving] = useState(false);

  // Re-sync when a saved reflection arrives or changes (initial load settling, or
  // our own post-save cache update).
  useEffect(() => {
    setWentWell(retrospective?.what_went_well ?? "");
    setDifferently(retrospective?.what_i_would_do_differently ?? "");
    setSkillsText((retrospective?.skills_practiced ?? []).join(", "));
  }, [retrospective]);

  const parsedSkills = splitSkills(skillsText);
  const dirty =
    wentWell !== (retrospective?.what_went_well ?? "") ||
    differently !== (retrospective?.what_i_would_do_differently ?? "") ||
    skillsText !== savedSkills.join(", ");
  const hasContent =
    wentWell.trim() !== "" || differently.trim() !== "" || parsedSkills.length > 0;

  async function save() {
    setSaving(true);
    try {
      await onSave({
        what_went_well: wentWell.trim(),
        what_i_would_do_differently: differently.trim(),
        skills_practiced: parsedSkills,
      });
    } catch {
      // The hook surfaces the failure as a toast; keep the draft so nothing is lost.
    } finally {
      setSaving(false);
    }
  }

  const buttonLabel = saving
    ? "Saving…"
    : retrospective && !dirty
      ? "Saved ✓"
      : retrospective
        ? "Update reflection"
        : "Save reflection";

  return (
    <section
      className="mech-section"
      id="retrospective"
      aria-labelledby="retrospective-h"
    >
      <SectionHead
        id="retrospective-h"
        icon="✍️"
        iconBg={color.goldTint}
        iconFg={color.goldInk}
        title="Retrospective"
        sub="Finished the build? Capture what you learned while it's fresh."
      />
      <div className="mech-card mech-retro">
        <label className="mech-retro__field">
          <span className="mech-retro__label">What went well?</span>
          <textarea
            className="mech-note__field"
            placeholder="What are you proud of? What clicked?"
            value={wentWell}
            onChange={(e) => setWentWell(e.target.value)}
          />
        </label>

        <label className="mech-retro__field">
          <span className="mech-retro__label">What would you do differently?</span>
          <textarea
            className="mech-note__field"
            placeholder="What would you change or try next time?"
            value={differently}
            onChange={(e) => setDifferently(e.target.value)}
          />
        </label>

        <label className="mech-retro__field">
          <span className="mech-retro__label">Skills you practiced</span>
          <input
            className="mech-retro__input"
            type="text"
            placeholder="measuring, drilling, wall anchoring — separate with commas"
            value={skillsText}
            onChange={(e) => setSkillsText(e.target.value)}
          />
          {parsedSkills.length > 0 && (
            <div className="mech-retro__skills">
              {parsedSkills.map((s, i) => (
                <Chip key={`${s}-${i}`} outline>
                  {s}
                </Chip>
              ))}
            </div>
          )}
        </label>

        <div className="mech-retro__actions">
          <button
            type="button"
            className={
              retrospective && !dirty
                ? "mech-btn mech-btn--success"
                : "mech-btn mech-btn--primary"
            }
            onClick={save}
            disabled={saving || !dirty || !hasContent}
          >
            {buttonLabel}
          </button>
        </div>
      </div>
    </section>
  );
}
