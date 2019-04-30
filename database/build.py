'''
    tactac - database for taxonomic ID and accession number resolution

    Manual under https://github.com/mariehoffmann/tactac/wiki

    author: Marie Hoffmann ozymandiaz147[at]gmail[.]com
'''

import csv
import os
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import subprocess
import sys
import urllib.request

import config as cfg

def fill_node_table(args):
    print("Start filling table 'nodes' ...")
    con = psycopg2.connect(dbname='taxonomy', user=cfg.user_name, host='localhost', password=args.password[0])
    con.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cur = con.cursor()
    with open(os.path.join(cfg.DIR_TAX_TMP, cfg.FILE_nodes), 'r') as f:
        i = 0
        for line in f:
            cells = [cell.strip() for cell in line.split('|')][:3]
            i += 1
            cur.execute('INSERT INTO node VALUES (%s, %s, %s)', tuple(cells))
            con.commit()
    cur.close()
    con.close()
    print("... done.")

def fill_names_table(args):
    print("Start filling 'names' ...")
    con = psycopg2.connect(dbname='taxonomy', user=cfg.user_name, host='localhost', password=args.password[0])
    con.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cur = con.cursor()
    with open(os.path.join(cfg.DIR_TAX_TMP, cfg.FILE_names), 'r') as f:
        for line in f:
            cells = [cell.strip() for cell in line.split('|')][:4]
            if cells[-1] != 'authority':
                cur.execute('INSERT INTO names VALUES (%s, %s, %s) ON CONFLICT DO NOTHING', tuple(cells[:3]))
                #print("insert: {}, {}, {}".format(cells[0], cells[1], cells[2]))
                con.commit()
    cur.close()
    con.close()
    print("... done.")

def fill_lineage_table(args):
    print("Start filling table 'lineage' ...")
    con = psycopg2.connect(dbname='taxonomy', user=cfg.user_name, host='localhost', password=args.password[0])
    con.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cur = con.cursor()
    with open(os.path.join(cfg.DIR_TAX_TMP, cfg.FILE_lineage), 'r') as f:
        for line in f:
            cells = [cell.strip() for cell in line.split('|')][:2]
            tax = cells[1].strip().replace(' ', ',')
            if len(tax) == 0:
                cur.execute("INSERT INTO lineage (tax_id) VALUES ({})".format(cells[0]))
            else:  # '{20000, 25000, 25000, 25000}',
                cur.execute("INSERT INTO lineage VALUES ({}, '{{{}}}')".format(cells[0], tax))
            con.commit()
    cur.close()
    con.close()
    print("... done.")

'''
    Grep accessions from fasta source file and query www.ncbi.nlm.nih.gov/nuccore/<accession>
    to resolve the taxonomic identifier for a given accession number. This requires
    an internet connection. On interruption fill_accessions_table will continue to fill
    the table instead of rebuilding it.
'''
def fill_accessions_table(args):
    log_file = os.path.join(cfg.WORK_DIR, 'unresolved_accessions.log')
    print("Start filling table 'accessions' ...")
    con = psycopg2.connect(dbname='taxonomy', user=cfg.user_name, host='localhost', password=args.password[0])
    con.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cur = con.cursor()

    line_continue = 0
    if not args.continue_flag:
        cur.execute("DROP TABLE accessions")
        cur.execute("CREATE TABLE accessions(tax_id int NOT NULL,accession varchar NOT NULL,PRIMARY KEY(tax_id, accession), FOREIGN KEY (tax_id) REFERENCES node(tax_id));")
    elif args.continue_flag is not None:
        print("Locating last processed accession ...")
        result = subprocess.check_output("grep -m 1 -n -e {} {}".format(args.continue_flag, cfg.FILE_ACC2TAX), stderr=subprocess.STDOUT, shell=True)
        line_continue = int(result.decode('ascii').split(':')[0])

    with open(cfg.FILE_ACC2TAX, 'r') as csvfile:
        reader = csv.DictReader(csvfile, delimiter='\t')
        for l_id, row in enumerate(reader):
            if l_id < line_continue:
                continue
            cur.execute("SELECT * FROM accessions WHERE accession = '{}';".format(row['accession']))
            # extracted accession is already in database, got to next
            if cur.fetchone() is not None:
                print("{} already in accessions table.".format(row['accession']))
                continue
            cur.execute("SELECT * FROM node WHERE tax_id = '{}';".format(row['taxid']))
            if cur.fetchone() is None:
                 os.system("echo 'Missing node with tax_id = {}' >> {}".format(row['taxid'], log_file))
                 continue
            cur.execute("INSERT INTO accessions VALUES ({}, '{}')".format(row['taxid'], row['accession']))
            print("INSERT INTO accessions VALUES ({}, '{}')".format(row['taxid'], row['accession']))
            con.commit()
    cur.close()
    con.close()
    print("Missing taxids in node table have been written to {}".format(log_file))

    print("... done.")

