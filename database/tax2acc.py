'''
    tactac - database for taxonomic ID and accession number resolution

    Manual under https://github.com/mariehoffmann/tactac/wiki

    author: Marie Hoffmann ozymandiaz147[at]gmail[.]com
'''

import os
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import sys

import config as cfg

def tax2acc_sql(con, cur, tax):
    results = ""
    stack = [tax]
    # collect sub nodes
    while len(stack) > 0:
        node = stack.pop()
        print("current node is: ", node)
        result = str(node)
        # query for accessions assigned directly to this node
        print("SELECT accession FROM accessions WHERE tax_id = {}".format(node))
        cur.execute("SELECT accession FROM accessions WHERE tax_id = {}".format(node))
        for record in cur:
            print("result: ", record[0])
            result += "," + record[0]  # or without indexing
        results += result + '\n'
        return results
        # push child nodes onto stack
        cur.execute("SELECT tax_id FROM node WHERE parent_taxi_id = {}".format(node))
        con.commit()
        for record in cur:
            child = record[0]
            # todo single element tuple might not be subscriptable
            # push back new child node as potential new parent node
            stack.append(child)
    return results

def tax2acc(args):
    # connect to database
    con = psycopg2.connect(dbname='taxonomy', user=cfg.user_name, host='localhost', password=args.password[0])
    con.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cur = con.cursor()

    f_out_name = os.path.join(cfg.WORK_DIR, 'tax2acc.csv')
    f_out_fail = os.path.join(cfg.WORK_DIR, 'tax2acc.unfound.csv')
    if os.path.isfile(args.tax2acc[0]) is True:
        with open(file_path, 'r') as f_in, open(f_out_name, 'w') as f_out, open(f_out_fail, 'w') as f_fail:
            line = f_in.readline()
            while line:
                mo = RX_TAXID.search(line)
                if mo is None:
                    print("Parse Error: could not extract accession number from fasta file '{}'".format(line))
                    f_fail.write("{}".format(line))
                else:
                    tax = mo.group(1)
                    acc_list = tax2acc_sql(con, cur, tax)
                    f_out.write(acc + ", " + ",".join([str(acc) for acc in acc_list]))
                    f_out.write("{},{}\n".format(acc, tax))
                line = f_in.readline()
    else:
        try:
            int(args.tax2acc[0])
            acc_list = tax2acc_sql(con, cur, args.tax2acc[0])
            print("Accessions for {}:".format(args.tax2acc[0]))
            print(acc_list)
        except ValueError:
            print("Value Error: taxid = '{}' is not an integer.".format(args.tax2acc[0]))

    # close database connection
    cur.close()
    con.close()