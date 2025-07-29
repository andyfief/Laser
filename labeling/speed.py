""" An Expertimental auto-speed labeler using mfccs and spectral flux. Labels based on energy."""

import numpy as np
import matplotlib.pyplot as plt
import librosa
import sounddevice as sd
from matplotlib.animation import FuncAnimation
import time
import threading
from scipy.signal import find_peaks

# ==== CONFIG ====
audio_path = "./wavs/where-the-wild-things-are.wav"
hop_length = 512
num_levels = 10  # 0-9 speed levels

# New chunk-based parameters
min_chunk_duration_sec = 3.0     # Minimum chunk duration in seconds
rolling_window_sec = 3.0         # Rolling average window in seconds

# Adaptive prominence thresholds for different spectral centroid regions
low_brightness_prominence = 0.05     # High sensitivity for dark/mellow sections
high_brightness_prominence = 0.15    # Lower sensitivity for bright/energetic sections
brightness_threshold = 0.4           # Threshold to separate low/high brightness regions

# ==== LOAD AUDIO ====
print("Loading audio...")
y, sr = librosa.load(audio_path)
print(f"Audio loaded: {len(y)} samples at {sr} Hz ({len(y)/sr:.2f} seconds)")

# ==== EXTRACT SPECTRAL CENTROID (BRIGHTNESS) ====
print("Extracting spectral centroid (brightness)...")
spectral_centroid = librosa.feature.spectral_centroid(y=y, sr=sr, hop_length=hop_length)[0]
frame_rate = sr / hop_length
print(f"Spectral centroid frames: {len(spectral_centroid)} at {frame_rate:.1f} fps")

# Convert time parameters to frames
min_chunk_frames = int(min_chunk_duration_sec * frame_rate)
rolling_window_frames = int(rolling_window_sec * frame_rate)

print(f"Min chunk duration: {min_chunk_duration_sec}s ({min_chunk_frames} frames)")
print(f"Rolling window: {rolling_window_sec}s ({rolling_window_frames} frames)")

# ==== APPLY ROLLING AVERAGE FOR SMOOTH SPECTRAL CURVE ====
print("Creating smooth spectral centroid curve with rolling average...")
# Pad spectral_centroid for proper convolution
pad_size = rolling_window_frames // 2
padded_centroid = np.pad(spectral_centroid, (pad_size, pad_size), mode='edge')
smoothed_centroid = np.convolve(padded_centroid, np.ones(rolling_window_frames) / rolling_window_frames, mode='valid')

# Ensure same length as original
smoothed_centroid = smoothed_centroid[:len(spectral_centroid)]

print(f"Spectral centroid smoothed with {rolling_window_frames}-frame rolling average")
print(f"Centroid range: {np.min(smoothed_centroid):.0f} - {np.max(smoothed_centroid):.0f} Hz")

# ==== DETECT PEAKS AND VALLEYS WITH ADAPTIVE SENSITIVITY ====
print("Detecting peaks and valleys with adaptive sensitivity based on brightness...")

# Normalize spectral centroid for peak detection
norm_centroid = (smoothed_centroid - np.min(smoothed_centroid)) / (np.max(smoothed_centroid) - np.min(smoothed_centroid) + 1e-9)

# Identify low-brightness and high-brightness regions
low_brightness_mask = norm_centroid < brightness_threshold
high_brightness_mask = norm_centroid >= brightness_threshold

print(f"Brightness regions: {np.sum(low_brightness_mask)} dark/mellow frames, {np.sum(high_brightness_mask)} bright/energetic frames")
print(f"Low-brightness threshold: {brightness_threshold} (prominence: {low_brightness_prominence})")
print(f"High-brightness threshold: {brightness_threshold} (prominence: {high_brightness_prominence})")

# Find peaks and valleys separately for each brightness region
all_peaks = []
all_valleys = []

