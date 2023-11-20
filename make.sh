#!/usr/bin/bash

# When using Neo4j installed on system (like Ubuntu's packaged version),
# the current directory must be writable by user "neo4j",
# and all parent directories must be executable by "other".
# Every interaction with the database must be done by user "neo4j",
# and the import will try to write reports in the current directory.
NEO_USER="sudo -u neo4j"

# Exit on error.
set -e

source $(poetry env info --path)/bin/activate

export JAVA_HOME="/usr/lib/jvm/java-11-openjdk-amd64"

neo_version=$(neo4j-admin --version | cut -d. -f 1)

if [[ "$neo_version" -eq 4 ]]; then
    server="${NEO_USER} neo4j"
else
    server="${NEO_USER} neo4j-admin server"
fi
$server stop
./weave.py --oncokb genomics_oncokbannotation.csv --cgi genomics_cgimutation.csv > tmp.sh
cat $(cat tmp.sh) | tee /dev/tty | ${NEO_USER} sh
$server start
sleep 5
cypher-shell --username neo4j --database oncodash --password $(cat neo4j.pass) "MATCH (n) RETURN n;"

