import React from "react";
import ReactDOM from "react-dom/client";
import { App } from "./app/App";
import { registerPwa } from "./pwa/registerPwa";

ReactDOM.createRoot(document.getElementById("root") as HTMLElement).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);

// Minimal PWA registration (§9). Full offline behavior is Phase 1.
registerPwa();
