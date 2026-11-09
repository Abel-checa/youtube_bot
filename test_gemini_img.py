import os
from modules.image_generator import generate_scene_image

os.makedirs("temp", exist_ok=True)
test_output = "temp/test_gemini_short.jpg"

prompt = "A glowing mysterious ancient temple submerged under deep ocean water, bioluminescent sea life"

generate_scene_image(prompt=prompt, output_path=test_output)
print(f"Comprueba la imagen en: {test_output}")