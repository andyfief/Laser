import numpy as np
import matplotlib.pyplot as plt

# Load the saved .npz file
npz_path = './labels/flip-it.mfcc_labels.npz'
data = np.load(npz_path)

# Extract MFCCs and both types of labels
X = data['mfcc']                 # Shape: (num_frames, 13)
pattern_labels = data['pattern_labels']  # Shape: (num_frames,)
speed_labels = data['speed_labels']      # Shape: (num_frames,)

# Summary
print(f"✅ Loaded data from: {npz_path}")
print(f"MFCC shape: {X.shape} — {X.shape[0]} time steps, {X.shape[1]} coefficients each")

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

print(f"\n🔎 First 10 MFCCs (Coeff 1): {X[:10, 0]}")

# Plotting
duration = X.shape[0] * 0.1  # Assuming 10 FPS
times = np.linspace(0, duration, X.shape[0])

plt.figure(figsize=(12, 8))

# Plot Pattern Labels
plt.subplot(3, 1, 1)
plt.plot(times, pattern_labels, color='green')
plt.title('Pattern Labels Over Time')
plt.ylabel('Pattern')
plt.ylim(-0.5, max(pattern_labels)+0.5)
plt.grid(True)

# Plot Speed Labels
plt.subplot(3, 1, 2)
plt.plot(times, speed_labels, color='red')
plt.title('Speed Labels Over Time')
plt.ylabel('Speed')
plt.ylim(-0.5, max(speed_labels)+0.5)
plt.grid(True)

# Plot MFCC Coefficient 1
plt.subplot(3, 1, 3)
plt.plot(times, X[:, 0], color='blue')
plt.title('First MFCC Coefficient Over Time')
plt.ylabel('MFCC 1')
plt.xlabel('Time (s)')
plt.grid(True)

plt.tight_layout()
plt.show()


def plot_all_mfccs(mfccs, fps=10, title="All 13 MFCC Coefficients Over Time"):
    """
    Plots all 13 MFCC coefficients in a stacked subplot layout.
    
    Args:
        mfccs (np.ndarray): Shape (num_frames, 13)
        fps (int): Frames per second of the audio labeling (default: 10)
        title (str): Plot title
    """
    num_frames, num_coeffs = mfccs.shape
    times = np.linspace(0, num_frames / fps, num_frames)

    fig, axes = plt.subplots(num_coeffs, 1, figsize=(12, 2 * num_coeffs), sharex=True)
    fig.suptitle(title, fontsize=16)

    for i in range(num_coeffs):
        axes[i].plot(times, mfccs[:, i], label=f"MFCC {i+1}")
        axes[i].set_ylabel(f"C{i+1}")
        axes[i].grid(True)
        axes[i].legend(loc="upper right")

    axes[-1].set_xlabel("Time (s)")
    plt.tight_layout(rect=[0, 0, 1, 0.97])
    plt.show()

# Call the MFCC plotter
plot_all_mfccs(X)
