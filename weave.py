#!/usr/bin/env python3
import sys
import yaml
import logging
import argparse
import pandas as pd
from biocypher import BioCypher
import os
import ontoweaver.src.ontoweaver as ontoweaver
import oncodashkb.adapters as od

def process_directory(bc, directory, columns, conf_filename, manager_t):

    nodes = []
    edges = []

    if os.path.isdir(directory):
        parquet_files = [os.path.join(directory, f) for f in os.listdir(directory) if f.endswith('.parquet')]
        logging.info(f"\tConcatenating {len(parquet_files)} parquet files")
        df = pd.concat([pd.read_parquet(file, columns=columns) for file in parquet_files])

        logging.info(f"\tLoading {conf_filename} config")
        with open(conf_filename) as fd:
            conf = yaml.full_load(fd)

        manager = manager_t(df, conf)
        manager.run()

        nodes += manager.nodes
        edges += manager.edges

        # logging.info(f"Extracted {len(list(manager.nodes))} nodes and {len(list(manager.edges))} edges.")

    return nodes, edges

if __name__ == "__main__":
    # TODO add adapter for parquet, one for csv and one that automatically checks filetype.

    usage = f"Extract nodes and edges from Oncodash' CSV tables from OncoKB and/or CGI and prepare a knowledge graph import script."
    parser = argparse.ArgumentParser(
        description=usage)

    parser.add_argument("-o", "--oncokb", metavar="CSV", nargs="+",
                        help="Extract from an OncoKB CSV file.")

    parser.add_argument("-c", "--cgi", metavar="CSV", nargs="+",
                        help="Extract from a CGI CSV file.")

    parser.add_argument("-i", "--clinical", metavar="CSV", nargs="+",
                        help="Extract from a clinical CSV file.")
    
    parser.add_argument("-snv", "--single_nucleotide_variants", metavar="CSV", action="append",
                        help="Extract from a CSV file with single nucleotide variants (SNV) annotations.")
    
    parser.add_argument("-cna", "--copy_number_alterations", metavar="CSV", action="append",
                        help="Extract from a CSV file with copy number alterations (CNA) annotations.")
    
    parser.add_argument("-o", "--oncokb", metavar="CSV", action="append",
                        help="Extract from an OncoKB CSV file.")

    parser.add_argument("-g", "--gene_ontology", metavar="CSV", nargs="+",
                        help="Extract from a Gene_Ontology_Annotation GAF file.")

    parser.add_argument("-n", "--gene_ontology_owl", metavar="OWL", nargs="+",
                        help="Download Gene_Ontology owl file.")

    parser.add_argument("-G", "--gene_ontology_genes", metavar="TXT",
                        help="List of genes for which we integrate Gene Ontology annotations (by default genes from OncoKB).")

    parser.add_argument("-e", "--open_targets_evidences", metavar="PARQUET", nargs="+",
                        help="Extract parquet files from the directory evidences CHEMBL.")

    parser.add_argument("-t", "--open_targets", metavar="PARQUET", nargs="+",
                        help="Extract parquet files from the directory targets.")

    parser.add_argument("-d", "--open_targets_drugs", metavar="PARQUET", nargs="+",
                        help="Extract parquet files from the directory molecule.")
    parser.add_argument("-p", "--open_targets_diseases", metavar="PARQUET", nargs="+",
                        help="Extract parquet files from the directory diseases.")
    levels = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL
    }

    parser.add_argument("-v", "--verbose", choices = levels.keys(), default = "WARNING",
                        help="Set the verbose level (default: %(default)s).")

    asked = parser.parse_args()

    # logging.basicConfig(level = levels[asked.verbose], format = "{levelname} -- {message}\t\t{filename}:{lineno}", style='{')

    bc = BioCypher(
        biocypher_config_path="config/biocypher_config.yaml",
        schema_config_path="config/schema_config.yaml"
    )
    # bc.show_ontology_structure()

    # Actually extract data.
    nodes = []
    edges = []

    data_mappings = {}

    if asked.open_targets:
        logging.info(f"Weave Open Targets...")
        directory_targets = asked.open_targets[0]
        columns_from_targets = ["id", "approvedSymbol", "approvedName", 'transcriptIds']
        conf_filename_targets = "oncodashkb/adapters/open_targets.yaml"
        target_nodes, target_edges = process_directory(bc, directory_targets, columns_from_targets, conf_filename_targets, od.open_targets.OpenTargets
        )
        nodes += target_nodes
        edges += target_edges
        logging.info(f"Wove Open Targets: {len(target_nodes)} nodes, {len(target_edges)} edges.")

    if asked.open_targets_drugs:
        logging.info(f"Weave Open Targets Drugs...")
        directory_drugs = asked.open_targets_drugs[0]
        columns_from_drugs = ["id", 'name', 'isApproved', 'tradeNames', 'description']
        conf_filename_drugs = "oncodashkb/adapters/open_targets_drugs.yaml"
        drug_nodes, drug_edges = process_directory(bc, directory_drugs, columns_from_drugs, conf_filename_drugs, od.open_targets_drugs.OpenTargetsDrugs
        )
        nodes += drug_nodes
        edges += drug_edges
        logging.info(f"Wove Open Targets Drugs: {len(drug_nodes)} nodes, {len(drug_edges)} edges.")

    if asked.open_targets_diseases:
        logging.info(f"Weave Open Targets Diseases...")
        directory_diseases = asked.open_targets_diseases[0]
        columns_from_diseases = ['id', 'code', 'description', 'name']
        conf_filename_diseases = "oncodashkb/adapters/open_targets_diseases.yaml"
        diseases_nodes, diseases_edges = process_directory(bc, directory_diseases, columns_from_diseases, conf_filename_diseases, od.open_targets_diseases.OpenTargetsDiseases
        )
        nodes += diseases_nodes
        edges += diseases_edges
        logging.info(f"Wove Open Targets Disease: {len(diseases_nodes)} nodes, {len(diseases_edges)} edges.")

    if asked.open_targets_evidences:
        logging.info(f"Weave Open Targets Evidences...")
        directory_evidence = asked.open_targets_evidences[0]
        columns_for_evidence = [
            'datasourceId', 'targetId', 'clinicalPhase', 'clinicalStatus',
            'diseaseFromSource', 'diseaseFromSourceMappedId', 'drugId',
            'targetFromSource', 'urls', 'diseaseId', 'score', 'variantEffect'
        ]
        conf_filename_evidence = "./oncodashkb/adapters/open_targets_evidences.yaml"
        evidence_nodes, evidence_edges = process_directory(bc, directory_evidence, columns_for_evidence, conf_filename_evidence,
            od.open_targets_evidences.OpenTargetsEvidences
        )
        nodes += evidence_nodes
        edges += evidence_edges
        logging.info(f"Wove Open Targets Evidences: {len(evidence_nodes)} nodes, {len(evidence_edges)} edges.")

    if asked.single_nucleotide_variants:
        logging.info(f"Weave SNVs...")
        #n, e = extract(asked.single_nucleotide_variants, "./oncodashkb/adapters/single_nucleotide_variants.yaml", csv_separator="\t")
        # nodes += n
        # edges += e
        # logging.info(f"Wove SNVs: {len(n)} nodes, {len(e)} edges.")

    if asked.copy_number_alterations:
        logging.info(f"Weave CNAs...")
        #n, e = extract(asked.copy_number_alterations, "./oncodashkb/adapters/copy_number_alterations.yaml", csv_separator="\t")
        # nodes += n
        # edges += e
        # logging.info(f"Wove CNAs: {len(n)} nodes, {len(e)} edges.")

    if asked.gene_ontology:
        logging.info(f"Weave Gene Ontology...")
        # Table input data.
        df = pd.read_csv(asked.gene_ontology[0], sep='\t', comment='!', header=None, dtype={15: str})

        # Extraction mapping configuration.
        conf_filename = "./oncodashkb/adapters/gene_ontology.yaml"
        with open(conf_filename) as fd:
            conf = yaml.full_load(fd)

        manager = od.gene_ontology.Gene_ontology(df, asked.gene_ontology_owl[0], asked.gene_ontology_genes[0], conf)
        manager.run()

        n = list(manager.nodes)
        e = list(manager.edges)
        nodes += n
        edges += e
        logging.info(f"Wove Gene Ontology: {len(n)} nodes, {len(e)} edges.")

    if asked.oncokb:
        logging.info(f"Weave OncoKB...")
        for file_path in asked.oncokb:
            data_mappings[file_path] =  "./oncodashkb/adapters/oncokb.yaml"

    if asked.cgi:
        logging.info(f"Weave CGI...")
        for file_path in asked.cgi:
            data_mappings[file_path] =  "./oncodashkb/adapters/cgi.yaml"

    if asked.clinical:
        logging.info(f"Weave Clinical data...")
        for file_path in asked.clinical:
            data_mappings[file_path] = "./oncodashkb/adapters/clinical.yaml"

    # Write everything.
    n, e = ontoweaver.extract(data_mappings)
    nodes += n
    edges += e

    import_file = ontoweaver.reconciliate_write(nodes, edges, "config/biocypher_config.yaml", "config/schema_config.yaml", separator=", ")

    print(import_file)

