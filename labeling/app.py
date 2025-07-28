import numpy as np
import matplotlib.pyplot as plt
import librosa
import sounddevice as sd
import threading
import time
from pathlib import Path

class SimpleSongLabeler:
    def __init__(self, audio_file_path, labelType, labels_per_second=10):

        self.labelType = labelType

        print("Loading audio...")
        # Load audio
        self.y, self.sr = librosa.load(audio_file_path)
        self.duration = len(self.y) / self.sr # length of array sampled / sample rate (sr in seconds) = length in seconds
        self.audio_file = audio_file_path
        print(f"Number of samples: {len(self.y)}")
        
        # Simple low-res labeling
        self.labels_per_second = labels_per_second # Frames per second
        self.n_labels = int(self.duration * labels_per_second)
        self.labels = np.zeros(self.n_labels, dtype=int)  # valid labels: 0–9
        
        # Playback state
        self.is_playing = False
        self.position = 0.0
        self.current_label = 0 # defaults to use label 0 when song starts
        
        # Simple plot setup
        self.setup_plot()
        print(f"Ready! {self.duration:.1f}s audio, {self.n_labels} labels")
        if self.labelType == 1:
            print("SPACE: play/pause, 0-9: set label, Click: seek, ESC: save, Q: quit")
        elif self.labelType == 2:
            print("SPACE: play/pause, 0-3: set label, Click: seek, ESC: save, Q: quit")

    
    def setup_plot(self):
        """Minimal plot setup for performance"""
        self.fig, (self.ax1, self.ax2) = plt.subplots(2, 1, figsize=(12, 6))
        
        # Downsample waveform display aggressively
        step = max(1, len(self.y) // 2000)  # Max 2000 points
        times = np.linspace(0, self.duration, len(self.y[::step]))
        
        if(self.labelType == 1):
            labelTypeStr = "Speed"
        elif(self.labelType == 2):
            labelTypeStr = "Patterns"

        # Static waveform
        self.ax1.plot(times, self.y[::step], 'b-', alpha=0.6, linewidth=0.5)
        self.position_line = self.ax1.axvline(0, color='red', linewidth=2)
        self.ax1.set_ylabel('Waveform')
        self.ax1.grid(True, alpha=0.3)
        
        # Labels plot
        label_times = np.linspace(0, self.duration, self.n_labels)
        self.label_line, = self.ax2.plot(label_times, self.labels, 'g-', linewidth=2)
        self.ax2.set_ylabel(f'{labelTypeStr} Labels')
        self.ax2.set_xlabel('Time (s)')
        if self.labelType == 1:
            self.ax2.set_ylim(0, 9.5)
        elif self.labelType == 2:
            self.ax2.set_ylim(0, 3.5)
        self.ax2.grid(True, alpha=0.3)
        
        # Events
        self.fig.canvas.mpl_connect('button_press_event', self.on_click)
        self.fig.canvas.mpl_connect('key_press_event', self.on_key)
        
        # Status
        self.status = self.fig.suptitle(f'Label: {self.current_label} | Pos: 0.0s | SPACE: play/pause')
        
        plt.tight_layout()
        
        # Start update timer
        self.timer = self.fig.canvas.new_timer(interval=50)  # 50ms updates
        self.timer.add_callback(self.update_display)
        self.timer.start()
    
    def on_click(self, event):
        """Click to seek"""
        if event.inaxes in [self.ax1, self.ax2] and event.xdata is not None:
            self.seek(event.xdata)
    
    def on_key(self, event):
        """Keyboard controls"""
        if event.key == ' ':
            self.toggle_play()
        elif event.key in '0123456789' and self.labelType == 1: # for labeling speed 0-9
            self.current_label = int(event.key)
            self.apply_label()
        elif event.key in '0123' and self.labelType == 2: # for labeling patterns 0-3
            self.current_label = int(event.key)
            self.apply_label()
        elif event.key == 'escape':
            self.save()
        elif event.key == 'q':
            plt.close()
    
    def seek(self, time_pos):
        """Jump to position"""
        self.position = max(0, min(time_pos, self.duration))
        if self.is_playing:
            sd.stop()
            self.play_from_position()
    
    def toggle_play(self):
        """Play/pause"""
        if self.is_playing:
            sd.stop()
            self.is_playing = False
        else:
            self.play_from_position()
    
    def play_from_position(self):
        """Start playback"""
        start_sample = int(self.position * self.sr)
        audio_chunk = self.y[start_sample:]
        
        if len(audio_chunk) > 100:  # Minimum chunk size
            self.is_playing = True
            self.play_start_time = time.time()
            self.play_start_pos = self.position
            
            def play():
                try:
                    sd.play(audio_chunk, self.sr)
                    sd.wait()
                    self.is_playing = False
                except:
                    self.is_playing = False
            
            threading.Thread(target=play, daemon=True).start()
    
    def apply_label(self):
        """Apply current label at current position"""
        label_idx = int(self.position * self.labels_per_second)
        if 0 <= label_idx < len(self.labels):
            # Apply to small window
            window = max(1, self.labels_per_second // 4)  # 0.25 second window
            start = max(0, label_idx - window//2)
            end = min(len(self.labels), label_idx + window//2)
            self.labels[start:end] = self.current_label
    
    def update_display(self):
        """Update display periodically"""
        # Update position if playing
        if self.is_playing:
            elapsed = time.time() - self.play_start_time
            self.position = min(self.play_start_pos + elapsed, self.duration)
            
            # Auto-apply labels while playing
            if self.current_label > 0:
                self.apply_label()
        
        # Update display
        self.position_line.set_xdata([self.position, self.position])
        self.label_line.set_ydata(self.labels)
        self.status.set_text(f'Label: {self.current_label} | Pos: {self.position:.1f}s | Playing: {self.is_playing}')
        
        try:
            self.fig.canvas.draw_idle()
        except:
            pass
    
    def save(self):
        """Save labels"""
        if self.labelType == 1:
            output_path = output_path = Path("labels") / Path(self.audio_file).with_suffix('.speedLabels.npy').name
        elif self.labelType == 2:
            output_path = output_path = Path("labels") / Path(self.audio_file).with_suffix('.patternLabels.npy').name

        np.save(output_path, self.labels)
        print(f"Saved: {output_path}")
    
    def run(self):
        """Show the interface"""
        plt.show()

if __name__ == "__main__":
    audio_file = "./wavs/where-the-wild-things-are.wav"

    labelType = input("Select label type: \n 1: Speed \n 2: Patterns\n")

    if labelType not in ["1", "2"]:
        print("Invalid Label Type")
        exit()

    labelType = int(labelType)
    
    try:
        app = SimpleSongLabeler(audio_file, labelType, labels_per_second=10)
        app.run() 
    except FileNotFoundError:
        print(f"File not found: {audio_file}")
    except Exception as e:
        print(f"Error: {e}")