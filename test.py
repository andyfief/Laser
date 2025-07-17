#!/usr/bin/env python3
"""
Simple DMX Control for COM3
Basic channel control for 36 channels
"""

import time
import random
random.seed(time.time())
import serial
import serial.tools.list_ports
import threading

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

class SimpleDMX:
    def __init__(self):
        self.ser = serial.Serial(
            port='COM3',
            baudrate=250000,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_TWO,
            timeout=1
        )
        # DMX universe: start code + 512 channels
        self.dmx_data = bytearray(34)
        self.dmx_data[0] = 0  # Start code
        
        # Threading for continuous transmission
        self.running = True
        self.transmit_thread = threading.Thread(target=self._continuous_transmit)
        self.transmit_thread.daemon = True
        self.transmit_thread.start()
        
    def _continuous_transmit(self):
        """Continuously send DMX data at ~40fps (closer to standard)"""
        while self.running:
            self._send_dmx()
            time.sleep(1/40)  # ~40fps transmission rate
    
    def _send_dmx(self):
        """Send DMX data with proper timing"""
        # Send break (longer for better compatibility)
        self.ser.break_condition = True
        time.sleep(0.000176)  # 176 microseconds break
        self.ser.break_condition = False
        time.sleep(0.000012)  # 12 microseconds mark after break
        
        # Send data
        self.ser.write(self.dmx_data)
        self.ser.flush()
    
    def set_channel(self, channel, value):
        """Set channel (1-34) to value (0-255)"""
        if 1 <= channel <= 34:
            self.dmx_data[channel] = max(0, min(255, value))
            # No need to send_dmx() here - continuous thread handles it
    
    def close(self):
        """Close connection"""
        self.running = False
        self.transmit_thread.join()
        self.ser.close()

# Check device first
if not check_device():
    print("Cannot proceed - device check failed")
    exit()

print("\nDevice check passed! Starting DMX control...")

# Create DMX controller
dmx = SimpleDMX()

def reset_dmx():
    for i in range(1, 34):
        dmx.set_channel(i, 0)

def crazyDots():
    dmx.set_channel(2, 0) # pattern group 2
    dmx.set_channel(3, 255) # 100% pattern size
    dmx.set_channel(4, 5) # circle
    dmx.set_channel(1, 250) # on

    for i in range(0, 20):
        dmx.set_channel(5, 127) # Zoomed in all the way (dot)
        dmx.set_channel(7, random.randint(0, 127))
        dmx.set_channel(8, random.randint(0, 127))
        time.sleep(0.05)
        print("dot")
        
        time.sleep(0.05)
        print("dot")

def zoomCircle(speed):
    assert(1 <= speed <= 32)
    dmx.set_channel(2, 0) # 100% pattern size
    dmx.set_channel(3, 255) # pattern group 2
    dmx.set_channel(4, 5) # circle
    dmx.set_channel(1, 23) # on, auto
    dmx.set_channel(11, 180) # color change to see pattern switch
    dmx.set_channel(5, 159 + speed) # Circle = 127, + speed = 128 - 159
    time.sleep(4)

crazyDots()
reset_dmx()
print("zoom")
zoomCircle(32)

print("Done!")
dmx.close()