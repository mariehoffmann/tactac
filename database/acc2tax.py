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
import urllib.request

import config as cfg

acc_rx = re.compile('\W+')

def acc2tax_sql(con, cur, acc):
    cur.execute("SELECT tax_id FROM accessions WHERE accession = '{}'".format(acc))
    con.commit()
    acc = cur.fetchone()[0]
    return acc

def acc2tax(args):
    # connect to database
    con = psycopg2.connect(dbname='taxonomy', user=cfg.user_name, host='localhost', password=args.password[0])
    con.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cur = con.cursor()
    # test if args.acc2tax argument is file
    # file format is fasta or accessions listed row-wise
    f_out_name = os.path.join(cfg.WORK_DIR, 'acc2tax.csv')
    f_out_fail = os.path.join(cfg.WORK_DIR, 'acc2tax.unfound.csv')
    fasta_flag = False
    if os.path.isfile(file_path) is True:
        with open(file_path, 'r') as f_in, open(f_out_name, 'w') as f_out, open(f_out_fail, 'w') as f_fail:
            line = f_in.readline()
            while line:
                if line.startswith('>'):
                    fasta_flag = True
                    mo = cfg.RX_ACC.search(line)
                    if mo is None:
                        print("Parse Error: could not extract accession number from fasta file '{}'".format(line))
                        f_fail.write("{}".format(line))
                    else:
                        acc = mo.group(1)
                        tax = acc2tax_sql(con, cur, acc)
                        f_out.write("{},{}\n".format(acc, tax))
                elif fasta_flag is not False and len(line.strip()) < 20:
                    mo = acc_rx.search(line)
                    if mo is None:
                        print("Parse Error: could not extract accession number from non-fasta file '{}'".format(line))
                        continue
                    acc = mo.group(1)
                    tax = acc2tax_sql(acc)
                    f_out.write("{},{}\n".format(acc, tax))

                line = f.readline()
        print('Result file written to:\t\t', f_out_name)
        print('Unresolved accessions written:\t', f_out_fail)
        value = True
    # else interprete as accession
    else:
        value = acc2tax_sql(cur, con, acc)

    # close database connection
    cur.close()
    con.close()
    return value
