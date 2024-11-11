from machine import I2C, Pin
import ssd1306
import time

# Initialize OLED display
i2c = I2C(1, scl=Pin(15), sda=Pin(14), freq=400000)
oled_width = 128
oled_height = 64
oled = ssd1306.SSD1306_I2C(oled_width, oled_height, i2c)

# Read data first
data = []
with open("capture_250Hz_02.txt", "r") as file:
    for line in file:
        data.append(int(line))

# Initialize scaling variables
prev_min = None
prev_max = None

def plot_window(start_index):
    global prev_min, prev_max
    
    # Check if enough data remains
    if start_index + (oled_width * 5) > len(data):
        return False
        
    # Clear display
    oled.fill(0)
    
    # Initialize or use previous scaling
    if prev_min is None:
        window_data = data[start_index:start_index + 250]
        prev_min = min(window_data)
        prev_max = max(window_data)
    
    scale = prev_max - prev_min if prev_max != prev_min else 1
    
    # Plot averaged data points
    for pixel in range(oled_width):
        sample_start = start_index + (pixel * 5)
        samples = data[sample_start:sample_start + 5]
        avg_value = sum(samples) / len(samples)
        
        # Scale to screen height
        y = int((avg_value - prev_min) / scale * (oled_height - 1))
        y = max(0, min(y, oled_height - 1))
        
        # Plot pixel
        oled.pixel(pixel, oled_height - 1 - y, 1)
    
    # Calculate next window's min/max
    next_window = data[start_index + 250:start_index + 500]
    if next_window:
        prev_min = min(next_window)
        prev_max = max(next_window)
    
    oled.show()
    return True

# Main loop 
start_index = 0
while plot_window(start_index):
    start_index += 250
    time.sleep(1)
