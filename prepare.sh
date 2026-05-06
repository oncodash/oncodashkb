#!/usr/bin/env bash

if [[ -z "$1" ]] ; then
    echo "ERROR, usage: $0 <DECIDER_data_dir>" >&2
    exit 2
fi

set -e
#set -o pipefail

data_dir="data"
decider_dir="$1"
log_file="prepare.log"
echo "" > $log_file
log=$(realpath $log_file)

script_dir="$(dirname $0)"

error_handler() {
    local line_number=$1
    local error_code=$2
    local command="$3"

    echo " └ERROR at line $line_number, failed with code $error_code" >&2
    echo "Full logs:" >&2
    echo "----------8<----------" >&2
    cat $log >&2
    echo "----------8<----------" >&2
    echo "ERROR ($error_code) in $0:$line_number, faulty command:" >&2
    echo "$command" >&2
}

trap 'error_handler ${LINENO} $? "$BASH_COMMAND"' ERR


download() {
    URL="$1"
    FILE="$2"

    TO_FILE=""
    if [[ -n "$FILE" ]] ; then
        if [[ -f $FILE ]] ; then
            TO_FILE="--output $FILE --time-cond $FILE"
        else
            TO_FILE="--output $FILE"
        fi
    else
        TO_FILE="--remote-name"
    fi

    cmd="curl --write-out %{filename_effective} $TO_FILE $URL"
    # echo "$cmd" 2>&1 >> $log
    FILENAME=$($cmd 2>> $log)

    if [[ -s "$FILENAME" ]] ; then
        echo "'$FILENAME' has data" >> $log
    else
        echo "ERROR: '$(realpath $FILENAME)' has no data" >&2
        exit 3
    fi
}

# 1 - Necessary checks

echo "Check for neo4j.pass..." >&2
if [[ ! -f neo4j.pass ]] ; then
    echo "File: neo4j.pass is missing." >&2
    exit 1
fi
echo " └OK" >&2


echo "Check dependencies..." >&2
REQUIRED_CMD="gzip zcat curl rsync head"
for p in $REQUIRED_CMD ; do
    if ! command -v $p > /dev/null ; then
        echo "Package '$p' is missing, please install it." >&2
        exit 1
    fi
done

if [[ -d $script_dir/.venv ]] ; then
    echo " │ Environment already existing, if you want to upgrade it, either:" >&2
    echo " │   - remove the '.venv' directory and run 'prepare.sh' again," >&2
    echo " │   - or run 'uv sync' manually." >&2
else
    echo " │ Install environment..." >&2
    uv sync --no-upgrade 2>&1 >> $log
    echo " │  └OK" >&2
fi
echo " └OK" >&2

# 2 - DATA

## 2.1 - External prior knowledge 

echo "Download data..." >&2
mkdir -p data
cd data

echo " │ Gene Ontology..." >&2
mkdir -p GO 2>&1 >> $log
cd GO
download https://current.geneontology.org/annotations/goa_human.gaf.gz
# gunzip goa_human.gaf.gz
download https://purl.obolibrary.org/obo/go.owl
cd ..
echo " │  └OK" >&2


echo " │ Open Targets..." >&2
rsync_cmd="rsync --ignore-existing -rpltvz --delete"
ot_version="25.12"
mkdir -p OT
cd OT

echo " │ │ Target..." >&2
$rsync_cmd rsync.ebi.ac.uk::pub/databases/opentargets/platform/${ot_version}/output/target . 2>&1 >> $log
echo " │ │  └OK" >&2

echo " │ │ Drug-Mechanism..." >&2
$rsync_cmd rsync.ebi.ac.uk::pub/databases/opentargets/platform/${ot_version}/output/drug_mechanism_of_action . 2>&1 >> $log
echo " │ │  └OK" >&2

echo " │ │ Drug-Molecule..." >&2
$rsync_cmd rsync.ebi.ac.uk::pub/databases/opentargets/platform/${ot_version}/output/drug_molecule . 2>&1 >> $log
echo " │ │  └OK" >&2

cd ..  # Out of OT/
echo " │ └OK" >&2


echo " │ OmniPath Networks..." >&2
mkdir -p omnipath_networks
cd omnipath_networks
download https://archive.omnipathdb.org/omnipath_webservice_interactions__latest.tsv.gz
cd ..
echo " │  └OK" >&2


echo " │ Gene Symbol to Ensembl ID" >&2
mkdir -p HGNC
cd HGNC
download https://storage.googleapis.com/public-download-files/hgnc/tsv/tsv/hgnc_complete_set.txt
cd ..
echo " │  └OK" >&2

cd ..  # Back to project root.
echo " └OK" >&2

## 2.2 - DECIDER data

### 2.2.1 - Symlinks

cd $decider_dir

ln -sf cnas_v2.9_external.csv cnas_external.csv
ln -sf cnas_v2.9_local.csv cnas_local.csv
ln -sf short_mutations_v4.10_external.csv short_mutations_external.csv
ln -sf short_mutations_v4.10_local.csv short_mutations_local.csv
# cd ../clinical/
# ln -sf 12122025_Clinical_export_DECIDER_collab.xlsx ../$1/clinical_export.xlsx
ln -sf ./../clinical/12122025_Clinical_export_DECIDER_collab.xlsx ./../clinical/clinical_export.xlsx
ln -sf ./../placeholders/brk_placeholder.xlsx structural_variants.xlsx

