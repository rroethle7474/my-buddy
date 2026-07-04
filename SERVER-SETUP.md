# my-buddy — Server Setup Runbook

**Audience:** Ryan, executing by hand. **Goal:** deploy my-buddy to a Hetzner
server via Coolify, put it behind Cloudflare with **Cloudflare Access** as the
security model, and verify it end-to-end.

> **Read this first — the security model.** The app has **zero auth code by
> design** (ARCHITECTURE.md §2/D2). Nothing in the app checks who you are.
> **Cloudflare Access IS the lock on the door.** Until Access is configured and
> enforcing, anyone with the URL can use the app (and spend your Anthropic
> credits). So the order below is deliberate: **configure Access BEFORE the URL
> is shared or even guessable in public.** Do not skip ahead.

This runbook packages the app as three containers (see `docker-compose.prod.yml`):

```
   Cloudflare (DNS + proxy + Access auth wall)   ← the only public entry
        │  HTTPS
        ▼
   web  (nginx)  ── serves the built PWA + reverse-proxies the API  ── ONE origin
        │
        ▼
   app  (FastAPI/uvicorn, non-root; runs `alembic upgrade head` on start)
        │
        ▼
   db   (PostgreSQL)              →  named volume  pgdata
   app storage  /data/storage     →  named volume  storage_data  (progress photos)
```

---

## 0. Prerequisites (gather before you start)

- **Hetzner Cloud** account.
- A **domain** you control, with its DNS on **Cloudflare** (a free plan is fine).
- **Anthropic API key** (server-side only; never goes in the repo or the client).
- The **GitHub repo** for my-buddy (Coolify deploys from it).
- An SSH keypair for the server.
- Placeholders used below — substitute your real values:
  - `SERVER_IP` — the Hetzner server's public IPv4.
  - `mybuddy.example.com` — the hostname you'll serve the app on.
  - `you@example.com` — the email(s) allowed through Cloudflare Access.

---

## 1. Hetzner — create and prep the server

1. **Create the server.** Hetzner Cloud Console → *Add Server*:
   - Image: **Ubuntu 24.04**.
   - Type: **CX22** (2 vCPU / 4 GB) is plenty for a single-user app; size up later if needed.
   - SSH key: add yours.
   - Create, then note the public IP → this is `SERVER_IP`.

2. **First SSH + updates.**
   ```bash
   ssh root@SERVER_IP
   apt update && apt -y upgrade
   ```

3. **Swap** (small server safety net; skip if you sized up):
   ```bash
   fallocate -l 2G /swapfile && chmod 600 /swapfile
   mkswap /swapfile && swapon /swapfile
   echo '/swapfile none swap sw 0 0' >> /etc/fstab
   ```

4. **Firewall.** Coolify installs and manages Docker; you mainly need SSH + web.
   ```bash
   ufw allow 22/tcp        # SSH
   ufw allow 80/tcp        # HTTP (Let's Encrypt + Cloudflare origin)
   ufw allow 443/tcp       # HTTPS
   ufw --force enable
   ```
   The **Coolify dashboard** runs on port **8000**. Don't open 8000 to the world —
   reach it through an SSH tunnel instead (Step 2). (Optionally
   `ufw allow from YOUR_HOME_IP to any port 8000`.)

---

## 2. Install Coolify

Coolify installs Docker + itself with one script (run as root on the server):

```bash
curl -fsSL https://cdn.coollabs.io/coolify/install.sh | bash
```

Then open the dashboard. Rather than exposing 8000, tunnel from your laptop:

```bash
ssh -L 8000:localhost:8000 root@SERVER_IP
# now browse http://localhost:8000 on your laptop
```

Create the **admin account** on first load. (This login protects Coolify, not the
app.)

---

## 3. Connect the GitHub repo

In Coolify:

1. **Sources → + Add → GitHub App** and install it against the my-buddy repo
   (preferred for private repos). A public-repo URL or a deploy key also works.
2. **Projects → + Add** → name it `my-buddy` → open the **Production**
   environment.

---

## 4. Add the app as a Docker Compose resource

1. In the environment: **+ New → Docker Compose** (Git-based).
2. Point it at:
   - **Repository:** the my-buddy repo.
   - **Branch:** `main`.
   - **Compose file:** `docker-compose.prod.yml`.
3. Save. Coolify parses the compose file and shows the three services
   (`db`, `app`, `web`) and two named volumes (`pgdata`, `storage_data`).

**Persistent storage.** The two named volumes carry all durable state:
- `pgdata` → Postgres data (specs, item state, learnings, retrospectives).
- `storage_data` → the photo bytes written by the storage adapter at
  `/data/storage` (§3/D3).

