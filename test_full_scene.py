import os
from modules.tts_engine import generate_speech
from modules.video_engine import build_scene, render_short_video
from modules.subtitle_engine import generate_ass_subtitles, burn_subtitles_to_video

def main():
    os.makedirs("temp", exist_ok=True)
    os.makedirs("output", exist_ok=True)

    texto_prueba = "¿Sabías que existe un lugar en la Tierra donde el tiempo parece haberse detenido por completo?"
    
    audio_path = "temp/test_voice.mp3"
    imagen_path = "assets/test/test_image.png"
    video_base = "temp/video_base_sin_subs.mp4"
    ass_path = "temp/subtitulos.ass"
    video_final = "output/short_completo_con_subtitulos.mp4"

    # 1. Generar audio
    print("\n--- PASO 1: VOZ CON ELEVENLABS ---")
    generate_speech(text=texto_prueba, output_path=audio_path)

    # 2. Renderizar vídeo base con la locución
    print("\n--- PASO 2: VÍDEO BASE 9:16 + KEN BURNS ---")
    clip = build_scene(image_path=imagen_path, audio_path=audio_path)
    render_short_video([clip], video_base)

    # 3. Transcribir y crear subtítulos .ass
    print("\n--- PASO 3: SUBTÍTULOS DINÁMICOS CON WHISPER ---")
    generate_ass_subtitles(audio_path=audio_path, output_ass_path=ass_path, words_per_line=3)

    # 4. Quemar subtítulos en el vídeo final
    print("\n--- PASO 4: QUEMAR SUBTÍTULOS CON FFMPEG ---")
    burn_subtitles_to_video(video_input_path=video_base, ass_path=ass_path, video_output_path=video_final)

    print(f"\n=======================================================")
    print(f" ¡ESCENA COMPLETA LISTA! Ábrelo fuera de VS Code en:")
    print(f" {os.path.abspath(video_final)}")
    print(f"=======================================================")

if __name__ == "__main__":
    main()