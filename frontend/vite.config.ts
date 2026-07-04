import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { VitePWA } from "vite-plugin-pwa";

// my-buddy frontend (ARCHITECTURE.md §3). PWA (C2, §9): installable app-shell
// with the Buddy mascot icons, offline app-shell precache (incl. the self-hosted
// font), and runtime caching of opened projects so they read offline. Offline
// *mutation* replay is deferred (TASKS.md) — reads work offline; writes fail
// gracefully.

// The browser only ever talks to one origin (§4); in local dev both the dev
// server and `vite preview` proxy the API paths to the FastAPI app on :8000.
const apiProxy = {
  "/health": "http://localhost:8000",
  "/modules": "http://localhost:8000",
  "/projects": "http://localhost:8000",
  "/shop": "http://localhost:8000",
  "/photos": "http://localhost:8000",
  "/generate": "http://localhost:8000",
};

export default defineConfig({
  plugins: [
    react(),
    VitePWA({
      registerType: "autoUpdate",
      includeAssets: ["buddy-icon.svg", "apple-touch-icon.png"],
      manifest: {
        name: "My Buddy",
        short_name: "My Buddy",
        description:
          "Pick and complete hands-on projects — My Buddy plans them with you.",
        theme_color: "#de3b2c", // primary action red (§16.1 tokens)
        background_color: "#f7f7f3", // warm off-white canvas (§16.1)
        display: "standalone",
        orientation: "portrait",
        scope: "/",
        start_url: "/",
        categories: ["education", "lifestyle", "productivity"],
        icons: [
          { src: "pwa-192x192.png", sizes: "192x192", type: "image/png", purpose: "any" },
          { src: "pwa-512x512.png", sizes: "512x512", type: "image/png", purpose: "any" },
          { src: "maskable-512x512.png", sizes: "512x512", type: "image/png", purpose: "maskable" },
          { src: "buddy-icon.svg", sizes: "any", type: "image/svg+xml", purpose: "any" },
        ],
      },
      workbox: {
        // App shell precache — add woff2 so the self-hosted font works offline.
        globPatterns: ["**/*.{js,css,html,ico,png,svg,woff2}"],
        // SPA deep-links resolve to index.html offline, EXCEPT the API paths
        // (those must hit the network / runtime cache, not the shell).
        navigateFallback: "index.html",
        navigateFallbackDenylist: [
          /^\/(health|modules|projects|shop|photos|generate)(\/|$)/,
        ],
        runtimeCaching: [
          {
            // Opening a project caches its payload so it's readable offline (§9).
            // NetworkFirst: fresh when online, last-known when offline.
            urlPattern: ({ url, request, sameOrigin }) =>
              sameOrigin &&
              request.method === "GET" &&
              /^\/(projects|modules)(\/|$)/.test(url.pathname),
            handler: "NetworkFirst",
            options: {
              cacheName: "my-buddy-api",
              networkTimeoutSeconds: 5,
              expiration: { maxEntries: 80, maxAgeSeconds: 60 * 60 * 24 * 30 },
              cacheableResponse: { statuses: [200] },
            },
          },
        ],
      },
      // Dev: keep the service worker off unless explicitly testing it.
      devOptions: { enabled: false },
    }),
  ],
  server: {
    port: 5173,
    proxy: apiProxy,
  },
  // `vite preview` serves the production build (with the service worker) — mirror
  // the proxy so the PWA can be exercised prod-like against a local backend.
  preview: {
    port: 4173,
    proxy: apiProxy,
  },
});
