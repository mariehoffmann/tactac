'''
    tactac - database for taxonomic ID and accession number resolution

    Manual under https://github.com/mariehoffmann/tactac/wiki

    author: Marie Hoffmann ozymandiaz147[at]gmail[.]com
'''

import os
from pathlib import Path
import subprocess
import sys

import config as cfg
from utilities.check_md5 import check_md5

def download_ref(args):
    if os.path.isfile(cfg.FILE_REF):
        print('file nt exists')
        response = input("Reference file '{}' exists, are you sure you want to replace it [Y|n]? ".format(cfg.FILE_REF))
        if response == 'n':
            return
    print("Start downloading taxonomy ...")
    path = Path(cfg.DIR_REF_TMP)
    path.mkdir(parents=True, exist_ok=True)

    result = ''
    result = subprocess.run(['wget', cfg.URL_REF, '-N', '-P', cfg.DIR_REF_TMP], stdout=subprocess.PIPE)
    if not os.path.exists(cfg.FILE_REF):
        print("Taxonomy download failed: ")
        print(result.stdout.decode('utf-8'))
        sys.exit(-1)
    print("... done.")

    result = subprocess.run(['wget', cfg.URL_REF_MD5, '-N', '-O', cfg.FILE_REF_MD5], stdout=subprocess.PIPE)
    if not os.path.exists(cfg.FILE_REF_MD5):
        print("Downloading md5 checksum for reference failed: ")
        print(result.stdout.decode('utf-8'))
        sys.exit(-1)

    check_md5(cfg.FILE_REF, cfg.FILE_REF_MD5)

    ref_arx = os.path.join(cfg.DIR_REF_TMP, os.path.basename(cfg.URL_REF))
    path = Path(cfg.DIR_REF)
    path.mkdir(parents=True, exist_ok=True)
    # unpack archive
    print(subprocess.check_output('tar xzf {} -C {} -f {}'.format(ref_arx, cfg.DIR_REF_TMP, cfg.DIR_REF), stderr=subprocess.STDOUT, shell=True))
    print("... done.")