# Detect in low-brightness regions with high sensitivity
if np.any(low_brightness_mask):
    # Find peaks in low-brightness regions
    low_peaks, _ = find_peaks(
        norm_centroid,
        prominence=low_brightness_prominence,
        distance=min_chunk_frames//4  # Allow closer peaks in mellow sections
    )
    
    # Filter peaks to only those in low-brightness regions
    low_peaks = low_peaks[low_brightness_mask[low_peaks]]
    all_peaks.extend(low_peaks)
    
    # Find valleys in low-brightness regions
    low_valleys, _ = find_peaks(
        -norm_centroid,
        prominence=low_brightness_prominence,
        distance=min_chunk_frames//4
    )
    
    # Filter valleys to only those in low-brightness regions
    low_valleys = low_valleys[low_brightness_mask[low_valleys]]
    all_valleys.extend(low_valleys)
    
    print(f"Low-brightness regions: {len(low_peaks)} peaks, {len(low_valleys)} valleys")

# Detect in high-brightness regions with lower sensitivity
if np.any(high_brightness_mask):
    # Find peaks in high-brightness regions
    high_peaks, _ = find_peaks(
        norm_centroid,
        prominence=high_brightness_prominence,
        distance=min_chunk_frames//2  # Standard distance for bright sections
    )
    
    # Filter peaks to only those in high-brightness regions
    high_peaks = high_peaks[high_brightness_mask[high_peaks]]
    all_peaks.extend(high_peaks)
    
    # Find valleys in high-brightness regions
    high_valleys, _ = find_peaks(
        -norm_centroid,
        prominence=high_brightness_prominence,
        distance=min_chunk_frames//2
    )
    
    # Filter valleys to only those in high-brightness regions
    high_valleys = high_valleys[high_brightness_mask[high_valleys]]
    all_valleys.extend(high_valleys)
    
    print(f"High-brightness regions: {len(high_peaks)} peaks, {len(high_valleys)} valleys")

# Convert to numpy arrays and combine
peaks = np.array(all_peaks) if all_peaks else np.array([])
valleys = np.array(all_valleys) if all_valleys else np.array([])

# Combine and sort all boundaries
all_boundaries = np.concatenate([peaks, valleys]) if len(peaks) > 0 or len(valleys) > 0 else np.array([])
all_boundaries = np.unique(np.sort(all_boundaries))

print(f"Total adaptive boundaries found: {len(all_boundaries)}")
print(f"Total peaks: {len(peaks)}, Total valleys: {len(valleys)}")

# ==== CREATE CHUNKS WITH MINIMUM DURATION ====
print("Creating chunks with minimum duration enforcement...")

# Start with boundaries and enforce minimum chunk size
chunk_boundaries = [0]  # Always start with first frame

for boundary in all_boundaries:
    # Only add boundary if it creates a chunk >= minimum size
    if boundary - chunk_boundaries[-1] >= min_chunk_frames:
        chunk_boundaries.append(boundary)

# Always end with last frame
if chunk_boundaries[-1] != len(spectral_centroid) - 1:
    chunk_boundaries.append(len(spectral_centroid) - 1)

chunk_boundaries = np.array(chunk_boundaries)
num_chunks = len(chunk_boundaries) - 1

print(f"Created {num_chunks} chunks after enforcing minimum duration")

# ==== ASSIGN SPEED LEVELS TO CHUNKS ====
print("Assigning speed levels based on spectral brightness...")

# Calculate mean spectral centroid for each chunk
chunk_brightness = []
chunk_speeds = np.zeros(len(spectral_centroid), dtype=int)

for i in range(num_chunks):
    start_idx = chunk_boundaries[i]
    end_idx = chunk_boundaries[i + 1]
    
    # Calculate mean spectral centroid for this chunk
    chunk_mean_brightness = np.mean(smoothed_centroid[start_idx:end_idx])
    chunk_brightness.append(chunk_mean_brightness)

# Normalize chunk brightness to use full 0-9 range
chunk_brightness = np.array(chunk_brightness)
min_chunk_brightness = np.min(chunk_brightness)
max_chunk_brightness = np.max(chunk_brightness)

print(f"Chunk brightness range: {min_chunk_brightness:.0f} - {max_chunk_brightness:.0f} Hz")

# Map to 0-9 speed levels using full dynamic range
normalized_chunk_brightness = (chunk_brightness - min_chunk_brightness) / (max_chunk_brightness - min_chunk_brightness + 1e-9)
chunk_speed_levels = np.round(normalized_chunk_brightness * (num_levels - 1)).astype(int)

