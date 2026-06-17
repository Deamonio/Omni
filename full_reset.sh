#!/bin/bash
set -euo pipefail

echo "Step 1: Check sudo"
if ! sudo -n true 2>/dev/null; then
    echo "NEED_SUDO_PASSWORD"
    exit 1
fi

echo "Step 2: Build reset targets"
if [ ! -f dashboard/students.json ]; then
    echo "Error: dashboard/students.json not found"
    exit 1
fi
TARGETS=$(jq -r '.[] | select(.id != null) | .id' dashboard/students.json)

echo "Step 3: Stop/remove student containers"
docker compose stop student01 student02 student03 student04 student05 student06 student07 student08 student09 student10 student11 student12 student13 student14 student15 student16 student17 student18 student19 student20 student21 student22 student23 student24 student25 student26 student27 student28 student29 2>/dev/null || true
docker compose rm -f student01 student02 student03 student04 student05 student06 student07 student08 student09 student10 student11 student12 student13 student14 student15 student16 student17 student18 student19 student20 student21 student22 student23 student24 student25 student26 student27 student28 student29 2>/dev/null || true

echo "Step 4: Wipe and Refill student directories"
USER_ID=$(id -u)
GROUP_ID=$(id -g)

for ID in $TARGETS; do
    echo "Processing $ID..."
    sudo mkdir -p "students/$ID" "student_logs/$ID"
    
    if [ "$ID" = "0000000" ]; then
        # Preserve omni, be robust against concurrent deletions if any
        sudo find "students/$ID" -mindepth 1 ! -name 'omni' -exec rm -rf {} + 2>/dev/null || true
    else
        sudo rm -rf "students/$ID"/* 2>/dev/null || true
    fi
    
    sudo rm -rf "student_logs/$ID"/* 2>/dev/null || true

    # Recreate baseline files
    echo "from flask import Flask
import os
import socket

app = Flask(__name__)

@app.route('/')
def hello():
    return 'Hello, Omni!'

def find_available_port(start_port=5000, max_tries=50):
    for port in range(start_port, start_port + max_tries):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            if sock.connect_ex(('127.0.0.1', port)) != 0:
                return port
    raise RuntimeError('No available port found')

if __name__ == '__main__':
    port = int(os.getenv('PORT') or find_available_port(5000))
    app.run(host='0.0.0.0', port=port)
" | sudo tee "students/$ID/app.py" > /dev/null
    
    sudo touch "students/$ID/index.html"
    
    # Set ownership
    sudo chown -R "$USER_ID:$GROUP_ID" "students/$ID" "student_logs/$ID"
done

echo "Step 5: Recreate services"
docker compose up -d --force-recreate student01 student02 student03 student04 student05 student06 student07 student08 student09 student10 student11 student12 student13 student14 student15 student16 student17 student18 student19 student20 student21 student22 student23 student24 student25 student26 student27 student28 student29

echo "Step 6: Post-checks"
docker compose ps --status running | sed -n '1,80p'
echo "Listing for 2501125:"
ls -la students/2501125 2>/dev/null | sed -n '1,60p' || echo "student 2501125 not found"
echo "Listing for 0000000:"
ls -la students/0000000 | sed -n '1,80p'
test -x students/0000000/omni && echo OMNI_OK || echo OMNI_MISSING

# Wait a few seconds for containers to start before health checks
sleep 5
curl -sS -I --max-time 8 http://127.0.0.1:30000 | head -n 1 || echo "Port 30000 check failed"
curl -sS -I --max-time 8 http://127.0.0.1:50000 | head -n 1 || echo "Port 50000 check failed"

echo "RESET_DONE"
