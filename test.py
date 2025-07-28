import time
import random
random.seed(time.time())
import serial.tools.list_ports
from DMXClass import SimpleDMX
import math

def check_device():
    """Check if COM3 is available"""
    print("Checking for DMX device on COM3...")
    
    ports = serial.tools.list_ports.comports()
    com3_found = False
    
    for port in ports:
        print(f"Found port: {port.device} - {port.description}")
        if port.device == "COM3":
            com3_found = True
            print(f"✓ COM3 found: {port.description}")
            if "FT232" in port.description or "FTDI" in port.description:
                print("✓ FTDI device confirmed")
            break
    
    if not com3_found:
        print("❌ COM3 not found!")
        print("Available ports:")
        for port in ports:
            print(f"  {port.device}: {port.description}")
        return False
    
    # Test if COM3 is available (not busy)
    try:
        test_ser = serial.Serial('COM3', timeout=1)
        test_ser.close()
        print("✓ COM3 is available")
        return True
    except serial.SerialException as e:
        print(f"❌ COM3 is busy or unavailable: {e}")
        print("Make sure QLC+ or other software isn't using the device")
        return False
    
if not check_device():
    print("Cannot proceed - device check failed")
    exit()

dmx = SimpleDMX()

def circleZoomIn(speed):
    dmx.set_channel(4, 5) # Circle
    while True:
        for i in range(0, 127):
            dmx.set_channel(5, i) # Circle Zooming in = 160 + speed <= 191
            time.sleep(1/(100*speed))

def crazyDots(speed):
    dmx.set_channel(4, 16) # Dot
    for i in range(0, 20): # number of dots / 2 -------------------------------- This does not currently play (once) once is 1 random dot. Might want to rework this since it
                                                                        # should be a random dot each time the function replays anyway since its seeded w time.
        dmx.set_channel(7, random.randint(0, 127)) # dot 1
        dmx.set_channel(8, random.randint(0, 127)) # dot 2
        time.sleep(1/(speed)) # time between dots (doing 1/ 200 * speed because this should be
                                  # faster generally than other functions that are 1-10)
def dotLR(speed):
    dmx.set_channel(4, 16) # Dot
    for i in range(33, 96):
                dmx.set_channel(8, i)
                time.sleep(1/(50 * speed))

def dotRL(speed):
     dmx.set_channel(4, 16) # Dot
     for i in range(96, 33, -1):
                dmx.set_channel(8, i)
                time.sleep(1/(50 * speed))

def wiggleLine(speed):
    dmx.set_channel(4, 51) # squiggle
    dmx.set_channel(6, 33) # rotate to horizontal
    while True:
        for i in range(40, 100):
            dmx.set_channel(10, i)
            time.sleep(1/(50*speed))
        for i in range(100, 40, -1):
            dmx.set_channel(10, i)
            time.sleep(1/(50 * speed))

def spazzCircle(speed):
    dmx.set_channel(4, 5) # Circle
    while True:
        dmx.set_channel(7, random.randint(0, 127))
        dmx.set_channel(8, random.randint(0, 127))
        time.sleep(1/(50 * speed))

def spotlight(speed=1.0, duration_range=(1, 3)):
    # Define boundaries
    min_bound = 47
    max_bound = 80

    # Initialize position
    x = random.uniform(min_bound, max_bound)
    y = random.uniform(min_bound, max_bound)

    dmx.set_channel(2, 29)  # smaller pattern size
    dmx.set_channel(4, 5)   # Circle or movement mode
    dmx.set_channel(7, int(x))
    dmx.set_channel(8, int(y))

    while True:
        # Pick a random angle in radians
        angle = random.uniform(0, 2 * math.pi)
        dx = math.cos(angle)
        dy = math.sin(angle)

        # Random duration for this direction
        duration = random.uniform(*duration_range)
        start_time = time.time()

        while time.time() - start_time < duration:
            # Update position
            x += dx * speed
            y += dy * speed

            # Bounce off edges by reflecting direction and clamping
            if x <= min_bound:
                dx *= -1
                x = min_bound
            elif x >= max_bound:
                dx *= -1
                x = max_bound

            if y <= min_bound:
                dy *= -1
                y = min_bound
            elif y >= max_bound:
                dy *= -1
                y = max_bound

            # Send to DMX (must be integers)
            dmx.set_channel(7, int(x))
            dmx.set_channel(8, int(y))

            time.sleep(0.1 / speed)