Coolify preserves named volumes across redeploys. Confirm both are listed as
persistent. On disk they live under
`/var/lib/docker/volumes/<coolify-project>_pgdata` and `…_storage_data` — note
these paths for backups (Step 10).

---

## 5. Environment variables / secrets

In the resource's **Environment Variables**, add the following. **You type the
secret values yourself** — never paste them into the repo, a PR, or a chat.

| Variable | Required? | Value |
|----------|-----------|-------|
| `POSTGRES_PASSWORD` | **yes** (secret) | a strong random string |
| `ANTHROPIC_API_KEY` | **yes** (secret) | your Anthropic key |
| `APP_BASE_URL` | recommended | `https://mybuddy.example.com` |
| `ANTHROPIC_MODEL` | optional | defaults to `claude-opus-4-8` |
| `POSTGRES_USER` | optional | defaults to `my_buddy` |
| `POSTGRES_DB` | optional | defaults to `my_buddy` |
| `WEB_PORT` | optional | host port for the nginx container (default `8080`) |

All are **runtime** variables. `.env.prod.example` in the repo lists the same
set.

> **`.env` gotcha:** an *empty* `VAR=` is worse than an unset one — leave a
> variable out entirely rather than setting it blank. The compose file guards
> the required ones (`${VAR:?…}` fails the deploy if a secret is missing/empty)
> and defaults the optional ones (`${VAR:-default}`).

---

## 6. First deploy

Click **Deploy**. Watch the build + runtime logs:

- Coolify builds two images: `backend/Dockerfile.prod` (multi-stage, non-root)
  and `frontend/Dockerfile.prod` (Vite build → nginx).
- `db` comes up and passes `pg_isready`.
- `app` starts: the entrypoint prints
  `applying database migrations (alembic upgrade head)` — this creates all §5
  tables and seeds `users` + the `mechanic` module — then `uvicorn` starts and
  the `/health` healthcheck goes green.
- `web` starts and its `/healthz` healthcheck goes green.

If the app container restart-loops, check the logs: a missing
`ANTHROPIC_API_KEY`/`POSTGRES_PASSWORD` fails fast at compose interpolation; a
migration error aborts before uvicorn (fix forward and redeploy — migrations are
idempotent).

At this point the app is running **but not yet reachable by domain, and not yet
protected.** Do not share anything.

---

## 7. DNS + TLS + Cloudflare proxy (in this order)

The sequence matters so Let's Encrypt can issue a cert before Cloudflare's proxy
sits in front, and so Access is enforcing before the app is publicly reachable.

1. **DNS record — start DNS-only (grey cloud).** Cloudflare dashboard → your
   domain → **DNS → Add record**: `A`, name `mybuddy`, IPv4 `SERVER_IP`,
   **Proxy status: DNS only** (grey cloud) for now.

2. **Point Coolify at the domain.** In the resource settings, set the domain for
   the **`web`** service to `https://mybuddy.example.com` (port 80). Redeploy if
   prompted. Coolify's proxy (Traefik) requests a **Let's Encrypt** certificate
   over HTTP-01 — which works because the record is currently direct (grey).

3. **Verify directly (still open — do NOT share).** In a browser:
   `https://mybuddy.example.com/health` → `{"status":"ok"}`. Confirm the app
   loads. It is wide open right now; keep it to yourself.

4. **Enable the Cloudflare proxy (orange cloud).** Flip the A record's proxy
   status to **Proxied**. Then **SSL/TLS → Overview → Full (strict)** (the origin
   now presents the valid LE cert).

---

## 8. Cloudflare Access — configure BEFORE sharing the URL

This is the security wall. Do it now, before the URL leaves your hands.

1. Cloudflare **Zero Trust** dashboard → **Access → Applications → Add an
   application → Self-hosted**.
2. **Application name:** `my-buddy`. **Session duration:** e.g. 24h (or 1 month
   for a personal app).
3. **Application domain:** `mybuddy.example.com` (subdomain, root path — covers
   the whole app, including the API paths served through nginx).
4. **Add a policy:**
   - Name: `owner`. Action: **Allow**.
   - Include → **Emails** → `you@example.com` (add any others you want to let in).
5. **Identity provider:** the default **One-time PIN** (email code) is enough for
   a personal app; enable it (or wire Google if you prefer).
6. **Save.**

> The app trusts every request that reaches it. If this policy is missing, too
> broad, or the application domain is wrong, the app is effectively public.
> Double-check the domain and the Allow list.

---

## 9. Post-deploy verification checklist

**A. Access is enforcing.**
- Open an incognito window → `https://mybuddy.example.com` → you should get the
  **Cloudflare Access login** (email one-time PIN), not the app.
