# === Imports and Initialization ===

import numpy as np  # For numerical operations and loading label arrays
import time         # For time delays and timing
import random       # For randomness in pattern selection and movement
import serial.tools.list_ports  # For detecting available serial ports (e.g., COM3)
import serial
from DMXClass import SimpleDMX  # Custom DMX control class for lighting via serial
from threading import Thread, Lock, Event
from pattern_functions import pattern_groups, reset_pattern_states

# Seed the random number generator with the current time to ensure variability
random.seed(time.time())

# === Shared State ===

pattern_state = {
    'func': None,
    'speed': None
}
pattern_lock = Lock()
stop_flag = Event()

# === Check DMX Device ===

def check_device():
    """
    Checks if the DMX lighting controller is connected on COM3.
    
    Returns:
        bool: True if COM3 is found and available; False otherwise.
    """
    print("Checking for DMX device on COM3...")
    
    # List all available COM ports on the system
    ports = serial.tools.list_ports.comports()
    
    for port in ports:
        if port.device == "COM3":
            try:
                # Attempt to open and immediately close the COM3 port to check availability
                test_ser = serial.Serial('COM3', timeout=1)
                test_ser.close()
                print("✓ COM3 is ready")
                return True
            except serial.SerialException:
                print("❌ COM3 is busy!")
                return False

    print("❌ COM3 not found.")
    return False

# Exit the script if DMX device is not detected
if not check_device():
    exit()

# === DMX Setup ===

# Instantiate a new DMX controller object (assumes the SimpleDMX class manages serial output)
dmx = SimpleDMX()

def setGlobalChannels():
    """
    Sets global DMX channels that should be applied to all lighting patterns.
    Channel layout:
    - Channel 1: On/Auto mode
    - Channel 2: Pattern group
    - Channel 3: Pattern size (brightness or intensity)
    """
    dmx.set_channel(1, 23)
    dmx.set_channel(2, 0)
    dmx.set_channel(3, 255)

def reset_dmx():
    """
    Resets all DMX channels (1–33) to 0, then reapplies global channel settings.
    """
    for i in range(1, 34):
        dmx.set_channel(i, 0)
    setGlobalChannels()

# === Persistent Pattern Thread ===

def persistent_pattern_runner():
    """
    Persistent thread that continuously runs the current pattern.
    Reads from shared state and switches patterns when needed.
    """
    last_func = None
    last_speed = None
    
    while not stop_flag.is_set():
        with pattern_lock:
            func = pattern_state['func']
            speed = pattern_state['speed']
        
        if func is None or speed is None:
            time.sleep(0.05)  # Idle waiting
            continue
        
        # Check if we need to switch patterns or speeds
        if func != last_func or speed != last_speed:
            print(f"Switching pattern to {func.__name__} at speed {speed}")
            reset_dmx()  # Clear old pattern state
            reset_pattern_states()  # Reset pattern function states
            last_func = func
            last_speed = speed
        
        # Execute one frame of the current pattern
        try:
            func(dmx, speed)
        except Exception as e:
            print(f"Error in pattern {func.__name__}: {e}")
            time.sleep(0.1)

# === Load Label Data ===

def load_mfcc_and_labels(audio_filename):
    """
    Load MFCC features and labels from the compressed .npz file.
    
    Args:
        audio_filename (str): Name of the audio file (without extension)
        
    Returns:
        tuple: (mfcc_features, pattern_labels, speed_labels)
    """
    from pathlib import Path
    
    # Construct the expected file path in labels directory
    labels_dir = Path("labeling/labels")
    npz_path = labels_dir / f"{audio_filename}.mfcc_labels.npz"
    
    if not npz_path.exists():
        raise FileNotFoundError(f"MFCC and labels file not found: {npz_path}")
    
    # Load the compressed data
    data = dict(np.load(npz_path))
    
    # Extract the components
    mfcc_features = data['mfcc']
    pattern_labels = data['pattern_labels']
    speed_labels = data['speed_labels']
    
    print(f"Loaded data from: {npz_path}")
    print(f"MFCC shape: {mfcc_features.shape}")
    print(f"Pattern labels length: {len(pattern_labels)}")
    print(f"Speed labels length: {len(speed_labels)}")
    
    # Ensure data consistency
    assert len(pattern_labels) == len(speed_labels) == len(mfcc_features), \
        f"Mismatch in data lengths: MFCC={len(mfcc_features)}, patterns={len(pattern_labels)}, speeds={len(speed_labels)}"
    
    return mfcc_features, pattern_labels, speed_labels

# Load the audio data - adjust the filename as needed
audio_filename = "one-three-nine"  # Without extension
mfcc_features, pattern_labels, speed_labels = load_mfcc_and_labels(audio_filename)

# === Main Loop ===

print("Starting light playback...")

# Initialize lights with default global settings
setGlobalChannels()

# Start the persistent pattern thread
pattern_thread = Thread(target=persistent_pattern_runner, daemon=True)
pattern_thread.start()

# 3-second countdown before starting
for i in range(3, 0, -1):
    print(f"Starting in {i}...")
    time.sleep(1)

# Track the currently running pattern/speed to avoid restarting identical ones
current_pattern = None
current_speed = None
current_func = None

try:
    for i in range(len(pattern_labels)):
        start = time.time()  # measure execution time to maintain 10 FPS
        
        # Load the current pattern and speed labels
        pattern = pattern_labels[i]
        speed = speed_labels[i]

        if pattern == 0 or speed == 0:
            # 0 means "turn off lights"
            if current_pattern is not None:
                print(f"[{i}] Pattern OFF")
                with pattern_lock:
                    pattern_state['func'] = None
                    pattern_state['speed'] = None
                current_pattern = None
                current_speed = None
                current_func = None
        else:
            # Only change pattern if pattern or speed changed
            if pattern != current_pattern or speed != current_speed:
                current_pattern = pattern
                current_speed = speed
                
                # Select a function from the pattern group
                group_funcs = pattern_groups.get(pattern)
                
                if not group_funcs:
                    print(f"[{i}] Unknown pattern group: {pattern}")
                else:
                    current_func = random.choice(group_funcs)
                    with pattern_lock:
                        pattern_state['func'] = current_func
                        pattern_state['speed'] = speed
                    print(f"[{i}] Pattern {pattern}, Speed {speed} → {current_func.__name__}")

        # Ensure loop runs roughly at 10 frames per second
        elapsed = time.time() - start
        time.sleep(max(0, 0.1 - elapsed))

except KeyboardInterrupt:
    # Handle Ctrl+C gracefully
    print("Interrupted. Shutting down...")
    
# Cleanup
stop_flag.set()
pattern_thread.join()
reset_dmx()
dmx.close()
print("Cleanup complete.")