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

### Download Taxonomy
`tactac` relies on a set of files provided by NCBI, namely, `nodes.dmp`, `names.dmp`, and `taxidlineage.dmp` in order to create the full taxonomy, and assign names to taxIDs.
```shell
python tactac.py --taxonomy
```

### Download Reference
`tactac` will resolve NCBI accession IDs to taxonomic identifiers. In order to do so, per default the complete non-human nucleotide data set in fasta format will be downloaded (`nt`). You can change the reference data set by editing the provided  configuration file.
```shell
python tactac.py --reference
```

### Build Database

#### From Scratch
Start running the installed PostgreSQL server. With the `build` option a new database will be created. It is assumed that the default settings are

| Server name | Host Name   | Port | User Name  |
|-------------| ------------|------|------------|
| 'local'     | 'localhost' | 5432 | 'postgres' |


```shell
python tactac.py --build
```

#### Continue or Update
HTTP queries are the bottleneck of the build process. In case of interruption or partial failure of queries, you can continue the filling of the `Accessions` table by setting the `--continue` flag. The other three tables won't be modified (i.e. `Node`, `Names`, `Lineage`)!

```shell
python tactac.py --build --continue
```
or with personalized configurator


## Queries

### Accession to TaxID
Give a single accession number as command line argument or file. The file format has to be either in `fasta` format which may also contain sequence data to be ignored or be a list of accessions (one per row). Whenever input values are given directly in  terminal, output will also be printed in terminal, otherwise a result file is generated.
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
python tactac.py --binning [<src_dir>|default='all'] [--threads <thread_num>]
```
