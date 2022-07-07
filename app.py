import os
import sys
import time
from datetime import datetime
from pytz import timezone
import numpy as np
import pandas as pd
import scipy.fft as fft
import matplotlib.pyplot as plt

app_tag = "App1"
exp_time = 540
window_length = 3600
amp_low_ratio = 0.25
freq_high_ratio = 1
bw_low_bound = 150
bw_high_bound = 200

filename = "hdd/app1_1024.bin"
record_fn0 = "hdd/bw_record_0.csv"
record_fn1 = "hdd/bw_record_1.csv"

def noise_prediction():
    df0 = pd.read_csv(record_fn0, header=None, names=['origin', 'date', 'time', 'bw'])
    df1 = pd.read_csv(record_fn1, header=None, names=['origin', 'date', 'time', 'bw'])
    print(df0.to_dict())
    print(df1.to_dict())

def noise_prediction_temp(samples, amp_low_ratio, freq_high_ratio):
    N = len(samples)
    mean = np.mean(samples)
    y_new = np.array(samples) - mean
    xf = fft.fftfreq(N, 1/N)
    yf = fft.fft(y_new)
    amp = np.abs(yf)
    amp_low_threshold = np.max(amp) * amp_low_ratio
    freq_high_threshold = np.max(xf) * freq_high_ratio

    yf_filtered = []
    for i in range(len(yf)):
        if amp[i] > amp_low_threshold and np.abs(xf[i]) < freq_high_threshold:
            yf_filtered.append(yf[i])
        else:
            yf_filtered.append(0)

    new_sig = fft.ifft(yf_filtered)
    new_sig = new_sig + mean
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
        if now_date - f_date >= 2 or now_date < f_date:
            f.truncate(0)
    f.close()

    f = open(record_fn1, 'r+')
    if os.path.getsize(record_fn1) != 0:
        f_firstline = f.readline().split(',')
        f_date = int(f_firstline[1])
        if now_date - f_date >= 2 or now_date < f_date:
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
    for i in range(int(exp_time/interval)):
        print("%s s"%(i*interval))

        start = time.time()
        f = open(filename, "rb")
        f.read(size*1024*1024)
        f.close()
        end_io = time.time()
        io_time = end_io - start

        end_ana = time.time()
        ana_time = end_ana - start
        bw = size / io_time
        bandwidth.append(bw)
        bw_write(start, bw, window_length)
        print("Time = %.2f s, Bandwidth = %.2f MB/s" % (ana_time, bw))
        if ana_time > interval:
            print("Analysis time is larger than the interval!")
        time.sleep(interval - ana_time)
    
    return bandwidth

def partial_read(size, interval, bw_low_bound, bw_high_bound, predict_result):
    bandwidth = []
    aug_record = []
    col_record = []
    collision_times = 0
    last_performance = 1
    for i in range(int(exp_time/interval)):
        print("%s s" % (i*interval))
        bw_predicted = predict_result[i]
        if bw_predicted < bw_low_bound:
            aug_ratio = 0.0
        elif bw_predicted > bw_high_bound:
            aug_ratio = 1.0
        else:
            aug_ratio = (bw_predicted - bw_low_bound) / (bw_high_bound - bw_low_bound)
        print("Augmentation = {:.0%}".format(aug_ratio))

        if last_performance < 0.5:
            collision_times += 1
            print("Collision detected!")
            random_factor = np.power(0.5, np.random.randint(collision_times+1))
            aug_ratio *= random_factor
            col_record.append(random_factor)
        else:
            collision_times = 0
            col_record.append(-1)

        start = time.time()
        f = open(filename, "rb")
        f.read(int(size*aug_ratio*1024*1024))
        f.close()
        end_io = time.time()
        io_time = end_io - start
        
        end_ana = time.time()
        ana_time = end_ana - start
        bw = size*aug_ratio / io_time
        bandwidth.append(bw)
        aug_record.append(aug_ratio)
        last_performance = bw / bw_predicted
        bw_write(start, bw, window_length)
        print("Time = %.2f s, Bandwidth = %.2f MB/s" % (ana_time, bw))
        if ana_time > interval:
            print("Analysis time is larger than the interval!")
        time.sleep(interval - ana_time)
    
    return bandwidth, aug_record, col_record

def make_plot(interval, bw1, bw_pred, bw_new, aug, col): 
    time1 = []
    time2 = []
    for i in range(int(exp_time/interval)):
        time1.append(i*interval)
        time2.append((i+int(exp_time/interval))*interval)
    fig, ax1 = plt.subplots()
    ax2 = ax1.twinx()
    ax2.bar(time2, aug, width=4, color='#bbbbbb')
    ax1.scatter(time1, bw1, color='red')
    ax1.plot(time1, bw1, color='red', label='Bandwidth')
    ax1.scatter(time2, bw_new, color='red')
    ax1.plot(time2, bw_new, color='red')
    ax1.scatter(time2, bw_pred, color='black')
    ax1.plot(time2, bw_pred, color='black', label='Predict')

    ax1.vlines(exp_time-5, 100, 270, color='black', linestyles='dashed')
    # ax1.ylim(120, 280)
    ax1.set_xlabel("Time (second)")
    ax1.set_ylabel("Bandwidth (MB/s)")
    ax2.set_ylabel("Augmentation (%)")
    ax1.set_zorder(10)
    ax1.legend()
    plt.savefig('log/app1.png')

def make_log(bw1, bw_pred, bw_new, aug, col): 
    f = open("log/app1_r.log", 'w+')
    s = '[' + ','.join(str(i) for i in bw1) + ']'
    f.write(s)
    s = '[' + ','.join(str(i) for i in bw_pred) + ']'
    f.write(s)
    s = '[' + ','.join(str(i) for i in bw_new) + ']'
    f.write(s)
    s = '[' + ','.join(str(i) for i in aug) + ']'
    f.write(s)
    s = '[' + ','.join(str(i) for i in col) + ']'
    f.write(s)
    f.close()

def work(read_size, interval):
    bw_record = fully_read(read_size, interval)
    print("bw:", bw_record)
    bw_predicted = noise_prediction_temp(bw_record, amp_low_ratio, freq_high_ratio)
    print("bw predicted:", bw_predicted)
    bw_new, aug_record, col_record = partial_read(read_size, interval, bw_low_bound, bw_high_bound, bw_predicted)
    print("bw new:", bw_new)
    print("augment:", aug_record)
    print("collision:", col_record)
    
    # make_plot(interval, bw_record, bw_predicted, bw_new, aug_record, col_record)
    make_log(bw_record, bw_predicted, bw_new, aug_record, col_record)

def main():
    read_size = int(sys.argv[1])
    interval = int(sys.argv[2])
    if sys.argv[3] == 'now':
        work(read_size, interval)
    else:
        while True:
            now_time = datetime.now(timezone('UTC'))
            if now_time.hour == int(sys.argv[3]) and now_time.minute == int(sys.argv[4]) and now_time.second == int(sys.argv[5]):
                work(read_size, interval)
                break


if __name__ == "__main__":
    main()