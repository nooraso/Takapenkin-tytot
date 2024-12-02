import network
import time
import ujson
from umqtt.simple import MQTTClient
from piotimer import Piotimer as Timer
from ssd1306 import SSD1306_I2C
from machine import Pin, ADC, I2C, PWM
from fifo import Fifo
import utime
import array

# WiFi and MQTT Configuration
SSID = 'KMD751_Group_1'
PASSWORD = 'tytot123'
MQTT_BROKER = '192.168.1.190'  # Replace with your computer's IP
MQTT_PORT = 1883
MQTT_TOPIC = 'heart_rate_data'
MQTT_CLIENT_ID = 'pico_heart_rate_monitor'



def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(SSID, PASSWORD)
    
    max_wait = 10
    while max_wait > 0:
        if wlan.status() < 0 or wlan.status() >= 3:
            break
        max_wait -= 1
        print('waiting for connection...')
        utime.sleep(1)
    
    if wlan.status() != 3:
        print('network connection failed')
        return False
    else:
        print('Connected')
        return True

# MQTT Client Setup
def setup_mqtt():
    try:
        client = MQTTClient(MQTT_CLIENT_ID, MQTT_BROKER, keepalive=60)
        client.connect()
        return client
    except Exception as e:
        print('MQTT Connection Failed:', e)
        return None

# ADC-converter
adc = ADC(26)

# OLED
i2c = I2C(1, scl = Pin(15), sda = Pin(14))
oled = SSD1306_I2C(128, 64, i2c)

# LEDs
led_onboard = Pin("LED", Pin.OUT)
led21 = PWM(Pin(21))
led21.freq(1000)

# Rotary Encoder
rot = Pin(12, mode = Pin.IN, pull = Pin.PULL_UP)

# Sample Rate, Buffer
samplerate = 250
samples = Fifo(32)

# Menu selection variables and switch filtering
mode = 0
count = 0
switch_state = 0

def read_adc(tid):
    x = adc.read_u16()
    samples.put(x)


def aloitus():
    oled.fill(1)
    
    for i in range(6):
        oled.text("Taikasydan", 29, 27, 0)
    oled.show()
    utime.sleep_ms(3250)
    

def start():
    oled.fill(0)
    oled.text("Press to start", 4, 7, 1)
    oled.text("the measurement", 4, 17, 1)
    oled.line(10, 53, 15, 53, 1)
    oled.line(93, 53, 124, 53, 1)
    oled.line(118, 48, 124, 53, 1)
    oled.line(118, 58, 124, 53, 1)
    oled.line(118, 48, 124, 53, 1)
    oled.line(118, 58, 124, 53, 1)
    oled.line(93, 53, 124, 53, 1)
    oled.line(48, 53, 60, 53, 1)
    horizontal = 0
    
    for i in range(2):
        oled.line(60-horizontal, 53, 63-horizontal, 50, 1)
        oled.line(63-horizontal, 50, 66-horizontal, 53, 1)
        oled.line(66-horizontal, 53, 68-horizontal, 53, 1)
        oled.line(68-horizontal, 53, 70-horizontal, 57, 1)
        oled.line(70-horizontal, 57, 73-horizontal, 31, 1)
        oled.line(73-horizontal, 31, 76-horizontal, 64, 1)
        oled.line(76-horizontal, 64, 78-horizontal, 53, 1)
        oled.line(78-horizontal, 53, 80-horizontal, 53, 1)
        oled.line(80-horizontal, 53, 84-horizontal, 47, 1)
        oled.line(84-horizontal, 47, 88-horizontal, 53, 1)
        oled.line(88-horizontal, 53, 89-horizontal, 53, 1)
        oled.line(89-horizontal, 53, 91-horizontal, 51, 1)
        oled.line(91-horizontal, 51, 93-horizontal, 53, 1)
        
        horizontal += 45
        
    oled.show()
    

def ppi_cal(data):
    sumPPI = 0 
    for i in data:
        sumPPI += i
    rounded_PPI = round(sumPPI/len(data), 0)
    return int(rounded_PPI)


