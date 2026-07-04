// Setup — step 1 of the guided flow (mock 1d). A short free-text description (or
// an idea chip) plus skill level + budget band → POST /generate/sessions. On
// success we hand the opened session to the chat step (1e).

import { useState } from "react";
import type {
  BudgetBand,
  GenerateSessionCreate,
  GenerateSessionStart,
  SkillLevel,
} from "../api/generate";
import { useStartSession } from "../api/generate";

const IDEAS: { emoji: string; label: string; seed: string }[] = [
  { emoji: "🔧", label: "Doorway pull-up bar", seed: "A pull-up bar I can hang in a doorway — no drilling, and it needs to hold my weight safely." },
  { emoji: "🪑", label: "Fix a wobbly chair", seed: "One of my wooden dining chairs wobbles and creaks. I'd like to fix it so it's solid again." },
  { emoji: "🧱", label: "Floating shelf", seed: "A floating shelf for the living room wall — no visible brackets, holds books and a few plants." },
  { emoji: "🖼️", label: "Hang a heavy mirror", seed: "Hang a large, heavy mirror on the wall so it's level and won't fall." },
];

const SKILLS: { value: SkillLevel; label: string }[] = [
  { value: "beginner", label: "Beginner" },
  { value: "handy", label: "Handy" },
  { value: "pro", label: "Pro" },
];

const BUDGETS: { value: BudgetBand; label: string }[] = [
  { value: "under_30", label: "Under $30" },
  { value: "30_to_75", label: "$30–75" },
  { value: "over_75", label: "$75+" },
];

export function SetupStep({
  onCancel,
  onStarted,
}: {
  onCancel: () => void;
  onStarted: (session: GenerateSessionStart, setup: GenerateSessionCreate) => void;
}) {
  const [description, setDescription] = useState("");
  const [skill, setSkill] = useState<SkillLevel>("beginner");
  const [budget, setBudget] = useState<BudgetBand>("under_30");
  const start = useStartSession();

  const canStart = description.trim().length > 0 && !start.isPending;

  function submit() {
    if (!canStart) return;
    const setup: GenerateSessionCreate = {
      description: description.trim(),
      skill_level: skill,
      budget_band: budget,
    };
    start.mutate(setup, { onSuccess: (session) => onStarted(session, setup) });
  }

  return (
    <div className="mech-setup">
      <h1 className="mech-h1">What do you want to build?</h1>
      <p className="mech-lead" style={{ margin: "8px 0 22px" }}>
        A sentence or two is plenty — My Buddy will ask the rest in the chat.
      </p>

      <div className="mech-field">
        <textarea
          className="mech-field__input"
          placeholder="I want to build…"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          onKeyDown={(e) => {
            if ((e.metaKey || e.ctrlKey) && e.key === "Enter") submit();
          }}
          rows={4}
          autoFocus
        />
        <div className="mech-field__hint">
          <span>Type as much or as little as you like</span>
          <span>⌘↵ to continue</span>
        </div>
      </div>

      <div className="mech-ideas">
        <div className="mech-ideas__label">Or start from an idea</div>
        <div className="mech-ideas__chips">
          {IDEAS.map((idea) => (
            <button
              key={idea.label}
              type="button"
              className="mech-idea-chip"
              onClick={() => setDescription(idea.seed)}
            >
              {idea.emoji} {idea.label}
            </button>
          ))}
        </div>
      </div>

      <div className="mech-constraints">
        <Segmented
          label="Skill level"
          options={SKILLS}
          value={skill}
          onChange={setSkill}
        />
        <Segmented
          label="Budget"
          options={BUDGETS}
          value={budget}
          onChange={setBudget}
        />
      </div>

      {start.isError && (
        <p className="mech-form-error" role="alert">
          {start.error instanceof Error
            ? start.error.message
            : "Couldn't start the chat. Try again."}
        </p>
      )}

      <div className="mech-setup__actions">
        <button type="button" className="mech-btn mech-btn--ghost" onClick={onCancel}>
          Cancel
        </button>
        <button
          type="button"
          className="mech-btn mech-btn--primary"
          onClick={submit}
          disabled={!canStart}
        >
          {start.isPending ? "Starting…" : "Start chatting →"}
        </button>
      </div>
    </div>
  );
}

function Segmented<T extends string>({
  label,
  options,
  value,
  onChange,
}: {
  label: string;
  options: { value: T; label: string }[];
  value: T;
  onChange: (v: T) => void;
}) {
  return (
    <div className="mech-seg">
      <div className="mech-seg__label">{label}</div>
      <div className="mech-seg__track" role="group" aria-label={label}>
        {options.map((o) => (
          <button
            key={o.value}
            type="button"
            className="mech-seg__opt"
            aria-pressed={value === o.value}
            onClick={() => onChange(o.value)}
          >
            {o.label}
          </button>
        ))}
      </div>
    </div>
  );
}
