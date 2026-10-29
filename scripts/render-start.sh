#!/usr/bin/env bash
set -euo pipefail

# Free web services have no pre-deploy command, so migrate before serving.
# A failed migration stops startup rather than serving an incompatible schema.
uv run --no-sync alembic upgrade head
exec uv run --no-sync uvicorn main:app --host 0.0.0.0 --port "${PORT:-8000}"
