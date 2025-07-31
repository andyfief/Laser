import subprocess
import json
import re
from pathlib import Path

def main():
    playlist_url = "https://www.youtube.com/playlist?list=PL7023U8m5rNNDlFu7PvK7DAjeCEuUUaaM"
    output_dir = Path("playlist_wavs")
    output_dir.mkdir(exist_ok=True)
    
    # Get playlist info
    result = subprocess.run(['yt-dlp', '--dump-json', '--flat-playlist', playlist_url], 
                          capture_output=True, text=True, check=True)
    
    videos = []
    for line in result.stdout.strip().split('\n'):
        if line:
            videos.append(json.loads(line))
    
    print(f"Found {len(videos)} videos")
    
    # Check existing files and download missing ones
    for i, video in enumerate(videos, 1):
        title = re.sub(r'[<>:"/\\|?*]', '', video.get('title', 'Unknown')).strip()
        expected_file = output_dir / f"{i:02d}_{title}.wav"
        
        # Check if any file with this index exists
        existing = list(output_dir.glob(f"{i:02d}_*.wav"))
        
        if existing:
            print(f"Skipping {i:02d}: {title} (already exists)")
            continue
            
        print(f"Downloading {i:02d}: {title}")
        video_url = f"https://www.youtube.com/watch?v={video['id']}"
        
        subprocess.run([
            'yt-dlp', '--extract-audio', '--audio-format', 'wav', '--audio-quality', '0',
            '--output', str(output_dir / f'{i:02d}_%(title)s.%(ext)s'),
            '--no-warnings', video_url
        ])
    
    # Show final results
    wav_files = list(output_dir.glob("*.wav"))
    print(f"\nCompleted! {len(wav_files)} WAV files in {output_dir.absolute()}")

if __name__ == "__main__":
    main()