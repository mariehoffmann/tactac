'''
    tactac - database for taxonomic ID and accession number resolution

    Manual under https://github.com/mariehoffmann/tactac/wiki

    author: Marie Hoffmann ozymandiaz147[at]gmail[.]com
'''

import multiprocessing
import os
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import sys

import config as cfg
from database.acc2tax import acc2tax

# input library files
src_files = []
# distributed library output files (=bins)
bin_files = [None for _ in range(cfg.NUM_BINS)]
# assignment of accessions to file IDs
acc2fid = {}

# create output bin files
def initbins():
    global bin_files
    os.system("mkdir -p {}".format(cfg.BINNING_DIR))
    for f_id in range(cfg.NUM_BINS):
        bin_file = os.path.join(cfg.BINNING_DIR, "{}{}.{}".format(cfg.FILE_PREFIX, f_id+1, cfg.LIBRARY_BIN_FORMAT))
        os.system("touch " + bin_file)
        bin_files.append(bin_file)

def write2bins(buffer):
    global bin_files
    for i, buffer_per_file in enumerate(buffer):
        if len(buffer_per_file) > 0:
            os.system("{} >> {}".format(buffer_per_file, bin_files[i]))

def distribute():
    # write back with one-pass over large src file, cache cfg.BUFFER_SIZE reference
    # sequence and write back in up to cfg.NUM_BINS bins
    buffer = [[] for _ in range(cfg.NUM_BINS)]
    local_buffer_size = 0
    for src_file in src_files:
        refseq = ''
        acc = ''
        with open(src_file, 'r') as f:
            ignore = False
            for line in f:
                # new header write back previous sequence
                if line.startswith(cfg.HEADER_PREFIX):
                    mobj = cfg.RX_ACC.search(line)
                    if mobj is None:
                        print("Error: could not extract accession from '", line, "'")
                        sys.exit()
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
                    buffer = [[] for _ in range(cfg.NUM_BINS)]
                    local_buffer_size = 0

            # last line quit for loop
            buffer[acc2fid[acc]] += refseq
            write2bins(bin_files, buffer)

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


# src_dir           directory containing one or many fasta files to be split w.r.t. the taxonomy
#                   If src_dir is not given (indicated by 'all'), then all database resident accessions are used
#                   (take care that all accessions have reference sequences in your reference file).
# num_processes     number of processes used for multithreading
def binning(args):
    src_dir = args.binning
    global acc2fid
    global src_files
    # create NUM_BINS bin files in BINNING_DIR
    initbins()

    # dictionary of taxonomic subtree IDs and the contained accessions {tax_i: [acc_i1, acc_i2, ...]}
    tax2accs = {}

    # accession number collection for binning
    accessions = []

    # fetch accessions from database, src_file is taken from config
    if src_dir == "all":
        src_files = [cfg.FILE_REF]
        # connect to database
        con = psycopg2.connect(dbname='taxonomy', user=cfg.user_name, host='localhost', password=args.password[0])
        con.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = con.cursor()
        cur.execute("SELECT accession FROM accessions LIMIT 128")
        con.commit()
        for record in cur:
            print("result: ", record[0])
            accessions.append(record[0])
        # close database connection
        cur.close()
        con.close()
    # extract accessions from source file
    else:
        # source files with sequences to be binned into cfg.NUM_BINS files
        src_files = [f_node for f_node in os.listdir(src_dir) if cfg.LIBRARY_FORMAT_RX.match(f_node) is not None]
        for f_node in os.listdir(src_dir):
            # extract accessions
            if cfg.LIBRARY_FORMAT_RX.match(f_node) is not None:
                with open(os.path.join(src_dir, f_node), 'r') as f:
                    for line in f:
                        mobj = cfg.RX_ACC.search(line)
                        if mobj is not None:
                            acc = mobj.group(1)
                            accessions.append(acc)

    # resolve all accessions at once to their taxIDs
    acc2tax_list = acc2tax(accessions)
    # todo: set levels based on DB query
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
    while len(tax2accs) > cfg.NUM_BINS:
        # parallel for loop
        #pool = multiprocessing.Pool(num_processes)
        key_list = sorted(list(tax2accs.keys()), key=lambda t: t[0])
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
            newkey_list = []
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
    distribute()

    # check files sizes in terms of line numbers
    for bin_file in bin_files:
        os.system("wc -l {}".format(bin_file))
