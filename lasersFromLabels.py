import numpy as np
import time
import random
import serial.tools.list_ports
from DMXClass import SimpleDMX
import threading

random.seed(time.time())

# ---- Check DMX Device (COM3) ----
def check_device():
    print("Checking for DMX device on COM3...")
    ports = serial.tools.list_ports.comports()
    for port in ports:
        if port.device == "COM3":
            try:
                test_ser = serial.Serial('COM3', timeout=1)
                test_ser.close()
                print("✓ COM3 is ready")
                return True
            except serial.SerialException:
                print("❌ COM3 is busy!")
                return False
    print("❌ COM3 not found.")
    return False

if not check_device():
    exit()

dmx = SimpleDMX()

# ---- Utility Functions ----
def setGlobalChannels():
    dmx.set_channel(1, 23)   # on, auto
    dmx.set_channel(2, 0)    # pattern group 2
    dmx.set_channel(3, 255)  # 100% pattern size

def reset_dmx():
    for i in range(1, 34):
        dmx.set_channel(i, 0)
    setGlobalChannels()

# ---- Pattern Functions ----

# Group 1: Panning
def dotLR(speed):
    dmx.set_channel(4, 16)
    for i in range(33, 96):
        if stop_flag.is_set():
            return
        dmx.set_channel(8, i)
        time.sleep(1/(50 * speed))

def dotRL(speed):
    dmx.set_channel(4, 16)
    for i in range(96, 33, -1):
        if stop_flag.is_set():
            return
        dmx.set_channel(8, i)
        time.sleep(1/(50 * speed))

def sideToSideDot(speed):
    dotRL(speed)
    dotLR(speed)

def horizontalLineRL(speed):
    dmx.set_channel(4, 45)
    for i in range(33, 96):
        if stop_flag.is_set():
            return
        dmx.set_channel(8, i)
        time.sleep(1/(100 * speed))

def horizontalLineLR(speed):
    dmx.set_channel(4, 45)
    for i in range(96, 33, -1):
        if stop_flag.is_set():
            return
        dmx.set_channel(8, i)
        time.sleep(1/(100 * speed))

def horizontalLineSideToSide(speed):
    horizontalLineRL(speed)
    horizontalLineLR(speed)

# Group 2: Flashing
def crazyDots(speed):
    dmx.set_channel(4, 16)
    for _ in range(5):
        if stop_flag.is_set():
            return
        dmx.set_channel(7, random.randint(0, 127))
        dmx.set_channel(8, random.randint(0, 127))
        time.sleep(1/(speed + 0.01))

def randomSingleDot(speed):
    dmx.set_channel(4, 16)
    dmx.set_channel(7, random.randint(0, 127))
    dmx.set_channel(8, random.randint(0, 127))
    # Sleep in chunks so we can detect stop_flag during the wait
    for _ in range(10):
        if stop_flag.is_set():
            return
        time.sleep(0.1)

def circleZoomIn(speed):
    dmx.set_channel(4, 5)
    for i in range(0, 127, 4):
        if stop_flag.is_set():
            return
        dmx.set_channel(5, i)
        time.sleep(1/(100 * speed))

# Group 3: Flowing
def wiggleLine(speed):
    dmx.set_channel(4, 51)
    dmx.set_channel(6, 33)
    for i in range(40, 100):
        if stop_flag.is_set():
            return
        dmx.set_channel(10, i)
        time.sleep(1/(50*speed))
    for i in range(100, 40, -1):
        if stop_flag.is_set():
            return
        dmx.set_channel(10, i)
        time.sleep(1/(50 * speed))

# ---- Pattern Dictionary ----
pattern_groups = {
    1: [dotLR, dotRL, sideToSideDot, horizontalLineRL, horizontalLineLR, horizontalLineSideToSide, circleZoomIn],
    2: [crazyDots, randomSingleDot],
    3: [wiggleLine],
}

# ---- Load Label Files ----
pattern_labels = np.load("where-the-wild-things-are.patternLabels.npy")
speed_labels = np.load("where-the-wild-things-are.speedLabels.npy")

assert len(pattern_labels) == len(speed_labels), "Mismatch in label lengths!"

# ---- Thread Management ----
stop_flag = threading.Event()
current_thread = None

def pattern_loop(func, speed):
    while not stop_flag.is_set():
        func(speed)

def start_pattern_thread(func, speed):
    global current_thread
    stop_pattern_thread()
    stop_flag.clear()
    current_thread = threading.Thread(target=pattern_loop, args=(func, speed))
    current_thread.daemon = True
    current_thread.start()

def stop_pattern_thread():
    global current_thread
    stop_flag.set()
    if current_thread and current_thread.is_alive():
        current_thread.join()
    current_thread = None

# ---- Main Loop ----
print("Starting light playback...")
setGlobalChannels()

for i in range(3, 0, -1):
    print(f"Starting in {i}...")
    time.sleep(1)

current_pattern = None
current_speed = None

try:
    for i in range(len(pattern_labels)):
        start = time.time()
        pattern = pattern_labels[i]
        speed = speed_labels[i]

        if pattern == 0 or speed == 0:
            if current_pattern is not None:
                print(f"[{i}] Pattern OFF")
                stop_pattern_thread()
                reset_dmx()
                current_pattern = None
                current_speed = None
        else:
            if pattern != current_pattern or speed != current_speed:
                current_pattern = pattern
                current_speed = speed
                group_funcs = pattern_groups.get(pattern)
                if not group_funcs:
                    print(f"[{i}] Unknown pattern group: {pattern}")
                else:
                    func = random.choice(group_funcs)
                    print(f"[{i}] Pattern {pattern}, Speed {speed} → {func.__name__}")
                    stop_pattern_thread()       # Wait for clean thread exit
                    reset_dmx()
                    start_pattern_thread(func, speed)

        # Keep 10 FPS
        elapsed = time.time() - start
        time.sleep(max(0, 0.1 - elapsed))

except KeyboardInterrupt:
    print("Interrupted. Resetting...")
    stop_pattern_thread()
    reset_dmx()
    dmx.close()
