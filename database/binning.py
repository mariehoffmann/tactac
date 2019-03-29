'''
    tactac - database for taxonomic ID and accession number resolution

    Manual under https://github.com/mariehoffmann/tactac/wiki

    author: Marie Hoffmann ozymandiaz147[at]gmail[.]com

    ---------------------------------------------------------------------

    1st parallelization
    2nd parallelization: One thread writes out buffer to num_bins files. Others
'''

import multiprocessing
import os
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import re
import subprocess
import sys

import config as cfg
from database.acc2tax import acc2tax

# input library files
src_files = []
# distributed library output files (=bins)
num_bins = None
bin_files = []
# assignment of accessions to file IDs
acc2fid = {}

# create output bin files
def initbins():
    global bin_files
    # create directory
    if os.path.isdir(cfg.BINNING_DIR):  # clear if existing
        response = input('Warning: Output directory ({}) already exists and will be overwritten. [Y|n] ? '.format(cfg.BINNING_DIR))
        if response == 'N':
            sys.exit(-1)
        os.system("rm {}/*".format(cfg.BINNING_DIR))
    else:   # create newly
        os.system("mkdir -p {}".format(cfg.BINNING_DIR))
    max_digits = len(str(num_bins))
    for f_id in range(num_bins):
        ctr_str = '0'*(max_digits - len(str(f_id+1))) + str(f_id+1)
        bin_file = os.path.join(cfg.BINNING_DIR, "{}{}.{}".format(cfg.FILE_PREFIX, \
            ctr_str, cfg.LIBRARY_BIN_FORMAT))
        os.system("touch " + bin_file)
        bin_files.append(bin_file)

def write2bins(buffer):
    global bin_files
    print(buffer)
    #sys.exit()
    for fid, buffer_per_file in enumerate(buffer):
        if len(buffer_per_file) > 0:
            #print("{} >> '{}'".format(buffer_per_file, bin_files[fid]))
            # remark single apostrophe (') may occur in header line
            os.system('echo "{}" >> {}'.format(buffer_per_file, bin_files[fid]))

def distribute():
    print("Status: write {} files in {}".format(num_bins, cfg.BINNING_DIR))
    # write back with one-pass over large src file, cache cfg.BUFFER_SIZE reference
    # sequence and write back in up to num_bins bins
    buffer = ['' for _ in range(num_bins)]
    local_buffer_size = 0
    for src_file in src_files:
        refseq = ''
        acc = ''
        acc_prev = None
        with open(src_file, 'r') as f:
            ignore = False
            for line in f:
                # new header write back previous sequence
                if line.startswith(cfg.HEADER_PREFIX):
                    mobj = cfg.RX_ACC.search(line)
                    if mobj is None:
                        print("Error: could not extract accession from '", line, "'")
                        sys.exit()
                    if acc in acc2fid: # del previously handled accession from dictionary
                        del acc2fid[acc]
                    if len(acc2fid) == 0:
                        break
                    acc = mobj.group(1)
                    if acc in acc2fid:
                        ignore = False
                        buffer[acc2fid[acc]] += line
                        local_buffer_size += 1
                    else:
                        ignore = True
                elif not ignore:
                    buffer[acc2fid[acc]] += line
                    local_buffer_size += 1
                # check if buffer full
                if local_buffer_size == cfg.BUFFER_SIZE:
                    write2bins(buffer)
                    buffer = ['' for _ in range(num_bins)]
                    local_buffer_size = 0

    write2bins(buffer)

# given db connection and cursor, and a taxid as (level, taxid) return the parent
# node (level+1, par(taxid))
def parent(con, cur, node):
    print(node)
    cur.execute("SELECT parent_tax_id FROM node WHERE tax_id = {}".format(node[1]))
    con.commit()
    row = cur.fetchone()
    if row is None:
        print("Missing key ({}) in table node".format(node[1]))
        sys.exit()
        #return None
    else:
        return (node[0] + 1, row[0]) # or just row?


