"""
Módulo: modules/subtitle_engine.py
Propósito: Transcripción local con Faster-Whisper, generación de subtítulos .ass
          con estilo YouTube Shorts y quemado de subtítulos con FFmpeg.
"""

import os
import subprocess
from faster_whisper import WhisperModel
import imageio_ffmpeg
import shutil

# Modelo rápido y ligero para CPU/GPU: 'base' o 'small'
WHISPER_MODEL_SIZE = "base"

_model = None

def get_whisper_model() -> WhisperModel:
    """Carga en memoria el modelo Whisper una única vez."""
    global _model
    if _model is None:
        print("[*] Cargando modelo Whisper (modo local)...")
        # 'int8' para bajo consumo de RAM en CPU; si tienes GPU Nvidia pon device="cuda", compute_type="float16"
        _model = WhisperModel(WHISPER_MODEL_SIZE, device="cpu", compute_type="int8")
    return _model


def format_ass_time(seconds: float) -> str:
    """Convierte segundos a formato de tiempo ASS: H:MM:SS.cs"""
    hrs = int(seconds // 3600)
    mins = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    centis = int(round((seconds - int(seconds)) * 100))
    return f"{hrs}:{mins:02d}:{secs:02d}.{centis:02d}"


def generate_ass_subtitles(audio_path: str, output_ass_path: str, words_per_line: int = 3) -> str:
    """
    Transcribe el audio palabra por palabra y genera un archivo .ass
    con estilo de subtítulos cortos para Shorts.
    """
    model = get_whisper_model()
    print(f"[*] Transcribiendo audio para subtítulos: {audio_path}")
    
    segments, _ = model.transcribe(audio_path, word_timestamps=True, language="es")

    # Extraer todas las palabras con sus marcas de tiempo
    words = []
    for segment in segments:
        for word in segment.words:
            clean_word = word.word.strip()
            if clean_word:
                words.append({
                    "word": clean_word,
                    "start": word.start,
                    "end": word.end
                })

    if not words:
        print("[!] Aviso: Whisper no detectó palabras en el audio.")
        return ""

    # Cabecera estándar de estilo ASS optimizado para Shorts (fuente grande, negrita, centrada)
    ass_header = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: ShortsDefault,Arial,84,&H0000FFFF,&H00000000,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,10,0,2,80,80,960,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

    dialogue_lines = []

    # Agrupar palabras en paquetes de 3 para que no sature la pantalla
    for i in range(0, len(words), words_per_line):
        group = words[i:i + words_per_line]
        start_time = format_ass_time(group[0]["start"])
        end_time = format_ass_time(group[-1]["end"])
        
        # Unir las palabras del bloque
        phrase = " ".join([w["word"].upper() for w in group])
        
        dialogue_lines.append(
            f"Dialogue: 0,{start_time},{end_time},ShortsDefault,,0,0,0,,{phrase}"
        )

    # Guardar archivo .ass
    os.makedirs(os.path.dirname(output_ass_path), exist_ok=True)
    with open(output_ass_path, "w", encoding="utf-8") as f:
        f.write(ass_header + "\n".join(dialogue_lines) + "\n")

    print(f"[+] Archivo de subtítulos generado en: {output_ass_path}")
    return output_ass_path


def burn_subtitles_to_video(video_input_path: str, ass_path: str, video_output_path: str) -> str:
    """Quema los subtítulos .ass en el vídeo utilizando FFmpeg."""
    ffmpeg_bin = shutil.which("ffmpeg") or imageio_ffmpeg.get_ffmpeg_exe()

    # Escapar ruta para el filtro de FFmpeg en Windows
    escaped_ass = os.path.abspath(ass_path).replace("\\", "/").replace(":", "\\:")

    print("[*] Quemando subtítulos sobre el vídeo con FFmpeg...")
    cmd = [
        ffmpeg_bin, "-y",
        "-i", os.path.abspath(video_input_path),
        "-vf", f"subtitles='{escaped_ass}'",
        "-c:v", "libx264",
        "-preset", "fast",
        "-c:a", "copy",
        os.path.abspath(video_output_path)
    ]

    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"Error al quemar subtítulos con FFmpeg: {res.stderr}")

    print(f"[+] Vídeo con subtítulos completado: {video_output_path}")
    return video_output_path