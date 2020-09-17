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
import timeit

from database.acc2tax import acc2tax
from database.binning import binning
from database.build import build
from database.subtree import subtree
from database.tax2acc import tax2acc
from download.acc2tax import download_acc2tax
from download.reference import download_ref
from download.taxonomy import download_tax


parser = argparse.ArgumentParser(description='Setup and build database relating \
    taxonomic identifiers with accessions and organism names.')
parser.add_argument('--acc2tax', '-a', nargs=1, \
    help='Get the taxID for given accession number or file containing accessions (row-wise or fasta-format).')
parser.add_argument('--annotate', nargs=1, \
    help='Give a FASTA file to augment the header lines with taxid information. \
    If the taxid information is not database-resident, you can set the download \
    flag to let tactac download the accession-to-taxid resolution file from NCBIs FTP server.')
parser.add_argument('--binning', nargs='?', \
    help='Split library into equally sized bins. Expects an input (fasta files) \
    directory or an "all" flag which will distribute all accessions registered in the accessions table.')
parser.add_argument('--build', '-b', dest='build', action='store_true', \
    help='Given reference and taxonomy files build the database schema.')
parser.add_argument('--continue', dest='continue_flag', nargs='?', default=False, \
    help='Continue flag for filling accession table.')
parser.add_argument('--download', dest='download', nargs=1, type=str, \
    help='Download taxonomy (tax), reference (ref), accession to taxid resolution file (acc2tax), or all (all). \
    Download urls are specified in config.py.')
parser.add_argument('--limit', dest='limit', type=int, nargs=1, \
    help="Running taxonomy-aware binning with first LIMIT accessions (e.g. for testing).")
parser.add_argument('--tax2acc', '-x', nargs=1, \
    help='Get all accessions for a taxonomic subtree given its root taxID.')
parser.add_argument('--num_bins', type=int, default=256, \
    help='Additional parameter for binning to give the number of bins into which library will be split.')
parser.add_argument('--password', '-p', type=str, dest='password', default='1234', \
    help='Password of the postgres user.')
parser.add_argument('--reference', '-r', dest='reference', action='store_true', \
    help='Download reference file given by its url in the configuration file.')
parser.add_argument('--num_samples', type=int, dest='num_samples', default=5, \
    help='Maximal number of references to be collected per taxon.')
parser.add_argument('--subtree', type=int, \
    help='Create library subset rooted by given taxID.')
parser.add_argument('--taxonomy', '-t', dest='taxonomy', action='store_true', \
    help='Download taxonomy file given by its url in the configuration file.')
parser.add_argument('--threads', type=int, default=1, \
    help='Parallelize with up to <THREADS> many threads.')

if __name__ == "__main__":
    args = parser.parse_args()
    print(args)
    print_help = True
    if args.download is not None:
        print_help = False
        if args.download[0] in ['tax', 'all']:
            download_tax()
        if args.download[0] in ['ref', 'all']:
            download_ref(args)
        if args.download[0] in ['acc2tax', 'all']:
            download_acc2tax()
        if args.download[0] in ['acc2tax', 'all', 'ref', 'tax'] is False:
            parser.print_help(sys.stderr)
            sys.exit()

    if args.build:
        print("Note: for connecting with the PostgreSQL database, use the --password flag to set a password other than the default one (=1234).")
        build(args)
    elif args.acc2tax is not None:
        acc2tax(args.acc2tax)
    elif args.tax2acc is not None:
        tax2acc(args.tax2acc)
    elif args.binning is not None:
        start = timeit.default_timer()
        binning(args)
        stop = timeit.default_timer()
        print('Elapsed time: ', stop - start, ' seconds')
    elif args.subtree is not None:
        subtree(args)
    elif print_help:
        parser.print_help(sys.stderr)
        sys.exit(-1)
