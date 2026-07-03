// my-buddy shell (ARCHITECTURE.md §10: frontend/src/app).
//
// Phase 0: an empty shell that boots and does nothing real. Routing, the module
// registry, and the mechanic module are Phase 1+ (frontend-shell / mechanic-ui,
// §12/§13). This exists so the app builds and runs; screens are not built here.

export function App() {
  return (
    <main
      style={{
        fontFamily: "system-ui, sans-serif",
        maxWidth: 640,
        margin: "0 auto",
        padding: "3rem 1.25rem",
        color: "#1b1b19",
      }}
    >
      <h1 style={{ fontWeight: 700 }}>my-buddy</h1>
      <p style={{ color: "#54544e" }}>
        Phase 0 scaffold — the shell boots. Screens and the mechanic module are
        built in later phases against the frozen API contract.
      </p>
    </main>
  );
}
