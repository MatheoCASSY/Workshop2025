#!/usr/bin/env bash

# === projet startup - script lancé au démarrage ===
# Objectif : attendre la connexion Wi-Fi (max 30s) puis tenter un git pull via SSH
# et lancer le script Python d'affichage.

LOG="/home/linux/projet/startup.log"
PY="/usr/bin/python3"
PROJ_DIR="/home/linux/projet"
SCRIPT="$PROJ_DIR/affichage/home.py"
SSH_KEY="/home/linux/.ssh/id_ed25519"

echo "=== projet startup $(date) ===" >> "$LOG"

# -----------------------------------------------------------------------------
# wait_for_network : attend la connexion réseau (wifi) jusqu'à TIMEOUT secondes
# -----------------------------------------------------------------------------
wait_for_network() {
  TIMEOUT=30   # délai max en secondes (demandé : 30s)
  NETWORK_OK=0

  for i in $(seq 1 $TIMEOUT); do
    if command -v nmcli >/dev/null 2>&1; then
      state=$(nmcli -t -f STATE g 2>/dev/null || echo "")
      if echo "$state" | grep -qi "connected"; then
        NETWORK_OK=1
        # réseau ok, on sort de la boucle
        break
      fi
    else
      # si nmcli absent, on essaye un ping rapide vers 8.8.8.8 (Google DNS)
      if ping -c1 -W1 8.8.8.8 >/dev/null 2>&1; then
        NETWORK_OK=1
        break
      fi
    fi

    # si pas encore connecté, j'attends 1 seconde et je réessaie
    sleep 1
  done

  return $NETWORK_OK
}

wait_for_network
NETWORK_OK=$?

if [ "$NETWORK_OK" -eq 1 ]; then
  echo "$(date) Network available. Attempting git pull (SSH)..." >> "$LOG"
  eval "$(ssh-agent -s)" >> "$LOG" 2>&1 || true

  if [ -f "$SSH_KEY" ]; then
    ssh-add "$SSH_KEY" >> "$LOG" 2>&1 || true
  else
    echo "$(date) SSH key not found at $SSH_KEY, skipping ssh-add." >> "$LOG"
  fi

  cd "$PROJ_DIR" || {
    echo "$(date) Failed to cd to $PROJ_DIR" >> "$LOG"
    exit 1
  }

  /usr/bin/git fetch --all --prune >> "$LOG" 2>&1 || true
  /usr/bin/git checkout main >> "$LOG" 2>&1 || true
  /usr/bin/git pull origin main >> "$LOG" 2>&1 || true
else
  echo "$(date) Network unavailable after 30s timeout; skipping git pull." >> "$LOG"
fi

echo "$(date) Starting $SCRIPT" >> "$LOG"
/usr/bin/env $PY "$SCRIPT" >> "$LOG" 2>&1
STATUS=$?
echo "$(date) $SCRIPT exited with status $STATUS" >> "$LOG"