def hr_cal(meanPPI):
    rounded_HR = round(60*1000/meanPPI, 0)
    return int(rounded_HR)


def sdnn_cal(data, PPI):
    summary = 0
    for i in data:
        summary += (i-PPI)**2
    SDNN = (summary/(len(data)-1))**(1/2)
    rounded_SDNN = round(SDNN, 0)
    return int(rounded_SDNN)


def rmssd_cal(data):
    i = 0
    summary = 0
    while i < len(data) - 1:
        diff = (data[i+1] - data[i])**2
        summary += diff
        i += 1
    rmssd = (summary / (len(data) - 1)) ** 0.5
    return int(round(rmssd, 0))


def sdsd_cal(data):
    PP_array = array.array('l')
    i = 0
    first_value = 0
    second_value = 0
    while i < len(data)-1:
        PP_array.append(int(data[i+1])-int(data[i]))
        i += 1
    i = 0
    while i < len(PP_array)-1:
        first_value += float(PP_array[i]**2)
        second_value += float(PP_array[i])
        i += 1
    first = first_value/(len(PP_array)-1)
    second = (second_value/(len(PP_array)))**2
    rounded_SDSD = round((first - second)**(1/2), 0)
    return int(rounded_SDSD)

 
def sd1_cal(SDSD):
    rounded_SD1 = round(((SDSD**2)/2)**(1/2), 0)
    return int(rounded_SD1)


def sd2_cal(SDNN, SDSD):
    rounded_SD2 = round(((2*(SDNN**2))-((SDSD**2)/2))**(1/2), 0)
    return int(rounded_SD2)


aloitus()
avg_size = 128  # originally: int(samplerate * 0.5)
buffer = array.array('H',[0]*avg_size)

connect_wifi()
mqtt_client = setup_mqtt()

while True:
    start()
    new_state = rot.value()

    if new_state != switch_state:
        count += 1
        if count > 3:
            if new_state == 0:
                if mode == 0:
                    mode = 1
                else:
                    mode = 0
                led_onboard.value(1)
                time.sleep(0.15)
                led_onboard.value(0)
            switch_state = new_state
            count = 0
    else:
        count = 0
    utime.sleep(0.01)
    
    if mode == 1:
        count = 0
        switch_state = 0

        oled.fill(0)
        oled.show()
        
        x1 = -1
        y1 = 32
        m0 = 65535 / 2
        a = 1 / 10

        disp_div = samplerate / 25
        disp_count = 0
        capture_length = samplerate * 60  # 60 = 60s, changable respectively

        index = 0
        capture_count = 0
        subtract_prev_sample = 0
        sample_sum = 0

        min_bpm = 30
        max_bpm = 200
        sample_peak = 0
        sample_index = 0
        prev_peak = 0
        prev_index = 0
        interval_ms = 0
        PPI_array = []
        
        brightness = 0

        tmr = Timer(freq = samplerate, callback = read_adc)

        # Flag to track if measurement should continue
        measurement_active = True

        while capture_count < capture_length and measurement_active:
            # Check rotary encoder to stop measurement
            new_state = rot.value()
            if new_state != switch_state:
                count += 1
                if count > 3:
                    if new_state == 0:
                        # Stop measurement if rotary encoder is pressed
                        measurement_active = False
                        break
                    switch_state = new_state
                    count = 0
            else:
                count = 0

            if not samples.empty():
                x = samples.get()
                disp_count += 1
        
                if disp_count >= disp_div:
                    disp_count = 0
                    m0 = (1 - a) * m0 + a * x
                    y2 = int(32 * (m0 - x) / 14000 + 35)
                    y2 = max(10, min(53, y2))
                    x2 = x1 + 1
                    oled.fill_rect(0, 0, 128, 9, 1)
                    oled.fill_rect(0, 55, 128, 64, 1)
                    if len(PPI_array) > 3:
                        actual_PPI = ppi_cal(PPI_array)
                        actual_HR = hr_cal(actual_PPI)
                        oled.text(f'HR:{actual_HR}', 2, 1, 0)
                        oled.text(f'PPI:{interval_ms}', 60, 1, 0)
                    oled.text(f'Timer:  {int(capture_count/samplerate)}s', 18, 56, 0)
                    oled.line(x2, 10, x2, 53, 0)
                    oled.line(x1, y1, x2, y2, 1)
                    oled.show()
                    x1 = x2
                    if x1 > 127:
                        x1 = -1
                    y1 = y2

                if subtract_prev_sample:
                    old_sample = buffer[index]
                else:
                    old_sample = 0
                sample_sum = sample_sum + x - old_sample

                if subtract_prev_sample:
                    sample_avg = sample_sum / avg_size
                    sample_val = x
                    if sample_val > (sample_avg * 1.05):
                        if sample_val > sample_peak:
                            sample_peak = sample_val
                            sample_index = capture_count

                    else:
                        if sample_peak > 0:
                            if (sample_index - prev_index) > (60 * samplerate / min_bpm):
                                prev_peak = 0
                                prev_index = sample_index
                            else:
                                if sample_peak >= (prev_peak*0.8):
                                    if (sample_index - prev_index) > (60 * samplerate / max_bpm):
                                        if prev_peak > 0:
                                            interval = sample_index - prev_index
                                            interval_ms = int(interval * 1000 / samplerate)
                                            PPI_array.append(interval_ms)
                                            brightness = 5
                                            led21.duty_u16(4000)
                                        prev_peak = sample_peak
                                        prev_index = sample_index
                        sample_peak = 0

                    if brightness > 0:
                        brightness -= 1
                    else:
                        led21.duty_u16(0)

                buffer[index] = x
                capture_count += 1
                index += 1
                if index >= avg_size:
                    index = 0
                    subtract_prev_sample = 1

        tmr.deinit()
        
        while not samples.empty():
            x = samples.get()

        oled.fill(0)
        if len(PPI_array) >= 3 and measurement_active:       
            mean_PPI = ppi_cal(PPI_array)
            mean_HR = hr_cal(mean_PPI)
            SDNN = sdnn_cal(PPI_array, mean_PPI)
            RMSSD = rmssd_cal(PPI_array)
            SDSD = sdsd_cal(PPI_array)
            SD1 = sd1_cal(SDSD)
            SD2 = sd2_cal(SDNN, SDSD)
            
