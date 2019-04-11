'''
    tactac - database for taxonomic ID and accession number resolution

    Manual under https://github.com/mariehoffmann/tactac/wiki

    author: Marie Hoffmann ozymandiaz147[at]gmail[.]com

'''

import os
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import re
import sys

import config as cfg
from database.acc2tax import acc2tax

def grep_accessions(args):
    accessions = []
    print('args.binning = ', args.binning)
    #sys.exit()
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
    return accessions
