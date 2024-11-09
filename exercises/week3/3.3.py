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
WINDOW_SIZE = 128  # Number of lines to display on the OLED
MAX_SCROLL_INDEX = 1000 - WINDOW_SIZE  # Adjust based on the number of values
MIN_SCROLL_INDEX = 0

# Simple FIFO queue implementation
turn_fifo = Fifo(size=10)  # Use the Fifo class with a size of 10

# Read 1000 values from a file to a list using Filefifo
values = []
fifo = Filefifo(size=1000, name='capture_250Hz_01.txt')
for _ in range(1000):
    try:
        value = fifo.get()  # Read a line
        values.append(int(value))
    except RuntimeError:
        break  # Stop reading if out of data

# Find minimum and maximum values from the list
minimum = min(values)
maximum = max(values)

# Initialize the window position
scroll_index = 0

def display(values, start_index):
    oled.fill(0)  # Clear the display
    for i in range(WINDOW_SIZE):
        if start_index + i < len(values):
            oled.text(str(values[start_index + i]), 0, i * 8)  # Display each value on a new line
    oled.show()

def encoder_callback(pin):
    global last_a, last_b
    a_val = encoder_a.value()
    b_val = encoder_b.value()
    if a_val != last_a or b_val != last_b:
        if a_val == b_val:
            try:
                turn_fifo.put(1)  # Clockwise turn
            except RuntimeError:
                pass  # Ignore if FIFO is full
        else:
            try:
                turn_fifo.put(-1)  # Counter-clockwise turn
            except RuntimeError:
                pass  # Ignore if FIFO is full
    last_a = a_val
    last_b = b_val

# Set up rotary encoder pins and interrupts
encoder_a = Pin(11, Pin.IN, Pin.PULL_UP)  # Encoder A pin
encoder_b = Pin(12, Pin.IN, Pin.PULL_UP)  # Encoder B pin
encoder_a.irq(trigger=Pin.IRQ_RISING | Pin.IRQ_FALLING, handler=encoder_callback)
encoder_b.irq(trigger=Pin.IRQ_RISING | Pin.IRQ_FALLING, handler=encoder_callback)

# Initialize last known states of encoder pins
last_a = encoder_a.value()
last_b = encoder_b.value()

# Main loop
while True:
    # Check for turns
    if not turn_fifo.empty():
        turn = turn_fifo.get()
        # Update scroll index based on turn
        if turn > 0 and scroll_index < MAX_SCROLL_INDEX:
            scroll_index += 1
        elif turn < 0 and scroll_index > MIN_SCROLL_INDEX:
            scroll_index -= 1

    # Display current window of values
    display(values, scroll_index)
    time.sleep(0.1)
