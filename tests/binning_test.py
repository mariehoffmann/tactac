import collections
import os
import re
import sys
from threading import Thread, Condition

num_bins = 2
bin_files = ['bin1.fasta', 'bin2.fasta']
# assignment of accessions to file IDs
acc2fid = {'X17276.1': 0, 'X51700.1': 0, 'X68321.1': 0, 'X55027.1': 0, 'Z12029.1': 0, \
            'X52700.1': 1, 'X52701.1': 1, 'X52702.1': 1, 'X52706.1': 1, 'X52703.1': 1}

# mutual exclusion for buffering and writing bin files
condition = Condition()
state = collections.namedtuple('state', 'file_id, file_offset, buffer_filled, in_progress')
buffer = ['' for _ in range(num_bins)]
buffer_cleared = False
BUFFER_SIZE = 2
HEADER_PREFIX = '>'
RX_ACC = re.compile('\>?([\S\.]+)')
BINNING_DIR = './bins'
src_files = ['binning_src.fasta']

def init_buffer():
    return ['' for _ in range(num_bins)]

# consumer thread copying from RAM to bin files
class Buffer2BinsThread(Thread):
    def run(self):
        global bin_files
        global buffer
        global buffer_cleared
        
        while True:
            # consume buffer
            condition.acquire()
            if in_progress == False:
                break
            buffer_cleared = False
            if len(buffer) == 0:
                break
            for fid, buffer_per_file in enumerate(buffer):
                if len(buffer_per_file) > 0:
                    #print("{} >> '{}'".format(buffer_per_file, bin_files[fid]))
                    # remark single apostrophe (') may occur in header line
                    os.system('echo "{}" >> {}'.format(buffer_per_file, bin_files[fid]))
            # clear active buffer
            buffer = ['' for _ in range(num_bins)]
            buffer_cleared = True
            condition.notify()
            condition.release()
            # await buffer to be full

# producer thread copying from library to RAM
class Lib2BufferThread(Thread):

    def run(self):
        global buffer
        local_buffer_size = 0
        print(src_files)
        while True:
            local_buffer = init_buffer()  #['' for _ in range(num_bins)]
            # switch write active buffer, consumer reads from inactive one

            for file_id, src_file in enumerate(src_files[state.file_id:], start=state.file_id):
                refseq = ''
                acc = ''
                acc_prev = None
                state.file_offset = 0
                with open(src_file, 'r') as f:
                    ignore = False
                    f.seek(state.file_offset)
                    for line in f:
                        state.file_offset += len(line)
                        # new header write back previous sequence
                        if line.startswith(HEADER_PREFIX):
                            mobj = RX_ACC.search(line)
                            if mobj is None:
                                print("Error: could not extract accession from '", line, "'")
                                sys.exit()
                            if acc in acc2fid: # del previously handled accession from dictionary
                                del acc2fid[acc]
                            if len(acc2fid) == 0:
                                break
                            acc = mobj.group(1)
                            if acc in acc2fid:
                                ignore = False
                                print(acc2fid[acc])
                                local_buffer[acc2fid[acc]] += line
                                local_buffer_size += 1
                            else:
                                ignore = True
                        elif not ignore:
                            local_buffer[acc2fid[acc]] += line
                            local_buffer_size += 1
                        # check if buffer full
                        if local_buffer_size == BUFFER_SIZE:
                            # set state
                            state.file_id = file_id

                            condition.acquire()
                            if buffer_cleared == False:
                                print("buffer full, producer is waiting")
                                condition.wait() # releases lock, blocks, re-acquires lock upon notification
                            print("overwrite global buffer and notify consumer")
                            buffer = local_buffer
                            condition.notify()
                            condition.release()
                            local_buffer = ['' for _ in range(num_bins)]
            condition.acquire()
            if buffer_cleared == False:
                print("buffer full, producer is waiting")
                condition.wait()
            print("overwrite global buffer and notify consumer")
            buffer = local_buffer
            in_progress = False
            condition.notify()
            condition.release()

                # TODO: set state

if __name__ == '__main__':

    state.file_id = 0
    state.file_offset = 0
    in_progress = True
    print("Status: write {} files in {}".format(num_bins, BINNING_DIR))

    Lib2BufferThread().start()
    Buffer2BinsThread().start()