def driftingDot(speed):
    if speed > 3:
        speed = 3
    dmx.set_channel(4, 16)  # dot

    # Define boundaries and center
    min_bound = 33
    max_bound = 96
    center_x = (min_bound + max_bound) / 2
    center_y = (min_bound + max_bound) / 2
    radius = (max_bound - min_bound) / 2 - 1  # just like original

    # Initial position and angle
    x, y = center_x, center_y
    angle = random.uniform(0, 2 * math.pi)

    # Control parameters
    drift_strength = 0.1 * speed  # how curvy the motion is
    movement_speed = 2 * speed  # how fast it moves

    while True:
        # Drift the angle slightly
        angle += random.uniform(-drift_strength, drift_strength)

        # Propose new position
        dx = math.cos(angle) * movement_speed
        dy = math.sin(angle) * movement_speed
        new_x = x + dx
        new_y = y + dy

        # Reflect angle if hitting bounds
        if new_x < min_bound or new_x > max_bound:
            angle = math.pi - angle
            new_x = x  # cancel movement in x
        if new_y < min_bound or new_y > max_bound:
            angle = -angle
            new_y = y  # cancel movement in y

        # Commit new position
        x = new_x
        y = new_y

        # Send to DMX
        dmx.set_channel(7, int(x))
        dmx.set_channel(8, int(y))

        time.sleep(0.05)

def stillBeam(speed):
    dmx.set_channel(4, 16)  # dot\
    dmx.set_channel(7, random.randint(0, 127))
    dmx.set_channel(8, random.randint(0, 127))

def lineWithDotsRL(speed):
    # a Horizontal line going up and down, with dots moving within it from right to left.
    speed = 1/10 * speed
    
    # Setup channels for line and dots
    dmx.set_channel(4, 45)  # vertical line
    dmx.set_channel(6, 32)  # rotate 90 degrees

    dmx.set_channel(18, 23)  # laser 2 on
    dmx.set_channel(19, 0)   # pattern size 100%
    dmx.set_channel(21, 57)  # spaced dots, laser 2
    dmx.set_channel(23, 32)  # rotate 90 degrees

    # Define vertical pan bounds (slow)
    min_y = 33
    max_y = 95

    # Define horizontal dot bounds (fast)
    min_x = 0
    max_x = 127

    # Vertical pan speed factor (slower)
    vertical_speed = speed * 0.3

    # Horizontal dot speed factor (faster)
    horizontal_speed = speed * 1.5

    y = min_y
    y_direction = 1

    x = min_x
    x_direction = 1

    while True:
        # Update vertical pan position
        y += y_direction
        if y >= max_y:
            y = max_y
            y_direction = -1
        elif y <= min_y:
            y = min_y
            y_direction = 1

        # Update horizontal dot position
        x += x_direction * 3  # move faster side to side by 3 units per step
        if x >= max_x:
            x = 0

        # Apply positions to DMX
        dmx.set_channel(7, y)     # vertical pan main line
        dmx.set_channel(24, y)    # move line down/up together
        dmx.set_channel(25, x)    # dots side to side inside the line

        # Sleep for the smaller of the two speeds (to keep smoothness)
        time.sleep(0.02 / speed)

def crazyDots2(speed):
    # less random but funky movement
    dmx.set_channel(4, 78)
    movementSpeed = calculateSpeedForRange(128, 159, speed)
    while True:
        if movementSpeed > 159:
            movementSpeed = 159 # justincase
        dmx.set_channel(9, movementSpeed)
        dmx.set_channel(10, movementSpeed)

def twoCircleSpin(speed):
    movementSpeed = calculateSpeedForRange(192, 223, speed)
    while True:
        dmx.set_channel(4, 83)
        dmx.set_channel(6, movementSpeed)

def voiceWave(speed):
    movementSpeed = calculateSpeedForRange(128, 159, speed)
    while True:
        dmx.set_channel(4, 5) # circle
        dmx.set_channel(9, movementSpeed) # same as crazyDots

def setGlobalChannels():
    dmx.set_channel(1, 23) # on, auto
    dmx.set_channel(2, 0) # 100% pattern size
    dmx.set_channel(3, 255) # Group selection

def reset_dmx():
    for i in range(1, 34):
        dmx.set_channel(i, 0)
    setGlobalChannels()

def calculateSpeedForRange(start, stop, speed):
    # some of these patterns use the auto movement range instead of for loops for speed.
        # the higher the value the faster the built-in animation. Channels 9 and 10 mostly
    # this function takes the start (slow animation) and stop (fast animation) of the pattern,
    # gets the difference, divides it by 10 to get steps for our 0-9 speed input, and returns a new value to play the pattern at.
    difference = stop - start
    movementSpeed = start + speed * (difference / 10)
    return math.floor(movementSpeed)

reset_dmx()
circleZoomIn
crazyDots
dotRL
dotLR
wiggleLine
voiceWave(4)

print("Done!")
dmx.close()