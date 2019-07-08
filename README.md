# tactac

Sets up a PostgreSQL database based by default on the latest taxonomy files provided by NCBI and the `nt` reference dataset. It resolves for each accession the taxonomic ID (taxID) it is assigned to by name.
**tactac** provides functions that let's you
  * annotate fasta headers by their accessions, e.g. as needed for lowest common ancestor computations
  * collect all accessions for a given taxID, e.g. for computing reference coverage rates for taxonomic branches or for subsampling reference sequences
  * taxonomic binning, i.e. distribute the library into `1 << x` bins (fasta files), such that a bin represents a clade, e.g. as pre-processing step for YARA

## Prerequisites

  * Operating Systems: Linux, MacOS
  * Python3
  * [PostgreSQL Database Server](https://www.postgresql.org/download/)
  * Optionally a PostgreSQL database client, e.g. [SQL Tabs](https://www.sqltabs.com/)

## Usage

Start the PostgreSQL Server in its default configuration. If you want to change configuration settings like io paths, connection details, etc., overwrite `config.py`. See the complete set of options with
```shell
  python tactac.py --help
```

### Download Reference and Taxonomy Files
#### Download Taxonomy
`tactac` relies on a set of files provided by NCBI, namely, `nodes.dmp`, `names.dmp`, and `taxidlineage.dmp` in order to create the full taxonomy, and assign names to taxIDs.
```shell
python tactac.py --download tax
```

#### Download Reference
`tactac` will resolve NCBI accession IDs to taxonomic identifiers. In order to do so, per default the complete non-human nucleotide data set in fasta format will be downloaded (`nt`). You can change the reference data set by editing the provided  configuration file.
```shell
python tactac.py --download ref
```

#### Download Accession to Reference Resolution Table
Per default the latest `nucl_gb.accession2taxid.gz` file from `ftp://ftp.ncbi.nih.gov/pub/taxonomy/accession2taxid` will be downloaded. To modify the edit `config.py`.

```shell
python tactac.py --download acc2tax
```

#### Download All
Alternatively, to download all files at once use the `all` option.
```shell
python tactac.py --download all
```


### Build Database

#### From Scratch
Start running the installed PostgreSQL server. With the `build` option a new database will be created. It is assumed that the default settings are

| Server name | Host Name   | Port | User Name  |
|-------------| ------------|------|------------|
| 'local'     | 'localhost' | 5432 | 'postgres' |


```shell
python tactac.py --build --password <pwd>
```

#### Continue or Update
In case the `Accessions` table filling got interrupted (`nugc_gb.accession2taxid` currently contains 258,753,642 entries), you can continue the filling by setting the `--continue` flag. Optionally, you can give a hint terms of last successfully inserted accession. The parser will jump to the succeeding line and omit database queries to test the presence. Note that continuation leaves the other three tables, i.e. `Node`, `Names`, `Lineage`, unmodified!

```shell
python tactac.py --build --continue [<last_ins_>] --password <pwd>
```
or with personalized configurator


## Queries

### Accession to TaxID
Give a single accession number (without the version prefix) as command line argument or file. The file format has to be either in `fasta` format which may also contain sequence data to be ignored or be a list of accessions (one per row). Whenever input values are given directly in  terminal, output will also be printed in terminal, otherwise a result file is generated.
```shell
python tactac.py --acc2tax [<file>|<acc>]
```

### TaxID and associated Accessions
For each taxonomic node in the subtree given by `acc` via command line or listed row-wise in a file, the list of directly associated accession will be output in the row format `taxid,acc1,acc2,...`. The output behaviour is the same as for `acc2tax`.
```shell
python tactac.py --tax2acc [<file>|<acc>]
```

### Taxonomy aware Binning
Splits your reference library (e.g. given by the raw `nt` fasta file) with respect to the taxonomy. This is an important pre-processing step to apply taxonomy-aware indexing with [DREAM-Yara](https://github.com/temehi/dream_yara). Be sure your PostgreSQL server is running and the previous steps have been finished. If you want to use all accessions that are currently in your database, leave the argument void - per default `all` will be set. You may have to handover the database user password (`--password <pwd>`). The binning output directory is set in the configurator file `config.py` (see `BINNING_DIR`).
```shell
python tactac.py --binning [<src_dir>|default='all'] [--num_bins <num_bins>]
```

### Taxonomic Subtree
Create a subset of the complete taxonomy database given a root `taxid`. Four files will be generated:

  * Taxonomy file (`*.tax`), i.e. the taxonomic clade rooted by `taxid` in csv format `#taxid, parent_taxid` stored in `tactac/subset/<taxid>/root_<taxid>.tax`
  * Taxid table (`*.acc`) with directly assigned accessions, i.e. all accessions assigned to the clade in csv format `#taxid,acc1,acc2,...` stored in `tactac/subset/<taxid>/root_<taxid>.accs`
  * Sequence file (`*.fasta`) containing all references assigned to the clade
  * Positional map (`ID2acc`), i.e. a 1-based counter corresponding to an accession and its position within the above generated fasta file

 ```shell
 python tactac.py --subtree <taxid:int> --password <pwd>
 ```

## All Parameters


  References:
  -----------

  [1] Federhen, S. (2012). The NCBI Taxonomy database. Nucleic Acids Research, 40(D1), D136–D143. http://doi.org/10.1093/nar/gkr1178
