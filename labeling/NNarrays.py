import numpy as np
import matplotlib.pyplot as plt

# Load the saved .npz file
npz_path = './labels/black-ice.mfcc_labels.npz'
data = np.load(npz_path)

# Extract MFCCs and labels
X = data['mfcc']       # Shape: (num_frames, 13)
y = data['labels']     # Shape: (num_frames,)

# Summary of data
print(f"✅ Loaded data from: {npz_path}")
print(f"MFCC shape: {X.shape} — {X.shape[0]} time steps, {X.shape[1]} coefficients each")
print(f"Label shape: {y.shape} — One label per time step")
print(f"Label range: {np.min(y)} to {np.max(y)}")
print(f"Unique labels: {np.unique(y)}")
print(f"First 10 MFCCs (1st coeff): {X[:10, 0]}")
print(f"First 10 Labels: {y[:10]}")

# Assume 10 FPS → 0.1s per frame
duration = X.shape[0] * 0.1
times = np.linspace(0, duration, X.shape[0])

# Plot labels + 1st MFCC coeff over time
plt.figure(figsize=(12, 6))

plt.subplot(2, 1, 1)
plt.plot(times, y, color='green')
plt.title('Pattern Labels Over Time')
plt.ylabel('Label')
plt.ylim(-0.5, max(y)+0.5)
plt.grid(True)

plt.subplot(2, 1, 2)
plt.plot(times, X[:, 0], color='blue')
plt.title('First MFCC Coefficient Over Time')
plt.ylabel('MFCC Coeff 1')
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

plot_all_mfccs(X)


# (For the neural net)
# What are n_mfcc=13 and why 13?
# MFCC stands for Mel-Frequency Cepstral Coefficients — features inspired by human hearing that capture timbral (tone color) characteristics of sound.

# n_mfcc=13 means you extract 13 coefficients per frame, which is a common standard in audio analysis (like speech recognition). 
# The first few coefficients capture the broad spectral shape, and higher ones capture finer details.

# 13 is a traditional choice because it balances capturing enough detail without too much redundancy or noise.