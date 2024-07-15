# Oncodash Knowledge Base

## Overview

OncodashKB is a data conversion tool that extracts data from Oncodash' tables
and feed them in a graph database.

It uses [Biocypher](https://biocypher.org) as the main tool for doing the ontology alignment
and for supporting several graph database backends.


## Installation

### Source Code

The project uses [Poetry](https://python-poetry.org). You can install like this:

```
git clone https://github.com/oncodash/oncodashkb.git
cd oncodashkb
poetry install
```

Poetry will create a virtual environment according to your configuration (either
centrally or in the project folder). You can activate it by running `poetry
shell` inside the project directory.

### Database

Theoretically, any graph database supported by Biocypher may be used.

As of now, OncodashKB targets using Neo4j, which have some particularities.

So far, it has been tested with Neo4j 5.11, using a
[patched version of Biocypher](https://github.com/jdreo/biocypher/tree/feat/neo4j-5+).

Note that the community edition of Neo4j do not support multiple database,
hence the need to configure the default database in `neo4j.conf` to be:
`initial.dbms.default_database=oncodash`, before starting Neo4j with
`neo4j-admin server start`.


## Usage

First, double-check that `config/biocypher_config.yaml` is aligned with your needs.

Do not forget to start the graph database and to run the following commands in a poetry shell:
```
neo4j-admin server start
poetry shell
```

OncodashKB takes CSV files as an input, and exports them to the graph database:
```
./make.py <CSV data file> <YAML mapping file>
```

The mapping file configures the kind of node the rows of the table will represent,
and how columns will be converted to an edge-node pair, or a property of a node.

Once executed, Biocypher prepares a shell script named `neo4j-admin-import-call.sh` in a timestamped sub-directory.
Executing this script will connect to the Neo4j server and feed it with the extracted graph.

OncodashKB prints the name of the produced print on the standard output,
so that you can execute it right away.


## Side steps

To check whether there is some data in your graph database, you can use the
command-line client of Neo4j:
```
cypher-shell -d oncodash -u neo4j "MATCH (n) RETURN n LIMIT 5;"
```
and you should see 5 nodes.

To visualize [a part of] the graph, you can use
[neo4j-browser](https://github.com/neo4j/neo4j-browser)
with a similar Cypher query.

Notes:
- Neo4j-browser [needs a specific node version](https://github.com/neo4j/neo4j-browser/issues/1833), you can install it with:
  ```
  pip install nodeenv
  nodeenv --node=16.10.0 env
  . env/bin/activate
  npm install yarn
  yarn install
  yarn start
  ```
- Neo4j server disable connection across the network by default.
  To connect the browser to a server on another machine,
  be sure to edit the server's `neo4j.conf` with the `0.0.0.0` address:
  `server.bolt.listen_address=0.0.0.0:7687`


## Development

Hints and tips about designing the ontology alignements:
- Ontologies may be browsed with [Protégé](https://protege.stanford.edu/).
- The [biolink model](https://biolink.github.io/biolink-model/biolink-model.owl.ttl)
  has (a lot of) classes attached at the root `Thing`.
  These are actually decomissioned stuff, the actual classes are under `entity`.

# OncodashKB Adapters

## CGI adapter 

**Cancer Genome Interpreter** is the cancer database that contains information about various genetic alterations that can be associated with the patient, gene details, samples, disease type, and transcript information.

To launch CGI adapter, use `--cgi` option and path to the CSV file with the data that you want to integrate.

**Example of use:**
```
./weave.py –cgi /path_to_file/test_genomics_cgimutation.csv
```



## OncoKB adapter

**OncoKB** is the cancer database that contains information about various genetic alterations that can be associated with the patient, gene details, samples, and disease type, as well as treatment options with FDA, OncoKB evidence levels, and related publications. 

To launch OncoKB adapter, use `--oncokb` option and path to the CSV file with the data that you want to integrate.

**Example of use:**
```
./weave.py –oncokb /path_to_file/test_genomics_oncokbannotation.csv
```

## Gene Ontology adapter

**Gene Ontology** is one of the biggest biomedical databases. The described adapter helps to integrate the data about the molecular function of the gene product, as well as the biological process in which these genes are involved.

- Molecular function: GO annotations that have relation type `enabled` or `contributes_to`.
- Biological process: GO annotations that have relation type `involved_in`.

**To integrate the data, three files are necessary:**
-	`--gene_ontology` option for GO annotations in GAF format  [Download GO annotations](http://current.geneontology.org/products/pages/downloads.html)
-	`--gene_ontology_owl` option for GO ontology in OWL format [Download GO ontology](https://geneontology.org/docs/download-ontology/)
-	`--gene_ontology_genes` option for the list of genes for which we want to integrate the GO annotations (example in adapters/Hugo_Symbol_genes.conf file, by default = list of genes from OncoKB database).

**Example of use:**
```
./weave.py --gene_ontology /path_to_file/goa_human.gaf --gene_ontology_owl /path_to_file/go.owl --gene_ontology_genes /path_to_file/Hugo_Symbol_genes.conf
```

If you want to integrate annotations with another type of relations, you can modify the `adapters/gene_ontology.py` file by adding the next code in the **class Gene_ontology** (example for the `involved_in` edge type):
```
# create new columns that depends on edge type
        df['GO_involved_in'] = None
        
# cut df to include only edge type that we have chosen and annotations for genes from OncoKB
        df = df[((df['Qualifier'].isin(['enables', 'involved_in', 'contributes_to'])) &
                 (df['DB_Object_Symbol'].isin(included_genes)))]
```
Also, you need to add code in `separate_edges_types` method:

```
# function to copy GO_term to related column for future ontoweaver mapping based on Qualifier column (relation type)
   def separate_edges_types(row):
        if row['Qualifier'] == 'enables':
            row['GO_enables'] = row['GO_term']
        elif row['Qualifier'] == 'involved_in':
            row['GO_involved_in'] = row['GO_term']
```

Finally, you need to specify the node and edge types in the `gene_ontology.yaml` for `GO_involved_in` column.


## Open Targets adapter

Open Targets is a public database that aims to systematically identify and prioritize drug targets for disease treatment. The described adapter helps to integrate the data about **the targets, disease/phenotypes, drugs** and **evidences.**

Current adapter works with the data in **Parquet** format. 

To download the data, you can visit [this page](https://platform.opentargets.org/downloads/data) and separately download needed datasets or execute the next bash script:

```bash

#!/bin/bash

mkdir OpenTargets

cd OpenTargets

rsync -rpltvz --delete rsync.ebi.ac.uk::pub/databases/opentargets/platform/24.06/output/etl/parquet/targets .

rsync -rpltvz --delete rsync.ebi.ac.uk::pub/databases/opentargets/platform/24.06/output/etl/parquet/diseases .

rsync -rpltvz --delete rsync.ebi.ac.uk::pub/databases/opentargets/platform/24.06/output/etl/parquet/molecule .

rsync -rpltvz --delete rsync.ebi.ac.uk::pub/databases/opentargets/platform/24.06/output/etl/parquet/evidence .


```

As Open Targets database contains millions of the rows of the data, in order to integrate only necessary information, you need to precise the genes (Hugo Symbols and Ensembl IDs) in the configuration files:

- Hugo symbols in the file`oncodashkb/adapters/Hugo_Symbol_genes.conf`
- Ensembl ID in the file `oncodashkb/adapters/Ensembl_genes.conf`

Example of use for targets, diseases, drugs and evidences (only from Chembl) integration:

```bash
 ./weave.py  --open_targets path_to_OpenTargets/OpenTargets/targets   --open_targets_drugs path_to_OpenTargets/OpenTargets/molecule  --open_targets_diseases path_to_OpenTargets/OpenTargets/diseases  --open_targets_evidences path_to_OpenTargets/OpenTargets/evidence/sourceId\=chembl  

```
