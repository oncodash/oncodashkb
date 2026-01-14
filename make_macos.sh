#!/usr/bin/bash

# Exit on error.
set -e
set -o pipefail

data_dir="data"
data_version="$1"

py_args="-O" # Optimize = remove asserts and optimize bytecode.
weave_args="-v INFO" # Default, for having clean progress bars.
if [[ "$2" == "debug" ]] ; then
    echo "DEBUG MODE" >&2
    py_args=""
    weave_args="-v DEBUG"
fi

echo "Activate virtual environment..." >&2
source $(poetry env info --path)/bin/activate


if [[ "$2" != "debug" ]] ; then
    echo "Stop Neo4j server..." >&2
    neo_version=$(neo4j-admin --version | cut -d. -f 1)
    if [[ "$neo_version" -eq 4 ]]; then
        server="neo4j"
    else
        server="neo4j-admin server"
    fi
    $server stop
fi

echo "Weave data..." >&2

cmd="python3 ${py_args} $(pwd)/weave.py --verbose INFO \
    --clinical                              $data_dir/DECIDER/$data_version/clinical_export.csv \
    --short-mutations-local                 $data_dir/DECIDER/$data_version/snv_local.csv \
    --short-mutations-external              $data_dir/DECIDER/$data_version/snv_external.csv  \
    --copy-number-amplifications-local      $data_dir/DECIDER/$data_version/cna_local.csv \
    --copy-number-amplifications-external   $data_dir/DECIDER/$data_version/cna_external.csv  \
    ${weave_args}" # \

echo "Weaving command:" >&2
echo "$cmd" >&2

$cmd > tmp.sh


if [[ "$2" != "debug" ]] ; then
    echo "Run import script..." >&2
    chmod a+x  $(cat tmp.sh)
    sh $(cat tmp.sh)

    echo "Restart Neo4j..." >&2
    $server start
    sleep 5

    echo "Send a test query..." >&2
    cypher-shell --username neo4j --database oncodash --password $(cat neo4j.pass) "MATCH (p:Patient) RETURN p LIMIT 20;"
fi

echo "Done" >&2