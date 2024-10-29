from machine import Pin, I2C
from ssd1306 import SSD1306_I2C
import time

# Constants
SCREEN_WIDTH = 128
UFO = "<=>"
UFO_WIDTH = 28

# Modified button setup - try with pull-up instead of pull-down
button_left = Pin(7, Pin.IN, Pin.PULL_UP)   # SW2
button_right = Pin(9, Pin.IN, Pin.PULL_UP)  # SW0

# I2C setup
i2c = I2C(1, scl=Pin(15), sda=Pin(14), freq=400000)
oled = SSD1306_I2C(128, 64, i2c, addr=0x3C)

# Initial position
ufo_position = (SCREEN_WIDTH - UFO_WIDTH) // 2

def draw_ufo():
    oled.fill(0)
    oled.text(UFO, ufo_position, 50)
    oled.show()

def test_buttons():
    """Test the button inputs by printing their values."""
    while True:
        # With pull-up, pressed = 0, not pressed = 1
        left_pressed = not button_left.value()
        right_pressed = not button_right.value()
        
        if left_pressed:
            print("SW2 (Left) pressed")
        if right_pressed:
            print("SW0 (Right) pressed")
        time.sleep(0.1)

def move_ufo():
    global ufo_position
    while True:
        # With pull-up, pressed = 0, not pressed = 1
        if not button_left.value():
            if ufo_position > 0:
                ufo_position -= 5
                draw_ufo()
            time.sleep(0.1)
            
        if not button_right.value():
            if ufo_position < SCREEN_WIDTH - UFO_WIDTH:
                ufo_position += 5
                draw_ufo()
            time.sleep(0.1)

# Initial screen draw
draw_ufo()

move_ufo()      # Run the UFO movement
