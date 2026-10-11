#!/bin/sh
set -e

# Apply database migrations, then start the app (CMD).
echo "Running database migrations..."
alembic upgrade head

exec "$@"
