// The guided new-project flow (mocks 1d → 1e → 1f). Owns the stepper (Describe →
// Chat → Documents) and the hand-off: when the agent is ready, finalize the spec,
// commit it via POST /projects (import path + shop diff §8), then route to the
// rendered docs (1f). Research fills in a second pass on the docs screen (02:40Z
// DECISION). Mounted by the shell at /{module}/new.

import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { moduleBySlug, projectPath } from "../../../app/modules/registry";
import { finalizeSession } from "../api/generate";
import type { GenerateSessionCreate, GenerateSessionStart } from "../api/generate";
import { useCreateProject } from "../api/projects";
import { SetupStep } from "./SetupStep";
import { ChatStep } from "./ChatStep";

type Phase = "setup" | "chat";

export function NewProjectFlow({ moduleSlug }: { moduleSlug: string }) {
  const navigate = useNavigate();
  const module = moduleBySlug(moduleSlug);
  const createProject = useCreateProject();

  const [phase, setPhase] = useState<Phase>("setup");
  const [session, setSession] = useState<GenerateSessionStart | null>(null);
  const [generating, setGenerating] = useState(false);
  const [genError, setGenError] = useState<string | null>(null);

  function handleStarted(started: GenerateSessionStart, _setup: GenerateSessionCreate) {
    setSession(started);
    setPhase("chat");
  }

  function restart() {
    setSession(null);
    setGenError(null);
    setPhase("setup");
  }

  async function handleGenerate() {
    if (!session || !module) return;
    setGenerating(true);
    setGenError(null);
    try {
      const spec = await finalizeSession(session.session_id);
      const project = await createProject.mutateAsync(spec);
      // Hand the fresh project to the docs screen so it renders instantly and
      // fires the research refresh (justCreated).
      navigate(projectPath(module, project.slug, "docs"), {
        state: { project, justCreated: true },
      });
    } catch (err) {
      setGenError(
        err instanceof Error ? err.message : "Could not generate your documents.",
      );
      setGenerating(false);
    }
  }

  const step = phase === "setup" ? 1 : 2;

  return (
    <div className="mech">
      <div className="mech-flow">
        <div className="mech-flow__bar">
          <button
            type="button"
            className="mech-flow__back"
            aria-label="Back"
            onClick={() =>
              phase === "chat" ? restart() : navigate(module ? `/${module.routeSlug}` : "/")
            }
          >
            ‹
          </button>
          <Stepper current={step} />
        </div>

        {phase === "setup" && (
          <SetupStep
            onCancel={() => navigate(module ? `/${module.routeSlug}` : "/")}
            onStarted={handleStarted}
          />
        )}
        {phase === "chat" && session && (
          <ChatStep
            session={session}
            generating={generating}
            genError={genError}
            onGenerate={handleGenerate}
            onRestart={restart}
          />
        )}
      </div>
    </div>
  );
}

const STEPS = ["Describe", "Chat it through", "Documents"];

function Stepper({ current }: { current: number }) {
  return (
    <ol className="mech-stepper" aria-label="Progress">
      {STEPS.map((label, i) => {
        const n = i + 1;
        const state = n < current ? "done" : n === current ? "active" : "todo";
        return (
          <li key={label} className={`mech-stepper__step mech-stepper__step--${state}`}>
            <span className="mech-stepper__num" aria-hidden="true">
              {state === "done" ? "✓" : n}
            </span>
            <span className="mech-stepper__label">{label}</span>
            {n < STEPS.length && <span className="mech-stepper__line" aria-hidden="true" />}
          </li>
        );
      })}
    </ol>
  );
}
