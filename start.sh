#!/data/data/com.termux/files/usr/bin/bash

cd "$(dirname "$0")" || exit 1

echo "===== 249 SHADOW DATABASE ====="
read -r -s -p "Enter admin password: " ADMIN_PASSWORD
printf '\n'

if [ -z "$ADMIN_PASSWORD" ]; then
    echo "Error: password cannot be empty."
    exit 1
fi

export ADMIN_PASSWORD
exec python3 backend/server.py
