import subprocess
import imageio_ffmpeg

ffmpeg_bin = imageio_ffmpeg.get_ffmpeg_exe()
audio_file = "temp/escena_test_audio.mp3"
video_file = "output/escena_test_con_voz.mp4"

print("--- 1. PROBANDO AUDIO ORIGINAL ---")
cmd_audio = [ffmpeg_bin, "-i", audio_file]
res1 = subprocess.run(cmd_audio, capture_output=True, text=True)
for line in res1.stderr.splitlines():
    if "Audio:" in line or "Duration:" in line:
        print(line.strip())

print("\n--- 2. PROBANDO VÍDEO FINAL ---")
cmd_video = [ffmpeg_bin, "-i", video_file]
res2 = subprocess.run(cmd_video, capture_output=True, text=True)
streams = [line.strip() for line in res2.stderr.splitlines() if "Stream #" in line or "Duration:" in line]
for s in streams:
    print(s)