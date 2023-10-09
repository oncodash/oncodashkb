#!/usr/bin/bash

source $(poetry env info --path)/bin/activate
neo4j-admin server stop && ./make.py genomics_oncokbannotation.csv oncodashkb/adapters/oncokb.yaml > tmp.sh && sh $(cat tmp.sh) && neo4j-admin server start && sleep 5 && cypher-shell --username neo4j --database oncodash --password $(cat neo4j.pass) "MATCH (n) RETURN n;"

