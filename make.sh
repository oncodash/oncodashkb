#!/usr/bin/env bash

CONFIG="config/neo4j.yaml"
if [[ -z "$1" ]] ; then
    echo "ERROR, usage: $0 <DECIDER_data_dir> [config] [debug]" >&2
    echo "    config defaults to: $CONFIG" >&2
    exit 2
fi

if [[ -z "$2" ]] ; then
    echo "Selecting Neo4j output configuration." >&2
elif [[ "$2" == "debug" ]] ; then
    echo "ERROR, if DEBUG MODE, usage: $0 <DECIDER_data_dir> <config> debug" >&2
    exit 2
else
    echo "Selecting output configuration: $2" >&2
    CONFIG="$2"
fi

set -e
set -o pipefail

decider_dir="$1"
data_dir="data"
if [[ "$3" == "debug" ]] ; then
    echo "DEBUG MODE" >&2
    data_dir="data_debug"
    decider_dir="data_debug/DECIDER/debug"
fi

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
if [[ "$3" == "debug" ]] ; then
    py_args=""
    weave_args="--debug -v DEBUG"
fi


echo "Activate virtual environment..." >&2
source $(dirname $(uv python find))/activate


if [[ "$CONFIG" == "config/neo4j.yaml" ]] ; then
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

cmd="uv run python3 ${py_args} $script_dir/weave.py \
    --config $CONFIG \
    --short-mutations-local                 $decider_dir/short_mutations_local.csv  \
    --short-mutations-external              $decider_dir/short_mutations_external.csv  \
    --copy-number-amplifications-local      $decider_dir/cnas_local.csv \
    --copy-number-amplifications-external   $decider_dir/cnas_external.csv  \
    --structural-variants                   $decider_dir/structural_variants.xlsx  \
    --cgi                                   $decider_dir/treatments_cgi.csv \
    --omnipath-networks                     $data_dir/omnipath_networks/omnipath_webservice_interactions__latest.tsv.gz \
    --open-targets-drug-molecule            $data_dir/OT/drug_molecule/
    --open-targets-drug_mechanism_of_action $data_dir/OT/drug_mechanism_of_action/
    --open-targets-target                   $data_dir/OT/target/
    ${weave_args}" # \
    # --clinical                              $data_dir/DECIDER/clinical/clinical_export.xlsx \
    # --oncokb                     $data_dir/DECIDER/$data_version/treatments.csv \


echo "Weaving command:" >&2
echo "$cmd" >&2

$cmd > tmp.sh


if [[ "$CONFIG" == "config/neo4j.yaml" ]] ; then
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

