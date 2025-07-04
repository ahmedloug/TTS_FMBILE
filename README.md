# TTS & Beep System - Système Audio en Temps Réel



###  Architecture

Le système est composé de **3 composants principaux** :

1. **Serveur TTS** (`app/main.py`) - API FastAPI qui convertit du texte en parole
2. **Listener** (`app/listener.py`) - Écoute les commandes réseau et déclenche TTS + bips
3. **Sender** (`app/sender.py`) - Simule l'envoi de commandes de vitesse/état

###  Mappage Réseau

Le système utilise une communication **TCP socket** sur le port `9696` :

```
Sender ──[TCP:9696]──> Listener ──[HTTP:8000]──> Serveur TTS
  │                        │                         │
  │                        │                         ▼
  │                        ▼                    Génération WAV
  │                   Décodage commande             │
  │                   [vitesse|refus|dt]            │
  │                        │                        │
  │                        ▼                        │
  │                 Logique Audio ◄─────────────────┘
  │                   TTS + Bips
  │
  ▼
Messages format:
[vitesse: 0-255] [update_refuse: 0/1] [dt: 0-255 bips/sec]
```

###  Fonctionnalités Audio

- **TTS dynamique** : Annonce vocale des vitesses et alertes
- **Bips configurables** : Fréquence ajustable (0-255 bips/seconde)
- **Logique intelligente** :
  - Pas de répétition TTS si message identique
  - Bips continuent tant que `dt > 0`
  - Arrêt automatique si `dt = 0`

---

##  Installation et Configuration

### Prérequis Audio

Installez les dépendances audio nécessaires :

```bash
apt update && apt install -y alsa-utils
apt update && apt install -y curl
apt update && apt install -y pulseaudio
apt update && apt install -y sox
```

### Configuration PulseAudio (pour containers)

Pour le support Bluetooth et audio avancé, vérifiez votre configuration :

```bash
echo $XDG_RUNTIME_DIR
```

Puis ajoutez les lignes correspondantes dans votre `devcontainer.json` pour le mappage PulseAudio.

---

##  Utilisation

### 0. Dans le Devcontainer.json mettez votre adresse IP 

### 1. Démarrer le Serveur TTS

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 2. Tester le TTS

**Test simple :**
```bash
curl "http://localhost:8000/tts?text=Hello%20from%20local%20HAHAHAHAH" --output speech.wav
```

**Test complexe :**
```bash
curl "http://localhost:8000/tts?text=Attention%2C%20speed%20limit%20is%2030%20kilometres%20per%20hour.%20Please%2C%20slow%20down%20immediately%21" --output speech.wav
```

### 3. Lancer le Système Complet

**Terminal 1 - Serveur TTS :**
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 - Listener :**
```bash
python app/listener.py
```

**Terminal 3 - Sender (test) :**
```bash
python app/sender.py
```

---

##  Format des Messages

Le système utilise des messages de **3 bytes** via TCP :

| Byte 1 | Byte 2 | Byte 3 |
|--------|---------|---------|
| `vitesse` (0-255) | `update_refuse` (0/1) | `dt` (0-255 bips/sec) |

### Exemples :
- `[50, 0, 0]` → "50 kilometres per hour" + silence
- `[50, 1, 2]` → "50 kilometres per hour" + "update rejected" + 2 bips/sec
- `[0, 0, 1]` → "Stop" + 1 bip/sec
- `[80, 0, 5]` → "80 kilometres per hour" + 5 bips/sec

---

##  Logique Comportementale

### TTS (Text-to-Speech)
- ✅ Déclenché uniquement sur **nouveau message**
- ❌ Pas de répétition si message identique
- 🔄 Délai de 1 seconde entre composantes

### Bips Audio
- 🔄 Continue tant que `dt > 0` même si message identique
- 🆕 Redémarre si `dt` change
- 🔇 S'arrête si `dt = 0`
- ⚡ Fréquence : 1-255 bips par seconde





```


