import os
from dotenv import load_dotenv
from elevenlabs.client import ElevenLabs

load_dotenv()

API_KEY = os.getenv("ELEVENLABS_API_KEY")
DEFAULT_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "JBFqnCBsd6RMkjVDRZzb")

client = ElevenLabs(api_key=API_KEY) if API_KEY else None


def generate_speech(
    text: str,
    output_path: str,
    voice_id: str = DEFAULT_VOICE_ID,
    model_id: str = "eleven_multilingual_v2"
) -> str:
    """
    Sintetiza texto a voz usando ElevenLabs y guarda el archivo en formato MP3.
    """
    if not API_KEY:
        raise ValueError("No se encontró ELEVENLABS_API_KEY en las variables de entorno.")

    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)

    # Conversión TTS
    audio_stream = client.text_to_speech.convert(
        voice_id=voice_id,
        text=text,
        model_id=model_id,
        output_format="mp3_44100_128"
    )

    with open(output_path, "wb") as f:
        for chunk in audio_stream:
            if chunk:
                f.write(chunk)

    return output_path