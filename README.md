# 🕵️ Q-Lab Nouvelle Génération – Gadget Espion Raspberry Pi

Prototype fonctionnel développé dans le cadre du **Workshop SN2 2025-2026 EPSI/WIS**.  
Notre mission : créer un gadget espion numérique inspiré de l’univers de James Bond, combinant **discrétion**, **détection** et **ingéniosité**.

---

## 🎯 Objectifs

- Concevoir un **gadget espion discret** avec un **Raspberry Pi** et un **GFX HAT 128×64**.
- Offrir une **interface style Flipper Zero** avec écran verrouillable.
- Fournir plusieurs **outils de cybersécurité/espionnage** accessibles via un menu.
- Respecter les contraintes de sécurité minimale (authentification, code secret, verrouillage).
- Automatiser la mise à jour du code à chaque redémarrage.

---

## 🛠️ Fonctionnalités

- **Écran GFX HAT avec menu animé**
  - Interface verrouillée par une **séquence secrète (haut-bas-haut)**.
  - **Tamagotchi espion** affiché en veille (mascotte animée + mini-stats).
  - Menu style **Flipper Zero** avec icônes.

- **Modules inclus**
  - 🔍 **Wi-Fi Scan** → détection des réseaux et IP locale `wifi_scan.py`  
  - 🔎 **Port Scan** → scan de ports locaux & LAN `port_scan.py`  
  - ⌨️ **Keylogger Sim** → simulation d’un keylogger inoffensif `keylogger_sim.py`  
  - 📡 **NFC Sim** → simulation de détection de tags NFC/RFID `nfc_sim.py`  
  - ❌ **Exit** → sortie sécurisée du menu `exit_script.py`

- **Sécurité & Discrétion**
  - Code secret pour déverrouillage.
  - Mode veille avec mascotte animée.
  - Faible consommation & affichage minimaliste.

- **Mise à jour automatique**
  - Script `startup.sh` qui :
    - Vérifie la connexion Wi-Fi (30s max).
    - Effectue un **commit/push Git** des changements locaux.
    - Vérifie les mises à jour distantes et force un **pull/reset** si nécessaire.
    - Redémarre en cas de nouveauté ou lance directement `Home.py`.

---

## 📂 Structure du projet

```
projet/
├── affichage/
│   └── Home.py              # Menu principal + gestion écran/verrouillage
├── scripts/
│   ├── wifi_scan.py         # Scan des réseaux Wi-Fi
│   ├── port_scan.py         # Scan de ports réseau
│   ├── keylogger_sim.py     # Simulation de keylogger
│   ├── nfc_sim.py           # Simulation NFC/RFID
│   └── exit_script.py       # Quitter le menu
├── startup.sh               # Script de lancement & Git auto-sync
└── README.md                # Documentation du projet
```

---

## 🚀 Installation & Utilisation

### Prérequis
- Raspberry Pi 3
- [GFX HAT Pimoroni](https://shop.pimoroni.com/products/gfx-hat)
- Python 3 + dépendances :  
  ```bash
  sudo apt update && sudo apt install python3-pip git
  pip3 install pillow gfxhat
  ```

### Démarrage
1. Cloner le dépôt :
   ```bash
   git clone <url_du_repo> ~/projet
   ```
2. Rendre le script de démarrage exécutable :
   ```bash
   chmod +x startup.sh
   ```
3. Lancer manuellement ou configurer en autostart :
   ```bash
   ./startup.sh
   ```

---

## 🔒 Sécurité

- Authentification par séquence **haut-bas-haut**.
- Aucun mot de passe en clair (hashage prévu pour extensions).
- Scripts de simulation (keylogger/NFC) sans danger → **POC éducatif uniquement**.

---

## 📖 Contexte Workshop

Projet réalisé dans le cadre du sujet officiel :  
**“Q-LAB Nouvelle Génération” – Workshop SN2 EPSI/WIS (15-19 septembre 2025)**.

Critères respectés :
- Prototype fonctionnel de gadget espion.
- Utilisation d’un **capteur/actionneur** (tactile GFX HAT, backlight).
- Intégration logicielle (Python).
- Workflow discret & scénarisé (007 doit déverrouiller pour accéder au menu).
- Code versionné et documenté.

---

## 👥 Équipe

- **Mathéo**
- **Grégoire**  
- **Xavier** 

---

## 📌 Améliorations possibles

- Intégrer un **capteur PIR** pour réveil automatique à la détection de mouvement.  
- Ajout d’une **communication chiffrée** (MQTT, webhook).  
- Personnalisation du Tamagotchi (sprites espions, mini-jeux).  
- Gestion avancée des logs et export vers serveur distant.  

---

## ⚠️ Disclaimer

> Ce projet est un **Proof of Concept éducatif**.  
> Les fonctionnalités simulées (keylogger, NFC, scans) sont limitées, non intrusives et destinées uniquement à un usage pédagogique dans le cadre du Workshop EPSI/WIS.

---

Démarrage

1. Cloner le dépôt :

```bash
git clone <url_du_repo> ~/projet
```

2. Rendre le script de démarrage exécutable :

```bash
chmod +x startup.sh
```

3. Lancer manuellement ou configurer en autostart :

```bash
./startup.sh
```

---

Sécurité

- Authentification par séquence haut-bas-haut.
- Aucun mot de passe en clair (hashage prévu pour extensions).
- Scripts de simulation (keylogger/NFC) sans danger → POC éducatif uniquement.

---

Contexte Workshop

Projet réalisé dans le cadre du sujet officiel :
"Q-LAB Nouvelle Génération" – Workshop SN2 EPSI/WIS (15-19 septembre 2025).

Critères respectés :

- Prototype fonctionnel de gadget espion.
- Utilisation d’un capteur/actionneur (tactile GFX HAT, backlight).
- Intégration logicielle (Python).
- Workflow discret & scénarisé (007 doit déverrouiller pour accéder au menu).
- Code versionné et documenté.

---

Améliorations possibles

- Intégrer un capteur PIR pour réveil automatique à la détection de mouvement.
- Ajout d’une communication chiffrée (MQTT, webhook).
- Personnalisation du Tamagotchi (sprites espions, mini-jeux).
- Gestion avancée des logs et export vers serveur distant.

---

Disclaimer

Ce projet est un Proof of Concept éducatif.
Les fonctionnalités simulées (keylogger, NFC, scans) sont limitées, non intrusives et destinées uniquement à un usage pédagogique dans le cadre du Workshop EPSI/WIS.
