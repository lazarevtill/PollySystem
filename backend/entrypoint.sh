#!/bin/bash
set -e

# Wait for Redis to be ready
echo "Waiting for Redis..."
while ! nc -z "$REDIS_HOST" "$REDIS_PORT"; do
  sleep 1
done
echo "Redis is ready!"

# Apply any pending migrations (if using alembic)
# alembic upgrade head

# Create necessary directories
mkdir -p logs config/plugins

# Start the application
echo "Starting PollySystem..."
exec "$@"