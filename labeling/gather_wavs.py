import subprocess
import json
import re
from pathlib import Path

def sanitize_filename(name):
    return re.sub(r'[<>:"/\\|?*]', '', name).strip()

def main():
    playlist_url = "https://www.youtube.com/playlist?list=PL7023U8m5rNNDlFu7PvK7DAjeCEuUUaaM"
    output_dir = Path("playlist_wavs")
    output_dir.mkdir(exist_ok=True)

    # Get playlist info
    print("📥 Fetching playlist metadata...")
    result = subprocess.run(
        ['yt-dlp', '--dump-json', '--flat-playlist', playlist_url], 
        capture_output=True, text=True, check=True
    )

    videos = [json.loads(line) for line in result.stdout.strip().split('\n') if line]
    print(f"✅ Found {len(videos)} videos in playlist")

    for video in videos:
        title = sanitize_filename(video.get('title', 'Unknown'))
        expected_file = output_dir / f"{title}.wav"

        if expected_file.exists():
            print(f"⏭️  Skipping: {title} (already downloaded)")
            continue

        print(f"🎵 Downloading: {title}")
        video_url = f"https://www.youtube.com/watch?v={video['id']}"

        subprocess.run([
            'yt-dlp', '--extract-audio', '--audio-format', 'wav', '--audio-quality', '0',
            '--output', str(output_dir / f'{title}.%(ext)s'),
            '--no-warnings', video_url
        ], check=True)

    # Final output
    wav_files = list(output_dir.glob("*.wav"))
    print(f"\n🎉 Completed! {len(wav_files)} WAV files in {output_dir.resolve()}")

if __name__ == "__main__":
    main()
