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
DIR_REF = os.path.join(HOME_DIR, 'tactac/refDB')
# The temporary folder for reference file downloads.
DIR_REF_TMP = os.path.join(HOME_DIR, 'tactac/refDB/tmp')
# The complete path to the reference file named after the basename of its url.
FILE_REF = os.path.join(DIR_REF, os.path.basename(URL_REF).split('.')[0])
# The complete path to the md5 file of the associated reference file.
FILE_REF_MD5 = os.path.join(DIR_REF_TMP, os.path.basename(URL_REF_MD5))

# regular expression to extract accession
RX_ACC = re.compile('\>(\S+)')
RX_TAXID = re.compile('ORGANISM=(\d+)\&amp')
