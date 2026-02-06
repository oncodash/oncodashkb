# Oncodash Knowledge Base

## Overview

OncodashKB is a set of modules to create a reproducible Semantic Knowledge Graph
from existing iterable databases, with the aim of helping finding actionable
drugs against cancers.

As of now, our main use case is a pre-clinical study about finding drugs that
are actionable on some high-grade serous ovarian cancers.

Under the hood, it uses [OntoWeaver](https://github.com/oncodash/ontoweaver) for
describing how to import data. OntoWeaver uses [Biocypher](https://biocypher.org)
as a tool for doing the ontology composition, and for exporting the SKG to a
Neo4j database.


## Installation

### Source Code

The project uses [UV](https://docs.astral.sh/uv/). You can install OncodashKB
using the commands below:

``` sh
git clone https://github.com/oncodash/oncodashkb.git
cd oncodashkb
uv sync
```

UV will create a virtual environment according to your configuration (either
centrally or in the project folder). You can activate it by running `uv run bash`
inside the project directory.

If you have a problem with the `uv sync` command, it may be that the
`uv lock` command has not been ran after changing dependencies modification in
`$ONCODASHKB_HOME/pyproject.toml`. Try running `uv lock` to fix the issue.


### Requirements for preventing publishing patient ids

Please, install [pre-commit](https://pre-commit.com/) hooks before committing or
pushing anything new:

``` sh
pre-commit install
pre-commit install --hook-type pre-push
pre-commit install --hook-type commit-msg
```


### Database

Theoretically, OncodashKB can be exported to any graph database supported by
BioCypher's backends.

As of now, OncodashKB targets using Neo4j, which have some restrictions (most
notably not supporting type hierarchies on edges).

So far, it has been extensively tested with Neo4j 5+ but it should also works
with Neo4j 4+.


### Set up

Neo4j "Graph Database Self-Managed" version can be downloaded
[from their website](https://neo4j.com/deployment-center/).
When using with this version, be sure to add the `bin/` directory to `PATH` and
`PYTHONPATH`, as well as the correct version of Java to `JAVA_HOME`.

Note that the community edition of Neo4j do not support multiple databases,
hence the need to configure the default database in `$NEO4J_HOME/conf/neo4j.conf`
to be: `initial.dbms.default_database=oncodash` (which is commented out by
default, hence the default database will be called neo4j).

Note that the default database does not always need to be named `oncodash`,
but should match the name of the database in
`$ONCODASHKB_HOME/config/biocypher_config.yaml`.


## Usage

### Quick start guide

The quickest possible build of OncodashKB is calling:

``` sh
./prepare.sh <DECIDER_data_dir> # Downloads all the needed data.
./make.sh [debug] # Runs what's needed to build the SKG, and run a test Cypher query.
```

Note the optional "debug" option for the `make.sh` script, which enable a more
verbose log, python non-optimized run, and will stop on any error.


### Detailled build

If you need to handle some of the steps yourself, the following sections tries
to explain some subtleties.


#### 1. Weave database

The `weave.py` command will include the data files that you indicate into a part
of the SKG. It follows the general form of:

``` sh
uv run weave.py --database-A <data_file> --database-B <data_file> […]
```

You can get a list of supported options by running:

``` sh
uv run weave.py --help
```


#### 2. Import the database

Once executed, `weave.py` prepares a shell script named
`neo4j-admin-import-call.sh` in a timestamped sub-directory in
'$ONCODASHKB_HOME/biocypher-out'. The complete path of this file is printed at
the end of execution, you can programmatically capture it with a subshell:

``` sh
import_script=$(uv run weave.py […])
```

In case your Neo4j installation needs the environment variable 'NEO4J_HOME',
you will have to delete the 'bin/' prefix in the import script:

``` sh
version=$(~~bin/~~neo4j-admin --version | cut -d '.' -f 1)
...
```

Before importing the data by calling the import script, be sure that the Neo4j
server is stopped. Executing the import script will connect directly to the
Neo4j server data files, and feed it with the extracted graph:

``` sh
sh $import_script # If you captured the path as shown above.
# OR
sh <YOUR_PATH_TO>/neo4j-admin-import-call.sh # To call it directly.
```


#### 3. Start the server

You can start the  Neo4j server by using either of the commands below.

Neo4j 5+:

``` sh
neo4j-admin server start
```

Neo4j 4:

``` sh
neo4j start
```

This will give you an HTTP link to the "Neo4j browser" where you can explore
your graph from your own Web browser. By default, the link to Neo4j browser is:
`http://localhost:7474`.


#### 4. Stop the server

You can stop the server by using either of the commands below.

Neo4j 5+:

``` sh
neo4j-admin server stop
```

Neo4j 4:

``` sh
neo4j stop
```


#### 5. Exit the UV environment

``` sh
exit
```


## OncodashKB Adapters

### CGI adapter

**Cancer Genome Interpreter** is the cancer database that contains information
about various genetic alterations that can be associated with the patient, gene
details, samples, disease type, and transcript information.

To launch CGI adapter, use `--cgi` option and path to the CSV file with the data
that you want to integrate.

**Example of use:**

``` sh
./weave.py –cgi /path_to_file/test_genomics_cgimutation.csv
```


### OncoKB adapter

**OncoKB** is the cancer database that contains information about various
genetic alterations that can be associated with the patient, gene details,
samples, and disease type, as well as treatment options with FDA, OncoKB
evidence levels, and related publications.

To launch OncoKB adapter, use `--oncokb` option and path to the CSV file with
the data that you want to integrate.

**Example of use:**

``` sh
./weave.py –oncokb /path_to_file/test_genomics_oncokbannotation.csv
```


### Gene Ontology adapter

**Gene Ontology** is one of the biggest biomedical databases. The described
adapter helps to integrate the data about the molecular function of the gene
product, as well as the biological process in which these genes are involved.

- Molecular function: GO annotations that have relation type `enabled`
  or `contributes_to`.
- Biological process: GO annotations that have relation type `involved_in`.

**To integrate the data, three files are necessary:**
- `--gene_ontology` option for GO annotations in GAF format  [Download GO annotations](http://current.geneontology.org/products/pages/downloads.html)
- `--gene_ontology_owl` option for GO ontology in OWL format [Download GO ontology](https://geneontology.org/docs/download-ontology/)
- `--gene_ontology_genes` option for the list of genes for which we want to
  integrate the GO annotations (example in adapters/Hugo_Symbol_genes.conf file,
  by default = list of genes from OncoKB database).

**Example of use:**

``` sh
./weave.py --gene_ontology /path_to_file/goa_human.gaf --gene_ontology_owl /path_to_file/go.owl --gene_ontology_genes /path_to_file/Hugo_Symbol_genes.conf
```

If you want to integrate annotations with another type of relations, you can
modify the `adapters/gene_ontology.py` file by adding the next code in the
**class Gene_ontology** (example for the `involved_in` edge type):

``` python
# Create new columns that depends on edge type.
df['GO_involved_in'] = None

# Cut df to include only edge type that we have chosen and annotations
# for genes from OncoKB.
df = df[((df['Qualifier'].isin(['enables', 'involved_in', 'contributes_to'])) &
         (df['DB_Object_Symbol'].isin(included_genes)))]
```
Also, you need to add code in `separate_edges_types` method:

``` sh
# Function to copy GO_term to related column for future ontoweaver mapping
# based on Qualifier column (relation type).
   def separate_edges_types(row):
        if row['Qualifier'] == 'enables':
            row['GO_enables'] = row['GO_term']
        elif row['Qualifier'] == 'involved_in':
            row['GO_involved_in'] = row['GO_term']
```

Finally, you need to specify the node and edge types in the `gene_ontology.yaml`
for `GO_involved_in` column.


### Open Targets adapter

Open Targets is a public database that aims to systematically identify and
prioritize drug targets for disease treatment. The described adapter helps to
integrate the data about **the targets, disease/phenotypes, drugs** and **evidences.**

Current adapter works with the data in **Parquet** format.

To download the data, you can visit
[Open Target's download page](https://platform.opentargets.org/downloads/data)
and separately download needed datasets or execute the following bash script:

``` sh
#!/bin/bash

mkdir OpenTargets
cd OpenTargets

rsync -rpltvz --delete rsync.ebi.ac.uk::pub/databases/opentargets/platform/24.06/output/etl/parquet/targets .
rsync -rpltvz --delete rsync.ebi.ac.uk::pub/databases/opentargets/platform/24.06/output/etl/parquet/diseases .
rsync -rpltvz --delete rsync.ebi.ac.uk::pub/databases/opentargets/platform/24.06/output/etl/parquet/molecule .
rsync -rpltvz --delete rsync.ebi.ac.uk::pub/databases/opentargets/platform/24.06/output/etl/parquet/evidence .
```

As Open Targets database contains millions of the rows of the data, in order to
integrate only necessary information, you need to precise the genes
(Hugo Symbols and Ensembl IDs) in the configuration files:

- Hugo symbols in the file`oncodashkb/adapters/Hugo_Symbol_genes.conf`
- Ensembl ID in the file `oncodashkb/adapters/Ensembl_genes.conf`

Example of use for targets, diseases, drugs and evidences (only from Chembl)
integration:

``` sh
 ./weave.py  --open_targets path_to_OpenTargets/OpenTargets/targets   --open_targets_drugs path_to_OpenTargets/OpenTargets/molecule  --open_targets_diseases path_to_OpenTargets/OpenTargets/diseases  --open_targets_evidences path_to_OpenTargets/OpenTargets/evidence/sourceId\=chembl
```


## Development

When modifying any dependencies in `$ONCODASHKB_HOME/pyproject.toml`,
be sure to run `uv lock`.

Hints and tips about designing the ontology alignements:

- Ontologies may be browsed with [Protégé](https://protege.stanford.edu/).
- The [biolink model](https://biolink.github.io/biolink-model/biolink-model.owl.ttl)
  has (a lot of) classes attached at the root `Thing`.
  These are actually decomissioned stuff, the actual classes are under `entity`.

If you operate OncodashKB over sensitive data, you may want to enable Git hooks
that checks if there is a potential data leak before committing anything.
See the "installation" section above.


## Side steps

To check whether there is some data in your graph database, you can use the
command-line client of Neo4j:

``` sh
cypher-shell -d oncodash -u neo4j "MATCH (n) RETURN n LIMIT 5;"
```
and you should see 5 nodes.

To visualize [a part of] the graph, you can use
[neo4j-browser](https://github.com/neo4j/neo4j-browser)
with a similar Cypher query.

Notes:
- Neo4j-browser [needs a specific node version](https://github.com/neo4j/neo4j-browser/issues/1833),
  you can install it with:
  ``` sh
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


