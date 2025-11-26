#!/usr/bin/env python3
import io
import os
import sys
import yaml
import math
import logging
import argparse

import pandas as pd

import biocypher

import ontoweaver
import oncodashkb.adapters as od
from alive_progress import alive_bar


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

        with alive_bar(len(df), file=sys.stderr) as progress:
            for n,e in manager.run():
                progress()

        nodes += manager.nodes
        edges += manager.edges

        logging.info(f"OK, wove {len(list(manager.nodes))} nodes and {len(list(manager.edges))} edges.")

    return nodes, edges


def progress_read(filename, hint=None, steps=100, estimate_lines=10, **kwargs):
    # df = pd.read_csv(filename, nrows=estimate_lines, **kwargs)
    # estimated_size = len(df.to_csv(index=False))
    # fsize = os.path.getsize(filename)

    chunks = []
    if hint:
        nb_lines = hint

        # How many lines to read at each iteration.
        if "chunksize" not in kwargs:
            chunksize = int(math.ceil(nb_lines / steps))

        with alive_bar(steps, file=sys.stderr) as progress:
            for chunk in pd.read_csv(filename, chunksize=chunksize, low_memory=False, **kwargs):
                chunks.append(chunk)
                progress()
    else:
        if "chunksize" not in kwargs:
            chunksize = 100

        with alive_bar(file=sys.stderr) as progress:
            for chunk in pd.read_csv(filename, chunksize=chunksize, low_memory=False, **kwargs):
                chunks.append(chunk)
                progress()

    df = pd.concat(chunks, axis=0)

    return df



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

    parser.add_argument("-r", "--gene_ontology_reverse", action='store_true',
                        help="Extract from a Gene_Ontology_Annotation GAF file.")

    parser.add_argument("-e", "--open_targets_evidences", metavar="PARQUET", nargs="+",
                        help="Extract parquet files from the directory evidences CHEMBL.")

    parser.add_argument("-t", "--open_targets", metavar="PARQUET", nargs="+",
                        help="Extract parquet files from the directory targets.")

    parser.add_argument("-d", "--open_targets_drugs", metavar="PARQUET", nargs="+",
                        help="Extract parquet files from the directory molecule.")
    parser.add_argument("-p", "--open_targets_diseases", metavar="PARQUET", nargs="+",
                        help="Extract parquet files from the directory diseases.")

    parser.add_argument("-s", "--separator", metavar="STRING", default=", ",
                        help="Separator in exported data files.")

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
    bc = biocypher.BioCypher(
        biocypher_config_path="config/biocypher_config.yaml",
        schema_config_path="config/schema_config.yaml"
    )

    logging.basicConfig()
    logging.getLogger().setLevel(asked.verbose)
    biocypher._logger.logger.setLevel(asked.verbose)
    ontoweaver.logger.setLevel(asked.verbose)

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
        logging.info(f"OK, wove Open Targets: {len(target_nodes)} nodes, {len(target_edges)} edges.")

    if asked.open_targets_drugs:
        logging.info(f"Weave Open Targets Drugs...")
        directory_drugs = asked.open_targets_drugs[0]
        columns_from_drugs = ["id", 'name', 'isApproved', 'tradeNames', 'description']
        conf_filename_drugs = "oncodashkb/adapters/open_targets_drugs.yaml"
        drug_nodes, drug_edges = process_directory(bc, directory_drugs, columns_from_drugs, conf_filename_drugs, od.open_targets_drugs.OpenTargetsDrugs
        )
        nodes += drug_nodes
        edges += drug_edges
        logging.info(f"OK, wove Open Targets Drugs: {len(drug_nodes)} nodes, {len(drug_edges)} edges.")

    if asked.open_targets_diseases:
        logging.info(f"Weave Open Targets Diseases...")
        directory_diseases = asked.open_targets_diseases[0]
        columns_from_diseases = ['id', 'code', 'description', 'name']
        conf_filename_diseases = "oncodashkb/adapters/open_targets_diseases.yaml"
        diseases_nodes, diseases_edges = process_directory(bc, directory_diseases, columns_from_diseases, conf_filename_diseases, od.open_targets_diseases.OpenTargetsDiseases
        )
        nodes += diseases_nodes
        edges += diseases_edges
        logging.info(f"OK, wove Open Targets Disease: {len(diseases_nodes)} nodes, {len(diseases_edges)} edges.")

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
        logging.info(f"OK, wove Open Targets Evidences: {len(evidence_nodes)} nodes, {len(evidence_edges)} edges.")

    if asked.gene_ontology:
        logging.info(f"Weave Gene Ontology data...")
        # Table input data.
        logging.info(f" | Load data...")
        df = progress_read(asked.gene_ontology[0], sep='\t', comment='!', header=None, dtype={15: str}, hint=969214)

        # logging.info(f" | Read mapping...")
        # Extraction mapping configuration.
        conf_filename = "./oncodashkb/adapters/gene_ontology.yaml"
        with open(conf_filename) as fd:
            conf = yaml.full_load(fd)

        logging.info(f" | Preprocess data...")
        manager = od.gene_ontology.Gene_ontology(df, asked.gene_ontology_owl, asked.gene_ontology_genes, conf)

        logging.info(f" | Transform data...")
        # Use manager.df because Gene_ontology does filter the input dataframe
        with alive_bar(len(manager.df), file=sys.stderr) as progress:
            for n,e in manager.run():
                progress()

        logging.info(f" | Save data...")
        n = list(manager.nodes)
        e = list(manager.edges)
        nodes += n
        edges += e
        logging.info(f"OK, wove Gene Ontology data: {len(n)} nodes, {len(e)} edges.")

    if asked.gene_ontology_reverse:
        logging.info(f"Weave Gene Ontology in reverse...")
        # Table input data.
        df = progress_read(asked.gene_ontology[0], sep='\t', comment='!', header=None, dtype={15: str}, hint=969214)

        # Extraction mapping configuration.
        conf_filename = "./oncodashkb/adapters/gene_ontology_reverse.yaml"
        with open(conf_filename) as fd:
            conf = yaml.full_load(fd)

        manager = od.gene_ontology.Gene_ontology(df, asked.gene_ontology_owl, asked.gene_ontology_genes, conf)
        with alive_bar(len(manager.df), file=sys.stderr) as progress:
            for n,e in manager.run():
                progress()

        n = list(manager.nodes)
        e = list(manager.edges)
        nodes += n
        edges += e
        logging.info(f"OK, wove Gene Ontology: {len(n)} nodes, {len(e)} edges.")

    # Extract from databases not requiring preprocessing.
    if asked.networks:
        logging.info(f"Weave Omnipath networks data...")

        networks_df = progress_read(asked.networks[0], sep="\t")
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
        with alive_bar(len(adapter.df), file=sys.stderr) as progress:
            for n,e in adapter.run():
                progress()

        nodes += adapter.nodes
        edges += adapter.edges

        logging.info(f"OK, wove Networks: {len(nodes)} nodes, {len(edges)} edges.")

    # Extract from databases not requiring preprocessing.
    if asked.small_molecules:
        logging.info(f"Weave Omnipath networks data...")

        small_molecules_df = progress_read(asked.small_molecules[0], sep="\t")
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
        with alive_bar(len(adapter.df), file=sys.stderr) as progress:
            for n,e in adapter.run():
                progress()

        nodes += adapter.nodes
        edges += adapter.edges

        logging.info(f"OK, wove Networks: {len(nodes)} nodes, {len(edges)} edges.")

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

        clinical_df = progress_read(asked.clinical[0], sep=",", hint=673)

        mapping_file = "./oncodashkb/adapters/clinical.yaml"
        with open(mapping_file) as fd:
            mapping = yaml.full_load(fd)

        adapter = ontoweaver.tabular.extract_table(
            # df=networks_df, config=mapping, separator=":", affix="suffix"
            df=clinical_df,
            config=mapping,
            separator=":",
            affix="suffix",
        )

        nodes += adapter.nodes
        edges += adapter.edges

        logging.info(f"OK, wove Clinical data: {len(nodes)} nodes, {len(edges)} edges.")

    if asked.single_nucleotide_variants:
        for file_path in asked.single_nucleotide_variants:
            data_mappings[file_path] = "./oncodashkb/adapters/single_nucleotide_variants.yaml"

    if asked.copy_number_alterations:
        for file_path in asked.copy_number_alterations:
            data_mappings[file_path] = "./oncodashkb/adapters/copy_number_alterations.yaml"

    # Map the data that were declared the simple way.
    for data_file, mapping_file in data_mappings.items():
        logging.info(f"Weave `{data_file}:{mapping_file}`...")
        logging.info(f" | Load data `{data_file}`...")
        table = progress_read(data_file, sep="\t")

        with open(mapping_file) as fd:
            ymapping = yaml.full_load(fd)

        logging.info(f" | Process {mapping_file}...")

        yparser = ontoweaver.tabular.YamlParser(ymapping)
        mapping = yparser()

        adapter = ontoweaver.tabular.PandasAdapter(
            table,
            *mapping,
            type_affix="suffix",
            type_affix_sep=":"
        )

        with alive_bar(len(table), file=sys.stderr) as progress:
            for n,e in adapter.run():
                # NOTE: here, n & e are ontoweaver.base.Element, not BioCypher tuples.
                progress()

        nodes += adapter.nodes
        edges += adapter.edges

        logging.info(f"OK, wove: {len(nodes)} nodes, {len(edges)} edges.")

    logging.debug(f"Extracted {len(nodes)} nodes and {len(edges)} edges.")

    logging.info(f"Reconciliate properties in elements...")
    # fnodes, fedges = ontoweaver.fusion.reconciliate(nodes, edges, separator = asked.separator)

    fusion_separator = ","

    # NODES FUSION
    # Find duplicates
    on_ID = ontoweaver.serialize.ID()
    nodes_congregater = ontoweaver.congregate.Nodes(on_ID)

    logging.info(f" | Congregate nodes")
    with alive_bar(len(nodes), file=sys.stderr) as progress:
        for n in nodes_congregater(nodes):
            progress()

    # Fuse them
    use_key    = ontoweaver.merge.string.UseKey()
    identicals = ontoweaver.merge.string.EnsureIdentical()
    in_lists   = ontoweaver.merge.dictry.Append(fusion_separator)
    node_fuser = ontoweaver.fuse.Members(ontoweaver.base.Node,
            merge_ID    = use_key,
            merge_label = identicals,
            merge_prop  = in_lists,
        )

    nodes_fusioner = ontoweaver.fusion.Reduce(node_fuser)
    fnodes = set()
    logging.info(f" | Fuse nodes")
    with alive_bar(len(nodes_congregater), file=sys.stderr) as progress:
        for n in nodes_fusioner(nodes_congregater):
            fnodes.add(n)
            progress()

    ID_mapping = node_fuser.ID_mapping

    # EDGES REMAP
    # If we use on_ID/use_key,
    # we shouldn't have any need to remap sources and target IDs in edges.
    assert(len(ID_mapping) == 0)
    # If one change this, you may want to remap like this:
    if len(ID_mapping) > 0:
        remaped_edges = []
        logging.info(f" | Remap edges")
        with alive_bar(len(edges), file=sys.stderr) as progress:
            for e in remap_edges(edges, ID_mapping):
                remaped_edges.append(e)
                progress()
        # logger.debug("Remaped edges:")
        # for n in remaped_edges:
        #     logger.debug("\t"+repr(n))
    else:
        remaped_edges = edges

    # EDGES FUSION
    # Find duplicates
    on_STL = ontoweaver.serialize.edge.SourceTargetLabel()
    edges_congregater = ontoweaver.congregate.Edges(on_STL)

    logging.info(f" | Congregate edges")
    with alive_bar(len(edges), file=sys.stderr) as progress:
        for e in edges_congregater(edges):
            progress()

    # Fuse them
    set_of_ID       = ontoweaver.merge.string.OrderedSet(fusion_separator)
    identicals      = ontoweaver.merge.string.EnsureIdentical()
    in_lists        = ontoweaver.merge.dictry.Append(fusion_separator)
    use_last_source = ontoweaver.merge.string.UseLast()
    use_last_target = ontoweaver.merge.string.UseLast()
    edge_fuser = ontoweaver.fuse.Members(ontoweaver.base.GenericEdge,
            merge_ID     = set_of_ID,
            merge_label  = identicals,
            merge_prop   = in_lists,
            merge_source = use_last_source,
            merge_target = use_last_target
        )

    edges_fusioner = ontoweaver.fusion.Reduce(edge_fuser)
    fedges = set()
    logging.info(f" | Fuse edges")
    with alive_bar(len(edges_congregater), file=sys.stderr) as progress:
        for e in edges_fusioner(edges_congregater):
            fedges.add(e)
            progress()

    # logger.debug("Fusioned edges:")
    # for n in fedges:
    #     logger.debug("\t"+repr(n))


    logging.info(f"Fused into {len(fnodes)} nodes and {len(fedges)} edges.")

    if fnodes:
        bc.write_nodes(n.as_tuple() for n in fnodes)
    if fedges:
        bc.write_edges(e.as_tuple() for e in fedges)
    #bc.summary()
    import_file = bc.write_import_call()

    print(import_file)

    logging.debug("Done")
