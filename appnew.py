import os
import sys
import time
from datetime import datetime
from pytz import timezone
import numpy as np
import pandas as pd
import scipy.fft as fft
import matplotlib.pyplot as plt
import cmath

app_tag = "App1"
exp_time = 540
window_length = 3600
window_interval = 10
amp_low_ratio = 0.25
freq_high_ratio = 1
bw_low_bound = 100
bw_high_bound = 200
pre_read_ratio = 0.1

filename = "hdd/app1_1024.bin"
record_fn0 = "hdd/bw_record_0.csv"
record_fn1 = "hdd/bw_record_1.csv"

log_path = "log/app1_r.log"

def partial_read_new(size, interval, bw_low_bound, bw_high_bound, pre_read_ratio):
    bandwidth = []
    aug_record = []
    bw1_record = []
    bw2_record = []
    # col_record = []
    # collision_times = 0

    for i in range(int(exp_time/interval)):
        print("\n%s s" % (i*interval))
        pre_size = size * pre_read_ratio
        start = time.time()
        f = open(filename, "rb")
        f.read(int(pre_size*1024*1024))
        f.close()
        end_io = time.time()
        pre_io_time = end_io - start
        bw_pre = pre_size / pre_io_time
        print("T1 = %.2f s, BW1 = %.2f MB/s" % (pre_io_time, bw_pre))
        bw1_record.append(bw_pre)

        if bw_pre < bw_low_bound:
            aug_ratio = 0.0
        elif bw_pre > bw_high_bound:
            aug_ratio = 1.0
        else:
            aug_ratio = (bw_pre - bw_low_bound) / (bw_high_bound - bw_low_bound)
        after_size = (size - pre_size) * aug_ratio
        # print("Aug = {:.0%}".format(aug_ratio))
        print("Size = %.2f MB" % after_size)

        # if bw_pre < bw_predicted * 0.75:
        #     collision_times += 1
        #     print("Collision detected!")
        #     random_factor = np.power(0.5, np.random.randint(collision_times+1))
        #     after_size *= random_factor
        #     col_record.append(random_factor)
        # else:
        #     collision_times = 0
        #     col_record.append(-1)
        
        start = time.time()
        f = open(filename, "rb")
        f.read(int(after_size*1024*1024))
        f.close()
        end_io = time.time()
        after_io_time = end_io - start
        bw_after = after_size / after_io_time
        end_ana = time.time()
        ana_time = end_ana - start
        print("T2 = %.2f s, BW2 = %.2f MB/s" % (after_io_time, bw_after))
        bw2_record.append(bw_after)
        
        bw = (pre_size + after_size) / (pre_io_time + after_io_time)
        bandwidth.append(bw)
        aug_record.append(aug_ratio)
        if ana_time > interval:
            print("Analysis time is larger than the interval!")
        time.sleep(interval - ana_time)
    
    return bw1_record, bw2_record, bandwidth, aug_record

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

def make_log_new(bw1, bw2, bw, aug): 
    f = open(log_path, 'w+')
    s = '[' + ','.join(str(i) for i in bw1) + ']\n'
    f.write(s)
    s = '[' + ','.join(str(i) for i in bw2) + ']\n'
    f.write(s)
    s = '[' + ','.join(str(i) for i in bw) + ']\n'
    f.write(s)
    s = '[' + ','.join(str(i) for i in aug) + ']\n'
    f.write(s)
    # s = '[' + ','.join(str(i) for i in col) + ']\n'
    # f.write(s)
    f.close()

def work(read_size, interval):
    bw1, bw2, bw, aug = partial_read_new(read_size, interval, bw_low_bound, bw_high_bound, pre_read_ratio)
    print("bw1:", bw1)
    print("bw2:", bw2)
    print("bw:", bw)
    print("augment:", aug)
    
    # make_plot(interval, bw_record, bw_predicted, bw_new, aug_record, col_record)
    make_log_new(bw1, bw2, bw, aug)

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