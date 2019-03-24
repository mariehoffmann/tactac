# tax2acc

Sets up a PostgreSQL database based by default on the latest taxonomy files provided by NCBI and the `nt` reference dataset. It resolves for each accession the taxonomic ID (taxID) it is assigned to by name. 
**tax2acc** provides functions that let's you annotate fasta headers by their accessions. Any tool parsing fasta reference files and needing a taxonomic mapping, e.g. lowest common ancestor computation, may profit from this annotation. 
Vice versa mapping is also possible, i.e., output all accessions for a given taxID. This allows you to compute reference coverage rates for taxonomic branches or subsample reference sequences for simulation experiments.

## Setup

see Wiki
