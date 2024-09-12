#!/usr/bin/bash

set -e
set -o pipefail

echo "Check for neo4j.pass..."
if [[ ! -f neo4j.pass ]] ; then
    echo "File: neo4j.pass is missing."
    exit 1
fi
echo "OK"

echo "Check OS dependencies..."
REQUIRED_PKG="python3-poetry"
PKG_OK=$(dpkg-query -W --showformat='${Status}\n' ${REQUIRED_PKG}|grep "install ok installed")
if [ "" = "${PKG_OK}" ]; then
  echo "Packages: ${REQUIRED_PKG} not installed. I will install them."
  sudo apt update
  sudo apt-get --yes install $REQUIRED_PKG
fi
echo "OK"

echo "Install Poetry environment..."
poetry install
echo "OK"


echo "Download data:"
mkdir -p data
cd data

echo "DECIDER data..."
check() {
    if [[ ! -f "$1" ]] ; then
        echo "File: data/DECIDER/$1 is missing."
        exit 1
    fi
}

if [[ ! -d DECIDER ]] ; then
    echo "The data/DECIDER directory is missing."
    exit 1
else
    cd DECIDER
    check genomics_oncokbannotation.csv
    check genomics_cgimutation.csv
    check genomics_cgidrugprescriptions.csv
    check genomics_cgicopynumberalteration.csv
    check clin_overview_clinicaldata.csv
    cd ..
fi
cp -a ../../oncodashkb/adapters/Hugo_Symbol_genes.conf .
echo "OK"

echo "Gene Ontology..."
mkdir -p GO
cd GO
wget --no-clobber https://current.geneontology.org/annotations/goa_human.gaf.gz
wget --no-clobber https://purl.obolibrary.org/obo/go.owl
cd ..
echo "OK"


echo "Open Targets..."
mkdir -p OT
cd OT
rsync --ignore-existing -rpltvz --delete rsync.ebi.ac.uk::pub/databases/opentargets/platform/24.06/output/etl/parquet/targets .
rsync --ignore-existing -rpltvz --delete rsync.ebi.ac.uk::pub/databases/opentargets/platform/24.06/output/etl/parquet/diseases .
rsync --ignore-existing -rpltvz --delete rsync.ebi.ac.uk::pub/databases/opentargets/platform/24.06/output/etl/parquet/molecule .
rsync --ignore-existing -rpltvz --delete rsync.ebi.ac.uk::pub/databases/opentargets/platform/24.06/output/etl/parquet/evidence .
cd ..
echo "OK"


echo "Everything is OK, you can now call: ./make.sh."
