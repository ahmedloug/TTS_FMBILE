# -----------------------------------------------------------------------------
# FastAPI Text-to-Speech (TTS) API using Piper
#
# Ce script expose une API FastAPI sur /tts qui prend un texte en entrée,
# génère un fichier audio .wav avec Piper TTS, le joue automatiquement sur
# les haut-parleurs de la machine hôte (via ALSA/`aplay`), et renvoie le
# fichier audio au client.
#
# Prérequis :
# - Le modèle Piper doit être présent dans le dossier "models"
# - Le conteneur doit avoir accès à la carte son de l’hôte (ex: --device=/dev/snd)
# - `aplay` (alsa-utils) doit être installé dans le conteneur
# -----------------------------------------------------------------------------




from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import FileResponse
import subprocess
import os
import uuid
import hashlib

app = FastAPI()

def synthesize_speech(
    text: str,
    voice: str = "en_US-amy-medium",
    models_dir: str = os.path.join(os.path.dirname(__file__), "models"),
    output_file: str = "welcome.wav"
):
    """
    Calls the `piper` binary using the model and config from the models_dir.
    """
    model_path = os.path.join(models_dir, f"{voice}.onnx")
    config_path = os.path.join(models_dir, f"{voice}.onnx.json")

    if not os.path.isfile(model_path) or not os.path.isfile(config_path):
        raise FileNotFoundError(f"Model or config not found in {models_dir}")

    # Create output directory if needed
    output_dir = os.path.dirname(output_file)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)

    subprocess.run(
        [
            "piper",
            "--model", model_path,
            "--config", config_path,
            "--output_file", output_file
        ],
        input=text.encode("utf-8"),
        check=True
    )
    print(f" Audio saved to {output_file}")

def play_audio(file_path: str):
    # Attend la fin de la lecture avant de continuer
    subprocess.run(["paplay", file_path])

def text_to_filename(text, output_dir):
    # Utilise un hash du texte pour nommer le fichier
    h = hashlib.sha256(text.encode("utf-8")).hexdigest()
    return os.path.join(output_dir, f"{h}.wav")

@app.get("/tts")
def tts(
    text: str = Query(..., min_length=1, description="Text to synthesize")
):
    voice = "en_US-amy-medium"
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)
    output_path = text_to_filename(text, output_dir)

    if not os.path.isfile(output_path):
        try:
            synthesize_speech(text, voice=voice, output_file=output_path)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    else:
        print(f"Utilisation du cache pour : {text}")

    play_audio(output_path)  # Play the audio on the server

    return FileResponse(
        output_path,
        media_type="audio/wav",
        filename="speech.wav"
    )