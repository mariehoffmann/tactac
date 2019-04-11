'''
    tactac - database for taxonomic ID and accession number resolution

    Manual under https://github.com/mariehoffmann/tactac/wiki

    author: Marie Hoffmann ozymandiaz147[at]gmail[.]com

    ---------------------------------------------------------------------

    Parallelization with two threads
        1. Producer thread writes references from library into buffer (string vector)
        2. Consumer thread writes buffer to bin files
'''

import collections
import os
import re
import sys
from threading import Thread, Condition

import config as cfg

# mutual exclusion for buffering and writing bin files
condition = Condition()
# global variable to set and share states
# in_progress       flag set by producer, indicating if there are still resources to distribute
# buffer_cleared    flag set by consumer to True when buffer consumed or by producer to False when refilled
state = collections.namedtuple('state', 'in_progress, buffer_cleared')
# number of bin files
num_bins = 0
# reset buffer in the size of the number of output files
def init_buffer():
    return ['' for _ in range(num_bins)]
# global buffer shared between producer and consumer thread
buffer = init_buffer()

# consumer thread copying from RAM to bin files
class Buffer2BinsThread(Thread):

    def __init__(self, bin_files):
        Thread.__init__(self)
        self.bin_files = bin_files

    def run(self):
        global buffer
        global state

        while True:
            # consume buffer
            condition.acquire()
            if state.in_progress == False:
                condition.release()
                break
            if state.buffer_cleared == True:
                condition.wait()
            condition.release()

            for fid, buffer_per_file in enumerate(buffer):
                if len(buffer_per_file) > 1:
                    #print("{} >> '{}'".format(buffer_per_file, bin_files[fid]))
                    # remark single apostrophe (') may occur in header line
                    os.system('echo "{}" >> {}'.format(buffer_per_file.strip(), self.bin_files[fid]))
            # clear active buffer
            condition.acquire()
            buffer = init_buffer()
            state.buffer_cleared = True
            condition.notify()
            condition.release()
            # await buffer to be full

# producer thread copying from library to RAM
class Lib2BufferThread(Thread):

    def __init__(self, acc2fid):
        Thread.__init__(self)
        self.acc2fid = acc2fid

    def run(self):
        global buffer
        global state
        global num_bins

        local_buffer_size = 0
        while True:
            local_buffer = init_buffer()
            refseq = ''
            acc = ''
            acc_prev = None
            with open(cfg.FILE_REF, 'r') as f:
                ignore = False
                for line in f:
                    # new header write back previous sequence
                    if line.startswith(cfg.HEADER_PREFIX):
                        mobj = cfg.RX_ACC.search(line)
                        if mobj is None:
                            sys.exit()
                        if acc in self.acc2fid: # del previously handled accession from dictionary
                            del self.acc2fid[acc]
                        if len(self.acc2fid) == 0:
                            break
                        acc = mobj.group(1)

                        if acc in self.acc2fid:
                            ignore = False
                            local_buffer[self.acc2fid[acc]] += line
                            local_buffer_size += 1
                        else:
                            ignore = True
                    elif not ignore:
                        local_buffer[self.acc2fid[acc]] += line
                        local_buffer_size += 1

                    # check if buffer full
                    if local_buffer_size >= cfg.BUFFER_SIZE:
                        condition.acquire()
                        if state.buffer_cleared == False:
                            condition.wait() # releases lock, blocks, re-acquires lock upon notification
                        buffer = local_buffer
                        state.buffer_cleared = False
                        condition.notify()
                        condition.release()
                        local_buffer = init_buffer()
                        local_buffer_size = 0

            # case: no more source files to read, buffer only partially filled
            if local_buffer_size > 0:
                condition.acquire()
                if state.buffer_cleared == False:
                    condition.wait()
                buffer = local_buffer
                state.buffer_cleared = False
                condition.notify()
                condition.release()
            # notify about finish
            condition.acquire()
            state.in_progress = False
            condition.notify()
            condition.release()
            break


def distribute(acc2fid, bin_files):
    global num_bins
    global state
    num_bins = len(bin_files)
    state.in_progress = True
    state.buffer_cleared = True
    Lib2BufferThread(acc2fid).start()
    Buffer2BinsThread(bin_files).start()
    print("Status: written {} bin files.".format(num_bins))
