from machine import Pin, I2C
import ssd1306
import time
from fifo import Fifo


def map_value(value, in_min, in_max, out_min, out_max):
    return int((value - in_min) * (out_max - out_min) / (in_max - in_min) + out_min)

# EKG
def draw_ekg(oled, data, window_start, offset=0, scale=1):
    oled.fill(0)  
    for x in range(127):  
        idx = window_start + x
        if idx + 1 < len(data):
            y1 = map_value(data[idx] * scale - offset, min(data), max(data), 0, 63)
            y2 = map_value(data[idx + 1] * scale - offset, min(data), max(data), 0, 63)
            oled.line(x, 63 - y1, x + 1, 63 - y2, 1)  # Flip vertically for OLED
    oled.show()

# Function to read data 
def read_and_average_data(filename):
    try:
        with open(filename, 'r') as f:
            raw_data = [int(line.strip()) for line in f.readlines()]
        averaged_data = [
            sum(raw_data[i:i+5]) // 5 for i in range(0, len(raw_data), 5)
        ]
        return averaged_data
    except Exception as e:
        print(f"Error reading file: {e}")
        return []

i2c = I2C(1, scl=Pin(15), sda=Pin(14), freq=400000)
oled = ssd1306.SSD1306_I2C(128, 64, i2c, addr=0x3C)

sw_1 = Pin(8, Pin.IN, Pin.PULL_UP)  # Read file
sw_2 = Pin(7, Pin.IN, Pin.PULL_UP)  # Adjust scaling
sw_0 = Pin(9, Pin.IN, Pin.PULL_UP)  # Adjust offset
sw_file = Pin(16, Pin.IN, Pin.PULL_UP)  # Switch between files

rot_a = Pin(10, Pin.IN, Pin.PULL_UP)
rot_b = Pin(11, Pin.IN, Pin.PULL_UP)

window_start = 0
scale = 1
offset = 0
data = []  # EKG data
current_file = 1  # Default to '01'

class Encoder:
    def __init__(self, a, b):
        self.a = a
        self.b = b
        self.fifo = Fifo(30, typecode='i')  # Store rotation events
        self.a.irq(handler=self.handler, trigger=Pin.IRQ_RISING, hard=True)

    def handler(self, pin):
        if self.b.value():
            self.fifo.put(-1)  # Rotate left
        else:
            self.fifo.put(1)  # Rotate right

encoder = Encoder(rot_a, rot_b)

file_names = ['capture_250Hz_01.txt', 'capture_250Hz_02.txt', 'capture_250Hz_03.txt']

try:
    while True:
        # Read EKG data from file when SW_1 is pressed
        if not sw_1.value():  # Button is pressed
            data = read_and_average_data(file_names[current_file - 1])
            if not data:
                oled.fill(0)
                oled.text("No data found", 0, 0)
                oled.show()
                time.sleep(1)
            else:
                window_start = 0

        # Switch between files when SW_FILE is pressed
        if not sw_file.value():  # Button is pressed
            current_file = (current_file % 3) + 1  # Cycle through 1, 2, 3
            oled.fill(0)
            oled.text(f"Using: {file_names[current_file - 1]}", 0, 0)
            oled.show()
            time.sleep(1)

        # Adjust scale with SW_2
        if not sw_2.value():  # Button is pressed
            if encoder.fifo.has_data():
                scale += encoder.fifo.get()
                scale = max(1, min(scale, 10))  # Keep scale in a reasonable range

        # Adjust offset with SW_0
        if not sw_0.value():  # Button is pressed
            if encoder.fifo.has_data():
                offset += encoder.fifo.get()
                offset = max(0, min(offset, 100))  # Keep offset in a reasonable range

        # Scroll EKG data using rotary encoder
        if encoder.fifo.has_data():
            rotation = encoder.fifo.get()
            window_start += rotation
            # Prevent scrolling beyond bounds
            window_start = max(0, min(window_start, len(data) - 128))

        # Draw EKG
        if data:
            draw_ekg(oled, data, window_start, offset, scale)
        else:
            oled.fill(0)
            oled.text("Press SW1", 0, 0)
            oled.show()

        time.sleep(0.05)  # Small delay for smoother updates
except KeyboardInterrupt:
    print("Exiting...")
    oled.fill(0)
    oled.show()