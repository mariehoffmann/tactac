import re
import subprocess
import sys

def bin_load(bin_files):
    # check files sizes in terms of line numbers
    lines_rx = re.compile('^\s+(\d+)\s+.+?')
    file_lines = []
    for bin_file in bin_files:
        result = subprocess.check_output("wc -l {}".format(bin_file), stderr=subprocess.STDOUT, shell=True)
        print(result.decode('ascii'))
        mobj = lines_rx.match(result.decode('ascii'))
        if mobj is None:
            print("Error: could not extract number of lines from '{}'".format(result))
            sys.exit(0)
        file_lines.append(int(mobj.group(1)))
    print(file_lines)
