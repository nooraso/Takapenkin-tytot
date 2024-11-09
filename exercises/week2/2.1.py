from filefifo import Filefifo

# Read data from the file
data = Filefifo(10, name='capture_250Hz_01.txt')
signal = [data.get() for _ in range(10000)]

# Peaks list
peaks = []

# Find peaks
for i in range(1, len(signal) - 1):
    if signal[i - 1] < signal[i] > signal[i + 1]:
        peaks.append(i)

# Sampling rate
sampling_rate = 250

# Check if there are enough peaks
if len(peaks) >= 3:
    samples = [peaks[i + 1] - peaks[i] for i in range(3)]
    seconds = [interval / sampling_rate for interval in samples]
    
    # Print the details of each peak interval
    for i in range(3):
        frequency = 1 / seconds[i]  
        print(f"signal {i + 1}: {samples[i]}, {seconds[i]:.1f} s, {frequency:.1f} Hz")

    # Average time and frequency
    average = sum(seconds) / len(seconds)
    average_frequency = 1 / average

    # Print the average signal frequency
    print(f"\nAverage signal frequency: {average_frequency:.1f} Hz") 
else:
    print("Not enough peaks detected to calculate intervals")
