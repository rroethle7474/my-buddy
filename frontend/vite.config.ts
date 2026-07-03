import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { VitePWA } from "vite-plugin-pwa";

// my-buddy frontend (ARCHITECTURE.md §3). Phase 0: an empty shell that boots,
// with vite-plugin-pwa wired minimally. Full app-shell precache + runtime
// caching of the active project is Phase 1 (frontend-shell, §9/§12/§13).
export default defineConfig({
  plugins: [
    react(),
    VitePWA({
      registerType: "autoUpdate",
      manifest: {
        name: "my-buddy",
        short_name: "my-buddy",
        description: "Pick and complete skill-building projects.",
        theme_color: "#de3b2c", // primary action red (§16.1 tokens)
        background_color: "#f7f7f3", // warm off-white canvas (§16.1)
        display: "standalone",
        start_url: "/",
        icons: [
          // Placeholder icon set — real Buddy-mascot icons land with the UI
          // work (design/buddy-mascot.svg, §16.4). Phase 0 keeps PWA minimal.
          {
            src: "buddy-mascot.svg",
            sizes: "any",
            type: "image/svg+xml",
            purpose: "any",
          },
        ],
      },
      // Dev: keep the service worker off unless explicitly testing it.
      devOptions: { enabled: false },
    }),
  ],
  server: {
    port: 5173,
    // Proxy API calls to the FastAPI app in local dev so the browser only talks
    // to one origin (the FastAPI app is the only backend, §4).
    proxy: {
      "/health": "http://localhost:8000",
      "/modules": "http://localhost:8000",
      "/projects": "http://localhost:8000",
      "/shop": "http://localhost:8000",
      "/photos": "http://localhost:8000",
      "/generate": "http://localhost:8000",
    },
  },
});
