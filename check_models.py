"""
Módulo: modules/story_generator.py
Propósito: Generación de guiones en JSON estructurado para YouTube Shorts
          usando el endpoint verificado 'gemini-flash-latest'.
"""

import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

SYSTEM_PROMPT = """Eres un guionista experto en YouTube Shorts y retención de audiencia.
Escribe un guion dinámico, intrigante y directo sobre el tema proporcionado.
Estructúralo exactamente en 4 a 5 escenas cortas.

REGLAS:
1. Cada escena debe contener una locución corta (4 a 6 segundos al hablar).
2. La primera escena DEBE ser un gancho intrigante para retener a la audiencia.
3. Para cada escena genera un 'image_prompt' en inglés, ultra descriptivo, cinematográfico y vertical (9:16 portrait).
4. Devuelve ÚNICAMENTE un JSON válido con esta estructura exacta:
{
  "title": "Titulo del Short",
  "scenes": [
    {
      "scene_id": 1,
      "narration": "Texto en español de la locución.",
      "image_prompt": "Cinematic 9:16 vertical shot of ..., dramatic lighting, highly detailed"
    }
  ]
}
"""


def generate_short_script(topic: str) -> dict:
    """Genera el guion estructurado llamando a la API de Gemini."""
    if not GEMINI_API_KEY:
        raise ValueError("No se encontró GEMINI_API_KEY en las variables de entorno (.env)")

    print(f"[*] Solicitando guion a Gemini para: '{topic}'...")

    # Usamos los modelos confirmados en tu lista de API
    models_to_try = ["gemini-flash-latest", "gemini-2.5-flash-lite", "gemini-3.8-flash"]

    payload = {
        "contents": [
            {
                "parts": [
                    {"text": f"{SYSTEM_PROMPT}\n\nTema: {topic}"}
                ]
            }
        ],
        "generationConfig": {
            "responseMimeType": "application/json",
            "temperature": 0.7
        }
    }
    headers = {"Content-Type": "application/json"}

    last_error = None
    for model_name in models_to_try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={GEMINI_API_KEY}"
        try:
            print(f"[*] Conectando con {model_name}...")
            response = requests.post(url, json=payload, headers=headers, timeout=60)

            if response.status_code == 200:
                data = response.json()
                raw_text = data["candidates"][0]["content"]["parts"][0]["text"].strip()
                script_data = json.loads(raw_text)
                print(f"[+] Guion generado con éxito usando {model_name}: '{script_data.get('title', 'Short')}' ({len(script_data.get('scenes', []))} escenas)")
                return script_data
            else:
                last_error = f"HTTP {response.status_code}: {response.text}"
        except Exception as e:
            last_error = str(e)

    raise RuntimeError(f"No se pudo generar el guion tras varios intentos: {last_error}")