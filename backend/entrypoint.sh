#!/bin/sh
# Podman/Docker auto-creates a directory at a bind-mount path when the source
# file does not yet exist on the host. Fix both cases:
#   1. A directory was auto-created  → remove it
#   2. File is still missing          → copy the baked-in example as fallback
if [ -d /app/flags.yml ]; then
    rm -rf /app/flags.yml
fi
if [ ! -f /app/flags.yml ]; then
    cp /app/flags.example.yml /app/flags.yml
    echo "[entrypoint] flags.yml not found — using flags.example.yml as fallback"
fi

exec "$@"
