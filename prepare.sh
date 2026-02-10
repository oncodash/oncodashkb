#!/usr/bin/bash

if [[ -z "$1" ]] ; then
    echo "ERROR, usage: $0 <DECIDER_data_version>" >&2
    exit 2
fi

set -eu
set -o pipefail

data_dir="data"
data_version="$1"

script_dir="$(dirname $0)"


echo "Check for neo4j.pass..." >&2
if [[ ! -f neo4j.pass ]] ; then
    echo "File: neo4j.pass is missing." >&2
    exit 1
fi
echo "neo4j — OK" >&2


echo "Check dependencies..." >&2
REQUIRED_CMD="gzip"
for p in $REQUIRED_CMD ; do
    if [ ! command -v $p ] ; then
        echo "Package `$p` is missing, please install it." >&2
        exit 1
    fi
done


if [[ -d $script_dir/.venv ]] ; then
    echo "Environment already existing, if you want to upgrade it, either:" >&2
    echo "- remove the `.venv` directory and run `prepare.sh` again," >&2
    echo "- or run `uv sync` manually." >&2
else
    echo "Install environment..." >&2
    uv sync --no-upgrade
    echo "Sync — OK" >&2
fi


echo "Download data:" >&2
mkdir -p data
cd data

echo " | Gene Ontology..." >&2
mkdir -p GO
cd GO
wget --no-clobber https://current.geneontology.org/annotations/goa_human.gaf.gz
# gunzip goa_human.gaf.gz
wget --no-clobber https://purl.obolibrary.org/obo/go.owl
cd ..
echo " | GO — OK" >&2


echo " | Open Targets..." >&2
mkdir -p OT
cd OT
rsync --ignore-existing -rpltvz --delete rsync.ebi.ac.uk::pub/databases/opentargets/platform/24.06/output/etl/parquet/targets .
rsync --ignore-existing -rpltvz --delete rsync.ebi.ac.uk::pub/databases/opentargets/platform/24.06/output/etl/parquet/diseases .
rsync --ignore-existing -rpltvz --delete rsync.ebi.ac.uk::pub/databases/opentargets/platform/24.06/output/etl/parquet/molecule .
rsync --ignore-existing -rpltvz --delete rsync.ebi.ac.uk::pub/databases/opentargets/platform/24.06/output/etl/parquet/evidence .
cd ..
echo " | OT — OK" >&2


echo "Check DECIDER data..." >&2
check() {
    if [[ ! -f "$data_dir/DECIDER/$data_version/$1" ]] ; then
        echo "File: $data_dir/DECIDER/$data_version/$1 is missing." >&2
        exit 1
    fi
}

if [[ ! -d $data_dir/DECIDER ]] ; then
    echo "The $data_dir/DECIDER directory is missing." >&2
    exit 1
else
    cd DECIDER
    # check genomics_oncokbannotation.csv
    # check genomics_cgimutation.csv
    # check genomics_cgidrugprescriptions.csv
    # check genomics_cgicopynumberalteration.csv
    # check clin_overview_clinicaldata.csv
    # check ../../oncodashkb/adapters/Hugo_Symbol_genes.conf
    # check treatments.csv
    # check snv_annotated.csv
    # check OncoKB_gene_symbols.conf
    # check cna_annotated.csv
    check clinical_export.csv
    check snv_local.csv
    check snv_external.csv
    check cna_local.csv
    check cna_external.csv
    cd ..
fi
# cp -a ../oncodashkb/adapters/Hugo_Symbol_genes.conf .
echo "DECIDER — OK" >&2

echo "Everything is OK, you can now call: ./make.sh." >&2
