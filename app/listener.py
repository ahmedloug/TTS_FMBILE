import socket
import requests
import threading
import time
import subprocess
import os

TTS_API_URL = "http://localhost:8000/tts?text={}"
PORT = 9696
DELAI_ENTRE_COMPOSANTES = 1  # secondes

def call_tts(text):
    url = TTS_API_URL.format(requests.utils.quote(text))
    try:
        requests.get(url, timeout=10)
        print(f"TTS appelé avec: {text}")
    except Exception as e:
        print(f"Erreur appel TTS: {e}")

def vitesse_to_text(vitesse):
    return f"{vitesse} kilometres per hour"

def update_refuse_text():
    return "The last update mission is rejected"

def play_beep_audible():
    """Joue un bip audible"""
    try:
        if os.path.exists("bip.wav"):
            subprocess.run(["paplay", "bip.wav"], 
                         stderr=subprocess.DEVNULL, check=False)
            return
        
        result = subprocess.run([
            "sox", "-n", "-t", "alsa", "default", 
            "synth", "0.3", "sine", "800", "gain", "-5"
        ], stderr=subprocess.DEVNULL, check=False)
        
        if result.returncode != 0:
            subprocess.run([
                "play", "-n", "synth", "0.3", "sine", "800", "gain", "-5"
            ], stderr=subprocess.DEVNULL, check=False)
            
    except Exception as e:
        print(f"Erreur beep: {e}")
        print("\a")

def bip_loop(dt, stop_event):
    """Joue dt bips par seconde tant que stop_event n'est pas activé"""
    if dt <= 0:
        return
    
    interval = 1.0 / dt
    print(f"🔊 Bip loop actif: {dt} bips/seconde")
    
    while not stop_event.is_set():
        print(f"🔊 BIP!")
        play_beep_audible()
        
        start_time = time.time()
        while time.time() - start_time < interval:
            if stop_event.is_set():
                return
            time.sleep(0.01)

def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", PORT))
        s.listen()
        print(f"En écoute sur le port {PORT}...")
        
        while True:
            conn, addr = s.accept()
            with conn:
                print(f"Connexion de {addr}")
                last_msg = None
                current_bip_thread = None
                current_bip_stop = None
                
                while True:
                    data = conn.recv(3)
                    if not data or len(data) < 3:
                        # Arrêt des bips à la déconnexion
                        if current_bip_stop:
                            current_bip_stop.set()
                        if current_bip_thread and current_bip_thread.is_alive():
                            current_bip_thread.join()
                        print(f"Déconnexion de {addr}")
                        break
                        
                    vitesse, update_refuse, dt = data[0], data[1], data[2]
                    current_msg = (vitesse, update_refuse, dt)
                    
                    print(f"Reçu: vitesse={vitesse}, update_refuse={update_refuse}, dt={dt}")

                    # === LOGIQUE BIP (toujours active) ===
                    # Si dt a changé, redémarrer le bip
                    if last_msg is None or last_msg[2] != dt:
                        print(f"dt changé: {last_msg[2] if last_msg else 'None'} -> {dt}")
                        
                        # Arrêter l'ancien bip
                        if current_bip_stop:
                            current_bip_stop.set()
                        if current_bip_thread and current_bip_thread.is_alive():
                            current_bip_thread.join()
                        
                        # Démarrer nouveau bip si dt > 0
                        if dt > 0:
                            print(f"🎵 Nouveau bip: {dt}/seconde")
                            current_bip_stop = threading.Event()
                            current_bip_thread = threading.Thread(
                                target=bip_loop, 
                                args=(dt, current_bip_stop)
                            )
                            current_bip_thread.daemon = True
                            current_bip_thread.start()
                        else:
                            print("🔇 Arrêt bip (dt=0)")
                            current_bip_stop = None
                            current_bip_thread = None

                    # === LOGIQUE TTS (seulement si message change) ===
                    if current_msg != last_msg:
                        print("Nouveau message -> TTS")
                        
                        if vitesse == 0:
                            call_tts("Stop")
                            time.sleep(DELAI_ENTRE_COMPOSANTES)
                        else:
                            call_tts(vitesse_to_text(vitesse))
                            time.sleep(DELAI_ENTRE_COMPOSANTES)
                            if update_refuse:
                                call_tts(update_refuse_text())
                                time.sleep(DELAI_ENTRE_COMPOSANTES)
                    else:
                        print("Message identique -> Pas de TTS, juste bip")

                    last_msg = current_msg

if __name__ == "__main__":
    main()