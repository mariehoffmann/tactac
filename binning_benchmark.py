'''
    2,8 GHz Intel Core i7
    Processor Speed:	2,8 GHz
    Number of Processors:	1
    Total Number of Cores:	4
    L2 Cache (per Core):	256 KB
    L3 Cache:	6 MB
    Memory:	16 GB
'''

import os
import subprocess
import sys
import time

import config as cfg

num_processes = [1] #, 2, 4, 8]

# 128 sequences
num_bins = 4

if __name__ == '__main__':

    runtimes = [None for _ in range(len(num_processes))]
    # clear binning output directory
    os.system("rm -r {}".format(cfg.BINNING_DIR))
    for i, p in enumerate(num_processes):
        start = time.time()
        os.system("python tactac.py --binning all --num_bins {} --threads {} --password Lake1970".format(num_bins, p))
        end = time.time()
        runtimes[i] = end - start
    print("Runtimes: ", runtimes)
