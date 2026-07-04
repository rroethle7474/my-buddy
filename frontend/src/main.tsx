import React from "react";
import ReactDOM from "react-dom/client";
import { App } from "./app/App";
import { registerPwa } from "./pwa/registerPwa";

// Design layer (§16.1): tokens define the vars, fonts self-hosts Instrument
// Sans, global applies the base element styles + the mascot motion.
import "./app/theme/tokens.css";
import "./app/theme/fonts.css";
import "./app/theme/global.css";

ReactDOM.createRoot(document.getElementById("root") as HTMLElement).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);

// Minimal PWA registration (§9). Full offline behavior is Phase 1.
registerPwa();
