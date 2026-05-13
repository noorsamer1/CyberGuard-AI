#!/bin/sh
set -e
cd /app
# Worker sets SKIP_ALEMBIC=1 so only one process runs migrations (avoids races with api).
if [ -z "${SKIP_ALEMBIC:-}" ]; then
  alembic upgrade head
fi
exec "$@"
