'''
    tactac - database for taxonomic ID and accession number resolution

    Manual under https://github.com/mariehoffmann/tactac/wiki

    author: Marie Hoffmann ozymandiaz147[at]gmail[.]com
'''

import csv
import os
import progressbar
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import sys
import urllib.request

import config as cfg

'''
    Produce two files representing a taxonomic subset of the library, namely
    a taxonomy file in csv format [taxid, p_taxid, is_species], list of accessions for each taxid
    in the format [taxid,acc1, acc2,...], and a fasta file with sequences
    corresponding to the collected accessions constituting the taxonomic subtree
    as a subset of the 'nt' dataset.
'''

# leaf nodes equivalent to species
leaf_ranks = set(['species', 'varietas', 'forma', 'subspecies', 'subvarietas', 'subforma'])

def subtree(args):
    print("Enter subtree ...")
    clade_taxid = int(args.subtree)
    if not os.path.exists(cfg.DIR_SUBSET):
        os.makedirs(cfg.DIR_SUBSET)
    dir_subset_tax = os.path.join(cfg.DIR_SUBSET, str(clade_taxid))
    if not os.path.exists(dir_subset_tax):
        os.mkdir(dir_subset_tax)
    # taxonomy as tuples [taxid, parent_taxid]
    file_tax = os.path.join(dir_subset_tax, 'root_{}.tax'.format(clade_taxid))
    # accessions as [taxid,acc1,acc2,...]
    file_acc = os.path.join(dir_subset_tax, 'root_{}.acc'.format(clade_taxid))
    # map of positional counter (ID) and written out accession
    file_ID2acc = os.path.join(dir_subset_tax, 'root_{}.id'.format(clade_taxid))
    # fasta file with all accessions of clade
    file_lib = os.path.join(dir_subset_tax, 'root_{}.fasta'.format(clade_taxid))

    # open DB connection
    con = psycopg2.connect(dbname='taxonomy', user=cfg.user_name, host='localhost', password=args.password)
    con.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cur = con.cursor()
    print("Connected to DB")

    # Select all taxids in this clade and write them back with flag indicating a species
    print("Collecting all taxids in clade (", clade_taxid, ")")
    taxid_stack = [clade_taxid]
    ctr_taxids = 0
    taxid_set = set()
    with open(file_tax, 'w') as ft:
        ft.write('taxid,parent_taxid,is_species \n')
        while (len(taxid_stack)) > 0:
            taxid = taxid_stack.pop()
            taxid_set.add(taxid)
            ctr_taxids += 1
            # push back taxonomic children
            cur.execute("SELECT tax_id, rank FROM node WHERE parent_tax_id = {};".format(taxid))
            #con.commit()
            for record in cur:
                taxid_stack.append(record[0])
                is_species = 1 if record[1] in leaf_ranks else 0
                ft.write('{},{},{}\n'.format(record[0], taxid, is_species))
    print("Taxonomic subtree written to ", file_tax)

    print("Collecting at most ", args.num_samples, " accessions per taxon ...")
    accs_set = set()
    with open(file_acc, 'w') as fa:
        fa.write('taxid,acc1,acc2,...\n')
        clade_size = 0
        for i in progressbar.progressbar(range(len(taxid_set))):
            taxid = taxid_set.pop()
            # grep at most args.num_samples (default=5) random accessions per taxid
            cur.execute("SELECT accession FROM accessions WHERE tax_id = {} ORDER BY RANDOM() LIMIT {};".format(taxid, args.num_samples))
            #con.commit()
            taxid2accs = str(taxid)
            for record in cur:
                taxid2accs += ',' + record[0]
                accs_set.add(record[0])
            # write only taxids with directly assigned accessions
            if taxid2accs.find(',') > -1:
                clade_size += 1
                fa.write(taxid2accs + '\n')

    cur.close()
    con.close()
    print("\nClade size (nodes with assigned accessions): ", clade_size)
    print("Taxonomic mapping written to ", file_acc)

    buffer = ''
    acc = ''
    acc_done_ctr = 0
    print("Copying accessions from nt[.FASTA] ...")
    with progressbar.ProgressBar(max_value = len(accs_set)) as bar:
        with open(cfg.FILE_REF, 'r') as f, open(file_lib, 'w') as fw, open(file_ID2acc, 'w') as fID:
            ignore = False
            ID = 1
            for line in f:
                # new header line, check ignore flag
                if line.startswith(cfg.HEADER_PREFIX):
                    mobj = cfg.RX_ACC.search(line)
                    if mobj is None:
                        print('Error: could not extract accession from ', line)
                    # del previously handled accession from dictionary
                    if acc in accs_set:
                        accs_set.remove(acc)
                        acc_done_ctr += 1
                        bar.update(acc_done_ctr)
                    if len(accs_set) == 0:
                        break
                    acc = mobj.group(1)
                    if acc in accs_set:
                        ignore = False
                        fID.write("{},{}\n".format(ID, acc))
                        ID += 1
                    else:
                        ignore = True
                if not ignore:
                    fw.write(line)

    print("Library sequences of subtree written to ", file_lib)
    print("Position IDs of accessions written to ", file_ID2acc)
