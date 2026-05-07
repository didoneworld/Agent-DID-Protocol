#!/usr/bin/env sh
set -eu

cd /app

# Production: use Gunicorn with Uvicorn workers
if [ "${ENV:-development}" = "production" ]; then
    exec gunicorn app.asgi:app \
        --workers 4 \
        --worker-class uvicorn.workers.UvicornWorker \
        --bind 0.0.0.0:${PORT:-8000} \
        --proxy-headers \
        --access-logfile - \
        --error-logfile -
fi

# Development: use uvicorn
exec uvicorn app.asgi:app --host 0.0.0.0 --port "${PORT:-8000}" --proxy-headers
