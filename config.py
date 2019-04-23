'''
    tactac - database for taxonomic ID and accession number resolution

    Manual under https://github.com/mariehoffmann/tactac/wiki

    author: Marie Hoffmann ozymandiaz147[at]gmail[.]com
'''

import os
import re

# PostgreSQL settings, default user name is 'postgres'
server_name = 'local'
host_name = 'localhost'
port = 5432
user_name = 'postgres'
password = 'Lake1970'

# taxonomy database directory and download urls
HOME_DIR = os.path.expanduser("~")
DIR_TAX = os.path.join(HOME_DIR, 'tactac/taxDB')
DIR_TAX_TMP = os.path.join(HOME_DIR, 'tactac/taxDB/tmp')
URL_TAX = 'ftp://ftp.ncbi.nih.gov/pub/taxonomy/new_taxdump/new_taxdump.tar.gz'
URL_TAX_MD5 = 'ftp://ftp.ncbi.nih.gov/pub/taxonomy/new_taxdump/new_taxdump.tar.gz.md5'
FILE_nodes = 'nodes.dmp'
FILE_lineage = 'taxidlineage.dmp'
FILE_names = 'names.dmp'
URL_ACC = 'https://www.ncbi.nlm.nih.gov/nuccore/{}'

# reference database directory and ftp urls
DIR_BLAST = os.path.join(HOME_DIR, 'tactac/refDB')
URL_REF = 'ftp://ftp.ncbi.nlm.nih.gov/blast/db/FASTA/nt.gz'
URL_REF_MD5 = 'ftp://ftp.ncbi.nlm.nih.gov/blast/db/FASTA/nt.gz.md5'
# all fasta files in this directory are assumed to be part of the library
DIR_REF = os.path.join(HOME_DIR, 'tactac/refDB')
# The temporary folder for reference file downloads.
DIR_REF_TMP = os.path.join(HOME_DIR, 'tactac/refDB/tmp')
# The complete path to the reference file named after the basename of its url.
FILE_REF = os.path.join(DIR_REF, os.path.basename(URL_REF).split('.')[0])
# The complete path to the md5 file of the associated reference file.
FILE_REF_MD5 = os.path.join(DIR_REF_TMP, os.path.basename(URL_REF_MD5))

# working directory for output
WORK_DIR = os.path.join(HOME_DIR, 'tmp', 'tactac')

## Settings for taxonomic binning of a sequence library.
# Output directory for bins
BINNING_DIR = os.path.join(HOME_DIR, 'tactac/binnning')
# Regular expression for input file format of library.
LIBRARY_FORMAT_RX = re.compile('[^\s]+\.(fa|FA|fasta|FASTA)')
# file suffix for binned reference library
LIBRARY_BIN_FORMAT = 'fasta'
# Maximal factor a bin size (in terms of space) differs from uniform (=1.0) distribution.
# E.g., 256 GB equally distributed over 256 bins are 1 GB per bin. With MAX_RATIO=2.0,
# the largest bin should not store than 2 GB of the sequences.
MAX_RATIO = 1.5
# number of reference sequences buffered before written to up to num_bins (set via argument parser) files
BUFFER_SIZE = 4
# source file header line prefix
HEADER_PREFIX = '>'
# file prefix for the binned library files, i.e. FILE_PREFIX1.fasta, FILE_PREFIX2.fasta, etc.
FILE_PREFIX = 'bin'

# regular expression to extract accession
RX_ACC = re.compile('\>?([\S\.]+)')
RX_WEB_TAXID = re.compile('ORGANISM=(\d+)\&amp')
RX_TAXID = re.compile('(\d+)')