# Assign speed levels to all frames in each chunk
for i in range(num_chunks):
    start_idx = chunk_boundaries[i]
    end_idx = chunk_boundaries[i + 1]
    chunk_speeds[start_idx:end_idx] = chunk_speed_levels[i]

print(f"Speed levels assigned: min={np.min(chunk_speed_levels)}, max={np.max(chunk_speed_levels)}")

# ==== UPSAMPLE SPEED TO AUDIO TIMELINE ====
print("Upsampling speed to audio timeline...")
frame_times = librosa.frames_to_time(np.arange(len(chunk_speeds)), sr=sr, hop_length=hop_length)
audio_times = np.arange(len(y)) / sr
upsampled_speed = np.interp(audio_times, frame_times, chunk_speeds)

# ==== SAVE RESULTS ====
print("Saving results...")
np.save('./labels/speed_levels_spectral_chunks.npy', chunk_speeds)
np.save('./labels/speed_levels_spectral_upsampled.npy', upsampled_speed)
np.save('./labels/chunk_boundaries_spectral.npy', chunk_boundaries)
np.save('./labels/spectral_centroid_raw.npy', spectral_centroid)
np.save('./labels/spectral_centroid_smoothed.npy', smoothed_centroid)

# ==== PLOTTING AND PLAYBACK ====
print("Setting up visualization...")

# Prepare plot data
decim_factor = len(y) // len(frame_times)
if decim_factor > 1:
    y_plot = y[::decim_factor][:len(frame_times)]
else:
    y_plot = y[:len(frame_times)]

y_plot_norm = y_plot / np.max(np.abs(y_plot)) if np.max(np.abs(y_plot)) > 0 else y_plot

# Create figure with four panels
fig, (ax1, ax2, ax3, ax4) = plt.subplots(4, 1, figsize=(14, 12), sharex=True)

# Plot 1: Waveform and spectral centroid with adaptive boundaries
ax1.plot(frame_times, y_plot_norm, alpha=0.4, color='lightblue', linewidth=0.5, label="Waveform")
ax1.plot(frame_times, norm_centroid, color='orange', linewidth=2, label="Normalized Spectral Centroid")

# Mark brightness threshold line
ax1.axhline(y=brightness_threshold, color='purple', linestyle=':', alpha=0.7, label=f'Brightness Threshold ({brightness_threshold})')

# Mark adaptive peaks and valleys with different colors
if len(peaks) > 0:
    # Color peaks based on brightness level
    low_brightness_peaks = peaks[norm_centroid[peaks] < brightness_threshold]
    high_brightness_peaks = peaks[norm_centroid[peaks] >= brightness_threshold]
    
    if len(low_brightness_peaks) > 0:
        ax1.scatter(frame_times[low_brightness_peaks], norm_centroid[low_brightness_peaks], 
                   color='darkred', s=60, marker='^', zorder=5, label='Dark/Mellow Peaks')
    if len(high_brightness_peaks) > 0:
        ax1.scatter(frame_times[high_brightness_peaks], norm_centroid[high_brightness_peaks], 
                   color='red', s=60, marker='^', zorder=5, label='Bright/Energetic Peaks')

if len(valleys) > 0:
    # Color valleys based on brightness level
    low_brightness_valleys = valleys[norm_centroid[valleys] < brightness_threshold]
    high_brightness_valleys = valleys[norm_centroid[valleys] >= brightness_threshold]
    
    if len(low_brightness_valleys) > 0:
        ax1.scatter(frame_times[low_brightness_valleys], norm_centroid[low_brightness_valleys], 
                   color='darkblue', s=60, marker='v', zorder=5, label='Dark/Mellow Valleys')
    if len(high_brightness_valleys) > 0:
        ax1.scatter(frame_times[high_brightness_valleys], norm_centroid[high_brightness_valleys], 
                   color='blue', s=60, marker='v', zorder=5, label='Bright/Energetic Valleys')

ax1.set_ylabel("Amplitude / Brightness")
ax1.legend()
ax1.grid(True, alpha=0.3)
ax1.set_title("Spectral Centroid-Based Peak/Valley Detection (Perceptual Brightness)")

