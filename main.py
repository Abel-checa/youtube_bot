"""
Orquestador Principal del Pipeline de YouTube Shorts
Ejecución completa: Tema -> Claude -> ElevenLabs + Imagen -> VideoEngine -> Whisper -> MP4 Final
"""

import os
import shutil
from datetime import datetime
from dotenv import load_dotenv

from modules.story_generator import generate_short_script
from modules.image_generator import generate_scene_image
from modules.tts_engine import generate_speech
from modules.video_engine import build_scene, render_short_video
from modules.subtitle_engine import generate_ass_subtitles, burn_subtitles_to_video

load_dotenv()


def create_youtube_short(topic: str):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_temp_dir = os.path.join("temp", f"run_{timestamp}")
    os.makedirs(run_temp_dir, exist_ok=True)
    os.makedirs("output", exist_ok=True)

    print(f"\n=======================================================")
    print(f" INICIANDO PRODUCCIÓN: {topic}")
    print(f"=======================================================\n")

    # 1. Claude genera el guion dividido en escenas
    script_data = generate_short_script(topic)
    scenes = script_data.get("scenes", [])

    if not scenes:
        raise ValueError("El guion generado no contiene escenas válidas.")

    scene_clips = []
    all_audio_paths = []

    # 2. Generación iterativa de cada escena (Imagen + Audio + Ken Burns)
    for idx, scene in enumerate(scenes):
        scene_id = scene.get("scene_id", idx + 1)
        narration = scene.get("narration")
        image_prompt = scene.get("image_prompt")

        print(f"\n--- Procesando Escena {scene_id}/{len(scenes)} ---")

        audio_file = os.path.join(run_temp_dir, f"audio_{scene_id}.mp3")
        image_file = os.path.join(run_temp_dir, f"image_{scene_id}.jpg")

        # Generar audio con ElevenLabs
        generate_speech(text=narration, output_path=audio_file)
        all_audio_paths.append(audio_file)

        # Generar imagen limpia 9:16
        generate_scene_image(prompt=image_prompt, output_path=image_file)

        # Montar la escena con zoom dinámico
        clip = build_scene(image_path=image_file, audio_path=audio_file)
        scene_clips.append(clip)

    # 3. Concatenación y renderizado base
    raw_video_path = os.path.join(run_temp_dir, "raw_stitched_video.mp4")
    print(f"\n[*] Ensamblando pistas de vídeo...")
    render_short_video(scene_clips, raw_video_path)

    # 4. Transcripción con Faster-Whisper para subtítulos palabra por palabra
    master_audio_path = os.path.join("temp", "temp_audio_master.mp3")
    if not os.path.exists(master_audio_path):
        master_audio_path = all_audio_paths[0]

    ass_subtitles_path = os.path.join(run_temp_dir, "subtitles.ass")
    print(f"\n[*] Generando subtítulos con Whisper...")
    generate_ass_subtitles(audio_path=master_audio_path, output_ass_path=ass_subtitles_path, words_per_line=3)

    # 5. Quemar subtítulos con FFmpeg en el archivo final
    clean_title = "".join(c for c in script_data.get("title", "short") if c.isalnum() or c in (" ", "_", "-")).strip()
    clean_title = clean_title.replace(" ", "_")
    final_output_path = os.path.join("output", f"{clean_title}_{timestamp}.mp4")

    print(f"\n[*] Quemando subtítulos sobre el montaje final...")
    burn_subtitles_to_video(
        video_input_path=raw_video_path,
        ass_path=ass_subtitles_path,
        video_output_path=final_output_path
    )

    # Limpieza del lote temporal
    shutil.rmtree(run_temp_dir, ignore_errors=True)

    print(f"\n=======================================================")
    print(f" ¡SHORT GENERADO CON ÉXITO!")
    print(f" Archivo final: {os.path.abspath(final_output_path)}")
    print(f"=======================================================\n")


if __name__ == "__main__":
    # Escribe aquí la idea sobre la que quieres el Short completo
    TEMA = "¿Qué ocurriría si los océanos se secaran durante 24 horas?"
    create_youtube_short(TEMA)