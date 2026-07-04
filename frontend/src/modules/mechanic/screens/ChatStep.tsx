// Chat — step 2 of the guided flow (mock 1e). A bounded conversation: the agent
// clarifies, may propose 2–3 candidate projects (vague input), then signals it's
// ready. Each turn is POST /generate/sessions/{id}/messages → a clarify/propose/
// ready turn (§11). "Generate documents" hands off to the parent, which finalizes
// → POST /projects → routes to the docs (1f).

import { useEffect, useMemo, useRef, useState } from "react";
import type { AgentTurn, Candidate, GenerateProgress, GenerateSessionStart } from "../api/generate";
import { useSendMessage } from "../api/generate";

type ChatMessage =
  | { id: number; role: "agent"; text: string; turn?: AgentTurn }
  | { id: number; role: "user"; text: string };

export function ChatStep({
  session,
  generating,
  genError,
  onGenerate,
  onRestart,
}: {
  session: GenerateSessionStart;
  generating: boolean;
  genError: string | null;
  onGenerate: () => void;
  onRestart: () => void;
}) {
  const idRef = useRef(0);
  const nextId = () => ++idRef.current;

  const [messages, setMessages] = useState<ChatMessage[]>(() => [
    { id: nextId(), role: "agent", text: session.agent_message },
  ]);
  const [progress, setProgress] = useState<GenerateProgress | null>(null);
  const [draft, setDraft] = useState("");
  const send = useSendMessage(session.session_id);

  const endRef = useRef<HTMLDivElement>(null);
  useEffect(() => {
    endRef.current?.scrollIntoView({ block: "end" });
  }, [messages, send.isPending]);

  const lastTurn = useMemo(() => {
    for (let i = messages.length - 1; i >= 0; i--) {
      const m = messages[i];
      if (m.role === "agent" && m.turn) return m.turn;
    }
    return null;
  }, [messages]);

  const isReady = lastTurn?.kind === "ready";
  const expired = send.isError && /expired/i.test((send.error as Error)?.message ?? "");

  function applyTurn(turn: AgentTurn) {
    setMessages((m) => [...m, { id: nextId(), role: "agent", text: turn.agent_message, turn }]);
    if (turn.progress) setProgress(turn.progress);
  }

  function submitText() {
    const text = draft.trim();
    if (!text || send.isPending || generating) return;
    setDraft("");
    setMessages((m) => [...m, { id: nextId(), role: "user", text }]);
    send.mutate({ message: text }, { onSuccess: applyTurn });
  }

  function pickCandidate(c: Candidate) {
    if (send.isPending || generating) return;
    setMessages((m) => [...m, { id: nextId(), role: "user", text: `Let's go with “${c.title}”.` }]);
    send.mutate({ select_candidate_id: c.id }, { onSuccess: applyTurn });
  }

  return (
    <div className="mech-chat">
      <header className="mech-chat__head">
        <div className="mech-chat__title">Chat with your buddy</div>
        {progress ? (
          <div className="mech-chat__progress">
            <span className="mech-chat__dot" aria-hidden="true" />
            {progress.label}
            {progress.total != null
              ? ` · ${progress.current} of ${progress.total}`
              : ` · step ${progress.current}`}
          </div>
        ) : (
          <div className="mech-chat__progress mech-chat__progress--muted">
            Design step · getting started
          </div>
        )}
      </header>

      <div className="mech-thread">
        {messages.map((m) =>
          m.role === "agent" ? (
            <div key={m.id} className="mech-turn mech-turn--agent">
              <div className="mech-avatar" aria-hidden="true">🤖</div>
              <div className="mech-bubble mech-bubble--agent">
                {m.text}
                {m.turn?.kind === "proposing" && (
                  <div className="mech-candidates">
                    {m.turn.candidates.map((c) => (
                      <button
                        key={c.id}
                        type="button"
                        className="mech-candidate"
                        onClick={() => pickCandidate(c)}
                        disabled={send.isPending || generating}
                      >
                        <div className="mech-candidate__title">{c.title}</div>
                        <div className="mech-candidate__summary">{c.summary}</div>
                        <div className="mech-candidate__meta">
                          {c.difficulty && <span className="mech-chip">{c.difficulty}</span>}
                          {c.est_cost_usd != null && (
                            <span className="mech-chip">~${c.est_cost_usd}</span>
                          )}
                          <span className="mech-candidate__pick">Pick this →</span>
                        </div>
                      </button>
                    ))}
                  </div>
                )}
              </div>
            </div>
          ) : (
            <div key={m.id} className="mech-turn mech-turn--user">
              <div className="mech-bubble mech-bubble--user">{m.text}</div>
            </div>
          ),
        )}

        {send.isPending && (
          <div className="mech-turn mech-turn--agent">
            <div className="mech-avatar" aria-hidden="true">🤖</div>
            <div className="mech-bubble mech-bubble--agent mech-bubble--typing" aria-label="My Buddy is typing">
              <span className="mech-typing"><i /><i /><i /></span>
            </div>
          </div>
        )}

        {isReady && (
          <div className="mech-ready-inline" role="status">
            <span>✓ We've got everything. Ready to generate your plan.</span>
            <button
              type="button"
              className="mech-btn mech-btn--success"
              onClick={onGenerate}
              disabled={generating}
            >
              {generating ? "Generating…" : "Generate documents →"}
            </button>
          </div>
        )}

        {genError && (
          <p className="mech-form-error" role="alert">{genError}</p>
        )}
        {send.isError && !expired && (
          <p className="mech-form-error" role="alert">
            {(send.error as Error)?.message ?? "Something went wrong. Try again."}
          </p>
        )}
        {expired && (
          <div className="mech-ready-inline mech-ready-inline--warn" role="alert">
            <span>This chat expired. Let's start a fresh one.</span>
            <button type="button" className="mech-btn mech-btn--ghost" onClick={onRestart}>
              Start over
            </button>
          </div>
        )}
        <div ref={endRef} />
      </div>

      {!isReady && !expired && (
        <div className="mech-composer">
          <textarea
            className="mech-composer__input"
            placeholder="Message My Buddy…"
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                submitText();
              }
            }}
            rows={1}
            disabled={generating}
          />
          <button
            type="button"
            className="mech-btn mech-btn--primary"
            onClick={submitText}
            disabled={!draft.trim() || send.isPending || generating}
          >
            Send
          </button>
        </div>
      )}

      <p className="mech-chat__disclaimer">
        Powered by the Claude API · My Buddy can make mistakes — double-check load
        ratings.
      </p>
    </div>
  );
}
