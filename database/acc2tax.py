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
    #print('exec: ', "SELECT tax_id FROM accessions WHERE accession = '{}'".format(acc))
    con.commit()
    tax = cur.fetchone()[0]
    return tax

def acc2tax(query):
    # connect to database
    con = psycopg2.connect(dbname='taxonomy', user=cfg.user_name, host='localhost', password=cfg.password)
    con.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cur = con.cursor()
    #print(query)
    if type(query) == type([]):
        results = []
        for acc in query:
            results.append((acc, acc2tax_sql(con, cur, acc)))
        # close database connection
        cur.close()
        con.close()
        return results
    elif os.path.isfile(query):
        if not os.path.isdir(cfg.WORK_DIR):
            os.makedirs(cfg.WORK_DIR)
        f_out_name = os.path.join(cfg.WORK_DIR, 'acc2tax.csv')
        f_out_fail = os.path.join(cfg.WORK_DIR, 'acc2tax.unfound.csv')
        fasta_flag = False
        with open(query, 'r') as f_in, open(f_out_name, 'w') as f_out, open(f_out_fail, 'w') as f_fail:
            line = f_in.readline()
            while line:
                if line.startswith('>'):
                    fasta_flag = True
                    mo = cfg.RX_ACC.search(line[1:])
                    if mo is None:
                        print("Parse Error: could not extract accession number from fasta file '{}'".format(line))
                        f_fail.write("{}".format(line))
                    else:
                        acc = mo.group(1)
                        tax = acc2tax_sql(con, cur, acc)
                        f_out.write("{},{}\n".format(acc, tax))
                elif not fasta_flag and len(line.strip()) < 20:
                    mo = cfg.RX_ACC.search(line)
                    if mo is None:
                        print("Parse Error: could not extract accession number from non-fasta file '{}'".format(line))
                    else:
                        acc = mo.group(1)
                        tax = acc2tax_sql(con, cur, acc)
                        f_out.write("{},{}\n".format(acc, tax))

                line = f_in.readline()
        print('Result file written to:\t\t', f_out_name)
        print('Unresolved accessions written:\t', f_out_fail)
        value = True
    # else interprete as accession
    else:
        tax = acc2tax_sql(con, cur, query)
        #print("TaxID for {}: {}".format(query, tax))

    # close database connection
    cur.close()
    con.close()
