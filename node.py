import sys
import time
import datetime
from pytz import timezone
import numpy as np
import pandas as pd
import scipy.fftpack as fft

app_tag = "App1"
filename = "hdd/noise1024.bin"
record_filename = "hdd/bw_record.csv"

def prediction_noise_wave(samples, hi_freq_ratio, interval):
    df = pd.read_csv(record_filename)
    sample_size = len(df)
    
    amp = fft.fft(samples)/sample_size
    amp_complex_h = amp
    amp_h = np.absolute(amp_complex_h)

    freq = fft.fftfreq(amp.size, interval)
    freq_h = freq

    if amp_h[0] > 1e-10:
        threshold = np.max(np.delete(amp_h, 0, axis=0)) * hi_freq_ratio
        dc = amp_h[0]
        start_index = 1
    else:
        threshold = np.max(amp_h) * hi_freq_ratio
        dc = 0
        start_index = 0
    
    selected_freq = []
    selected_amp = []
    selected_complex=[]
    for i in range(start_index,len(amp_h)):
        if amp_h[i] >= threshold:
            selected_freq.append(freq_h[i])
            selected_amp.append(amp_h[i])
            selected_complex.append(amp_complex_h[i])

    selected_phase = np.arctan2(np.array(selected_complex).imag,np.array(selected_complex).real)

    for i in range(len(selected_phase)):
        if np.fabs(selected_phase[i])<1e-10:
            selected_phase[i]=0.0
    
    return dc, selected_amp, selected_freq, selected_phase   

def bw_write(start, bw):
    start_int = round(start)

    # Pandas method
    # df = pd.read_csv(record_filename)
    # size = len(df)
    # df.loc[size] = {'origin': app_tag, 'time': start_int, 'bw': bw}
    # df.to_csv(record_filename, index=False)

    # File I/O method
    f = open(record_filename, 'a+')
    content = app_tag + ',' + str(start_int) + ',' + str(bw) + '\n'
    f.write(content)
    f.close()


def work(size, interval):
    bandwidth = []
    for i in range(20):
        print("%s s"%(i*interval))

        print("Start reading")
        start = time.time()
        f = open(filename, "rb")
        f.close()
        end_io = time.time()
        print("End reading")
        io_time = end_io - start
        
        bw = size / io_time
        bandwidth.append(bw)
        bw_write(start, bw)
        print("Perceived bandwidth = %f MB/s" % bw)

        end_ana = time.time()
        ana_time = end_ana - start
        print("Analysis time = ", ana_time)

        if ana_time > interval:
            print("Analysis time is larger than interval!\n")
        time.sleep(interval - ana_time)


def main():
    read_size = int(sys.argv[1])
    interval = int(sys.argv[2])
    if sys.argv[3] == 'now':
        work(read_size, interval)
    else:
        while True:
            now_time = datetime.datetime.now(timezone('EST'))
            if now_time.hour == int(sys.argv[3]) and now_time.minute == int(sys.argv[4]) and now_time.second == int(sys.argv[5]):
                work(read_size, interval)
                break


if __name__ == "__main__":
    main()