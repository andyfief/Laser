# === DMX Pattern Testing Suite ===
# Interactive testing tool for viewing patterns frame by frame

import time
import serial.tools.list_ports
import serial
from DMXClass import SimpleDMX
from pattern_functions import pattern_groups, reset_pattern_states
import inspect

class PatternTester:
    def __init__(self):
        self.dmx = None
        self.current_pattern = None
        self.current_speed = 5
        self.frame_count = 0
        self.auto_mode = False
        
    def check_device(self):
        """Check if DMX device is available on COM3."""
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
    
    def setup_dmx(self):
        """Initialize DMX controller."""
        if not self.check_device():
            print("DMX device not available. Running in simulation mode.")
            return False
            
        self.dmx = SimpleDMX()
        self.set_global_channels()
        return True
    
    def set_global_channels(self):
        """Set global DMX channels."""
        if self.dmx:
            self.dmx.set_channel(1, 23)  # On/Auto mode
            self.dmx.set_channel(2, 0)   # Pattern group
            self.dmx.set_channel(3, 255) # Pattern size/brightness
    
    def reset_dmx(self):
        """Reset all DMX channels to 0 and reapply globals."""
        if self.dmx:
            for i in range(1, 34):
                self.dmx.set_channel(i, 0)
            self.set_global_channels()
    
    def get_all_patterns(self):
        """Get all available patterns organized by group."""
        all_patterns = {}
        pattern_index = 1
        
        for group_num, functions in pattern_groups.items():
            all_patterns[group_num] = []
            for func in functions:
                all_patterns[group_num].append((pattern_index, func))
                pattern_index += 1
                
        return all_patterns
    
    def display_menu(self):
        """Display the main menu with all available patterns."""
        print("\n" + "="*60)
        print("DMX PATTERN TESTING SUITE")
        print("="*60)
        
        all_patterns = self.get_all_patterns()
        
        for group_num, patterns in all_patterns.items():
            print(f"\nGroup {group_num}:")
            for idx, func in patterns:
                print(f"  {idx:2d}. {func.__name__}")
        
        print(f"\nCurrent Settings:")
        print(f"  Pattern: {self.current_pattern.__name__ if self.current_pattern else 'None'}")
        print(f"  Speed: {self.current_speed}")
        print(f"  Frame: {self.frame_count}")
        print(f"  Auto Mode: {'ON' if self.auto_mode else 'OFF'}")
        
        print(f"\nControls:")
        print(f"  1-{len([p for group in all_patterns.values() for p in group])}: Select pattern")
        print(f"  s: Set speed (1-10)")
        print(f"  n: Next frame")
        print(f"  a: Toggle auto mode")
        print(f"  r: Reset pattern state")
        print(f"  c: Clear/turn off lights")
        print(f"  q: Quit")
        print("="*60)
    
    def get_pattern_by_index(self, index):
        """Get pattern function by its menu index."""
        all_patterns = self.get_all_patterns()
        current_index = 1
        
        for group_num, patterns in all_patterns.items():
            for idx, func in patterns:
                if current_index == index:
                    return func
                current_index += 1
        return None
    
    def execute_frame(self, autoFlag):
        """Execute one frame of the current pattern."""
        if not self.current_pattern:
            print("No pattern selected.")
            return
            
        try:
            if self.dmx:
                self.current_pattern(self.dmx, self.current_speed)
            else:
                # Simulation mode - just print what would happen
                print(f"[SIM] Executing {self.current_pattern.__name__} frame {self.frame_count} at speed {self.current_speed}")
            
            self.frame_count += 1
            if not autoFlag:
                print(f"Frame {self.frame_count} executed for {self.current_pattern.__name__}")
            
        except Exception as e:
            print(f"Error executing pattern: {e}")
    
    def auto_run(self):
        """Run pattern continuously in auto mode."""
        from threading import Thread
        
        print(f"Auto mode started for {self.current_pattern.__name__ if self.current_pattern else 'None'}")
        print("Use 'a' to toggle auto mode off, or any other commands while it runs...")
        
        def pattern_loop():
            while self.auto_mode and self.current_pattern:
                try:
                    self.execute_frame(autoFlag=1)
                except Exception as e:
                    print(f"Error in auto mode: {e}")
        
        # Start pattern loop in background thread
        auto_thread = Thread(target=pattern_loop, daemon=True)
        auto_thread.start()
        
        # Return control to main menu immediately
    
    def run(self):
        """Main testing loop."""
        self.setup_dmx()
        
        while True:
            self.display_menu()
            
            try:
                choice = input("\nEnter command: ").strip().lower()
                
                if choice == 'q':
                    break
                elif choice == 'n':
                    self.execute_frame(autoFlag=0)
                elif choice == 'a':
                    self.auto_mode = not self.auto_mode
                    if self.auto_mode:
                        self.auto_run()
                elif choice == 'r':
                    reset_pattern_states()
                    self.frame_count = 0
                    self.reset_dmx()
                    print("Pattern state reset.")
                elif choice == 'c':
                    self.current_pattern = None
                    self.frame_count = 0
                    self.reset_dmx()
                    print("Lights cleared.")
                elif choice == 's':
                    try:
                        new_speed = int(input("Enter speed (1-10): "))
                        if 1 <= new_speed <= 10:
                            self.current_speed = new_speed
                        else:
                            print("Speed must be between 1 and 10.")
                    except ValueError:
                        print("Invalid speed value.")
                elif choice.isdigit():
                    # Pattern selection
                    pattern_index = int(choice)
                    selected_pattern = self.get_pattern_by_index(pattern_index)
                    
                    if selected_pattern:
                        self.current_pattern = selected_pattern
                        self.frame_count = 0
                        reset_pattern_states()
                        self.reset_dmx()
                        print(f"Selected pattern: {selected_pattern.__name__}")
                    else:
                        print("Invalid pattern number.")
                else:
                    print("Invalid command.")
                    
            except KeyboardInterrupt:
                print("\nExiting...")
                break
            except Exception as e:
                print(f"Error: {e}")
        
        # Cleanup
        if self.dmx:
            self.reset_dmx()
            self.dmx.close()
        print("Testing suite closed.")

if __name__ == "__main__":
    tester = PatternTester()
    tester.run()