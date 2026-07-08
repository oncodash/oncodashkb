#!/usr/bin/env bash

if [[ -z "$1" ]] ; then
    echo "ERROR, usage: $0 <DECIDER_Eduuni_archive_dir> <DECIDER_snapshot_dir>" >&2
    echo "First argument is the archive of the DECIDER project, with at least WP1 and WP9 subdirectories." >&2
    echo "Second argument is where you want to put the prepared DECIDER data snapshot." >&2
    echo "For instance:" >&2
    echo "    From Eduuni, check WP1 and WP9 directories, and click 'Download'" >&2
    echo "    Unzip the archive." >&2
    echo "    Run: ./prepare.sh <wherever is the unziped dir> DECIDER_2026-06-26" >&2
    echo "    This will copy the necessary DECIDER files in: data/DECIDER_2026-06-26" >&2
    echo "    and the public databases files in: data/<DB name>" >&2
    exit 2
fi

set -e
#set -o pipefail

root_dir=$(pwd)
data_dir="data"
decider_dir="$(realpath $1)"
decider_snapshot_dir="$data_dir/$2"

log_file="prepare.log"
echo "" > $log_file
log=$(realpath $log_file)

script_dir="$(realpath $(dirname $0))"

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
echo "Prepare patients data..." >&2

if [[ ! -d $decider_snapshot_dir ]] ; then
    echo " │ Copy DECIDER data..." >&2
    mkdir -p $decider_snapshot_dir

    cp "$decider_dir/SVs/SVannotated_perGene_clusters_20260702.csv" "$decider_snapshot_dir/structural_variants_2.csv"

    p="$decider_dir/DECIDER WP9 Oncodash/Annotated Genomic Data/cnas_v2.9_short_mutations_v4.10"
    cp "$p/short_mutations_v4.10_local.csv" "$decider_snapshot_dir/short_mutations_local.csv"
    cp "$p/short_mutations_v4.10_external.csv" "$decider_snapshot_dir/short_mutations_external.csv"
    cp "$p/cnas_v2.9_local.csv" "$decider_snapshot_dir/cnas_local.csv"
    cp "$p/cnas_v2.9_external.csv" "$decider_snapshot_dir/cnas_external.csv"
    cp "$p/treatments_oncokb.csv" "$decider_snapshot_dir/treatments_oncokb.csv"

    p="$decider_dir/DECIDER WP9 Oncodash/Annotated Genomic Data/vTMB"
    cp "$p/brk_placeholder_vTMB.xlsx" "$decider_snapshot_dir/structural_variants.xlsx"
    cp "$p/NETWORK_OT_OKB_filtered_2024_12_17.csv" "$decider_snapshot_dir/oncokb_gene_status_info.csv"

    p="$decider_dir/DECIDER WP1 Clinical data"
    cp "$p/12122025_Clinical export DECIDER collab.xlsx" "$decider_snapshot_dir/clinical_export.xlsx"

    echo " └OK" >&2
else
    echo " └ DECIDER data directory '$decider_snapshot_dir' exists, I'll just check files." >&2

fi

cd $root_dir

### 2.2.2 - Check DECIDER data

echo "Check DECIDER data..." >&2
check() {
    if [[ ! -f "$1" ]] ; then
        echo "File: $1 is missing." >&2
        exit 1
    fi
}
declare -a decider_files=(
    $decider_snapshot_dir/short_mutations_local.csv
    $decider_snapshot_dir/short_mutations_external.csv
    $decider_snapshot_dir/cnas_local.csv
    $decider_snapshot_dir/cnas_external.csv
    $decider_snapshot_dir/structural_variants.xlsx
    $decider_snapshot_dir/treatments_oncokb.csv
    $decider_snapshot_dir/oncokb_gene_status_info.csv
    $decider_snapshot_dir/clinical_export.xlsx
    $decider_snapshot_dir/structural_variants_2.csv
)
if [[ -d "$decider_snapshot_dir" ]] ; then
    for f in ${decider_files[@]}; do
        check $f
    done
else
    echo "The '$decider_snapshot_dir' directory does not exists." >&2
    exit 1
fi

echo " └OK" >&2


### 2.2.3 – adapters paths

echo "Instantiate templated adapters..." >&2
cd $script_dir/oncodashkb/adapters/

declare -a decider_adapters=(
    short_mutations_local.yaml
    short_mutations_external.yaml
    copy_number_amplifications_local.yaml
    copy_number_amplifications_external.yaml
    structural_variants.yaml
    structural_variants_2.yaml
)

for a in ${decider_adapters[@]} ; do
    cat template__$a | sed "s,{{{DECIDER_DIR}}},$decider_snapshot_dir,g" > $a
done
echo " └OK" >&2

cd $root_dir


# ## 2.3 - Debugging data

echo "Create a smaller debuging data set in data_debug/..." >&2
lines=100
echo " │ DECIDER..." >&2
mkdir -p data_debug
mkdir -p data_debug/DECIDER_debug/
for f in ${decider_files[@]}; do
    head -n $lines $f > data_debug/DECIDER_debug/$(basename $f)
done

cp $decider_snapshot_dir/structural_variants.xlsx data_debug/DECIDER_debug/
cp $decider_snapshot_dir/clinical_export.xlsx data_debug/DECIDER_debug/

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
cd $script_dir/oncodashkb

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

echo "Everything is OK, you can now call: ./make.sh $decider_snapshot_dir" >&2

