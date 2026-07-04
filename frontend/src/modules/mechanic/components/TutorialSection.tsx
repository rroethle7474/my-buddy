// Tutorial (§1.3) — ordered, novice-level steps with a per-step safety note
// and time estimate, plus the learning-journal note ("where I got stuck", §5).
// completed toggle → PATCH …/steps/{sid} {completed}; note → {note}.

import { useEffect, useState } from "react";
import type { StepRead } from "../types";
import { minutes, totalTime } from "../format";
import { color } from "../tokens";
import { Checkbox, Chip, SectionHead } from "./ui";

/** Journal note field — locally controlled, persisted on blur so typing doesn't
 *  churn the whole project tree (and, later, doesn't fire a PATCH per keystroke). */
function StepNote({
  value,
  onSave,
}: {
  value: string | null;
  onSave: (note: string) => void;
}) {
  const [draft, setDraft] = useState(value ?? "");
  useEffect(() => setDraft(value ?? ""), [value]);

  return (
    <div className="mech-note">
      <label className="mech-note__label">
        <span aria-hidden="true">✎</span> Your notes on this step
      </label>
      <textarea
        className="mech-note__field"
        placeholder="Where did you get stuck? What would you tell yourself next time?"
        value={draft}
        onChange={(e) => setDraft(e.target.value)}
        onBlur={() => {
          if (draft !== (value ?? "")) onSave(draft);
        }}
      />
    </div>
  );
}

function Step({
  step,
  onToggle,
  onNote,
}: {
  step: StepRead;
  onToggle: (stepId: number, completed: boolean) => void;
  onNote: (stepId: number, note: string) => void;
}) {
  return (
    <article className={step.completed ? "mech-step mech-step--done" : "mech-step"}>
      <div className="mech-step__head">
        <span className="mech-step__num" aria-hidden="true">
          {step.completed ? "✓" : step.order}
        </span>
        <div className="mech-step__heading">
          <div className="mech-step__title">{step.title}</div>
          <div className="mech-step__time">⏱ {minutes(step.est_time_minutes)}</div>
        </div>
        <Checkbox
          checked={step.completed}
          green
          onChange={(c) => onToggle(step.id, c)}
          label={`Mark step ${step.order}, ${step.title}, complete`}
        />
      </div>
      <div className="mech-step__body">
        <p className="mech-step__instruction">{step.instruction}</p>

        {(step.tools_used.length > 0 || step.materials_used.length > 0) && (
          <div className="mech-step__used">
            {step.tools_used.map((t) => (
              <Chip key={`t-${t}`} outline>
                🧰 {t}
              </Chip>
            ))}
            {step.materials_used.map((m) => (
              <Chip key={`m-${m}`} outline>
                🛒 {m}
              </Chip>
            ))}
          </div>
        )}

        {step.safety_note && (
          <div className="mech-step__safety">
            <span aria-hidden="true">⚠️</span>
            <div>
              <div className="mech-step__safety-label">Safety</div>
              <div className="mech-step__safety-text">{step.safety_note}</div>
            </div>
          </div>
        )}

        <StepNote value={step.note ?? null} onSave={(note) => onNote(step.id, note)} />
      </div>
    </article>
  );
}

export function TutorialSection({
  steps,
  onToggle,
  onNote,
}: {
  steps: StepRead[];
  onToggle: (stepId: number, completed: boolean) => void;
  onNote: (stepId: number, note: string) => void;
}) {
  const ordered = [...steps].sort((a, b) => a.order - b.order);
  const done = ordered.filter((s) => s.completed).length;

  return (
    <section className="mech-section" id="tutorial" aria-labelledby="tutorial-h">
      <SectionHead
        id="tutorial-h"
        icon="📋"
        iconBg={color.redTint}
        iconFg={color.red}
        title="Tutorial"
        sub={`${ordered.length} steps · about ${totalTime(ordered)} · ${done}/${ordered.length} done`}
      />
      <div className="mech-steps">
        {ordered.map((s) => (
          <Step key={s.id} step={s} onToggle={onToggle} onNote={onNote} />
        ))}
      </div>
    </section>
  );
}
