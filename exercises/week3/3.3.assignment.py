from machine import I2C, Pin
import ssd1306
import time
from filefifo import Filefifo
from fifo import Fifo

# Initialize I2C and OLED display
i2c = I2C(1, scl=Pin(15), sda=Pin(14), freq=400000)
oled_width = 128
oled_height = 64
oled = ssd1306.SSD1306_I2C(oled_width, oled_height, i2c)

# Scroll variables
WINDOW_SIZE = oled_width
MAX_SCROLL_INDEX = 1000 - WINDOW_SIZE
MIN_SCROLL_INDEX = 0
SCROLL_STEP = 10  # Increased scroll step size (adjust this value to change scroll speed)

# Simple FIFO queue implementation
turn_fifo = Fifo(size=10)

# Read values from file
values = []
fifo = Filefifo(size=1000, name='capture_250Hz_01.txt')
for _ in range(1000):
    try:
        value = fifo.get()
        values.append(int(value))
    except RuntimeError:
        break

# Find minimum and maximum values
minimum = min(values)
maximum = max(values)
value_range = maximum - minimum

def map_value(value, from_min, from_max, to_min, to_max):
    """Map a value from one range to another"""
    return (value - from_min) * (to_max - to_min) / (from_max - from_min) + to_min

def display(values, start_index):
    oled.fill(0)  # Clear the display
    
    # Display min and max values
    oled.text(f"Max:{maximum}", 0, 0)
    oled.text(f"Min:{minimum}", 0, 8)
    
    # Calculate graph area
    graph_top = 20
    graph_height = oled_height - graph_top
    
    # Draw the line graph
    for i in range(WINDOW_SIZE - 1):
        if start_index + i + 1 >= len(values):
            break
            
        x1 = i
        x2 = i + 1
        
        y1 = int(map_value(values[start_index + i], minimum, maximum, 
                          graph_height + graph_top - 1, graph_top))
        y2 = int(map_value(values[start_index + i + 1], minimum, maximum, 
                          graph_height + graph_top - 1, graph_top))
        
        oled.line(x1, y1, x2, y2, 1)
    
    # Display current position indicator
    position = int((start_index / MAX_SCROLL_INDEX) * 100)
    oled.text(f"{position}%", 90, 0)  # Added position indicator
    
    oled.show()

def encoder_callback(pin):
    global last_a, last_b, scroll_index
    a_val = encoder_a.value()
    b_val = encoder_b.value()
    
    if a_val != last_a or b_val != last_b:
        if a_val == last_b:
            try:
                turn_fifo.put(1)  # Clockwise turn
            except RuntimeError:
                pass
        else:
            try:
                turn_fifo.put(-1)  # Counter-clockwise turn
            except RuntimeError:
                pass
    last_a = a_val
    last_b = b_val

# Set up rotary encoder pins and interrupts
encoder_a = Pin(11, Pin.IN, Pin.PULL_UP)
encoder_b = Pin(12, Pin.IN, Pin.PULL_UP)
encoder_a.irq(trigger=Pin.IRQ_RISING | Pin.IRQ_FALLING, handler=encoder_callback)
encoder_b.irq(trigger=Pin.IRQ_RISING | Pin.IRQ_FALLING, handler=encoder_callback)

# Initialize last known states of encoder pins
last_a = encoder_a.value()
last_b = encoder_b.value()

# Initial scroll position
scroll_index = 0

# Main loop
while True:
    # Check for turns
    if not turn_fifo.empty():
        turn = turn_fifo.get()
        # Update scroll index based on turn with increased step size
        if turn > 0:
            scroll_index = min(scroll_index + SCROLL_STEP, MAX_SCROLL_INDEX)
        elif turn < 0:
            scroll_index = max(scroll_index - SCROLL_STEP, MIN_SCROLL_INDEX)

    # Display current window of values
    display(values, scroll_index)
    time.sleep(0.05)  # Reduced sleep time for more responsive updates