# Plot 2: Raw vs smoothed spectral centroid
ax2.plot(frame_times, spectral_centroid, alpha=0.5, color='gray', linewidth=1, label="Raw Spectral Centroid")
ax2.plot(frame_times, smoothed_centroid, color='orange', linewidth=2, label="Smoothed Spectral Centroid")
ax2.set_ylabel("Frequency (Hz)")
ax2.legend()
ax2.grid(True, alpha=0.3)
ax2.set_title("Raw vs Smoothed Spectral Centroid")

# Plot 3: Chunk boundaries
ax3.plot(frame_times, norm_centroid, color='orange', linewidth=2, alpha=0.7)
# Draw vertical lines at chunk boundaries
for boundary in chunk_boundaries:
    if boundary < len(frame_times):
        ax3.axvline(frame_times[boundary], color='green', linestyle='--', alpha=0.8)
ax3.set_ylabel("Brightness")
ax3.set_title(f"Chunk Boundaries (Min Duration: {min_chunk_duration_sec}s, Based on Spectral Changes)")
ax3.grid(True, alpha=0.3)

# Plot 4: Final speed levels
ax4.step(frame_times, chunk_speeds, where='mid', color='red', linewidth=3, label="Speed Levels")
ax4.fill_between(frame_times, 0, chunk_speeds, step='mid', alpha=0.3, color='red')
ax4.set_ylabel("Speed Level")
ax4.set_xlabel("Time (s)")
ax4.set_ylim(-0.5, num_levels - 0.5)
ax4.legend()
ax4.grid(True, alpha=0.3)
ax4.set_title("Final Speed Levels (Spectral Brightness-Based)")

plt.tight_layout()

# Add playback markers
marker_lines = []
for ax in [ax1, ax2, ax3, ax4]:
    marker_line = ax.axvline(0, color='black', linewidth=2, label='Playback Position')
    marker_lines.append(marker_line)

# ==== PLAYBACK CONTROL ====
class AudioPlayer:
    def __init__(self, audio, sample_rate):
        self.audio = audio
        self.sr = sample_rate
        self.start_time = None
        self.is_playing = False
        self.duration = len(audio) / sample_rate
    
    def start_playback(self):
        self.start_time = time.time()
        self.is_playing = True
        
        def play_audio():
            sd.play(self.audio, self.sr)
            
        audio_thread = threading.Thread(target=play_audio)
        audio_thread.daemon = True
        audio_thread.start()
    
    def get_current_time(self):
        if self.start_time is None:
            return 0
        elapsed = time.time() - self.start_time
        return min(elapsed, self.duration)
    
    def stop(self):
        self.is_playing = False
        sd.stop()

player = AudioPlayer(y, sr)

def update_visualization(frame):
    if player.is_playing:
        current_time = player.get_current_time()
        for marker_line in marker_lines:
            marker_line.set_xdata([current_time, current_time])
        
        if current_time >= player.duration:
            player.is_playing = False
    
    return marker_lines

def start_visualization():
    print("Starting playback and visualization...")
    print("Close the plot window to stop.")
    
    player.start_playback()
    ani = FuncAnimation(fig, update_visualization, interval=50, blit=False, repeat=False)
    plt.show()
    player.stop()

# ==== ANALYSIS FUNCTIONS ====
def analyze_chunks():
    """Analyze the chunk-based speed assignment"""
    print(f"\nSpectral Centroid Chunk Analysis:")
    print(f"Number of chunks: {num_chunks}")
    
    chunk_durations = []
    for i in range(num_chunks):
        duration_frames = chunk_boundaries[i + 1] - chunk_boundaries[i]
        duration_sec = duration_frames / frame_rate
        chunk_durations.append(duration_sec)
        
        start_time = chunk_boundaries[i] / frame_rate
        end_time = chunk_boundaries[i + 1] / frame_rate
        speed = chunk_speed_levels[i]
        brightness = chunk_brightness[i]
        
        print(f"Chunk {i+1}: {start_time:.1f}-{end_time:.1f}s ({duration_sec:.1f}s) → Speed {speed} (Brightness: {brightness:.0f} Hz)")
    
    print(f"\nChunk duration stats:")
    print(f"Average: {np.mean(chunk_durations):.1f}s")
    print(f"Min: {np.min(chunk_durations):.1f}s")
    print(f"Max: {np.max(chunk_durations):.1f}s")

