RUN THESE 4 commands
apt update && apt install -y alsa-utils
apt update && apt install -y curl
apt update && apt install -y pulseaudio
apt update && apt install -y sox

RUN le serveur : uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

tester dans le contenaire et à l'exterieur: curl "http://localhost:8000/tts?text=Hello%20from%20local%20HAHAHAHAH" --output speech.wav

curl "http://localhost:8000/tts?text=Attention%2C%20speed%20limit%20is%2030%20kilometres%20per%20hour.%20Please%2C%20slow%20down%20immediately%21" --output speech.wav

Pour le BT ,echo $XDG_RUNTIME_DIR pour voir pulseaudio ensuite add les lines correspendantes sur devcontainer.json 


