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

# data_dir="$1"
data_dir="data"

export JAVA_HOME="/usr/lib/jvm/java-21-openjdk-amd64"


echo "Activate virtual environment..." >&2
source $(poetry env info --path)/bin/activate


echo "Stop Neo4j server..." >&2
neo_version=$(neo4j-admin --version | cut -d. -f 1)
if [[ "$neo_version" -eq 4 ]]; then
    server="${NEO_USER} neo4j"
else
    server="${NEO_USER} neo4j-admin server"
fi
$server stop


echo "Weave data..." >&2

# $(pwd)/weave.py --verbose INFO \
#     --open_targets $data_dir/OT/targets \
#     --open_targets_drugs $data_dir/OT/molecule \
#     --open_targets_diseases $data_dir/OT/diseases \
#     --open_targets_evidences $data_dir/OT/evidence/sourceId\=chembl \
#     --oncokb $data_dir/DECIDER/genomics_oncokbannotation.csv \
#     --cgi $data_dir/DECIDER/genomics_cgimutation.csv \
#     --gene_ontology_owl $data_dir/GO/go.owl \
#     --gene_ontology_genes $data_dir/DECIDER/Hugo_Symbol_genes.conf \
#     --gene_ontology $data_dir/GO/goa_human.gaf \
#     --clinical $data_dir/DECIDER/clin_overview_clinicaldata.csv \
#     > tmp.sh

$(pwd)/weave.py --verbose INFO \
    --clinical                   $data_dir/DECIDER/clinical_export.csv \
    --single_nucleotide_variants $data_dir/DECIDER/snv_annotated_external.csv  \
    --copy_number_alterations    $data_dir/DECIDER/cna_annotated_external.csv \
    --oncokb                     $data_dir/DECIDER/treatments.csv \
    --gene_ontology_genes        $data_dir/DECIDER/OncoKB_gene_symbols.conf \
    --gene_ontology              $data_dir/GO/goa_human.gaf.gz \
    --gene_ontology_owl          $data_dir/GO/go.owl \
    --gene_ontology_reverse \
    #--small_molecules           $data_dir/omnipath_networks/omnipath_webservice_interactions__small_molecule_interactions_filtered.tsv.gz \
    > tmp.sh


echo "Run import script..." >&2
$(cat tmp.sh) | tee /dev/tty | ${NEO_USER} sh


echo "Restart Neo4j..." >&2
$server start
sleep 5


echo "Send a test query..." >&2
cypher-shell --username neo4j --database oncodash --password $(cat neo4j.pass) "MATCH (p:Patient) RETURN p LIMIT 20;"

echo "Done" >&2
