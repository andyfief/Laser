import time
import serial
import threading

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