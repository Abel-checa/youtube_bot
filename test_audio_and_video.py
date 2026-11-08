import os
from modules.tts_engine import generate_speech
from modules.video_engine import build_scene, render_short_video

def main():
    os.makedirs("temp", exist_ok=True)
    os.makedirs("output", exist_ok=True)

    # 1. Definir texto de prueba
    texto_locucion = "¿Qué pasaría si la Tierra dejara de girar repentinamente durante solo cinco segundos?"
    
    audio_temp = "temp/escena_test_audio.mp3"
    imagen_test = "assets/test/test_image.png"
    video_output = "output/escena_test_con_voz.mp4"

    print("[1/3] Sintetizando voz con ElevenLabs...")
    generate_speech(text=texto_locucion, output_path=audio_temp)
    print(f"Audio generado con éxito: {audio_temp}")

    print("[2/3] Montando escena con efecto Ken Burns (1080x1920)...")
    clip = build_scene(image_path=imagen_test, audio_path=audio_temp)

    print("[3/3] Renderizando MP4 final con FFmpeg...")
    render_short_video([clip], video_output)
    print(f"\n¡Vídeo terminado! Compruébalo en: {video_output}")

if __name__ == "__main__":
    main()