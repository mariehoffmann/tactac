'''
    tactac - database for taxonomic ID and accession number resolution

    Manual under https://github.com/mariehoffmann/tactac/wiki

    author: Marie Hoffmann ozymandiaz147[at]gmail[.]com

    ---------------------------------------------------------------------

    Parallelizations:
        1. Taxonomic subtree merging: Partitioning of taxID list and parent taxID
            querying for potential merge
        2. Distribution: One thread writes out buffer to num_bins files.
            Other fills buffer with library sequences.
'''

import multiprocessing
import os
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import re
import subprocess
import sys
from threading import Lock, Thread

import config as cfg
from database.acc2tax import acc2tax
from database.distribute import distribute
from database.parent import parent
from utilities.grep_accessions import grep_accessions

# input library files
src_files = []
# distributed library output files (=bins)
num_bins = None
bin_files = []
# assignment of accessions to file IDs
acc2fid = {}

# create output bin files
def init_bins():
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


# args.binning      Directory containing one or many fasta files to be split w.r.t.
#                   the taxonomy. If no source directory is given (indicated by 'all'),
#                   then all database resident accessions are used (take care that
#                   all accessions have reference sequences in your reference file).
def binning(args):
    global acc2fid
    global src_files
    global num_bins

    # TODO: continue here
    if args.binning == 'all':
        src_files = [cfg.FILE_REF]
    else:
        if not os.path.isdir(args.binning):
            print('Error: {} is not are directory'.format(args.binning))
        src_files = [f for f in os.listdir(args.binning) if LIBRARY_FORMAT_RX.match(f) is not None]
    print(src_files)

    # create NUM_BINS bin files in BINNING_DIR
    num_bins = int(args.num_bins[0])
    init_bins()

    # dictionary of taxonomic subtree IDs and the contained accessions {tax_i: [acc_i1, acc_i2, ...]}
    tax2accs = {}

    # accession number collection for binning
    accessions = grep_accessions(args)
    max_load = cfg.MAX_RATIO * int(max(2, float(len(accessions)/num_bins)))
    print("max_load: ", max_load)

    # resolve all accessions at once to their taxIDs, format [(acc, tax)]
    acc2tax_list = acc2tax(accessions)

    make_key = lambda k : (1, k)
    # encode level in first position of key tuple
    # note: if all accessions are from identical taxonomic node, they end up in one bin!
    for a2t in acc2tax_list:
        a2t_key = make_key(a2t[1])
        if a2t_key in tax2accs:
            tax2accs[a2t_key].append(a2t[0])
        else:
            tax2accs[a2t_key] = [a2t[0]]

    # connect to database
    con = psycopg2.connect(dbname='taxonomy', user=cfg.user_name, host='localhost', password=args.password[0])
    con.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cur = con.cursor()
    # merge as long key list exceeds target bin number
    print("{} initial bins".format(len(tax2accs)))
    print("top 5 bins: ", sorted([len(val) for val in tax2accs.values()])[-5:])
    full_set = set([key for key, val in tax2accs.items() if len(val) > max_load])

    while len(tax2accs) > num_bins:
        # parallel for loop
        #TODO: pool = multiprocessing.Pool(num_processes)
        key_list = sorted(list(tax2accs.keys()), key=lambda t: t[0])

        # concurrent key querying, key = (level, taxid)
        # parfor, per thread: blocked, newkey_list
        newkey_list = []
        blocked = set().union(full_set)
        # parse taxonomic subtrees starting with lowest levels
        for key in key_list:
            # block keys that will be merged with lower level subtrees
            if key in blocked:
                continue
            # set p_key = (level+1, parent(taxid))
            p_key = parent(con, cur, key)
            pp_key = parent(con, cur, p_key)
            if p_key in key_list:
                blocked.add(p_key)
            if pp_key in key_list:
                blocked.add(pp_key)
            # note: in concurrent situation this key might turn out to be someone's
            # else parent key to be merged later (=> 2nd check necessary)
            newkey_list.append((p_key, key))  # i.e. p_key will replace key
        # sequential merge of node to its ancestor
        # keys are set to their ancestor and are either new or to be merged
        for p_key, key in newkey_list:
            if key in blocked:
                continue
            if p_key in tax2accs.keys():
                tax2accs[p_key] += tax2accs.pop(key)
            else:
                tax2accs[p_key] = tax2accs.pop(key)
            # stop merging for all future iterations, if size exceeds max_load
            if len(tax2accs[p_key]) >= max_load:
                full_set.add(p_key)

    # close database connection
    cur.close()
    con.close()

    print("final distribution: ")
    # split given the global accession to file ID dictionary
    for fid, key in enumerate(sorted(tax2accs.keys())):
        for acc in tax2accs[key]:
            acc2fid[acc] = fid
        print("{}: {} accs".format(fid, len(tax2accs[key])))

    # concurrent library distribution
    distribute(acc2fid, bin_files)

    # check files sizes in terms of line numbers
    lines_rx = re.compile('^\s+(\d+)\s+.+?')
    file_lines = []
    for bin_file in bin_files:
        result = subprocess.check_output("wc -l " + str(bin_file), stderr=subprocess.STDOUT, shell=True)
        mobj = lines_rx.match(result.decode('ascii'))
        if mobj is None:
            print("Error: could not extract number of lines from '{}'".format(result))
            sys.exit(0)
        file_lines.append(int(mobj.group(1)))
    print('lines per bin: ', file_lines)
