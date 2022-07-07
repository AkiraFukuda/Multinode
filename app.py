import os
import sys
import time
from datetime import datetime
from pytz import timezone
import numpy as np
import pandas as pd
import scipy.fft as fft

app_tag = "App1"
read_size = 1024
interval = 15
read_times = 20
filename = "hdd/noise1_1024.bin"

record_fn0 = "hdd/bw_record_0.csv"
record_fn1 = "hdd/bw_record_1.csv"
window_length = 86400
amp_low_threshold = 1e-10
freq_high_ratio = 0.5

def noise_prediction():
    df0 = pd.read_csv(record_fn0, header=None, names=['origin', 'date', 'time', 'bw'])
    df1 = pd.read_csv(record_fn1, header=None, names=['origin', 'date', 'time', 'bw'])
    print(df0.to_dict())
    print(df1.to_dict())

def noise_prediction_temp(samples, amp_low_threshold, freq_high_ratio):
    N = len(samples)
    xf = fft.fftfreq(N, 1/N)
    yf = fft.fft(samples)
    amp = np.abs(yf)
    freq_high_threshold = np.max(xf) * freq_high_ratio

    yf_filtered = []
    for i in range(len(yf)):
        if amp[i] > amp_low_threshold and np.abs(xf[i]) < freq_high_threshold:
            yf_filtered.append(yf[i])
        else:
            yf_filtered.append(0)

    new_sig = fft.ifft(yf_filtered)
    return list(np.abs(new_sig))

def bw_write(start, bw, window_length):

    now_date = int(round(start) / window_length)
    start_time_int = round(start) % window_length

    # Pandas method
    # df = pd.read_csv(record_fn)
    # size = len(df)
    # df.loc[size] = {'origin': app_tag, 'date': now_date, 'time': start_time_int, 'bw': bw}
    # df.to_csv(record_filename, index=False)

    # Sliding window via 2 files
    f = open(record_fn0, 'r+')
    if os.path.getsize(record_fn0) != 0:
        f_firstline = f.readline().split(',')
        f_date = int(f_firstline[1])
        if now_date - f_date >= 2:
            f.truncate(0)
    f.close()

    f = open(record_fn1, 'r+')
    if os.path.getsize(record_fn1) != 0:
        f_firstline = f.readline().split(',')
        f_date = int(f_firstline[1])
        if now_date - f_date >= 2:
            f.truncate(0)
    f.close()

    if now_date & 1 == 0:
        f = open(record_fn0, 'a+')
    else:
        f = open(record_fn1, 'a+')

    # File I/O method
    # f = open(record_fn0, 'a+')
    content = app_tag + ',' + str(now_date) + ',' + str(start_time_int) + ',' + str(bw) + '\n'
    f.write(content)
    f.close()

def fully_read(size, interval):
    bandwidth = []
    for i in range(read_times):
        print("%s s"%(i*interval))

        print("Start reading")
        start = time.time()
        f = open(filename, "rb")
        f.read()
        f.close()
        end_io = time.time()
        print("End reading")
        io_time = end_io - start

        end_ana = time.time()
        ana_time = end_ana - start
        print("Analysis time = %.2f s" % ana_time)
        if ana_time > interval:
            print("Analysis time is larger than the interval!")
            
        bw = size / io_time
        bandwidth.append(bw)
        bw_write(start, bw, window_length)
        print("Perceived bandwidth = %.2f MB/s" % bw)
        time.sleep(interval - ana_time)
    
    print("bw:", bandwidth)
    return bandwidth

def partial_read(size, interval, bw_low_bound, bw_high_bound, predict_result):
    bandwidth = []
    aug_record = []
    collision_threshold = 0.5
    last_performance = 1
    for i in range(read_times):
        print("%s s"%(i*interval))

        bw_predicted = predict_result[i]
        if bw_predicted < bw_low_bound:
            aug_ratio = 0.0
        elif bw_predicted > bw_high_bound:
            aug_ratio = 1.0
        else:
            aug_ratio = (bw_predicted - bw_low_bound) / (bw_high_bound - bw_low_bound)
            random_factor = np.random.rand()
            if last_performance < collision_threshold and random_factor < 0.5:
                aug_ratio /= 2

        print("Start reading, Augmentation = {:.0%}".format(aug_ratio))
        start = time.time()
        f = open(filename, "rb")
        f.read(int(size*1024*1024*aug_ratio))
        f.close()
        end_io = time.time()
        print("End reading")
        io_time = end_io - start
        
        end_ana = time.time()
        ana_time = end_ana - start
        print("Analysis time = %.2f s" % ana_time)
        if ana_time > interval:
            print("Analysis time is larger than the interval!")
            
        bw = size*aug_ratio / io_time
        bandwidth.append(bw)
        aug_record.append(aug_ratio)
        last_performance = bw / bw_predicted
        bw_write(start, bw, window_length)
        print("Perceived bandwidth = %.2f MB/s" % bw)
        time.sleep(interval - ana_time)
    
    print("bw new:", bandwidth)
    print("aug ratio:", aug_ratio)

def work():
    bw_record = fully_read(read_size, interval)
    bw_predicted = noise_prediction_temp(bw_record, amp_low_threshold, freq_high_ratio)
    print("bw predicted:", bw_predicted)
    partial_read(read_size, interval, 100, 200, bw_predicted)

def main():
    if sys.argv[1] == 'now':
        work()
    else:
        while True:
            now_time = datetime.now(timezone('UTC'))
            if now_time.hour == int(sys.argv[1]) and now_time.minute == int(sys.argv[2]) and now_time.second == int(sys.argv[3]):
                work()
                break


if __name__ == "__main__":
    main()