cd -

### 2.2.2 - Check DECIDER data

echo "Check DECIDER data..." >&2
check() {
    if [[ ! -f "$1" ]] ; then
        echo "File: $1 is missing." >&2
        exit 1
    fi
}
declare -a decider_files=(
    $decider_dir/short_mutations_local.csv
    $decider_dir/short_mutations_external.csv
    $decider_dir/cnas_local.csv
    $decider_dir/cnas_external.csv
    $decider_dir/treatments_cgi.csv
    $decider_dir/treatments_oncokb.csv
)
if [[ -d "$decider_dir" ]] ; then
    for f in ${decider_files[@]}; do
        check $f
    done
else
    echo "The '$decider_dir' directory does not exists." >&2
    exit 1
fi
check $data_dir/DECIDER/clinical/clinical_export.xlsx
check $decider_dir/structural_variants.xlsx
echo " └OK" >&2

## 2.3 - Debugging data

echo "Create a smaller debuging data set in data_debug/..." >&2
lines=100
echo " │ DECIDER..." >&2
mkdir -p data_debug
mkdir -p data_debug/DECIDER/debug/
for f in ${decider_files[@]}; do
    head -n $lines $f > data_debug/DECIDER/debug/$(basename $f)
done
cp $decider_dir/structural_variants.xlsx data_debug/DECIDER/debug/structural_variants.xlsx
mkdir -p data_debug/DECIDER/clinical/
cp $data_dir/DECIDER/clinical/clinical_export.xlsx data_debug/DECIDER/clinical
echo " │  └OK" >&2

echo " │ GO & HGNC..." >&2
mkdir -p data_debug/GO
cp data/GO/go.owl data_debug/GO/

mkdir -p data_debug/HGNC
cp data/HGNC/hgnc_complete_set.txt data_debug/HGNC/
echo " │  └OK" >&2

echo " │ OpenTargets..." >&2
mkdir -p data_debug/OT
declare -a ot_dirs=(
    "drug_mechanism_of_action"
    "drug_molecule"
    "target"
)
for d in ${ot_dirs[@]}; do
    echo " │  │ $d..." >&2
    mkdir -p data_debug/OT/$d
    # Only the first parquet file
    cp data/OT/$d/part-00000* data_debug/OT/$d/
    echo " │  │  └OK" >&2
done
echo " │  └OK" >&2

echo " │ OmniPath..." >&2
mkdir -p data_debug/omnipath_networks
gunzip --to-stdout data/omnipath_networks/omnipath_webservice_interactions__latest.tsv.gz | head -n $lines | gzip > data_debug/omnipath_networks/omnipath_webservice_interactions__latest.tsv.gz
echo " │  └OK" >&2
echo " └OK" >&2

# 3 - Third party source code

echo "Download third-party source code..."
cd oncodashkb

echo " │ OmniPath networks transformer..." >&2
mkdir -p transformers
cd transformers
download https://raw.githubusercontent.com/njmmatthieu/omnipath-secondary-adapter/refs/heads/directed/src/omnipath_secondary_adapter/transformers/networks.py networks.py
cd ..
echo " │  └OK" >&2

echo " │ OmniPath networks adapter..." >&2
cd adapters
download https://raw.githubusercontent.com/njmmatthieu/omnipath-secondary-adapter/refs/heads/directed/src/omnipath_secondary_adapter/adapters/networks.yaml omnipath_networks.yaml
cd ..
echo " │  └OK" >&2

echo " │ OpenTargets Drug-Target Indications..." >&2
echo " │  │ Custom transformers..." >&2
cd transformers
download https://raw.githubusercontent.com/njmmatthieu/opentargets-dti/refs/heads/for_oncodashkb/adapters/ot-transformers.py ot_transformers.py
cd ..
echo " │  │  └OK" >&2

echo " │  │ Targets adapter..." >&2
cd adapters
download https://raw.githubusercontent.com/njmmatthieu/opentargets-dti/refs/heads/for_oncodashkb/adapters/target.yaml open_targets_target.yaml
cd ..
echo " │  │  └OK" >&2

echo " │  │ Drug adapter..." >&2
cd adapters
download https://raw.githubusercontent.com/njmmatthieu/opentargets-dti/refs/heads/for_oncodashkb/adapters/drug_mechanism_of_action.yaml open_targets_drug_mechanism_of_action.yaml
cd ..
echo " │  │  └OK" >&2

echo " │  │ Molecules adapter..." >&2
cd adapters
download https://raw.githubusercontent.com/njmmatthieu/opentargets-dti/refs/heads/for_oncodashkb/adapters/drug_molecule.yaml open_targets_drug_molecule.yaml
cd ..
echo " │  │  └OK" >&2

cd ..  # Out of the subdir oncodashkb
echo " │  └OK" >&2
echo " └OK" >&2

echo "Everything is OK, you can now call: ./make.sh." >&2

