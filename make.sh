#!/usr/bin/env bash

CONFIG="config/neo4j.yaml"
if [[ -z "$1" ]] ; then
    echo "ERROR, usage: $0 <DECIDER_data_dir> <DECIDER_data_version> [config] [debug]" >&2
    echo "    config defaults to: $CONFIG" >&2
    exit 2
fi

if [[ -z "$2" ]] ; then
    echo "ERROR, usage: $0 <DECIDER_data_dir> <DECIDER_data_version> [config] [debug]" >&2
    echo "    config defaults to: $CONFIG" >&2
    exit 2
fi

if [[ -z "$3" ]] ; then
    echo "Selecting Neo4j output configuration." >&2
elif [[ "$3" == "debug" ]] ; then
    echo "ERROR, if DEBUG MODE, usage: $0 <DECIDER_data_dir> <DECIDER_data_version> <config> debug" >&2
    exit 2
else
    echo "Selecting output configuration: $3" >&2
    CONFIG="$3"
fi

set -e
set -o pipefail

data_dir="data"
decider_dir="$1"
decider_version="$2"
# decider_version_dir="$1/$2"
# decider_clinical_dir="$1/clinical"

if [[ "$4" == "debug" ]] ; then
    echo "DEBUG MODE" >&2
    data_dir="data_debug"
    decider_dir="data_debug/DECIDER"
    decider_version="debug"
fi

decider_version_dir="$decider_dir/$decider_version"
decider_clinical_dir="$decider_dir/clinical"

script_dir="$(dirname $0)"

case "$(uname)" in
    FreeBSD)   OS=FreeBSD ;;
    DragonFly) OS=FreeBSD ;;
    OpenBSD)   OS=OpenBSD ;;
    Darwin)    OS=Darwin  ;;
    SunOS)     OS=SunOS   ;;
    *)         OS=Linux   ;;
esac

echo $OS

if [[ "$OS" == "Linux" ]] ; then
    # When using Neo4j installed on system (like Ubuntu's packaged version),
    # the current directory must be writable by user "neo4j",
    # and all parent directories must be executable by "other".
    # Every interaction with the database must be done by user "neo4j",
    # and the import will try to write reports in the current directory.
    NEO_USER="sudo -u neo4j"
    # export JAVA_HOME="/usr/lib/jvm/java-21-openjdk-amd64"
else
    NEO_USER=""
fi

py_args="-O" # Optimize = remove asserts and optimize bytecode.
weave_args="-v INFO" # Default, for having clean progress bars.
if [[ "$4" == "debug" ]] ; then
    py_args=""
    weave_args="--debug -v DEBUG"
fi


echo "Activate virtual environment..." >&2
source $(dirname $(uv python find))/activate


# echo "Remove old BioCypher data" >&2
# rm -rf biocypher-*


echo "Weave data..." >&2

cmd="uv run python3 ${py_args} $script_dir/weave.py \
    --config $CONFIG \
    --clinical                              $decider_clinical_dir/clinical_export.xlsx \
    --short-mutations-local                 $decider_version_dir/short_mutations_local.csv  \
    --short-mutations-external              $decider_version_dir/short_mutations_external.csv  \
    --copy-number-amplifications-local      $decider_version_dir/cnas_local.csv \
    --copy-number-amplifications-external   $decider_version_dir/cnas_external.csv  \
    --structural-variants                   $decider_version_dir/structural_variants.xlsx  \
    --oncokb                                $decider_version_dir/treatments_oncokb.csv \
    --omnipath-networks                     $data_dir/omnipath_networks/omnipath_webservice_interactions__latest.tsv.gz \
    --open-targets-drug-molecule            $data_dir/OT/drug_molecule/
    --open-targets-drug_mechanism_of_action $data_dir/OT/drug_mechanism_of_action/
    --open-targets-target                   $data_dir/OT/target/
    ${weave_args}" # \
    # --cgi                                   $decider_version_dir/treatments_cgi.csv \
    # --oncokb-gene-status                    $decider_version_dir/oncokb_gene_status_info.csv \


echo "Weaving command:" >&2
echo "$cmd" >&2

$cmd > tmp.sh


if [[ "$CONFIG" == "config/neo4j.yaml" ]] ; then
    echo "Stop Neo4j server..." >&2
    neo_version=$(neo4j-admin --version | cut -d. -f 1)
    if [[ "$neo_version" -eq 4 ]]; then
        server="${NEO_USER} neo4j"
    else
        server="${NEO_USER} neo4j-admin server"
    fi
    $server stop

    echo "Run import script..." >&2
    chmod a+x  $(cat tmp.sh)
    ${NEO_USER} $SHELL $(cat tmp.sh)

    echo "Restart Neo4j..." >&2
    $server start
    sleep 5

    echo "Send a test query..." >&2
    ${NEO_USER} cypher-shell --username neo4j --database oncodash --password $(cat neo4j.pass) "MATCH (p:Patient) RETURN p LIMIT 20;"
fi

echo "Done" >&2

