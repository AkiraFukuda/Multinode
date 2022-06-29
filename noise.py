import os
import sys
import time
from datetime import datetime
from pytz import timezone
import numpy as np
import pandas as pd
import scipy.fft as fft

app_tag = "Noise1"
read_size = 1024
interval = 30
read_times = 10
filename = "hdd/noise2_1024.bin"

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
        print("Analysis time = ", ana_time)
        if ana_time > interval:
            print("Analysis time is larger than the interval!")
            
        bw = size / io_time
        bandwidth.append(bw)
        # bw_write(start, bw)
        print("Perceived bandwidth = %.2f MB/s" % bw)
        time.sleep(interval - ana_time)
    
    return bandwidth

def work():
    bw_record = fully_read(read_size, interval)

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