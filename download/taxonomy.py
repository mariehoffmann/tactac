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

def download_tax():

    # create database directory
    print(cfg.DIR_TAX)
    if not os.path.exists(cfg.DIR_TAX):
        os.makedirs(cfg.DIR_TAX)
    # create tmp folder for downloads
    if not os.path.exists(cfg.DIR_TAX_TMP):
        os.makedirs(cfg.DIR_TAX_TMP)
    tax_arx = os.path.join(cfg.DIR_TAX_TMP, os.path.basename(cfg.URL_TAX))
    print("Start downloading taxonomy ...")
    result = ''
    result = subprocess.run(['wget', cfg.URL_TAX, '-P', cfg.DIR_TAX_TMP, '-N'], stdout=subprocess.PIPE)
    if not os.path.exists(tax_arx):
        print("Taxonomy download failed: ")
        print(result.stdout.decode('utf-8'))
        sys.exit(-1)
    print("... done.")

    result = subprocess.run(['wget', cfg.URL_TAX_MD5, '-P', cfg.DIR_TAX_TMP, '-N'], stdout=subprocess.PIPE)
    tax_arx_md5 = os.path.join(cfg.DIR_TAX_TMP, os.path.basename(cfg.URL_TAX_MD5))
    if not os.path.exists(tax_arx_md5):
        print("Downloading md5 checksum for taxonomy failed: ")
        print(result.stdout.decode('utf-8'))
        sys.exit(-1)

    check_md5(tax_arx, tax_arx_md5)

    # unpack archive
    print(subprocess.check_output('tar xzf {} -C {}'.format(tax_arx, cfg.DIR_TAX_TMP), stderr=subprocess.STDOUT, shell=True))
    # delete unused dump files
    for fname in os.listdir(cfg.DIR_TAX_TMP):
        if fname not in ['nodes.dmp', 'taxidlineage.dmp', 'names.dmp', tax_arx, tax_arx_md5]:
            os.remove(os.path.join(cfg.DIR_TAX_TMP, fname))
    print("... ok.")
