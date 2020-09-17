import argparse
import os
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import subprocess
import sys
import urllib.request

parser = argparse.ArgumentParser(description='Setup and build database relating taxonomic identifiers with accessions and organism names.')
parser.add_argument('--taxonomy', '-t', dest='taxonomy', action='store_true', \
    help='Download or build ')
parser.add_argument('--reference', '-r', dest='reference', action='store_true')
parser.add_argument('--download', '-d', dest='download', action='store_true')
parser.add_argument('--build', '-b', dest='build', action='store_true')
parser.add_argument('--password', '-p', dest='password', nargs=1, default='1234', \
    help='Password of the postgres user.')
parser.add_argument('--config', '-c', dest='config_file', nargs=1, default='config', \
    help='Alternative configuration file to set database connection details.')

def fill_accessions(args):
    con = psycopg2.connect(dbname='taxonomy', user=cfg.user_name, host='localhost', password=args.password[0])
    con.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cur = con.cursor()
    cur.execute("DROP TABLE accessions")
    cur.execute("CREATE TABLE accessions(tax_id int NOT NULL,accession varchar NOT NULL,PRIMARY KEY(tax_id, accession), FOREIGN KEY (tax_id) REFERENCES node(tax_id));")
    # extract data from taxidlineage.dmp and fill 'names' table
    print("Start filling 'accessions' ...")
    with open(cfg.FILE_NT, 'r') as f:
        for line in f:
            if line.startswith('>'):
                print(line)
                mobj = cfg.RX_ACC.search(line)
                if mobj is None:
                    print("ERROR: could not extract accession number from '{}'".format(line))
                    continue
                print(mobj.groups()[0])
                acc = mobj.groups()[0]
                print(cfg.URL_ACC.format(acc))
                fp = urllib.request.urlopen(cfg.URL_ACC.format(acc))
                html_str = fp.read().decode("utf8")
                mobj = cfg.RX_WEB_TAXID.search(html_str)
                if mobj is None:
                    print("ERROR: could not extract accession number from query '{}'".format(URL_ACC.format(mobj.group(0))))
                    continue
                print("mobj.group_0 = {}".format(mobj.group(0)))
                print(mobj.groups())
                print(mobj.groups()[0])

                tax_id = int(mobj.groups()[0])
                print(tax_id)

                cur.execute("INSERT INTO accessions VALUES (%s, %s)", (tax_id, acc));
                con.commit()

    cur.close()
    con.close()

def taxonomy_build(args):

    print("Start building taxonomy database ...")
    # read database creation script
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
    print(sql_db)
    print(sql_tab)
    # create database by connecting first to default, then create new one
    con = psycopg2.connect(dbname='postgres', user=cfg.user_name, host='localhost', password=args.password[0])
    con.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cur = con.cursor()
    for sql in sql_db:
        print('exec: {}'.format(sql))
        cur.execute(sql)
        con.commit()
    cur.close()
    con.close()
    # connecto to newly created taxonomy DB
    con = psycopg2.connect(dbname='taxonomy', user=cfg.user_name, host='localhost', password=args.password[0])
    con.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cur = con.cursor()
    # create tables
    for sql in sql_tab:
        print('exec: {}'.format(sql))
        cur.execute(sql)
        con.commit()


    limit = 100000000
    # extract data from nodes.dmp and fill 'node' table
    print("Start filling 'nodes' ...")
    with open(os.path.join(cfg.DIR_TAX_TMP, cfg.FILE_nodes), 'r') as f:
        i = 0
        for line in f:
            cells = [cell.strip() for cell in line.split('|')][:3]
            i += 1
            cur.execute('INSERT INTO node VALUES (%s, %s, %s)', tuple(cells))
            con.commit()
            if i == limit:
                break
    print("Table 'nodes' done.")

    # extract data from names.dmp and fill 'names' table
    print("Start filling 'names' ...")
    with open(os.path.join(cfg.DIR_TAX_TMP, cfg.FILE_names), 'r') as f:
        i = 0
        for line in f:
            cells = [cell.strip() for cell in line.split('|')][:4]
            if cells[-1] != 'authority':
                cur.execute('INSERT INTO names VALUES (%s, %s, %s) ON CONFLICT DO NOTHING', tuple(cells[:3]))
                #print("insert: {}, {}, {}".format(cells[0], cells[1], cells[2]))
                con.commit()
                i += 1
                if i == limit:
                    break
    print("Table 'names' done.")

    # extract data from taxidlineage.dmp and fill 'names' table
    print("Start filling 'lineage' ...")
    with open(os.path.join(cfg.DIR_TAX_TMP, cfg.FILE_lineage), 'r') as f:
        i = 0
        for line in f:
            cells = [cell.strip() for cell in line.split('|')][:2]
            tax = cells[1].strip().replace(' ', ',')
            if len(tax) == 0:
                cur.execute("INSERT INTO lineage (tax_id) VALUES ({})".format(cells[0]))
            else:  # '{20000, 25000, 25000, 25000}',
                cur.execute("INSERT INTO lineage VALUES ({}, '{{{}}}')".format(cells[0], tax))
            con.commit()
            i += 1
            if i == limit:
                break
    print("Table 'lineage' done.")

    # extract data from taxidlineage.dmp and fill 'names' table
    print("Start filling 'accessions' ...")
    with open(cfg.FILE_NT, 'r') as f:
        for line in f:
            if line.startswith('>'):
                mobj = cfg.RX_ACC(line)
                if mobj is None:
                    print("ERROR: could not extract accession number from '{}'".format(line))
                    continue
                http_url = URL_ACC.format(mobj.group(0))
                fp = urllib.request.urlopen(URL_ACC.format(mobj.group(0)))
                mystr = fp.read().decode("utf8")
                mobj = cfg.RX_WEB_TAXID.search(html_str)
                if mobj is None:
                    print("ERROR: could not extract accession number from query '{}'".format(URL_ACC.format(mobj.group(0))))
                    continue
                tax_id = int(mobj.group(0))
                print(tax_id)
                sys.exit()
    print("Table 'accessions' done.")

    # close cursor and connection
    cur.close()
    con.close()
    print("... ok.")


if __name__ == "__main__":
    args = parser.parse_args()
    if (args.)
    print(args)
    import args.config_file as cfg

#    taxonomy_build(args)
    fill_accessions(args)