# args.binning      Directory containing one or many fasta files to be split w.r.t.
#                   the taxonomy. If no source directory is given (indicated by 'all'),
#                   then all database resident accessions are used (take care that
#                   all accessions have reference sequences in your reference file).
def binning(args):
    src_dir = args.binning
    global acc2fid
    global src_files
    global num_bins

    # create NUM_BINS bin files in BINNING_DIR
    num_bins = int(args.num_bins[0])
    initbins()

    # dictionary of taxonomic subtree IDs and the contained accessions {tax_i: [acc_i1, acc_i2, ...]}
    tax2accs = {}

    # accession number collection for binning
    accessions = []

    # fetch accessions from database, src_file is taken from config
    if args.binning == "all":
        src_files = [cfg.FILE_REF]
        # connect to database
        con = psycopg2.connect(dbname='taxonomy', user=cfg.user_name, host='localhost', password=args.password[0])
        con.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = con.cursor()
        cur.execute("SELECT accession FROM accessions LIMIT 128")
        con.commit()
        for record in cur:
            accessions.append(record[0])
        # close database connection
        cur.close()
        con.close()
    # extract accessions from source file
    else:
        # source files with sequences to be binned into num_bins files
        src_files = [f_node for f_node in os.listdir(args.binning) if cfg.LIBRARY_FORMAT_RX.match(f_node) is not None]
        for f_node in os.listdir(args.binning):
            # extract accessions
            if cfg.LIBRARY_FORMAT_RX.match(f_node) is not None:
                with open(os.path.join(args.binning, f_node), 'r') as f:
                    for line in f:
                        mobj = cfg.RX_ACC.search(line)
                        if mobj is not None:
                            acc = mobj.group(1)
                            accessions.append(acc)

    # resolve all accessions at once to their taxIDs
    acc2tax_list = acc2tax(accessions)
    # encode level in first position of key tuple
    for a2t in acc2tax_list:
        accs = tax2accs.get(a2t[1], [])
        if (1, a2t[1]) in tax2accs:
            tax2accs[(1, a2t[1])].append(a2t[0])
        else:
            tax2accs[(1, a2t[1])] = [a2t[0]]

    # connect to database
    con = psycopg2.connect(dbname='taxonomy', user=cfg.user_name, host='localhost', password=args.password[0])
    con.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cur = con.cursor()
    # merge as long key list exceeds target bin number
    while len(tax2accs) > num_bins:
        # parallel for loop
        #pool = multiprocessing.Pool(num_processes)
        key_list = sorted(list(tax2accs.keys()), key=lambda t: t[0])
        print(key_list)

        # concurrent key querying, key = (level, taxid)
        # parfor, per thread: blocked, newkey_list
        newkey_list = []
        blocked = set()
        # parse taxonomic subtrees starting with lowest levels
        for key in key_list:
            # block keys that will be merged with lower level subtrees
            # remove this shared set due to global interpreter lock? or thread-local set
            if key in blocked:
                continue

            # set parent_key = (level+1, parent(taxid))
            parent_key = parent(con, cur, key)
            if parent_key in key_list:
                blocked.add(parent_key)
            # note: in concurrent situation this key might turn out to be someone's
            # else parent key to be merged later (=> 2nd check necessary)
            newkey_list.append((parent_key, key))
        # sequential merge of node to its ancestor
        # keys are set to their ancestor and are either new or to be merged
        for parent_key, key in newkey_list:
            if key in blocked:
                continue
            if parent_key in tax2accs.keys():
                tax2accs[parent_key] += tax2accs.pop(key)
            else:
                tax2accs[parent_key] = tax2accs.pop(key)

    # close database connection
    cur.close()
    con.close()

    # split given the global accession to file ID dictionary
    for fid, key in enumerate(sorted(tax2accs.keys())):
        for acc in tax2accs[key]:
            acc2fid[acc] = fid
    distribute()

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
