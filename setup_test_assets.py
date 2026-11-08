import numpy as np
from PIL import Image, ImageDraw
import wave
import struct
import os

os.makedirs("assets/test", exist_ok=True)

# 1. Crear imagen de prueba (1080x1920 con un gradiente/patrón)
img = Image.new("RGB", (1080, 1920), color=(25, 25, 40))
draw = ImageDraw.Draw(img)
draw.rectangle([(100, 700), (980, 1220)], fill=(70, 130, 180), outline=(255, 255, 255), width=8)
draw.text((250, 930), "TEST SHORT SCENE 1", fill=(255, 255, 255))
img.save("assets/test/test_image.png")
print("Imagen generada: assets/test/test_image.png")

# 2. Crear un archivo .wav de audio silencioso/tono de 4 segundos
sample_rate = 44100
duration = 4.0  # segundos
freq = 440.0   # Tono La (440Hz)
t = np.linspace(0, duration, int(sample_rate * duration), False)
tone = np.sin(freq * t * 2 * np.pi) * 0.1  # volumen bajo
audio_data = (tone * 32767).astype(np.int16)

with wave.open("assets/test/test_audio.wav", "w") as wav_file:
    wav_file.setnchannels(1)
    wav_file.setsampwidth(2)
    wav_file.setframerate(sample_rate)
    wav_file.writeframes(audio_data.tobytes())
print("Audio generado: assets/test/test_audio.wav")