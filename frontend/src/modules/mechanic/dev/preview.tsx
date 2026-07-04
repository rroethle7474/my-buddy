// Scaffold-ahead preview harness (TASKS D1). Mounts the mechanic read view
// against the fixture with the mocked data hook, so the four sections are
// demoable end-to-end before any live endpoint exists. This is a DEV-ONLY entry
// (referenced by preview.html) — it is not part of the shipped app, which the
// shell (C) wires up on integration. Nothing outside src/modules/mechanic is
// touched.

import React from "react";
import ReactDOM from "react-dom/client";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MechanicProject } from "../components/MechanicProject";
import { useMechanicProject } from "../hooks/useMechanicProject";
import { doorwayPullUpBar } from "../fixtures/doorwayPullUpBar";
import "../styles.css";

// No `options` → the hook stays local-only (no PATCH, no cache writes); the
// provider is only here because the hook calls `useQueryClient()` unconditionally.
const queryClient = new QueryClient();

function Preview() {
  const api = useMechanicProject(doorwayPullUpBar);
  return (
    <div style={{ background: "#f7f7f3", minHeight: "100vh", padding: "8px 0 0" }}>
      <MechanicProject api={api} showReadyBanner />
    </div>
  );
}

ReactDOM.createRoot(document.getElementById("root") as HTMLElement).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <Preview />
    </QueryClientProvider>
  </React.StrictMode>,
);
