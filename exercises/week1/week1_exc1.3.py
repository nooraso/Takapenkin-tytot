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


x = 0
y = oled_height // 2


oled.fill(0)
oled.show()

while True:
    oled.pixel(x, y, 1)
    oled.show()

    if not button_up.value():
        if y > 0:
            y -= 1
    elif not button_down.value():
        if y < oled_height - 1:
            y += 1
    elif not button_clear.value():
        oled.fill(0)
        x = 0
        y = oled_height // 2

    x += 1
    if x >= oled_width:
        x = 0

    time.sleep(0.05)

