'''
    tactac - database for taxonomic ID and accession number resolution

    Manual under https://github.com/mariehoffmann/tactac/wiki

    author: Marie Hoffmann ozymandiaz147[at]gmail[.]com
'''

import os
import subprocess
import sys

import config as cfg
from utilities.check_md5 import check_md5

def download_acc2tax():

    # create tmp folder for downloads
    if not os.path.exists(cfg.DIR_TAX_TMP):
        os.makedirs(cfg.DIR_TAX_TMP)

    acc2tax_arx = os.path.join(cfg.DIR_TAX_TMP, os.path.basename(cfg.URL_ACC2TAX))
    print("Start downloading taxonomy ...")
    result = subprocess.run(['wget', cfg.URL_ACC2TAX, '-P', cfg.DIR_TAX_TMP, '-N'], stdout=subprocess.PIPE)
    if not os.path.exists(acc2tax_arx):
        print("Taxonomy download failed: ")
        print(result.stdout.decode('utf-8'))
        sys.exit(-1)
    print("... done.")

    result = subprocess.run(['wget', cfg.URL_ACC2TAX_MD5, '-P', cfg.DIR_TAX_TMP, '-N'], stdout=subprocess.PIPE)
    acc2tax_arx_md5 = os.path.join(cfg.DIR_TAX_TMP, os.path.basename(cfg.URL_ACC2TAX_MD5))
    print(acc2tax_arx_md5)
    if not os.path.exists(acc2tax_arx_md5):
        print("Downloading md5 checksum for taxonomy failed: ")
        print(result.stdout.decode('utf-8'))
        sys.exit(-1)

    check_md5(acc2tax_arx, acc2tax_arx_md5)

    # unpack archive, should be named nucl_gb.accession2taxid
    print(subprocess.check_output('gunzip -d --uncompress {}'.format(acc2tax_arx, cfg.DIR_TAX_TMP), stderr=subprocess.STDOUT, shell=True))
    print("... ok.")
