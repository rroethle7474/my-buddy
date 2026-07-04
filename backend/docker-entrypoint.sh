#!/bin/sh
# my-buddy backend container entrypoint (TASKS.md E1).
# Applies database migrations, then hands off to the CMD (uvicorn).
# depends_on: db service_healthy (compose) guarantees Postgres is reachable
# before this runs. Fail-fast: a failed migration aborts the container.
set -e

echo "[entrypoint] applying database migrations (alembic upgrade head)..."
alembic upgrade head

echo "[entrypoint] starting: $*"
exec "$@"
