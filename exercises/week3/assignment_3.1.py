from machine import Pin, PWM
import time

ENCODER_A = Pin(11, Pin.IN, pull=Pin.PULL_UP)  
ENCODER_B = Pin(10, Pin.IN, pull=Pin.PULL_UP)  
ENCODER_BUTTON = Pin(12, Pin.IN, pull=Pin.PULL_UP)  


LEDs = [Pin(20, Pin.OUT), Pin(21, Pin.OUT), Pin(22, Pin.OUT)]
led_pwm = [PWM(LEDs[i]) for i in range(len(LEDs))]  


for pwm in led_pwm:
    pwm.freq(1000)  
    pwm.duty_u16(0)   


rotation_flag = None
brightness = 0  
led_on = False
debounce_time = 200  
last_button_press = 0
brightness_step = 1000  # Amount of brightness adjustment per encoder turn


def encoder_button_handler(pin):
    global button_pressed, last_button_press, led_on, brightness
    current_time = time.ticks_ms()
    if time.ticks_diff(current_time, last_button_press) > debounce_time:
        last_button_press = current_time
        led_on = not led_on  # Toggle LED state
        if led_on:
            brightness = 3000  
            set_brightness(brightness)
        else:
            for pwm in led_pwm:
                pwm.duty_u16(0)  

def encoder_turn_handler(pin):
    global rotation_flag, brightness
    if ENCODER_A.value() == ENCODER_B.value():
        rotation_flag = "RIGHT"  # Clockwise rotation
    else:
        rotation_flag = "LEFT"  # Counter-clockwise rotation

def set_brightness(brightness):
    brightness = max(0, min(brightness, 65535))
    for pwm in led_pwm:
        pwm.duty_u16(brightness)

ENCODER_A.irq(trigger=Pin.IRQ_RISING, handler=encoder_turn_handler)
ENCODER_B.irq(trigger=Pin.IRQ_RISING, handler=encoder_turn_handler)
ENCODER_BUTTON.irq(trigger=Pin.IRQ_FALLING, handler=encoder_button_handler)

# Main loop
while True:
    if rotation_flag == "RIGHT":
        # Increase brightness when rotating clockwise
        brightness += brightness_step
        brightness = min(brightness, 65535)  
        set_brightness(brightness)
        rotation_flag = None  # Reset the flag after handling

    elif rotation_flag == "LEFT":
        brightness -= brightness_step
        brightness = max(brightness, 0) 
        set_brightness(brightness)
        rotation_flag = None  

    time.sleep(0.1)  # Small delay to prevent overloading the CPU       

