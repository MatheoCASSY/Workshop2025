#!/usr/bin/env python3
import subprocess

def scan_wifi_networks():
    try:
        # Liste les réseaux Wi-Fi détectés
        result = subprocess.run(
            ['nmcli', '-t', '-f', 'SSID', 'dev', 'wifi', 'list'],
            capture_output=True, text=True, check=True
        )
        networks = set(line.strip() for line in result.stdout.split('\n') if line.strip())
        return list(networks)
    except Exception as e:
        print("Erreur lors du scan Wi-Fi:", e)
        return []

def get_wifi_ip():
    try:
        # Récupère l'adresse IP sur l'interface wlan0
        result = subprocess.run(
            ['hostname', '-I'],
            capture_output=True, text=True, check=True
        )
        # Généralement la première IP est celle du Wi-Fi si connecté
        ip = None
        for addr in result.stdout.strip().split():
            if addr.startswith("192.") or addr.startswith("10.") or addr.startswith("172."):
                ip = addr
                break
        return ip
    except Exception as e:
        print("Erreur pour obtenir l'IP :", e)
        return None

if __name__ == "__main__":
    print("Scan des réseaux Wi-Fi disponibles...")
    networks = scan_wifi_networks()
    if networks:
        print("Réseaux détectés :")
        for n in networks:
            print(f" - {n}")
    else:
        print("Aucun réseau Wi-Fi détecté.")

    ip = get_wifi_ip()
    if ip:
        print(f"\nAdresse IP locale du Raspberry Pi (Wi-Fi) : {ip}")
    else:
        print("\nNon connecté à un réseau Wi-Fi ou impossible d'obtenir l'adresse IP.")
