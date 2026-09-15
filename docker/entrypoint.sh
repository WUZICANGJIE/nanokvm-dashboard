#!/bin/sh
set -eu

case "${PORT:-8080}" in
    ''|*[!0-9]*) printf '%s\n' 'PORT must be numeric.' >&2; exit 1 ;;
esac
if [ "$PORT" -lt 1 ] || [ "$PORT" -gt 65535 ]; then
    printf '%s\n' 'PORT must be between 1 and 65535.' >&2
    exit 1
fi

if [ "$(id -u)" = 0 ]; then
    case "$PUID:$PGID" in
        *[!0-9:]*|:*|*:) printf '%s\n' 'PUID and PGID must be numeric.' >&2; exit 1 ;;
    esac
    mkdir -p "$DATA_DIR"
    chown "$PUID:$PGID" "$DATA_DIR"
    for file in "$DATA_DIR"/dashboard.db "$DATA_DIR"/dashboard.db-wal "$DATA_DIR"/dashboard.db-shm; do
        if [ -f "$file" ]; then chown "$PUID:$PGID" "$file"; fi
    done
    exec gosu "$PUID:$PGID" python -m uvicorn nanokvm_dashboard.app:app \
        --host 0.0.0.0 --port "$PORT" --no-server-header
fi

exec python -m uvicorn nanokvm_dashboard.app:app \
    --host 0.0.0.0 --port "$PORT" --no-server-header
