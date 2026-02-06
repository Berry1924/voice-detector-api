import os
import time
from yt_dlp import YoutubeDL
from pydub import AudioSegment

# --- CONFIGURATION ---
OUTPUT_FOLDER = "human_dataset"
CLIPS_PER_LANG = 15
CLIP_DURATION_MS = 35 * 1000  # 35 seconds (Buffer to be safe >30s)

# --- SOURCES (Verified News Channels - Real Human Speech) ---
# We use long videos or live streams to get enough audio
SOURCES = {
    "ta": "https://www.youtube.com/watch?v=B8c-4qkSUg4", # Tamil (Polimer News)
    "en": "https://www.youtube.com/watch?v=htv-C6r-LHQ", # English (BBC)
    "hi": "https://www.youtube.com/watch?v=Nq2wYlWFucg", # Hindi (Aaj Tak)
    "ml": "https://www.youtube.com/watch?v=IdejM6wCvxA", # Malayalam (Asianet)
    "te": "https://www.youtube.com/watch?v=hWyj_tC0sIM"  # Telugu (TV9)
}

def harvest_voices():
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)
    print(f"🚀 Starting HUMAN Voice Harvest...")

    for lang, url in SOURCES.items():
        print(f"\n🔵 Processing {lang.upper()} from YouTube...")
        
        # 1. Download Audio from YouTube
        temp_filename = f"temp_{lang}"
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': temp_filename,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'quiet': True
        }

        try:
            with YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            
            # 2. Load the long audio file
            # yt-dlp adds the extension, usually .mp3
            audio_path = f"{temp_filename}.mp3"
            if not os.path.exists(audio_path):
                # sometimes it might save differently, check current dir
                for f in os.listdir("."):
                    if f.startswith(temp_filename):
                        audio_path = f
                        break
            
            print(f"   ↳ Downloaded. Now chopping into {CLIPS_PER_LANG} parts...")
            full_audio = AudioSegment.from_mp3(audio_path)

            # 3. Chop into 15 files
            for i in range(CLIPS_PER_LANG):
                start_time = i * CLIP_DURATION_MS
                end_time = start_time + CLIP_DURATION_MS
                
                # Check if we have enough audio left
                if len(full_audio) < end_time:
                    print("   ⚠️ Video too short for all clips. Using what we have.")
                    break

                chunk = full_audio[start_time:end_time]
                
                # Save final file
                final_name = f"{lang}_human_{i+1:02d}.mp3"
                final_path = os.path.join(OUTPUT_FOLDER, final_name)
                
                # Export with high bitrate to ensure >200KB
                chunk.export(final_path, format="mp3", bitrate="192k")
                
                # Verify size
                size_kb = os.path.getsize(final_path) / 1024
                print(f"   ✅ Saved: {final_name} | {size_kb:.0f} KB | 35.0s")

            # Cleanup temp file
            os.remove(audio_path)

        except Exception as e:
            print(f"❌ Error harvesting {lang}: {e}")

    print(f"\n🏆 HUMAN HARVEST COMPLETE.")
    print(f"📂 Check folder: {OUTPUT_FOLDER}")

if __name__ == "__main__":
    harvest_voices()
