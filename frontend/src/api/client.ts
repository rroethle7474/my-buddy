import createClient from "openapi-fetch";
import type { paths } from "./schema";

/**
 * The typed API client. Types come from the generated OpenAPI schema
 * (`schema.d.ts`, never hand-edited — §3/§14), so every path, param, and
 * response body is checked against the backend contract at compile time.
 *
 * `baseUrl: "/"` keeps the browser on one origin (ARCHITECTURE.md §4): in dev,
 * Vite proxies the API paths to the FastAPI app on :8000 (vite.config.ts); in
 * prod the app is served same-origin behind Cloudflare Access (D2).
 */
export const api = createClient<paths>({ baseUrl: "/" });
