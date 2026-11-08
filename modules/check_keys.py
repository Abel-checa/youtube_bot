import os
from dotenv import load_dotenv
from elevenlabs.client import ElevenLabs

# Cargar variables de .env
load_dotenv()

api_key = os.getenv("ELEVENLABS_API_KEY")
voice_id = os.getenv("ELEVENLABS_VOICE_ID")

print("--- Verificando credenciales ---")
print(f"API Key detectada: {'Sí' if api_key else 'NO (revisa el archivo .env)'}")
print(f"Voice ID detectado: {voice_id}")

if not api_key:
    exit(1)

try:
    client = ElevenLabs(api_key=api_key)
    
    # 1. Consultar estado de suscripción y caracteres restantes
    user = client.user.get()
    subscription = user.subscription
    chars_used = subscription.character_count
    chars_limit = subscription.character_limit
    print(f"\nConexión con ElevenLabs: EXITOSA")
    print(f"Plan actual: {subscription.tier}")
    print(f"Caracteres disponibles: {chars_limit - chars_used} / {chars_limit}")

    # 2. Listar las primeras 5 voces disponibles en tu cuenta
    voices_response = client.voices.get_all()
    print("\nVoces disponibles para usar:")
    for v in voices_response.voices[:5]:
        print(f" - Nombre: {v.name.ljust(15)} | ID: {v.voice_id}")

except Exception as e:
    print(f"\nError al conectar con ElevenLabs: {e}")