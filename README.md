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