- Complete the PIN with an allowed email → the app loads.
- A non-allowed email is rejected.
- `curl https://mybuddy.example.com/health` from an unauthenticated shell should
  return the Access challenge (a redirect / 302), **not** `{"status":"ok"}` —
  that's proof the wall is up.

**B. One full UI loop** (authenticated browser):
- Homepage (mascot hero + projects grid) → **Open My Mechanic** → **Start new
  project** → describe a build → chat until **✓ Generate documents** → land on
  the docs view → toggle a shopping-cart checkbox → mark a step complete + write
  a note → the research section fills → **upload a progress photo** (it displays)
  → fill the retrospective → **Download all** (PDF export). Everything should
  persist across a reload.

**C. Backend smoke test** (`backend/scripts/e2e_smoke.py`).
This drives the whole real path: generate → chat → finalize → `POST /projects`
→ research refresh → hydrated GET.
- ⚠️ **It hits real Claude (generation + web search) and COSTS MONEY**, and it
  **leaves a seed project in the DB** (no cleanup).
- Access blocks non-browser requests, so run it **from the server against the
  origin**, bypassing Cloudflare (the published `web` port, default 8080):
  ```bash
  ssh root@SERVER_IP
  pip install httpx        # or use a venv; httpx isn't in the app image
  SMOKE_BASE_URL=http://localhost:8080 python /path/to/repo/backend/scripts/e2e_smoke.py
  ```
  Expect it to end with `E2E SMOKE PASSED`.
- *Alternative (from your laptop, through Access):* create a Cloudflare Access
  **service token** and an Allow policy that accepts it, then send the
  `CF-Access-Client-Id` / `CF-Access-Client-Secret` headers. The plain script
  doesn't add those headers, so the server-side run above is simpler.

Phone install, airplane-mode reading, camera upload, and PDF-from-phone are the
device-validation pass (**E4**) — do those from an actual phone once the URL is
live behind Access.

---

## 10. Backups (both volumes — they're one dataset)

The DB rows reference photos by `storage_key`; the bytes live on the storage
volume. **Back up both**, or a restore is half a dataset.

**Postgres** (logical dump; adjust the container name Coolify assigns):
```bash
docker ps   # find the db container name, e.g. my-buddy-db-1
docker exec <db_container> pg_dump -U my_buddy my_buddy | gzip > mybuddy-db-$(date +%F).sql.gz
```
Coolify also offers **scheduled database backups** (to local or S3) in the
resource UI — enabling that covers Postgres automatically.

**Storage volume** (the photos):
```bash
tar czf mybuddy-storage-$(date +%F).tgz \
    -C /var/lib/docker/volumes/<coolify-project>_storage_data/_data .
```
Copy both artifacts **off the server** (Hetzner Storage Box, S3, or `scp` home)
and schedule via `cron`. When you later migrate storage to Cloudflare R2 (D3),
the photo backup becomes an R2 bucket concern instead.

---

## 11. Operating notes & troubleshooting

- **Migrations run on every app start** (entrypoint → `alembic upgrade head`);
  they're idempotent, so a redeploy that adds a migration just applies it.
- **Model:** change the Claude model by setting `ANTHROPIC_MODEL` (default
  `claude-opus-4-8`) and redeploying — no code change (`config.py`).
- **`/health` green but generation 502s** → almost always a missing/invalid
  `ANTHROPIC_API_KEY`. The health check is intentionally DB-independent, so it
  can be green while Claude or the DB is misconfigured — use the smoke test /
  UI loop for real end-to-end confidence.
- **Storage adapter only** (§14): photos are read back via
  `GET /photos/{id}/content` (proxied under the `/photos` prefix in nginx), never
  a direct filesystem URL — an R2 swap stays a config change.
- **PWA + Access session expiry:** offline *reads* work from cache; if the Access
  session expires, a queued request returns the Access challenge — re-authenticate
  in the browser and retry (ARCHITECTURE.md §9). (Offline *mutation* replay is a
  deferred, post-v1 feature.)
- **nginx upstream:** the API proxy re-resolves the `app` service name every ~10s
  (Docker DNS), so a backend restart doesn't pin nginx to a stale IP. A full
  redeploy restarts all three services together regardless.
- **Redeploy:** push to `main` (or click Deploy in Coolify). Coolify rebuilds and
  swaps containers; the named volumes persist.

---

*Infra files owned by the `deploy` agent (TASKS.md E1/E2): `docker-compose.prod.yml`,
`backend/Dockerfile.prod`, `backend/docker-entrypoint.sh`, `frontend/Dockerfile.prod`,
`frontend/nginx.conf`, `.env.prod.example`, this runbook.*
