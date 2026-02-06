import wave
import math
import struct
import base64

# 1. Create a dummy 1-second audio file (sine wave beep)
filename = "test_beep.wav"
with wave.open(filename, 'w') as wav_file:
    # Settings: 1 channel, 2 bytes per sample, 44100Hz sample rate
    wav_file.setnchannels(1)
    wav_file.setsampwidth(2)
    wav_file.setframerate(44100)
    
    # Write 1 second of audio
    for i in range(44100):
        # Generate a simple sine wave tone
        value = int(32767.0 * math.sin(i * math.pi / 10.0))
        data = struct.pack('<h', value)
        wav_file.writeframesraw(data)

print(f"✅ Created small audio file: {filename}")

# 2. Convert it to Base64
with open(filename, "rb") as audio_file:
    encoded_string = base64.b64encode(audio_file.read()).decode('utf-8')

# 3. Save the clean Base64 string to a new text file
with open("new_audio.txt", "w") as text_file:
    text_file.write(encoded_string)

print("✅ Converted to Base64.") 
print("👉 ACTION: Open 'new_audio.txt', copy everything, and paste it into your tester!")
