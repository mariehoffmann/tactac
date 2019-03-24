'''
    tactac - database for taxonomic ID and accession number resolution

    Manual under https://github.com/mariehoffmann/tactac/wiki

    author: Marie Hoffmann ozymandiaz147[at]gmail[.]com
'''

# Setup script for downloading and installing the taxonomy and reference databases.
# Directories and URLS are set in config.py
import argparse
import os
import psycopg2
import subprocess
import sys
import tarfile

import config as cfg
import reference
from taxonomy.build import build as tax_build
from taxonomy.download import download as tax_download
from reference.build import build as ref_build
from reference.download import download as ref_download


parser = argparse.ArgumentParser(description='Setup and build database relating taxonomic identifiers with accessions and organism names.')
parser.add_argument('--taxonomy', '-t', dest='taxonomy', action='store_true', \
    help='Download taxonomy file given by its url in the configuration file.')
parser.add_argument('--reference', '-r', dest='reference', action='store_true', \
    help='Download reference file given by its url in the configuration file.')
parser.add_argument('--build', '-b', dest='build', action='store_true', \
    help='Given reference and taxonomy files build the database schema.')
parser.add_argument('--password', '-p', dest='password', nargs=1, default='1234', \
    help='Password of the postgres user.')
parser.add_argument('--config', '-c', dest='config_file', nargs=1, default='config', \
    help='Alternative configuration file to set database connection details.')
parser.add_argument('--continue', dest='continue_flag', default=False, action='store_true', \
    help='Continue flag for filling accession table.')

if __name__ == "__main__":
    args = parser.parse_args()
    print(args)
    if args.taxonomy:
        download_tax(args)
    if args.reference:
        download_ref(args)
    if args.build:
        print("Note: for connecting with the PostgreSQL database, use the --password flag to set a password other than the default one (=1234).")
        build(args)
    else:
        print("Usage: python tactac.py --(reference|taxonomy|(build [--continue])) [--password <pwd>] [--config <config_file>]")
        sys.exit(-1)
