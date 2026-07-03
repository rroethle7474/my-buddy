// PWA service-worker registration (ARCHITECTURE.md §9).
//
// Phase 0: minimal. vite-plugin-pwa auto-registers the generated service worker
// in production builds; this hook is the seam where Phase 1 wires app-shell
// precache, runtime caching of the active project, and the offline mutation
// replay (§9). Kept a no-op-friendly stub for now.

export function registerPwa(): void {
  // vite-plugin-pwa (registerType: "autoUpdate") injects and registers the SW
  // at build time. Nothing to do here in Phase 0; the hook exists so Phase 1
  // can add update prompts / offline-ready UX without touching main.tsx.
}
