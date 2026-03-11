#!/bin/bash
set -euo pipefail

PUID=${PUID:-1000}
PGID=${PGID:-1000}

# Create internal user matching the host UID/GID
if ! getent group abc >/dev/null 2>&1; then
    groupadd --non-unique -g "${PGID}" abc
fi
if ! getent passwd abc >/dev/null 2>&1; then
    useradd --non-unique -u "${PUID}" -g "${PGID}" -m -s /bin/sh abc
fi

# Set ownership on the directories themselves, then only fix files that need it.
# Avoids walking every file in large libraries on every container start.
chown abc:abc /app/config /Comics_in /Comics_out /Books_in /Books_out /Comics_raw
find /app/config /Comics_in /Comics_out /Books_in /Books_out /Comics_raw \
     ! -user abc -exec chown abc:abc {} +

# Drop privileges and execute application
exec gosu abc "$@"
