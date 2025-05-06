#!/usr/bin/env python3
import sys
import yaml
import logging
import argparse
import pandas as pd
from biocypher import BioCypher
import os
import ontoweaver
import oncodashkb.adapters as od

def capitalize_first_letter(s):
    return s.lower().capitalize()

def process_directory(bc, directory, columns, conf_filename, manager_t):

    nodes = []
    edges = []

    #TODO check if reading directory is necessary, and the .* option.
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
    
    parser.add_argument("-snv", "--single_nucleotide_variants", metavar="CSV",nargs="+",
                        help="Extract from a CSV file with single nucleotide variants (SNV) annotations.")
    
    parser.add_argument("-cna", "--copy_number_alterations", metavar="CSV",nargs="+",
                        help="Extract from a CSV file with copy number alterations (CNA) annotations.")


    parser.add_argument("-g", "--gene_ontology", metavar="CSV", nargs="+",
                        help="Extract from a Gene_Ontology_Annotation GAF file.")

    parser.add_argument("-n", "--gene_ontology_owl", metavar="OWL",
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
    
    parser.add_argument(
        "-net",
        "--networks",
        metavar="TSV",
        nargs="+",
        help="Extract from the Omnipath networks TSV file.",
    )

    parser.add_argument(
        "-sm",
        "--small_molecules",
        metavar="TSV",
        nargs="+",
        help="Extract from the Omnipath networks TSV file.",
    )

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
    bc = BioCypher(
        biocypher_config_path="config/biocypher_config.yaml",
        schema_config_path="config/schema_config.yaml"
    )
    # bc.show_ontology_structure()

    # Actually extract data.
    nodes = []
    edges = []

    data_mappings = {}


    # Extract from databases requiring specialized preprocessing adapters.
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

    if asked.gene_ontology:
        logging.info(f"Weave Gene Ontology...")
        # Table input data.
        df = pd.read_csv(asked.gene_ontology[0], sep='\t', comment='!', header=None, dtype={15: str})

        # Extraction mapping configuration.
        conf_filename = "./oncodashkb/adapters/gene_ontology.yaml"
        with open(conf_filename) as fd:
            conf = yaml.full_load(fd)

        manager = od.gene_ontology.Gene_ontology(df, asked.gene_ontology_owl, asked.gene_ontology_genes, conf)
        manager.run()

        n = list(manager.nodes)
        e = list(manager.edges)
        nodes += n
        edges += e
        logging.info(f"Wove Gene Ontology: {len(n)} nodes, {len(e)} edges.")
    
    # Extract from databases not requiring preprocessing.
    if asked.networks:
        logging.info(f"Weave Omnipath networks data...")

        networks_df = pd.read_csv(asked.networks[0], sep="\t")
        print(networks_df.info())

        mapping_file = "./oncodashkb/adapters/networks.yaml"
        with open(mapping_file) as fd:
            mapping = yaml.full_load(fd)

        adapter = ontoweaver.tabular.extract_table(
            # df=networks_df, config=mapping, separator=":", affix="suffix"
            df=networks_df,
            config=mapping,
            separator=":",
            affix="suffix",
        )

        nodes += adapter.nodes
        edges += adapter.edges

        logging.info(f"Wove Networks: {len(nodes)} nodes, {len(edges)} edges.")

    # Extract from databases not requiring preprocessing.
    if asked.small_molecules:
        logging.info(f"Weave Omnipath networks data...")

        small_molecules_df = pd.read_csv(asked.small_molecules[0], sep="\t")
        small_molecules_df["source_genesymbol"] = small_molecules_df["source_genesymbol"].apply(capitalize_first_letter)
        # small_molecules_df["target_genesymbol"] = small_molecules_df["target_genesymbol"].apply(capitalize_first_letter)
        print(small_molecules_df.info())

        mapping_file = "./oncodashkb/adapters/small_molecules.yaml"
        with open(mapping_file) as fd:
            mapping = yaml.full_load(fd)

        adapter = ontoweaver.tabular.extract_table(
            # df=networks_df, config=mapping, separator=":", affix="suffix"
            df=small_molecules_df,
            config=mapping,
            separator=":",
            affix="suffix",
        )

        nodes += adapter.nodes
        edges += adapter.edges

        logging.info(f"Wove Networks: {len(nodes)} nodes, {len(edges)} edges.")

    # Extract from databases not requiring preprocessing.
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

    if asked.single_nucleotide_variants:
        logging.info(f"Weave SNVs...")
        for file_path in asked.single_nucleotide_variants:
            data_mappings[file_path] = "./oncodashkb/adapters/single_nucleotide_variants.yaml"

    if asked.copy_number_alterations:
        logging.info(f"Weave CNAs...")
        for file_path in asked.copy_number_alterations:
            data_mappings[file_path] = "./oncodashkb/adapters/copy_number_alterations.yaml"

    # Write everything.
    n, e = ontoweaver.extract(data_mappings, sep="\t", affix="suffix")
    nodes += n
    edges += e

    import_file = ontoweaver.reconciliate_write(nodes, edges, "config/biocypher_config.yaml", "config/schema_config.yaml", separator=", ")

    print(import_file)

