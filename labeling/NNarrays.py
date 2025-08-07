import numpy as np
import matplotlib.pyplot as plt

# Load the saved .npz file
npz_path = './app/labels/04_Chase & Status and Stormzy - BACKBONE (Lyric Video).labels.npz'
data = np.load(npz_path)

waveform = data['waveform']
sr = data['sample_rate']
pattern_labels = data['pattern_labels']
speed_labels = data['speed_labels']

# Summary
print(f"✅ Loaded data from: {npz_path}")
print(f"Waveform shape: {waveform.shape}")
print(f"Sample rate: {sr}")

print(f"\n🔷 Pattern Labels:")
print(f"  Shape: {pattern_labels.shape}")
print(f"  Range: {np.min(pattern_labels)} to {np.max(pattern_labels)}")
print(f"  Unique values: {np.unique(pattern_labels)}")
print(f"  First 10: {pattern_labels[:10]}")

print(f"\n🔶 Speed Labels:")
print(f"  Shape: {speed_labels.shape}")
print(f"  Range: {np.min(speed_labels)} to {np.max(speed_labels)}")
print(f"  Unique values: {np.unique(speed_labels)}")
print(f"  First 10: {speed_labels[:10]}")

# Plotting
label_fps = 10  # Assuming labels are at 10 FPS
num_label_frames = pattern_labels.shape[0]
label_times = np.linspace(0, num_label_frames / label_fps, num_label_frames)


step = max(1, len(waveform) // 2000)
downsampled_waveform = waveform[::step]
waveform_times = np.linspace(0, len(waveform) / sr, len(downsampled_waveform))

plt.figure(figsize=(12, 8))

# Plot Pattern Labels
plt.subplot(3, 1, 1)
plt.plot(label_times, pattern_labels, color='green')
plt.title('Pattern Labels Over Time')
plt.ylabel('Pattern')
plt.ylim(-0.5, max(pattern_labels) + 0.5)
plt.grid(True)

# Plot Speed Labels
plt.subplot(3, 1, 2)
plt.plot(label_times, speed_labels, color='red')
plt.title('Speed Labels Over Time')
plt.ylabel('Speed')
plt.ylim(-0.5, max(speed_labels) + 0.5)
plt.grid(True)

# Plot Waveform
plt.subplot(3, 1, 3)
plt.plot(waveform_times, downsampled_waveform, color='blue')
plt.title('Waveform')
plt.ylabel('Amplitude')
plt.xlabel('Time (s)')
plt.grid(True)

plt.tight_layout()
plt.show()
