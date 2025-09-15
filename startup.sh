#!/usr/bin/env bash

LOG="/home/linux/projet/startup.log"
PY="/usr/bin/python3"
PROJ_DIR="/home/linux/projet"
SCRIPT="$PROJ_DIR/affichage/flipper_hacking.py"
SSH_KEY="/home/linux/.ssh/id_ed25519"

echo "=== projet startup $(date) ===" >> "$LOG"

NETWORK_OK=0
for i in $(seq 1 30); do
  if command -v nmcli >/dev/null 2>&1; then
    state=$(nmcli -t -f STATE g 2>/dev/null || echo "")
    if echo "$state" | grep -qi "connected"; then
      NETWORK_OK=1
      break
    fi
  else
    if ping -c1 -W1 8.8.8.8 >/dev/null 2>&1; then
      NETWORK_OK=1
      break
    fi
  fi
  sleep 1
done

if [ "$NETWORK_OK" -eq 1 ]; then
  echo "$(date) Network available. Attempting git pull (SSH)..." >> "$LOG"
  eval "$(ssh-agent -s)" >> "$LOG" 2>&1 || true
  if [ -f "$SSH_KEY" ]; then
    ssh-add "$SSH_KEY" >> "$LOG" 2>&1 || true
  fi
  cd "$PROJ_DIR" || exit 1
  /usr/bin/git fetch --all --prune >> "$LOG" 2>&1 || true
  /usr/bin/git checkout main >> "$LOG" 2>&1 || true
  /usr/bin/git pull origin main >> "$LOG" 2>&1 || true
else
  echo "$(date) Network unavailable after timeout; skipping git pull." >> "$LOG"
fi

echo "$(date) Starting $SCRIPT" >> "$LOG"
/usr/bin/env $PY "$SCRIPT" >> "$LOG" 2>&1
echo "$(date) $SCRIPT exited with status $? at $(date)" >> "$LOG"
