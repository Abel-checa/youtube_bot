"""
Módulo: modules/image_generator.py
Propósito: Generación de imágenes 9:16 con eliminación automática
          de marcas de agua en el borde inferior.
"""

import os
import urllib.parse
from io import BytesIO
import requests
from PIL import Image
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")


def clean_watermark(image_bytes: bytes, crop_bottom_px: int = 70) -> Image.Image:
    """
    Elimina cualquier marca de agua ubicada en el borde inferior recortando
    la franja final y reescalando a 1080x1920 con interpolación Lanczos.
    """
    with Image.open(BytesIO(image_bytes)) as img:
        img = img.convert("RGB")
        w, h = img.size

        # Recortar los últimos píxeles inferiores donde se ubica el logo
        cropped = img.crop((0, 0, w, h - crop_bottom_px))

        # Reescalar de nuevo al tamaño exacto de Shorts (1080x1920)
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
        f"hyper-detailed, 8k resolution, atmospheric, clean, no text"
    )

    print(f"[*] Solicitando imagen: '{prompt[:45]}...'")

    # 1. Intento con Google Imagen 3
    if GEMINI_API_KEY:
        try:
            from google import genai
            from google.genai import types

            client = genai.Client(api_key=GEMINI_API_KEY, vertexai=False)
            result = client.models.generate_images(
                model="imagen-3.0-generate-002",
                prompt=enhanced_prompt,
                config=types.GenerateImagesConfig(
                    number_of_images=1,
                    aspect_ratio=aspect_ratio,
                    output_mime_type="image/jpeg",
                    person_generation="ALLOW_ADULT",
                ),
            )

            if result.generated_images:
                img_bytes = result.generated_images[0].image.image_bytes
                with open(output_path, "wb") as f:
                    f.write(img_bytes)
                print(f"[+] Imagen limpia generada con Google Imagen 3: {output_path}")
                return output_path

        except Exception as e:
            print(f"[!] Fallback activado ({e}).")

    # 2. Descarga con motor alternativo y limpieza de marca de agua
    encoded = urllib.parse.quote(enhanced_prompt)
    seed = os.urandom(2).hex()
    url = f"https://image.pollinations.ai/prompt/{encoded}?width=1080&height=1920&model=flux&seed={seed}"

    res = requests.get(url, timeout=60)
    if res.status_code == 200:
        # Pasa por el filtro de recorte para borrar el logo de pollinations.ai
        clean_img = clean_watermark(res.content, crop_bottom_px=70)
        clean_img.save(output_path, format="JPEG", quality=95)

        print(f"[+] Imagen sin marca de agua guardada en: {output_path}")
        return output_path
    else:
        raise RuntimeError(f"Fallo al descargar la imagen (HTTP {res.status_code})")