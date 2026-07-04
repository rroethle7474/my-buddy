import { registerSW } from "virtual:pwa-register";

/**
 * PWA service-worker registration (ARCHITECTURE.md §9).
 *
 * registerType is "autoUpdate" (vite.config.ts), so a new service worker skips
 * waiting and reloads automatically — there's no update prompt to manage. We
 * surface one gentle, on-brand toast the first time the app shell is cached, so
 * the user knows the app now works offline (readable projects; mutations still
 * need a connection — offline replay is deferred, TASKS.md).
 */
export function registerPwa(): void {
  registerSW({
    immediate: true,
    onOfflineReady() {
      showToast("My Buddy is ready to use offline.");
    },
  });
}

function showToast(message: string): void {
  const el = document.createElement("div");
  el.textContent = message;
  el.setAttribute("role", "status");
  Object.assign(el.style, {
    position: "fixed",
    left: "50%",
    bottom: "24px",
    transform: "translateX(-50%) translateY(8px)",
    zIndex: "1000",
    maxWidth: "min(92vw, 360px)",
    padding: "12px 18px",
    borderRadius: "12px",
    background: "var(--ink, #1b1b19)",
    color: "#fff",
    font: "600 14px/1.4 var(--font, system-ui, sans-serif)",
    boxShadow: "0 12px 30px -12px rgba(20,20,20,.5)",
    opacity: "0",
    transition: "opacity .25s ease, transform .25s ease",
  } satisfies Partial<CSSStyleDeclaration>);
  document.body.appendChild(el);

  requestAnimationFrame(() => {
    el.style.opacity = "1";
    el.style.transform = "translateX(-50%) translateY(0)";
  });
  setTimeout(() => {
    el.style.opacity = "0";
    el.style.transform = "translateX(-50%) translateY(8px)";
    setTimeout(() => el.remove(), 300);
  }, 3600);
}
