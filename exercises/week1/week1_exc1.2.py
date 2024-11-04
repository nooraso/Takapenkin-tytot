import time
from machine import I2C, Pin
from ssd1306 import SSD1306_I2C

i2c = I2C(1, scl=Pin(15), sda=Pin(14), freq=400000)
oled_width = 128
oled_height = 64
oled = SSD1306_I2C(oled_width, oled_height, i2c)

line_height = 10
max_lines = oled_height // line_height
lines = []

while True:
    oled.fill(0)
    user_input = input("Enter text: ")
    lines.append(user_input)

    if len(lines) > max_lines:
        lines.pop(0)
    for i, line in enumerate(lines):
        oled.text(line, 0, i * line_height)

    oled.show()

    time.sleep(0.1)

