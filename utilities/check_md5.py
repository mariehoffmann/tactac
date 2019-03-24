'''
    tactac - database for taxonomic ID and accession number resolution

    Manual under https://github.com/mariehoffmann/tactac/wiki

    author: Marie Hoffmann ozymandiaz147[at]gmail[.]com
'''

import subprocess
import sys

def check_md5(file_down, file_md5):
    print("Check with md5 hash ...")
    md5_down = subprocess.run(['md5', file_down], stdout=subprocess.PIPE)
    md5_down = md5_down.stdout.decode('utf-8').split('=')[-1].strip()
    md5 = ''
    with open(file_md5, 'r') as f:
        md5 = f.readline().split(' ')[0].strip()
    if not (md5 == md5_down):
        print("Checksum for taxonomy download not as expected: is {}, but should be {}".format(md5_down, md5))
        sys.exit(-1)
    print("... md5 as expected.")
