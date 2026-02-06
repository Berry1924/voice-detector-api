import wave
import math
import struct
import base64

filename = "test_beep.wav"
with wave.open(filename, 'w') as wav_file:
    wav_file.setnchannels(1)
    wav_file.setsampwidth(2)
    wav_file.setframerate(44100)
    for i in range(44100):
        value = int(32767.0 * math.sin(i * math.pi / 10.0))
        data = struct.pack('<h', value)
        wav_file.writeframesraw(data)

print(f"✅ Created small audio file: {filename}")

with open(filename, "rb") as audio_file:
    encoded_string = base64.b64encode(audio_file.read()).decode('utf-8')

with open("new_audio.txt", "w") as text_file:
    text_file.write(encoded_string)

print("✅ Converted to Base64.")
