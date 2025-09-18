#!/usr/bin/env bash

# === projet startup - script lancé au démarrage ===
# Objectif : attendre la connexion Wi-Fi (max 30s) puis tenter un git push/force-pull
#           Si il y a de nouveaux commits distants (ou après push local), on reboot
#           Sinon on lance le script Python d'affichage (home.py).

LOG="/home/linux/projet/startup.log"
PY="/usr/bin/python3"
GIT="/usr/bin/git"
PROJ_DIR="/home/linux/projet"
SCRIPT="$PROJ_DIR/affichage/Home.py"
SSH_KEY="/home/linux/.ssh/id_ed25519"

echo "=== projet startup $(date) ===" >> "$LOG"

# -------------------------------------------------------------------------
# wait_for_network : attend la connexion réseau (wifi) jusqu'à TIMEOUT secondes
# -------------------------------------------------------------------------
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
  echo "$(date) Network available. Proceeding with git operations..." >> "$LOG"

  # démarrage agent ssh pour la clé
  eval "$(ssh-agent -s)" >> "$LOG" 2>&1 || true

  if [ -f "$SSH_KEY" ]; then
    ssh-add "$SSH_KEY" >> "$LOG" 2>&1 || true
  else
    echo "$(date) SSH key not found at $SSH_KEY, skipping ssh-add." >> "$LOG"
  fi

  # aller dans le répertoire du projet
  cd "$PROJ_DIR" || {
    echo "$(date) Failed to cd to $PROJ_DIR" >> "$LOG"
    exit 1
  }

  # On récupère l'HEAD local AVANT toute modification/push pour comparaison après fetch
  LOCAL_BEFORE=$($GIT rev-parse --verify HEAD 2>/dev/null || echo "")
  echo "$(date) Local HEAD before operations: ${LOCAL_BEFORE:-<none>}" >> "$LOG"

  $GIT add -A >> "$LOG" 2>&1 || true
  if $GIT commit -m "Auto-commit: $(date '+%Y-%m-%d %H:%M:%S')" >> "$LOG" 2>&1; then
    echo "$(date) Local changes committed." >> "$LOG"
  else
    echo "$(date) No local changes to commit (or commit failed)." >> "$LOG"
  fi

  # tentative de push vers origin main (si la remote accepte)
  echo "$(date) Attempting git push origin main..." >> "$LOG"
  if $GIT push origin main >> "$LOG" 2>&1; then
    echo "$(date) git push succeeded (or nothing to push)." >> "$LOG"
  else
    echo "$(date) git push failed or was rejected; continuing with fetch/reset." >> "$LOG"
  fi

  echo "$(date) Fetching origin/main..." >> "$LOG"
  if $GIT fetch origin main --quiet >> "$LOG" 2>&1; then
    echo "$(date) Fetch OK." >> "$LOG"
  else
    echo "$(date) Fetch may have failed (network/remote). Continuing anyway." >> "$LOG"
  fi

  REMOTE_SHA=$($GIT rev-parse --verify origin/main 2>/dev/null || echo "")
  echo "$(date) Remote origin/main: ${REMOTE_SHA:-<none>}" >> "$LOG"

  if [ -n "$REMOTE_SHA" ] && [ "$REMOTE_SHA" != "$LOCAL_BEFORE" ]; then
    echo "$(date) New commits detected on origin/main (different from local HEAD before)." >> "$LOG"
    echo "$(date) New commits (origin/main .. from ${LOCAL_BEFORE:-<none>}):" >> "$LOG"
    if [ -n "$LOCAL_BEFORE" ]; then
      $GIT --no-pager log --oneline "${LOCAL_BEFORE}..origin/main" >> "$LOG" 2>&1 || true
    else
      # si pas de local_before (repo sans HEAD), afficher quelques commits récents du remote
      $GIT --no-pager log --oneline -n 20 origin/main >> "$LOG" 2>&1 || true
    fi

    # Force pull : on force l'état local pour correspondre au remote
    echo "$(date) Performing force pull: git reset --hard origin/main" >> "$LOG"
    if $GIT reset --hard origin/main >> "$LOG" 2>&1; then
      echo "$(date) Reset to origin/main successful." >> "$LOG"
    else
      echo "$(date) Reset failed." >> "$LOG"
    fi

    # redémarrage du Raspberry Pi pour appliquer les changements
    echo "$(date) Changes applied from remote. Rebooting system now..." >> "$LOG"
    # a les droits, sinon systemd/service doit lancer le script en root)
    /sbin/reboot >> "$LOG" 2>&1 || {
      echo "$(date) Reboot command failed or returned. Exiting." >> "$LOG"
      exit 0
    }

    # normalement on n'atteint jamais cette ligne car reboot redémarre la machine
    exit 0
  else
    # pas de nouveautés distantes -> lancer home.py
    echo "$(date) No new remote commits compared to local HEAD before. Launching $SCRIPT" >> "$LOG"
    /usr/bin/env $PY "$SCRIPT" >> "$LOG" 2>&1
    STATUS=$?
    echo "$(date) $SCRIPT exited with status $STATUS" >> "$LOG"
    exit $STATUS
  fi

else
  # pas de réseau après 30s : on skip git et on lance quand même le programme local
  echo "$(date) Network unavailable after 30s timeout; skipping git operations." >> "$LOG"
  echo "$(date) Starting $SCRIPT (offline mode)..." >> "$LOG"
  /usr/bin/env $PY "$SCRIPT" >> "$LOG" 2>&1
  STATUS=$?
  echo "$(date) $SCRIPT exited with status $STATUS" >> "$LOG"
  exit $STATUS
fi
