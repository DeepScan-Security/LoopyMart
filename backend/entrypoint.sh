#!/bin/sh
# Podman/Docker auto-creates a directory at a bind-mount path when the source
# file does not yet exist on the host. If that happened to flags.yml, remove
# the empty directory so the app falls back to the baked-in flags.example.yml.
if [ -d /app/flags.yml ]; then
    rm -rf /app/flags.yml
fi

exec "$@"
