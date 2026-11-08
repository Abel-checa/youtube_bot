"""
Módulo: modules/video_engine.py
Propósito: Renderizado de vídeo vertical 9:16 (1080x1920), efecto Ken Burns
          y acople garantizado de audio detectando el binario FFmpeg de imageio.
"""

import os
import shutil
import subprocess
from typing import List
import numpy as np
from PIL import Image
import imageio_ffmpeg
from moviepy import (
    ImageClip,
    AudioFileClip,
    concatenate_videoclips
)

CANVAS_WIDTH = 1080
CANVAS_HEIGHT = 1920
DEFAULT_FPS = 30
DEFAULT_ZOOM_RATIO = 0.05


def get_ffmpeg_binary() -> str:
    """Devuelve la ruta ejecutable de FFmpeg (sistema o empaquetado con imageio)."""
    system_ffmpeg = shutil.which("ffmpeg")
    if system_ffmpeg:
        return system_ffmpeg
    return imageio_ffmpeg.get_ffmpeg_exe()


def prepare_base_image(image_path: str, temp_target_path: str) -> str:
    """Ajusta y recorta una imagen al formato 1080x1920 (9:16) mediante recorte centrado."""
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"No se encontró la imagen en: {image_path}")

    with Image.open(image_path) as img:
        img = img.convert("RGB")
        img_ratio = img.width / img.height
        target_ratio = CANVAS_WIDTH / CANVAS_HEIGHT

        if img_ratio > target_ratio:
            new_height = CANVAS_HEIGHT
            new_width = int(CANVAS_HEIGHT * img_ratio)
        else:
            new_width = CANVAS_WIDTH
            new_height = int(CANVAS_WIDTH / img_ratio)

        resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

        left = (new_width - CANVAS_WIDTH) // 2
        top = (new_height - CANVAS_HEIGHT) // 2
        right = left + CANVAS_WIDTH
        bottom = top + CANVAS_HEIGHT

        cropped = resized.crop((left, top, right, bottom))
        cropped.save(temp_target_path, format="JPEG", quality=95)

    return temp_target_path


def apply_ken_burns(base_clip: ImageClip, duration: float, zoom_ratio: float = DEFAULT_ZOOM_RATIO):
    """Aplica zoom continuo hacia adelante sobre la imagen."""
    def zoom_effect(get_frame, t: float):
        scale = 1.0 + (zoom_ratio * (t / duration))
        frame = get_frame(t)
        h, w, _ = frame.shape

        new_w = int(w * scale)
        new_h = int(h * scale)

        pil_frame = Image.fromarray(frame).resize((new_w, new_h), Image.Resampling.BILINEAR)

        x_center = (new_w - w) // 2
        y_center = (new_h - h) // 2

        cropped_frame = pil_frame.crop((x_center, y_center, x_center + w, y_center + h))
        return np.array(cropped_frame)

    return base_clip.transform(zoom_effect)


def build_scene(image_path: str, audio_path: str, zoom_ratio: float = DEFAULT_ZOOM_RATIO):
    """Construye una escena vinculando imagen con zoom y registra la ruta del audio."""
    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"No se encontró el audio en: {audio_path}")

    audio_clip = AudioFileClip(audio_path)
    duration = float(audio_clip.duration)
    audio_clip.close()

    os.makedirs("temp", exist_ok=True)
    temp_img_name = f"temp_scaled_{os.path.basename(image_path)}.jpg"
    temp_img_path = os.path.join("temp", temp_img_name)
    prepare_base_image(image_path, temp_img_path)

    raw_clip = ImageClip(temp_img_path).with_duration(duration)
    animated_clip = apply_ken_burns(raw_clip, duration=duration, zoom_ratio=zoom_ratio)

    animated_clip.audio_filepath = audio_path
    animated_clip.scene_duration = duration

    return animated_clip


def render_short_video(
    scene_clips: List,
    output_path: str,
    fps: int = DEFAULT_FPS,
    preset: str = "fast"
) -> str:
    """Renderiza el vídeo uniendo vídeo y audio mediante el binario de FFmpeg."""
    if not scene_clips:
        raise ValueError("La lista de clips a renderizar está vacía.")

    ffmpeg_bin = get_ffmpeg_binary()
    print(f"[*] Binario FFmpeg en uso: {ffmpeg_bin}")

    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)

    os.makedirs("temp", exist_ok=True)
    temp_silent_video = os.path.join("temp", "temp_video_silent.mp4")
    temp_concat_audio = os.path.join("temp", "temp_audio_master.mp3")

    # 1. Exportar el vídeo sin sonido desde MoviePy
    if len(scene_clips) == 1:
        final_video = scene_clips[0]
    else:
        final_video = concatenate_videoclips(scene_clips)

    print("[*] Renderizando pista visual con MoviePy...")
    final_video.write_videofile(
        temp_silent_video,
        fps=fps,
        codec="libx264",
        preset=preset,
        threads=4,
        ffmpeg_params=["-pix_fmt", "yuv420p"]
    )
    final_video.close()
    for clip in scene_clips:
        clip.close()

    # 2. Gestionar audio
    audio_files = [getattr(c, "audio_filepath", None) for c in scene_clips if getattr(c, "audio_filepath", None)]

    if len(audio_files) == 1:
        final_audio_path = audio_files[0]
    else:
        concat_txt = os.path.join("temp", "audio_list.txt")
        with open(concat_txt, "w", encoding="utf-8") as f:
            for a_path in audio_files:
                abs_a_path = os.path.abspath(a_path).replace("\\", "/")
                f.write(f"file '{abs_a_path}'\n")

        subprocess.run([
            ffmpeg_bin, "-y", "-f", "concat", "-safe", "0",
            "-i", concat_txt, "-c", "copy", temp_concat_audio
        ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        final_audio_path = temp_concat_audio

    # 3. Multiplexar vídeo + audio
    print(f"[*] Acoplando audio ({os.path.basename(final_audio_path)}) mediante FFmpeg...")
    ffmpeg_cmd = [
        ffmpeg_bin, "-y",
        "-i", temp_silent_video,
        "-i", final_audio_path,
        "-c:v", "copy",
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        output_path
    ]

    result = subprocess.run(ffmpeg_cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"Error en FFmpeg al multiplexar audio: {result.stderr}")

    # 4. Limpieza del archivo mudo
    if os.path.exists(temp_silent_video):
        os.remove(temp_silent_video)

    print(f"[+] Vídeo final con audio exportado en: {output_path}")
    return output_path