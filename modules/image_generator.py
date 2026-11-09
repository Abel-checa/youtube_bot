"""
Módulo: modules/image_generator.py
Propósito: Generación robusta de imágenes verticales (9:16) sin marca de agua
          usando Gemini Flash Image / motores rápidos sin errores 402.
"""

import os
import time
import urllib.parse
from io import BytesIO
import requests
from PIL import Image
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")


def clean_watermark(image_bytes: bytes, crop_bottom_px: int = 70) -> Image.Image:
    """Recorta la franja inferior para eliminar cualquier logo y reescala a 1080x1920."""
    with Image.open(BytesIO(image_bytes)) as img:
        img = img.convert("RGB")
        w, h = img.size
        cropped = img.crop((0, 0, w, h - crop_bottom_px))
        cleaned = cropped.resize((1080, 1920), Image.Resampling.LANCZOS)
        return cleaned


def generate_scene_image(
    prompt: str,
    output_path: str,
    aspect_ratio: str = "9:16"
) -> str:
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)

    enhanced_prompt = (
        f"{prompt}, 9:16 vertical portrait composition, cinematic lighting, "
        f"hyper-detailed, 8k resolution, atmospheric, clean, no text, no watermark"
    )

    print(f"[*] Solicitando imagen: '{prompt[:45]}...'")

    # 1. Intento nativo con Gemini Imagen vía generate_content
    if GEMINI_API_KEY:
        try:
            from google import genai
            from google.genai import types

            client = genai.Client(api_key=GEMINI_API_KEY, vertexai=False)
            
            # Usar el modelo de imagen presente en tu cuenta
            response = client.models.generate_content(
                model="gemini-2.5-flash-image",
                contents=enhanced_prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="image/jpeg",
                )
            )

            for part in response.candidates[0].content.parts:
                if getattr(part, "inline_data", None) and part.inline_data.data:
                    with open(output_path, "wb") as f:
                        f.write(part.inline_data.data)
                    print(f"[+] Imagen nativa generada con Gemini: {output_path}")
                    return output_path

        except Exception as e:
            print(f"[!] Fallback activado ({e}).")

    # 2. Motores alternativos resilientes (sin error 402)
    encoded = urllib.parse.quote(enhanced_prompt)
    seed = os.urandom(2).hex()

    # Probamos endpoints que no exigen cuota de pago comercial
    endpoints = [
        f"https://image.pollinations.ai/prompt/{encoded}?width=1080&height=1920&model=turbo&seed={seed}",
        f"https://image.pollinations.ai/prompt/{encoded}?width=1080&height=1920&seed={seed}"
    ]

    for url in endpoints:
        try:
            time.sleep(1.5)  # Breve pausa para no saturar peticiones consecutivas
            res = requests.get(url, timeout=45)
            if res.status_code == 200 and len(res.content) > 1000:
                clean_img = clean_watermark(res.content, crop_bottom_px=75)
                clean_img.save(output_path, format="JPEG", quality=95)
                print(f"[+] Imagen sin marca de agua guardada en: {output_path}")
                return output_path
        except Exception:
            continue

    raise RuntimeError("No se pudo descargar la imagen de ningún motor disponible.")