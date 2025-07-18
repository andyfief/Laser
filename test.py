import time
import random
random.seed(time.time())
import serial.tools.list_ports
from DMXClass import SimpleDMX

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
    for i in range(0, 127):
        dmx.set_channel(5, i) # Circle Zooming in = 160 + speed <= 191
        time.sleep(1/(100*speed))

def crazyDots(speed):
    dmx.set_channel(4, 16) # Dot
    for i in range(0, 20): # number of dots / 2
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

def sideToSideDot(speed):
    dmx.set_channel(4, 16) # Dot
    dotRL(speed)
    dotLR(speed)

def horizontalLineRL(speed): # right to left
    # Pans horizontally left once
    dmx.set_channel(4, 45)
    for i in range(33, 96): # channel 9 left-right range
        dmx.set_channel(8, i)
        time.sleep(1/(100 * speed))

def horizontalLineLR(speed): # left to right
    # Pans horizontally left once
    dmx.set_channel(4, 45)
    for i in range(96, 33, -1): # channel 9 left-right range
        dmx.set_channel(8, i)
        time.sleep(1/(100 * speed))

def horizontalLineSideToSide(speed):
    horizontalLineRL(speed)
    horizontalLineLR(speed)

def setGlobalChannels():
    dmx.set_channel(1, 23) # on, auto
    dmx.set_channel(2, 0) # pattern group 2
    dmx.set_channel(3, 255) # 100% pattern size

def reset_dmx():
    for i in range(1, 34):
        dmx.set_channel(i, 0)
    setGlobalChannels()


reset_dmx()
circleZoomIn(7)

reset_dmx()
dotLR(7)
dotRL(7)

reset_dmx()
sideToSideDot(7)
crazyDots(7)

reset_dmx()
horizontalLineRL(7)
horizontalLineLR(7)

reset_dmx()
horizontalLineSideToSide(7)

print("Done!")
dmx.close()