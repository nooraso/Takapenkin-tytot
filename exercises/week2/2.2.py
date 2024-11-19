from filefifo import Filefifo
import time

def scale_data(signal, min_value, max_value):
    for i in range(len(signal)):
        signal[i] = (signal[i] - min_value) / (max_value - min_value) * 100


data = Filefifo(10, name='capture_250Hz_01.txt')


signal = [data.get() for _ in range(1000)]


min_value = min(signal)
max_value = max(signal)

scale_data(signal, min_value, max_value)

print("Scaled Values:")
for i, value in enumerate(signal):
    print(value)
    if (i + 1) % 100 == 0:
        time.sleep(0.5)


peaks = []

for i in range(1, len(signal) - 1):
    if signal[i - 1] < signal[i] > signal[i + 1]:
        peaks.append(i)


sampling_rate = 100


if len(peaks) >= 3:
    samples = [peaks[i + 1] - peaks[i] for i in range(3)]
    seconds = [interval / sampling_rate for interval in samples]


    for i in range(3):
        frequency = 1 / seconds[i]
        print(f"signal {i + 1}: {samples[i]}, {seconds[i]:.1f} s, {frequency:.1f} Hz")


    average = sum(seconds) / len(seconds)
    average_frequency = 1 / average


    print(f"\nAverage signal frequency: {average_frequency:.1f} Hz")
else:
    print("Not enough peaks detected to calculate intervals")


import sys
sys.modules['__main__'].plot_data = signal

print("Plotting data...")

