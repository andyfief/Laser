import numpy as np
import librosa
import matplotlib.pyplot as plt

# Load label data
labelData = np.load('where-the-wild-things-are.labels.npy')
print("Label data shape:", labelData.shape)

# Load audio
y, sr = librosa.load("where-the-wild-things-are.wav", sr=22050)

# Hop length to get ~10 FPS
hop_length = int(sr / 10)

# Extract MFCC features
mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13, hop_length=hop_length)
X = mfcc.T
print("MFCC shape:", X.shape)  # (num_frames, 13)

# Time vectors for plotting
duration = len(y) / sr
times_labels = np.linspace(0, duration, len(labelData))
times_mfcc = np.linspace(0, duration, X.shape[0])

plt.figure(figsize=(12, 6))

# Plot labels
plt.subplot(2,1,1)
plt.plot(times_labels, labelData, label='Labels', color='green')
plt.title('Label Data Over Time')
plt.ylabel('Label Value')
plt.ylim(-0.5, 9.5)
plt.grid(True)

# Plot first MFCC coefficient over time
plt.subplot(2,1,2)
plt.plot(times_mfcc, X[:,0], label='MFCC Coeff 1', color='blue')
plt.title('First MFCC Coefficient Over Time')
plt.ylabel('MFCC Value')
plt.xlabel('Time (s)')
plt.grid(True)

plt.tight_layout()
plt.show()


# (For the neural net)
# What are n_mfcc=13 and why 13?
# MFCC stands for Mel-Frequency Cepstral Coefficients — features inspired by human hearing that capture timbral (tone color) characteristics of sound.

# n_mfcc=13 means you extract 13 coefficients per frame, which is a common standard in audio analysis (like speech recognition). 
# The first few coefficients capture the broad spectral shape, and higher ones capture finer details.

# 13 is a traditional choice because it balances capturing enough detail without too much redundancy or noise.