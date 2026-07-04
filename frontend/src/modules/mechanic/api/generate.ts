// Generate-via-chat data layer (§7.1, mocks 1d–1e). Thin typed wrappers over the
// shared openapi-fetch client (C's src/api/client.ts) + TanStack mutations so the
// chat UI gets pending/error state. Session state lives server-side keyed by
// session_id (in-memory, Ryan 07-03) — a 404 mid-chat means the session expired
// and the client should start over.

import { useMutation } from "@tanstack/react-query";
import { api } from "../../../api/client";
import type { components } from "../../../api/schema";

export type SkillLevel = components["schemas"]["SkillLevel"];
export type BudgetBand = components["schemas"]["BudgetBand"];
export type GenerateSessionCreate = components["schemas"]["GenerateSessionCreate"];
export type GenerateSessionStart = components["schemas"]["GenerateSessionStart"];
export type GenerateMessageCreate = components["schemas"]["GenerateMessageCreate"];
export type Candidate = components["schemas"]["Candidate"];
export type GenerateProgress = components["schemas"]["GenerateProgress"];
export type ProjectSpec = components["schemas"]["ProjectSpec"];

/** One agent turn — the discriminated union keyed on `kind` (§11). */
export type AgentTurn =
  | components["schemas"]["ClarifyTurn"]
  | components["schemas"]["ProposeTurn"]
  | components["schemas"]["ReadyTurn"];

function fail(status: number): string {
  if (status === 404) return "This chat expired — let's start a new one.";
  if (status === 502) return "My Buddy had trouble thinking that through. Try again in a moment.";
  return "Something went wrong talking to My Buddy. Try again.";
}

/** POST /generate/sessions — open a session from the setup payload (1d). */
export async function startSession(
  body: GenerateSessionCreate,
): Promise<GenerateSessionStart> {
  const { data, error, response } = await api.POST("/generate/sessions", { body });
  if (error || !data) throw new Error(fail(response.status));
  return data;
}

/** POST /generate/sessions/{id}/messages — one user turn (§11). */
export async function sendMessage(
  sessionId: string,
  body: GenerateMessageCreate,
): Promise<AgentTurn> {
  const { data, error, response } = await api.POST(
    "/generate/sessions/{session_id}/messages",
    { params: { path: { session_id: sessionId } }, body },
  );
  if (error || !data) throw new Error(fail(response.status));
  return data as AgentTurn;
}

/** POST /generate/sessions/{id}/finalize — emit the §6 spec as strict JSON. */
export async function finalizeSession(sessionId: string): Promise<ProjectSpec> {
  const { data, error, response } = await api.POST(
    "/generate/sessions/{session_id}/finalize",
    { params: { path: { session_id: sessionId } } },
  );
  if (error || !data) throw new Error(fail(response.status));
  return data;
}

/** Start-session mutation (the 1d "Start chatting →" action). */
export function useStartSession() {
  return useMutation({ mutationFn: startSession });
}

/** Send-turn mutation (each chat turn; drives the "typing…" state). */
export function useSendMessage(sessionId: string) {
  return useMutation({
    mutationFn: (body: GenerateMessageCreate) => sendMessage(sessionId, body),
  });
}