# MQTT Publishing
            if mqtt_client:
                try:
                    data = {
                        'mean_PPI': int(mean_PPI),
                        'mean_HR': int(mean_HR),
                        'SDNN': int(SDNN),
                        'RMSSD': int(RMSSD),
                        'SD1': int(SD1),
                        'SD2': int(SD2)
                    }
                    mqtt_client.publish(MQTT_TOPIC, ujson.dumps(data))
                    print('Data published to MQTT')
                except Exception as e:
                    print('MQTT Publish Error:', e)
         
            oled.text('MeanPPI:'+ str(int(mean_PPI)) +' ms', 0, 0, 1)
            oled.text('MeanHR:'+ str(int(mean_HR)) +' bpm', 0, 9, 1)
            oled.text('SDNN:'+str(int(SDNN)) +' ms', 0, 18, 1)
            oled.text('RMSSD:'+str(int(RMSSD)) +' ms', 0, 27, 1)
            oled.text('SD1:'+str(int(SD1))+' SD2:'+str(int(SD2)), 0, 36, 1)
        elif not measurement_active:
            oled.text('Measurement', 20, 10, 1)
            oled.text('Stopped', 35, 30, 1)
            oled.text('Press to exit', 15, 50, 1)
        else:
            oled.text('Error', 45, 10, 1)
            oled.text('Please restart', 8, 30, 1)
            oled.text('measurement', 20, 40, 1)
        oled.show()
        
        # Wait for user to exit results screen
        while mode == 1:
            new_state = rot.value()
            if new_state != switch_state:
                count += 1
                if count > 3:
                    if new_state == 0:
                        mode = 0
                        led_onboard.value(1)
                        time.sleep(0.15)
                        led_onboard.value(0)
                    switch_state = new_state
                    count = 0
            else:
                count = 0
            utime.sleep(0.01)
