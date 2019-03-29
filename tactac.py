'''
    tactac - database for taxonomic ID and accession number resolution

    Manual under https://github.com/mariehoffmann/tactac/wiki

    author: Marie Hoffmann ozymandiaz147[at]gmail[.]com
'''

# Setup script for downloading and installing the taxonomy and reference databases.
# Directories and URLS are set in config.py
import argparse
import config as cfg
import os
import psycopg2
import subprocess
import sys
import tarfile

from database.acc2tax import acc2tax
from database.binning import binning
from database.build import build
from database.tax2acc import tax2acc
from download.reference import ref_download
from download.taxonomy import tax_download

parser = argparse.ArgumentParser(description='Setup and build database relating taxonomic identifiers with accessions and organism names.')
parser.add_argument('--taxonomy', '-t', dest='taxonomy', action='store_true', \
    help='Download taxonomy file given by its url in the configuration file.')
parser.add_argument('--reference', '-r', dest='reference', action='store_true', \
    help='Download reference file given by its url in the configuration file.')
parser.add_argument('--build', '-b', dest='build', action='store_true', \
    help='Given reference and taxonomy files build the database schema.')
parser.add_argument('--password', '-p', dest='password', nargs=1, default='1234', \
    help='Password of the postgres user.')
parser.add_argument('--continue', dest='continue_flag', default=False, action='store_true', \
    help='Continue flag for filling accession table.')
parser.add_argument('--acc2tax', '-a', nargs=1, \
    help='Get the taxID for given accession number or file containing accessions (row-wise or fasta-format).')
parser.add_argument('--tax2acc', '-x', nargs=1, \
    help='Get all accessions for a taxonomic subtree given its root taxID.')
parser.add_argument('--binning', nargs='?', default='all', \
    help='Split library into equally sized bins. Expects an input (fasta files) directory or \
    an "all" flag which will distribute all accessions registered in the accessions table.')
parser.add_argument('--num_bins', nargs=1, default=256, \
    help='Additional parameter for binning to give the number of bins into which library will be split.')
parser.add_argument('--threads', nargs=1, default=1, \
    help='Parallelize with up to <THREADS> many threads.')

if __name__ == "__main__":
    args = parser.parse_args()
    print(args)
    if args.taxonomy:
        taxonomy()
    if args.reference:
        reference()
    if args.build:
        print("Note: for connecting with the PostgreSQL database, use the --password flag to set a password other than the default one (=1234).")
        build(args)
    elif args.acc2tax is not None:
        acc2tax(args.acc2tax)
    elif args.tax2acc is not None:
        tax2acc(args.tax2acc)
    elif args.binning is not None:
        binning(args)
    else:
        parser.print_help(sys.stderr)
        sys.exit(-1)