'''
    with open(cfg.FILE_REF, 'r') as f:
        for line in f:
            if line.startswith(cfg.HEADER_PREFIX):
                #print(line)
                mobj = cfg.RX_ACC.search(line)
                if mobj is None:
                    print("ERROR: could not extract accession number from '{}'".format(line))
                    sys.exit(-1)
                    continue
                acc = mobj.groups()[0]
                cur.execute("SELECT * FROM accessions WHERE accession = '{}';".format(acc))
                # extracted accession is already in database, got to next
                if cur.fetchone() is not None:
                    print("{} already in accessions table.".format(acc))
                    continue
                print("Fetching {}".format(acc))
                #print(cfg.URL_ACC.format(acc))
                fp = urllib.request.urlopen(cfg.URL_ACC.format(acc))
                html_str = fp.read().decode("utf8")
                mobj = cfg.RX_WEB_TAXID.search(html_str)
                if mobj is None:
                    os.system("echo 'Regex RX_WEB_TAXID not found for {}' >> {}".format(acc, log_file))
                    continue
                tax_id = int(mobj.groups()[0])
                cur.execute("SELECT * FROM node WHERE tax_id = {}".format(tax_id))
                if cur.fetchone() is None:
                    os.system("echo 'Missing node with tax_id = {}' >> {}".format(tax_id, log_file))
                    continue
                cur.execute("INSERT INTO accessions VALUES (%s, %s)", (tax_id, acc));
                con.commit()
'''


'''
    Create database "taxonomy", define schema from taxonomy.sql script, and fill tables.
    If continue_flag is true, it is assumed that "taxonomy" and schema exists, and
    also the timely uncritical "node", "names", "lineage" table are filled.
'''
def build(args):
    if args.continue_flag is False:
        sql_db = []  # database setup
        sql_tab = []  # table creation commands
        with open('taxonomy.sql', 'r') as f:
            sql = ''
            for line in f.readlines():
                if len(line.strip()) > 0:
                    sql += line
                if line.strip().endswith(';'):
                    sql = sql.rstrip()
                    if sql.startswith("CREATE TABLE"):
                        sql_tab.append(sql)
                    else:
                        sql_db.append(sql)
                    sql = ''
        # create database by connecting first to default, then create new one
        con = psycopg2.connect(dbname='postgres', user=cfg.user_name, host='localhost', password=args.password[0])
        con.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = con.cursor()
        for sql in sql_db:
            cur.execute(sql)
            con.commit()
        cur.close()
        con.close()
        # connect to newly created taxonomy DB
        con = psycopg2.connect(dbname='taxonomy', user=cfg.user_name, host='localhost', password=args.password[0])
        con.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = con.cursor()
        # create tables
        for sql in sql_tab:
            cur.execute(sql)
            con.commit()
        cur.close()
        con.close()

        # extract data from nodes.dmp and fill 'nodes' table
        fill_node_table(args)

        # extract data from names.dmp and fill 'names' table
        fill_names_table(args)

        # extract data from taxidlineage.dmp and fill 'lineage' table
        fill_lineage_table(args)

    # collect taxids for accessions
    fill_accessions_table(args)
