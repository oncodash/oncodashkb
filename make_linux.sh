#!/usr/bin/bash

# When using Neo4j installed on system (like Ubuntu's packaged version),
# the current directory must be writable by user "neo4j",
# and all parent directories must be executable by "other".
# Every interaction with the database must be done by user "neo4j",
# and the import will try to write reports in the current directory.
NEO_USER="sudo -u neo4j"

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

# export JAVA_HOME="/usr/lib/jvm/java-21-openjdk-amd64"


echo "Activate virtual environment..." >&2
source $(poetry env info --path)/bin/activate


if [[ "$2" != "debug" ]] ; then
    echo "Stop Neo4j server..." >&2
    neo_version=$(neo4j-admin --version | cut -d. -f 1)
    if [[ "$neo_version" -eq 4 ]]; then
        server="${NEO_USER} neo4j"
    else
        server="${NEO_USER} neo4j-admin server"
    fi
    $server stop
fi

echo "Weave data..." >&2

cmd="python3 ${py_args} $(pwd)/weave.py --verbose INFO \
    --clinical                   $data_dir/DECIDER/$data_version/clinical_export.csv \
    --single_nucleotide_variants $data_dir/DECIDER/$data_version/snv_external.csv  \
    --copy_number_alterations    $data_dir/DECIDER/$data_version/cna_external.csv \
    --gene_ontology_genes        $data_dir/DECIDER/$data_version/OncoKB_gene_symbols.conf \
    --oncokb                     $data_dir/DECIDER/$data_version/treatments.csv \
    --gene_ontology              $data_dir/GO/goa_human.gaf.gz \
    --gene_ontology_owl          $data_dir/GO/go.owl \
    --gene_ontology_reverse
    ${weave_args}" # \
    #--small_molecules           $data_dir/omnipath_networks/omnipath_webservice_interactions__small_molecule_interactions_filtered.tsv.gz"

echo "Weaving command:" >&2
echo "$cmd" >&2

$cmd > tmp.sh


if [[ "$2" != "debug" ]] ; then
    echo "Run import script..." >&2
    chmod a+x  $(cat tmp.sh)
    $(cat tmp.sh) | tee /dev/tty | ${NEO_USER} sh

    echo "Restart Neo4j..." >&2
    $server start
    sleep 5

    echo "Send a test query..." >&2
    sudo -u neo4j cypher-shell --username neo4j --database oncodash --password $(cat neo4j.pass) "MATCH (p:Patient) RETURN p LIMIT 20;"
fi

echo "Done" >&2