def analyze_speed_distribution():
    """Analyze the distribution of speed levels"""
    unique, counts = np.unique(chunk_speed_levels, return_counts=True)
    print(f"\nSpeed Level Distribution (across {num_chunks} chunks):")
    for level, count in zip(unique, counts):
        percentage = count / len(chunk_speed_levels) * 100
        print(f"Level {level}: {count} chunks ({percentage:.1f}%)")

def analyze_spectral_characteristics():
    """Analyze spectral centroid characteristics"""
    print(f"\nSpectral Centroid Analysis:")
    print(f"Raw centroid range: {np.min(spectral_centroid):.0f} - {np.max(spectral_centroid):.0f} Hz")
    print(f"Smoothed centroid range: {np.min(smoothed_centroid):.0f} - {np.max(smoothed_centroid):.0f} Hz")
    print(f"Mean brightness: {np.mean(smoothed_centroid):.0f} Hz")
    
    # Analyze brightness distribution
    low_brightness_frames = np.sum(norm_centroid < brightness_threshold)
    high_brightness_frames = np.sum(norm_centroid >= brightness_threshold)
    
    print(f"Brightness distribution:")
    print(f"Dark/mellow regions: {low_brightness_frames} frames ({low_brightness_frames/len(norm_centroid)*100:.1f}%)")
    print(f"Bright/energetic regions: {high_brightness_frames} frames ({high_brightness_frames/len(norm_centroid)*100:.1f}%)")

def get_speed_at_time(time_sec):
    """Get the speed level at a specific time"""
    frame_idx = int(time_sec * frame_rate)
    if 0 <= frame_idx < len(chunk_speeds):
        return chunk_speeds[frame_idx]
    return None

# ==== MAIN EXECUTION ====
if __name__ == "__main__":
    print("\n" + "="*70)
    print("SPECTRAL CENTROID-BASED SPEED DETECTION SYSTEM")
    print("="*70)
    
    analyze_chunks()
    analyze_speed_distribution()
    analyze_spectral_characteristics()
    
    print(f"\nConfiguration:")
    print(f"Audio duration: {len(y)/sr:.2f} seconds")
    print(f"Frame rate: {frame_rate:.1f} fps")
    print(f"Min chunk duration: {min_chunk_duration_sec}s")
    print(f"Rolling window: {rolling_window_sec}s")
    print(f"Brightness threshold: {brightness_threshold}")
    print(f"Low-brightness prominence: {low_brightness_prominence}")
    print(f"High-brightness prominence: {high_brightness_prominence}")
    print(f"Speed levels range: 0 to {num_levels-1}")
    
    print(f"\nAdaptive Boundary Detection:")
    low_brightness_peaks = len([p for p in peaks if norm_centroid[p] < brightness_threshold]) if len(peaks) > 0 else 0
    high_brightness_peaks = len([p for p in peaks if norm_centroid[p] >= brightness_threshold]) if len(peaks) > 0 else 0
    low_brightness_valleys = len([v for v in valleys if norm_centroid[v] < brightness_threshold]) if len(valleys) > 0 else 0
    high_brightness_valleys = len([v for v in valleys if norm_centroid[v] >= brightness_threshold]) if len(valleys) > 0 else 0
    
    print(f"Dark/mellow peaks: {low_brightness_peaks}, valleys: {low_brightness_valleys}")
    print(f"Bright/energetic peaks: {high_brightness_peaks}, valleys: {high_brightness_valleys}")
    print(f"Final chunks: {num_chunks}")
    
    # Test speed lookup
    test_times = [0, len(y)/sr/4, len(y)/sr/2, 3*len(y)/sr/4]
    print(f"\nSpeed levels at different times:")
    for t in test_times:
        speed = get_speed_at_time(t)
        print(f"Time {t:.1f}s: Speed level {speed}")
    
    print(f"\nStarting visualization...")
    print("Four panels show:")
    print("1. Waveform + spectral centroid + detected peaks/valleys")
    print("2. Raw vs smoothed spectral centroid")
    print("3. Spectral centroid + chunk boundaries")
    print("4. Final flat speed plateaus")
    print("\nSpeed now represents perceptual brightness:")
    print("0-3: Dark/mellow sounds (bass, pads, quiet sections)")
    print("4-6: Medium brightness")
    print("7-9: Bright/energetic sounds (leads, hi-hats, energetic sections)")
    
    start_visualization()