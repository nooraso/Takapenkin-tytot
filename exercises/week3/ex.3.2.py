import time
from machine import I2C, Pin
from ssd1306 import SSD1306_I2C

i2c = I2C(1, scl=Pin(15), sda=Pin(14), freq=400000)
oled_width = 128
oled_height = 64
oled = SSD1306_I2C(oled_width, oled_height, i2c)

button_up = Pin(9, Pin.IN, Pin.PULL_UP)  # SW0
button_down = Pin(8, Pin.IN, Pin.PULL_UP)  # SW2
button_clear = Pin(7, Pin.IN, Pin.PULL_UP)  # SW1

# GPIO setup for LEDs and rotary encoder
LED_PINS = [Pin(22, Pin.OUT), Pin(21, Pin.OUT), Pin(20, Pin.OUT)]
ENCODER_A = Pin(11, Pin.IN)
ENCODER_B = Pin(12, Pin.IN)
ENCODER_BUTTON = Pin(7, Pin.IN, Pin.PULL_UP)

# Constants
BOUNCE_THRESHOLD = 50  # Debounce threshold in ms
MENU_ITEMS = ["LED1", "LED2", "LED3"]

# Globals
menu_position = 0        # Current menu selection
led_states = [False, False, False]  # LED states (all OFF initially)
last_button_press = 0    # Last press time for debounce
rotation_flag = None     # Tracks rotation direction
button_pressed = False   # Tracks button press

# Rotary encoder handling
def encoder_turn_handler(pin):
    global rotation_flag
    if ENCODER_A.value() == ENCODER_B.value():
        rotation_flag = "RIGHT"
    else:
        rotation_flag = "LEFT"

# Button press handler with debounce
def encoder_button_handler(pin):
    global button_pressed, last_button_press
    current_time = time.ticks_ms()
    if time.ticks_diff(current_time, last_button_press) > BOUNCE_THRESHOLD:
        last_button_press = current_time
        button_pressed = True

# Attach interrupt handlers for encoder and button
ENCODER_A.irq(trigger=Pin.IRQ_RISING, handler=encoder_turn_handler)
ENCODER_BUTTON.irq(trigger=Pin.IRQ_FALLING, handler=encoder_button_handler)

# Update OLED display to show the menu and LED states
def update_display():
    oled.fill(0)  # Clear display
    for i, led in enumerate(led_states):
        led_status = "ON" if led else "OFF"
        selector = ">" if i == menu_position else " "  # Highlight selected item
        oled.text(f"{selector} {MENU_ITEMS[i]} - {led_status}", 0, i * 10)  # Print each item
    oled.show()

# Toggle LED state
def toggle_led(index):
    led_states[index] = not led_states[index]
    LED_PINS[index].value(led_states[index])
def main():
    global menu_position, rotation_flag, button_pressed  # Declare globals
    print("Menu initialized")
    update_display()

    while True:
        if rotation_flag:
            if rotation_flag == "RIGHT":
                menu_position = (menu_position + 1) % len(MENU_ITEMS)
            elif rotation_flag == "LEFT":
                menu_position = (menu_position - 1) % len(MENU_ITEMS)
            rotation_flag = None  # Clear flag after processing
            update_display()

        if button_pressed:
            toggle_led(menu_position)
            button_pressed = False  # Clear press flag after processing
            update_display()

        time.sleep(0.1)  # Small delay to reduce flicker

# Run the main program loop
main()