import numpy as np
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import librosa
import sounddevice as sd
import threading
import time
from pathlib import Path
import os

class TkinterSongLabeler:
    def __init__(self, root):
        self.root = root
        self.root.title("Audio Labeling Tool")
        self.root.geometry("1200x800")
        
        # Audio data
        self.y = None
        self.sr = None
        self.duration = 0
        self.audio_file = None
        self.labels_per_second = 10
        self.n_labels = 0

        self.vocals_y = None
        self.vocals_sr = None
        self.vocals_file = None
        self.vocals_position_line = None
        
        # Labels for both types
        self.speed_labels = None
        self.pattern_labels = None
        self.current_label_set = "speed"  # Current active label set
        
        # Playback state
        self.is_playing = False
        self.position = 0.0
        self.current_label = 0
        self.play_start_time = 0
        self.play_start_pos = 0
        self.play_thread = None
        self.should_stop_playback = False

        self.auto_apply = True
        
        # GUI elements
        self.position_line = None
        self.label_line = None
        self.status_label = None
        self.update_timer = None
        
        self.setup_gui()
        self.setup_bindings()
        # Bind focus reset to any widget interaction
        self.root.bind_all('<Button-1>', lambda e: self.root.after_idle(self.reset_focus))
        
    def setup_gui(self):
        """Setup the GUI layout"""
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(2, weight=1)
        
        # File selection frame
        file_frame = ttk.LabelFrame(main_frame, text="File Selection", padding="5")
        file_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        file_frame.columnconfigure(1, weight=1)
        
        ttk.Button(file_frame, text="Load Audio File", command=self.load_audio_file).grid(row=0, column=0, padx=(0, 10))
        self.file_label = ttk.Label(file_frame, text="No file loaded")
        self.file_label.grid(row=0, column=1, sticky=(tk.W, tk.E))
        
        # Add vocal stems loading - ADD THIS
        ttk.Button(file_frame, text="Load Vocal Stems", command=self.load_vocals_file).grid(row=2, column=0, padx=(0, 10), pady=(5, 0))
        self.vocals_label = ttk.Label(file_frame, text="No vocal stems loaded")
        self.vocals_label.grid(row=2, column=1, sticky=(tk.W, tk.E), pady=(5, 0))

        # Label type selection
        label_type_frame = ttk.LabelFrame(file_frame, text="Current Label Set")
        label_type_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0))
        
        self.label_type_var = tk.StringVar(value="speed")
        ttk.Radiobutton(label_type_frame, text="Speed Labels (0-9)", variable=self.label_type_var, 
                       value="speed", command=self.on_label_type_change).grid(row=0, column=0, padx=(0, 20))
        ttk.Radiobutton(label_type_frame, text="Pattern Labels (0-3)", variable=self.label_type_var, 
                       value="pattern", command=self.on_label_type_change).grid(row=0, column=1)
        
        # Control frame
        control_frame = ttk.LabelFrame(main_frame, text="Controls", padding="5")
        control_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Playback controls
        playback_frame = ttk.Frame(control_frame)
        playback_frame.grid(row=0, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.play_button = ttk.Button(playback_frame, text="Play", command=self.toggle_play, state="disabled")
        self.play_button.grid(row=0, column=0, padx=(0, 10))
        
        ttk.Label(playback_frame, text="Position:").grid(row=0, column=1, padx=(0, 5))
        self.position_var = tk.DoubleVar()
        self.position_scale = ttk.Scale(playback_frame, from_=0, to=100, variable=self.position_var, 
                                       command=self.on_position_change, state="disabled")
        self.position_scale.grid(row=0, column=2, sticky=(tk.W, tk.E), padx=(0, 10))
        playback_frame.columnconfigure(2, weight=1)
        
        self.position_label = ttk.Label(playback_frame, text="0.0s / 0.0s")
        self.position_label.grid(row=0, column=3)
        
        # Label controls
        label_control_frame = ttk.Frame(control_frame)
        label_control_frame.grid(row=1, column=0, columnspan=4, sticky=(tk.W, tk.E))
        
        ttk.Label(label_control_frame, text="Current Label:").grid(row=0, column=0, padx=(0, 5))
        self.current_label_var = tk.IntVar()
        self.label_spinbox = ttk.Spinbox(label_control_frame, from_=0, to=9, width=5, 
                                        textvariable=self.current_label_var, command=self.on_label_change)
        self.label_spinbox.grid(row=0, column=1, padx=(0, 10))
        
        ttk.Button(label_control_frame, text="Apply Label", command=self.apply_label).grid(row=0, column=2, padx=(0, 10))
        ttk.Button(label_control_frame, text="Save Labels", command=self.save_mfccs_and_labels).grid(row=0, column=3)

        quick_label_frame = ttk.LabelFrame(control_frame, text="Quick Labels", padding="5")
        quick_label_frame.grid(row=2, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=(10, 0))

        # Create label buttons
        label_buttons = [
            (0, "0: None"),
            (1, "1: Vocals"), 
            (2, "2: Ambient"),
            (3, "3: Buildup"),
            (4, "4: Pre-Drop"),
            (5, "5: Drop"),
            (6, "6: Drop2")
        ]

        for i, (value, text) in enumerate(label_buttons):
            btn = ttk.Button(quick_label_frame, text=text, 
                            command=lambda v=value: self.set_quick_label(v))
            btn.grid(row=0, column=i, padx=2)

        # Auto-apply toggle
        auto_apply_frame = ttk.Frame(quick_label_frame)
        auto_apply_frame.grid(row=1, column=0, columnspan=7, pady=(10, 0))

        self.auto_apply_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(auto_apply_frame, text="Toggle Label Apply", 
                    variable=self.auto_apply_var, command=self.toggle_auto_apply).pack()
        
        # Plot frame
        plot_frame = ttk.LabelFrame(main_frame, text="Visualization", padding="5")
        plot_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S))
        plot_frame.columnconfigure(0, weight=1)
        plot_frame.rowconfigure(0, weight=1)
        
        # Create matplotlib figure
        self.fig = Figure(figsize=(12, 8), dpi=100)
        self.ax1, self.ax2, self.ax3 = self.fig.subplots(3, 1)
        
        self.canvas = FigureCanvasTkAgg(self.fig, plot_frame)
        self.canvas.get_tk_widget().grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Status bar
        self.status_label = ttk.Label(main_frame, text="Ready - Load an audio file to begin")
        self.status_label.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0))
        
        # Instructions
        instructions = """
                        Controls:
                        • SPACE: Play/Pause
                        • 0-9: Set label (Speed mode) / 0-3: Set label (Pattern mode)
                        • Click on plot: Seek to position
                        • ESC: Save labels
                        • Q: Quit
                        """
        instructions_label = ttk.Label(main_frame, text=instructions, justify=tk.LEFT, 
                                     font=('TkDefaultFont', 8))
        instructions_label.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(5, 0))

    def reset_focus(self):
        """Reset focus to main window"""
        self.root.focus_set()
    
    def setup_bindings(self):
        """Setup keyboard bindings"""
        self.root.bind('<KeyPress>', self.on_key_press)
        self.root.focus_set()  # Ensure window can receive key events
        
        # Canvas click binding
        self.canvas.mpl_connect('button_press_event', self.on_canvas_click)
    
    def load_audio_file(self):
        """Load audio file dialog"""
        file_path = filedialog.askopenfilename(
            title="Select Audio File",
            filetypes=[
                ("Audio files", "*.wav *.mp3 *.flac *.m4a *.aac"),
                ("WAV files", "*.wav"),
                ("MP3 files", "*.mp3"),
                ("All files", "*.*")
            ]
        )
        
        if file_path:
            try:
                self.load_audio(file_path)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load audio file:\n{str(e)}")
    
    def load_audio(self, file_path):
        """Load and process audio file"""
        self.status_label.config(text="Loading audio...")
        self.root.update()
        
        # Load audio
        self.y, self.sr = librosa.load(file_path)
        self.duration = len(self.y) / self.sr
        self.audio_file = file_path
        
        # Setup labels
        self.n_labels = int(self.duration * self.labels_per_second)
        self.speed_labels = np.zeros(self.n_labels, dtype=int)
        self.pattern_labels = np.zeros(self.n_labels, dtype=int)
        
        # Check if existing labels file exists and load them
        self.load_existing_labels()
        
        # Reset playback state
        self.stop_playback()
        self.is_playing = False
        self.position = 0.0
        self.current_label = 0
        self.current_label_var.set(0)
        
        # Update GUI
        self.file_label.config(text=f"Loaded: {Path(file_path).name}")
        self.position_scale.config(to=self.duration, state="normal")
        self.play_button.config(state="normal")
        
        # Update label spinbox range based on current type
        self.on_label_type_change()
        
        # Setup plot
        self.setup_plot()
        
        # Start update timer
        self.start_update_timer()
        
        self.status_label.config(text=f"Ready! {self.duration:.1f}s audio, {self.n_labels} labels")

    def load_vocals_file(self):
        """Load vocal stems file dialog"""
        file_path = filedialog.askopenfilename(
            title="Select Vocal Stems File",
            filetypes=[
                ("Audio files", "*.wav *.mp3 *.flac *.m4a *.aac"),
                ("WAV files", "*.wav"),
                ("MP3 files", "*.mp3"),
                ("All files", "*.*")
            ]
        )
        
        if file_path:
            try:
                self.load_vocals(file_path)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load vocal stems:\n{str(e)}")

    def load_vocals(self, file_path):
        """Load and process vocal stems file"""
        self.status_label.config(text="Loading vocal stems...")
        self.root.update()
        
        # Load vocal stems
        self.vocals_y, self.vocals_sr = librosa.load(file_path)
        self.vocals_file = file_path
        
        # Update GUI
        self.vocals_label.config(text=f"Vocals: {Path(file_path).name}")
        
        # Update plot if main audio is loaded
        if self.y is not None:
            self.setup_plot()
        
        self.status_label.config(text="Vocal stems loaded!")
    
    def load_existing_labels(self):
        """Load existing labels if the npz file exists"""
        output_path = Path("labels") / Path(self.audio_file).with_suffix('.mfcc_labels.npz').name
        
        if output_path.exists():
            try:
                data = np.load(output_path)
                if 'speed_labels' in data:
                    self.speed_labels = data['speed_labels']
                if 'pattern_labels' in data:
                    self.pattern_labels = data['pattern_labels']
                print(f"Loaded existing labels from {output_path}")
            except Exception as e:
                print(f"Error loading existing labels: {e}")
    
    def on_label_type_change(self):
        """Handle label type change"""
        self.current_label_set = self.label_type_var.get()
        max_label = 9 if self.current_label_set == "speed" else 6
        self.label_spinbox.config(to=max_label)
        if self.current_label_var.get() > max_label:
            self.current_label_var.set(max_label)
            self.current_label = max_label
        if hasattr(self, 'ax2'):
            self.update_plot_labels()

    def set_quick_label(self, label_value):
        """Set current label from quick buttons"""
        max_label = 9 if self.current_label_set == "speed" else 6
        if label_value <= max_label:
            self.current_label = label_value
            self.current_label_var.set(label_value)
            if self.auto_apply:
                self.apply_label()
    
    def get_current_labels(self):
        """Get the currently active label array"""
        return self.speed_labels if self.current_label_set == "speed" else self.pattern_labels
    
    def setup_plot(self):
        """Setup the matplotlib plots"""
        self.ax1.clear()
        self.ax2.clear()
        self.ax3.clear()
        
        # Downsample waveform for display
        step = max(1, len(self.y) // 2000)
        times = np.linspace(0, self.duration, len(self.y[::step]))
        
        # Waveform plot
        self.ax1.plot(times, self.y[::step], 'b-', alpha=0.6, linewidth=0.5)
        self.position_line = self.ax1.axvline(0, color='red', linewidth=2)
        self.ax1.set_ylabel('Waveform')
        self.ax1.grid(True, alpha=0.3)

        # Vocal stems plot (if loaded)
        if self.vocals_y is not None:
            vocals_duration = len(self.vocals_y) / self.vocals_sr
            vocals_step = max(1, len(self.vocals_y) // 2000)
            vocals_times = np.linspace(0, vocals_duration, len(self.vocals_y[::vocals_step]))
            
            self.ax3.plot(vocals_times, self.vocals_y[::vocals_step], 'purple', alpha=0.6, linewidth=0.5)
            self.vocals_position_line = self.ax3.axvline(0, color='red', linewidth=2)
            self.ax3.set_ylabel('Vocal Stems')
            self.ax3.grid(True, alpha=0.3)
        else:
            self.ax3.text(0.5, 0.5, 'No vocal stems loaded', ha='center', va='center', 
                        transform=self.ax3.transAxes, fontsize=12, alpha=0.5)
            self.vocals_position_line = None
        
        # Labels plot
        label_times = np.linspace(0, self.duration, self.n_labels)
        current_labels = self.get_current_labels()
        self.label_line, = self.ax2.plot(label_times, current_labels, 'g-', linewidth=2)
        self.position_line_labels = self.ax2.axvline(0, color='red', linewidth=2)  # vertical marker
        
        label_type_str = "Speed" if self.current_label_set == "speed" else "Pattern"
        self.ax2.set_ylabel(f'{label_type_str} Labels')
        self.ax2.set_xlabel('Time (s)')
        
        y_max = 9.5 if self.current_label_set == "speed" else 6.5
        self.ax2.set_ylim(0, y_max)
        self.ax2.grid(True, alpha=0.3)
        
        self.fig.tight_layout()
        self.canvas.draw()
    
    def update_plot_labels(self):
        """Update plot with current label type"""
        if self.ax2 and self.label_line:
            label_type_str = "Speed" if self.current_label_set == "speed" else "Pattern"
            self.ax2.set_ylabel(f'{label_type_str} Labels')
            y_max = 9.5 if self.current_label_set == "speed" else 6.5
            self.ax2.set_ylim(0, y_max)
            
            # Update the line data
            current_labels = self.get_current_labels()
            self.label_line.set_ydata(current_labels)
            self.canvas.draw()
    
    def start_update_timer(self):
        """Start the update timer for 10fps updates"""
        if self.update_timer:
            self.root.after_cancel(self.update_timer)
        self.update_display()
    
    def update_display(self):
        """Update display periodically (10fps)"""
        if not self.audio_file:
            return
            
        # Update position if playing
        if self.is_playing and not self.should_stop_playback:
            elapsed = time.time() - self.play_start_time
            new_position = self.play_start_pos + elapsed
            
            # Check if we've reached the end
            if new_position >= self.duration:
                self.stop_playback()
                self.position = self.duration
            else:
                self.position = new_position
                
                # Auto-apply labels while playing
                if self.current_label > 0 and self.auto_apply:
                    self.apply_label()
        
        # Update GUI elements
        self.position_var.set(self.position)
        self.position_label.config(text=f"{self.position:.1f}s / {self.duration:.1f}s")
        
        # Update plot
        if self.position_line:
            self.position_line.set_xdata([self.position, self.position])
        if hasattr(self, 'position_line_labels') and self.position_line_labels: 
            self.position_line_labels.set_xdata([self.position, self.position])
        if self.label_line:
            current_labels = self.get_current_labels()
            self.label_line.set_ydata(current_labels)
        if hasattr(self, 'vocals_position_line') and self.vocals_position_line:
            self.vocals_position_line.set_xdata([self.position, self.position])
        
        # Update status
        status_text = f"Label: {self.current_label} | Position: {self.position:.1f}s | "
        status_text += f"Playing: {self.is_playing} | Mode: {self.current_label_set.title()}"
        self.status_label.config(text=status_text)
        
        # Update play button text
        self.play_button.config(text="Pause" if self.is_playing else "Play")
        
        try:
            self.canvas.draw_idle()
        except:
            pass
        
        # Schedule next update (100ms = 10fps)
        self.update_timer = self.root.after(100, self.update_display)
    
    def on_key_press(self, event):
        """Handle keyboard input"""
        if not self.audio_file:
            return
            
        key = event.keysym
        
        if key == 'space':
            self.toggle_play()
        elif key == 'Escape':
            self.save_mfccs_and_labels()
        elif key == 'q':
            self.root.quit()
        elif key.isdigit():
            digit = int(key)
            max_label = 9 if self.current_label_set == "speed" else 6
            if digit <= max_label:
                self.current_label = digit
                self.current_label_var.set(digit)
                if self.auto_apply:
                    self.apply_label()
    
    def on_canvas_click(self, event):
        """Handle canvas click for seeking"""
        if event.inaxes in [self.ax1, self.ax2, self.ax3] and event.xdata is not None:  # Add ax3
            self.seek(event.xdata)
    
    def on_position_change(self, value):
        """Handle position scale change"""
        if not self.is_playing:  # Only allow manual seeking when not playing
            self.seek(float(value))
    
    def on_label_change(self):
        """Handle label spinbox change"""
        self.current_label = self.current_label_var.get()
    
    def stop_playback(self):
        """Stop current playback completely"""
        self.should_stop_playback = True
        sd.stop()
        if self.play_thread and self.play_thread.is_alive():
            self.play_thread.join(timeout=0.1)  # Brief wait for thread cleanup
        self.is_playing = False
        self.should_stop_playback = False
    
    def seek(self, time_pos):
        """Jump to position"""
        old_position = self.position
        self.position = max(0, min(time_pos, self.duration))
        
        # If we're playing and position changed significantly, restart playback
        if self.is_playing and abs(self.position - old_position) > 0.1:
            self.stop_playback()
            self.play_from_position()
    
    def toggle_play(self):
        """Play/pause toggle"""
        if self.is_playing:
            self.stop_playback()
        else:
            self.play_from_position()
    
    def play_from_position(self):
        """Start playback from current position"""
        # Stop any existing playback first
        self.stop_playback()
        
        start_sample = int(self.position * self.sr)
        audio_chunk = self.y[start_sample:]
        
        if len(audio_chunk) > 100:  # Minimum chunk size
            self.is_playing = True
            self.play_start_time = time.time()
            self.play_start_pos = self.position
            self.should_stop_playback = False
            
            def play():
                try:
                    # Check if we should stop before starting
                    if not self.should_stop_playback:
                        sd.play(audio_chunk, self.sr)
                        sd.wait()
                    
                    # Only set to False if this thread wasn't interrupted
                    if not self.should_stop_playback:
                        self.is_playing = False
                except Exception as e:
                    self.is_playing = False
            
            self.play_thread = threading.Thread(target=play, daemon=True)
            self.play_thread.start()

    def toggle_auto_apply(self):
        """Toggle auto-apply mode"""
        self.auto_apply = self.auto_apply_var.get()
    
    def apply_label(self):
        """Apply current label at current position"""
        current_labels = self.get_current_labels()
        if not current_labels.size:
            return
            
        label_idx = int(self.position * self.labels_per_second)
        if 0 <= label_idx < len(current_labels):
            # Apply to small window
            window = max(1, self.labels_per_second // 4)  # 0.25 second window
            start = max(0, label_idx - window//2)
            end = min(len(current_labels), label_idx + window//2)
            current_labels[start:end] = self.current_label

    def save_mfccs_and_labels(self):
        """Save MFCCs and labels to a compressed .npz file"""
        if not self.audio_file:
            messagebox.showwarning("Warning", "No audio loaded")
            return

        try:
            # Ensure labels directory exists
            labels_dir = Path("labels")
            labels_dir.mkdir(exist_ok=True)
            
            output_path = labels_dir / Path(self.audio_file).with_suffix('.mfcc_labels.npz').name
            
            # Check if file already exists
            existing_data = {}
            if output_path.exists():
                existing_data = dict(np.load(output_path))
            
            # Extract MFCC features if not already present
            # if 'mfcc' not in existing_data:
            #     hop_length = int(self.sr / self.labels_per_second)
            #     mfcc = librosa.feature.mfcc(y=self.y, sr=self.sr, n_mfcc=20, hop_length=hop_length)
            #     X = mfcc.T  # Shape: (num_frames, 20)
                
            #     # Ensure MFCC and labels have same length
            #     min_len = min(len(X), self.n_labels)
            #     X = X[:min_len]
            #     self.speed_labels = self.speed_labels[:min_len]
            #     self.pattern_labels = self.pattern_labels[:min_len]
                
            #    existing_data['mfcc'] = X
            
            # Add current labels
            existing_data['speed_labels'] = self.speed_labels
            existing_data['pattern_labels'] = self.pattern_labels
            
            # Save everything
            np.savez_compressed(output_path, **existing_data)
            
            messagebox.showinfo("Success", f"MFCCs ARE NOT CURRENTLY BEING SAVED. labels saved to:\n{output_path}")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to save MFCCs and labels:\n{str(e)}")

def main():
    root = tk.Tk()
    app = TkinterSongLabeler(root)
    
    try:
        root.mainloop()
    except KeyboardInterrupt:
        pass
    finally:
        # Stop any playing audio
        sd.stop()

if __name__ == "__main__":
    main()