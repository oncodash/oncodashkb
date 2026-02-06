#!/usr/bin/env python3
import io
import os
import sys
import yaml
import math
import logging
import argparse
import traceback
import subprocess

import pandas as pd

import biocypher

import ontoweaver
import oncodashkb.adapters as od
from alive_progress import alive_bar

error_codes = {
    "ParsingError"    :  65, # "data format"
    "RunError"        :  70, # "internal"
    "DataValidationError": 76,  # "protocol"
    "ConfigError"     :  78, # "bad config"
    "CannotAccessFile": 126, # "no perm"
    "FileError"       : 127, # "not found"
    "SubprocessError" : 128, # "bad exit"
    "NetworkXError"   : 129, # probably "type not in the digraph"
    "OntoWeaverError" : 254,
    "Exception"       : 255,
}

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


def process_OT(bc, directory, columns, name, manager_t):
    logging.info(f" | Weave Open Targets {name}...")

    conf_filename = f"oncodashkb/adapters/{name}.yaml"
    nodes = []
    edges = []

    #TODO check if reading directory is necessary, and the .* option.
    if os.path.isdir(directory):
        parquet_files = [os.path.join(directory, f) for f in os.listdir(directory) if f.endswith('.parquet')]
        logging.info(f" |  | Concatenating {len(parquet_files)} parquet files...")
        df = pd.concat([pd.read_parquet(file, columns=columns) for file in parquet_files])

        logging.info(f" |  | Read {name} mapping...")
        try:
            with open(conf_filename) as fd:
                conf = yaml.full_load(fd)
        except Exception as e:
            logging.error(e)
            sys.exit(error_codes["CannotAccessFile"])

        logging.info(f" |  | Transform {name} data...")
        manager = manager_t(df, conf, raise_errors = True)

        with alive_bar(len(df), file=sys.stderr) as progress:
            for n,e in manager():
                progress()

        nodes += manager.nodes
        edges += manager.edges
    else:
        logging.error(f"`{directory}` is not a directory. I need a directory to be able to load the parquet files within it.")
        sys.exit(error_codes["FileError"])

    return nodes, edges


def process_GO(name):
    logging.info(f" | Weave {name} data...")
    # Table input data.
    logging.info(f" |  | Load {name} data...")
    df = progress_read(asked.gene_ontology[0], sep='\t', comment='!', header=None, dtype={15: str}, hint=969214)

    logging.info(f" |  | Read {name} mapping...")
    # Extraction mapping configuration.
    try:
        with open(f"./oncodashkb/adapters/{name}.yaml") as fd:
            conf = yaml.full_load(fd)
    except Exception as e:
        logging.error(e)
        sys.exit(error_codes["CannotAccessFile"])

    logging.info(f" |  | Preprocess {name} data...")
    manager = od.gene_ontology.Gene_ontology(df, asked.gene_ontology_owl, asked.gene_ontology_genes, conf)

    logging.info(f" |  | Transform {name} data...")
    local_nodes = []
    local_edges = []
    # Use manager.df because Gene_ontology does filter the input dataframe
    with alive_bar(len(manager.df), file=sys.stderr) as progress:
        for n,e in manager():
            local_nodes += n
            local_edges += e
            progress()

    return local_nodes, local_edges


def process_OmniPath(name):
    logging.info(f" | Weave Omnipath {name} data...")

    logging.info(f" |  | Load {name} data...")
    networks_df = progress_read(asked.networks[0], sep="\t")
    print(networks_df.info())

    logging.info(f" |  | Read {name} mapping...")
    try:
        with open(f"./oncodashkb/adapters/{name}.yaml") as fd:
            mapping = yaml.full_load(fd)
    except Exception as e:
        logging.error(e)
        sys.exit(error_codes["CannotAccessFile"])

    logging.info(f" |  | Transform {name} data...")
    adapter = ontoweaver.tabular.extract_table(
        df=networks_df,
        config=mapping,
        affix="suffix",
        type_affix_sep=":",
        raise_errors = True
    )
    with alive_bar(len(adapter.df), file=sys.stderr) as progress:
        for n,e in adapter():
            progress()

    return adapter.nodes, adapter.edges


if __name__ == "__main__":
    # TODO add adapter for parquet, one for csv and one that automatically checks filetype.

    usage = f"Extract nodes and edges from Oncodash' CSV tables from OncoKB and/or CGI and prepare a knowledge graph import script."
    parser = argparse.ArgumentParser(
        description=usage)

    parser.add_argument("-i", "--clinical", metavar="CSV", nargs="+",
                        help="Extract from a clinical CSV file.")

    parser.add_argument("-sml", "--short-mutations-local", metavar="CSV", nargs="+",
                        help="Extract from a CSV file with short mutations' local annotations.")

    parser.add_argument("-sme", "--short-mutations-external", metavar="CSV", nargs="+",
                        help="Extract from a CSV file with short mutations' variants external annotations.")

    parser.add_argument("-cnal", "--copy-number-amplifications-local", metavar="CSV", nargs="+",
                        help="Extract from a CSV file with copy number amplifications' local annotations.")

    parser.add_argument("-cnae", "--copy-number-amplifications-external", metavar="CSV", nargs="+",
                        help="Extract from a CSV file with copy number amplifications' external annotations.")

    parser.add_argument("-o", "--oncokb", metavar="CSV", nargs="+",
                        help="Extract from an OncoKB CSV file.")

    parser.add_argument("-c", "--cgi", metavar="CSV", nargs="+",
                        help="Extract from a CGI CSV file.")

    parser.add_argument("-g", "--gene-ontology", metavar="CSV", nargs="+",
                        help="Extract from a Gene_Ontology_Annotation GAF file.")

    parser.add_argument("-n", "--gene-ontology-owl", metavar="OWL",
                        help="Download Gene_Ontology owl file.")

    parser.add_argument("-G", "--gene-ontology-genes", metavar="TXT",
                        help="List of genes for which we integrate Gene Ontology annotations (by default genes from OncoKB).")

    parser.add_argument("-r", "--gene-ontology-reverse", action='store_true',
                        help="Extract from a Gene_Ontology_Annotation GAF file.")

    parser.add_argument("-t", "--open-targets", metavar="PARQUET", nargs="+",
                        help="Extract parquet files containing targets from the given directory.")

    parser.add_argument("-e", "--open-targets-evidences", metavar="PARQUET", nargs="+",
                        help="Extract parquet files containing evidences from the given directory.")

    parser.add_argument("-d", "--open-targets-drugs", metavar="PARQUET", nargs="+",
                        help="Extract parquet files containing molecule from the given directory.")

    parser.add_argument("-p", "--open-targets-diseases", metavar="PARQUET", nargs="+",
                        help="Extract parquet files containing diseases from the given directory.")

    parser.add_argument("-s", "--separator", metavar="STRING", default=", ",
                        help="Separator in exported data files.")

    parser.add_argument("-im", "--import-script-run", action="store_true",
                        help=f"If passed, it will call the import scripts created byBioCypher for you. ")

    parser.add_argument("-net", "--networks", metavar="TSV", nargs="+",
        help="Extract from the Omnipath networks TSV file.", )

    parser.add_argument("-sm", "--small_molecules", metavar="TSV", nargs="+",
        help="Extract from the Omnipath networks TSV file.", )

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


    all_options = [
        "clinical",
        "short_mutations_local",
        "short_mutations_external",
        "copy_number_amplifications_local",
        "copy_number_amplifications_external",
        "oncokb",
        "cgi",
        "gene_ontology",
        "gene_ontology_owl",
        "gene_ontology_genes",
        "gene_ontology_reverse",
        "open_targets",
        "open_targets_evidences",
        "open_targets_drugs",
        "open_targets_diseases",
    ]
    opt_total = 0
    for opt in all_options:
        if getattr(asked, opt):
            opt_total += 1
    opt_loaded = 0

    ###################################################
    # Map the data requiring special loadings         #
    ###################################################

    ## DECIDER Patient Clinical Data

    if asked.clinical:
        opt_loaded += 1
        logging.info(f"########## Adapter #{opt_loaded}/{opt_total} ##########")
        data_file = asked.clinical[0]
        mapping_file = "./oncodashkb/adapters/clinical.yaml"

        # logging.info(f"Weave Clinical data...")
        logging.info(f" | Weave `{data_file}:{mapping_file}`...")
        logging.info(f" |  | Load data `{data_file}`...")
        table = progress_read(data_file, sep=",", hint=673)

        try:
            with open(mapping_file) as fd:
                ymapping = yaml.full_load(fd)
        except Exception as e:
            logging.error(e)
            sys.exit(error_codes["CannotAccessFile"])

        logging.info(f" |  | Process {mapping_file}...")

        yparser = ontoweaver.mapping.YamlParser(ymapping)
        mapping = yparser()

        adapter = ontoweaver.tabular.PandasAdapter(
            table,
            *mapping,
            type_affix="suffix",
            type_affix_sep=":",
            raise_errors = True
        )

        local_nodes = []
        local_edges = []
        with alive_bar(len(table), file=sys.stderr) as progress:
            for n,e in adapter():
                # NOTE: here, n & e are ontoweaver.base.Element, not BioCypher tuples.
                local_nodes += n
                local_edges += e
                progress()

        logging.info(f" |  | OK, wove: {len(local_nodes)} nodes, {len(local_edges)} edges.")
        nodes += local_nodes
        edges += local_edges
        logging.info(f"Done adapter {opt_loaded}/{opt_total}")

    ## OpenTarget

    ### OpenTargets
    if asked.open_targets:
        opt_loaded += 1
        logging.info(f"########## Adapter #{opt_loaded}/{opt_total} ##########")
        directory = asked.open_targets[0]
        columns = ["id", "approvedSymbol", "approvedName", 'transcriptIds']
        name = "open_targets"
        local_nodes, local_edges = process_OT(
            bc, directory, columns, name,
            od.open_targets.OpenTargets
        )
        logging.info(f"OK, wove {name}: {len(local_nodes)} nodes and {len(local_edges)} edges.")
        nodes += local_nodes
        edges += local_edges
        logging.info(f"Done adapter {opt_loaded}/{opt_total}")

    ### OpenTarget drugs
    if asked.open_targets_drugs:
        opt_loaded += 1
        logging.info(f"########## Adapter #{opt_loaded}/{opt_total} ##########")
        directory = asked.open_targets_drugs[0]
        columns = ["id", 'name', 'isApproved', 'tradeNames', 'description']
        name = "open_targets_drugs"
        local_nodes, local_edges = process_OT(
            bc, directory, columns, name,
            od.open_targets_drugs.OpenTargetsDrugs
        )
        logging.info(f"OK, wove {name}: {len(local_nodes)} nodes and {len(local_edges)} edges.")
        nodes += local_nodes
        edges += local_edges
        logging.info(f"Done adapter {opt_loaded}/{opt_total}")

    ### OpenTarget diseases
    if asked.open_targets_diseases:
        opt_loaded += 1
        logging.info(f"########## Adapter #{opt_loaded}/{opt_total} ##########")
        directory = asked.open_targets_diseases[0]
        columns = ['id', 'code', 'description', 'name']
        name = "open_targets_diseases"
        local_nodes, local_edges = process_OT(
            bc, directory, columns, name,
            od.open_targets_diseases.OpenTargetsDiseases
        )
        logging.info(f"OK, wove {name}: {len(local_nodes)} nodes and {len(local_edges)} edges.")
        nodes += local_nodes
        edges += local_edges
        logging.info(f"Done adapter {opt_loaded}/{opt_total}")

    ### OpenTarget evidences
    if asked.open_targets_evidences:
        opt_loaded += 1
        logging.info(f"########## Adapter #{opt_loaded}/{opt_total} ##########")
        directory = asked.open_targets_evidences[0]
        columns = [
            'datasourceId', 'targetId', 'clinicalPhase', 'clinicalStatus',
            'diseaseFromSource', 'diseaseFromSourceMappedId', 'drugId',
            'targetFromSource', 'urls', 'diseaseId', 'score', 'variantEffect'
        ]
        name = "open_targets_evidences"
        local_nodes, local_edges = process_OT(
            bc, directory, columns, name,
            od.open_targets_evidences.OpenTargetsEvidences
        )
        logging.info(f"OK, wove {name}: {len(local_nodes)} nodes and {len(local_edges)} edges.")
        nodes += local_nodes
        edges += local_edges
        logging.info(f"Done adapter {opt_loaded}/{opt_total}")

    ## GeneOntology

    ### GO
    if asked.gene_ontology:
        opt_loaded += 1
        logging.info(f"########## Adapter #{opt_loaded}/{opt_total} ##########")
        local_nodes, local_edges = process_GO("gene_ontology")
        logging.info(f" | Save data...")
        nodes += local_nodes
        edges += local_edges
        logging.info(f"OK, wove Gene Ontology data: {len(local_nodes)} nodes, {len(local_edges)} edges.")
        logging.info(f"Done adapter {opt_loaded}/{opt_total}")

    ### GO reversed
    if asked.gene_ontology_reverse:
        opt_loaded += 1
        logging.info(f"########## Adapter #{opt_loaded}/{opt_total} ##########")
        local_nodes, local_edges = process_GO("gene_ontology_reverse")
        nodes += local_nodes
        edges += local_edges
        logging.info(f"OK, reverse-wove Gene Ontology: {len(local_nodes)} nodes, {len(local_edges)} edges.")
        logging.info(f"Done adapter {opt_loaded}/{opt_total}")

    ## OmniPath

    ### OmniPath networks
    if asked.networks:
        opt_loaded += 1
        logging.info(f"########## Adapter #{opt_loaded}/{opt_total} ##########")
        local_nodes, local_edges = process_OmniPath("networks")
        nodes += local_nodes
        edges += local_edges
        logging.info(f"OK, wove Networks: {len(nodes)} nodes, {len(edges)} edges.")
        logging.info(f"Done adapter {opt_loaded}/{opt_total}")

    ### Omnipath small molecules
    if asked.small_molecules:
        opt_loaded += 1
        logging.info(f"########## Adapter #{opt_loaded}/{opt_total} ##########")
        local_nodes, local_edges = process_OmniPath("small_molecules")
        nodes += local_nodes
        edges += local_edges
        logging.info(f"OK, wove small molecules: {len(nodes)} nodes, {len(edges)} edges.")
        logging.info(f"Done adapter {opt_loaded}/{opt_total}")


    ###################################################
    # Map the data not requiring special loadings.    #
    ###################################################

    ## DECIDER Patient molecular Data
    ### Short mutations
    ### Copy number amplifications

    ## Other
    ### OncoKB
    ### CGI

    direct_mappings = [
        "short_mutations_local",
        "short_mutations_external",
        "copy_number_amplifications_local",
        "copy_number_amplifications_external",
        "oncokb",
        "cgi",
    ]
    for name in direct_mappings:
        option = getattr(asked, name)
        if option:
            for file_path in option:
                data_mappings[file_path] = f"./oncodashkb/adapters/{name}.yaml"

    for data_file, mapping_file in data_mappings.items():
        opt_loaded += 1
        logging.info(f"########## Adapter #{opt_loaded}/{opt_total} ##########")
        logging.info(f" | Weave `{data_file}:{mapping_file}`...")
        logging.info(f" |  | Load data `{data_file}`...")
        table = progress_read(data_file, sep="\t")

        try:
            with open(mapping_file) as fd:
                ymapping = yaml.full_load(fd)
        except Exception as e:
            logging.error(e)
            sys.exit(error_codes["CannotAccessFile"])

        logging.info(f" |  | Read mapping `{mapping_file}`...")

        yparser = ontoweaver.mapping.YamlParser(ymapping)
        mapping = yparser()

        adapter = ontoweaver.tabular.PandasAdapter(
            table,
            *mapping,
            type_affix="suffix",
            type_affix_sep=":",
            raise_errors = True
        )

        logging.info(f" |  | Transform data...")
        local_nodes = []
        local_edges = []
        with alive_bar(len(table), file=sys.stderr) as progress:
            for n,e in adapter():
                # NOTE: here, n & e are ontoweaver.base.Element, not BioCypher tuples.
                local_nodes += n
                local_edges += e
                progress()

        logging.info(f" | OK, wove: {len(local_nodes)} nodes, {len(local_edges)} edges.")
        nodes += local_nodes
        edges += local_edges
        logging.info(f"Done adapter {opt_loaded}/{opt_total}")


    ###################################################
    # Fusion.
    ###################################################

    logging.info(f"Reconciliate properties in elements...")
    # NODES FUSION
    fusion_separator = ","

    # We need BioCypher's nodes and edges tuples, not OntoWeaver classes.
    bc_nodes = [n.as_tuple() for n in nodes]
    bc_edges = [e.as_tuple() for e in edges]

    # Find duplicates
    on_ID = ontoweaver.serialize.ID()
    nodes_congregater = ontoweaver.congregate.Nodes(on_ID)

    logging.info(f" | Congregate nodes")
    with alive_bar(len(bc_nodes), file=sys.stderr) as progress:
        for n in nodes_congregater(bc_nodes):
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
        with alive_bar(len(bc_edges), file=sys.stderr) as progress:
            for e in ontoweaver.fusion.remap_edges(bc_edges, ID_mapping):
                remaped_edges.append(e)
                progress()
        # logger.debug("Remaped edges:")
        # for n in remaped_edges:
        #     logger.debug("\t"+repr(n))
    else:
        remaped_edges = bc_edges

    # EDGES FUSION
    # Find duplicates
    on_STL = ontoweaver.serialize.edge.SourceTargetLabel()
    edges_congregater = ontoweaver.congregate.Edges(on_STL)

    logging.info(f" | Congregate edges")
    with alive_bar(len(bc_edges), file=sys.stderr) as progress:
        for e in edges_congregater(bc_edges):
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


    ###################################################
    # Export the final SKG.
    ###################################################

    logging.info(f"Write the final SKG into files...")
    if fnodes:
        bc.write_nodes(n.as_tuple() for n in fnodes)
    if fedges:
        bc.write_edges(e.as_tuple() for e in fedges)
    #bc.summary()
    import_file = bc.write_import_call()
    logging.info(f"OK, wrote files.")

    # Print on stdout for other scripts to get.
    print(import_file)

    if asked.import_script_run:
        shell = os.environ["SHELL"]
        logging.info(f"Run the import scripts with {shell}...")
        try:
            subprocess.run([shell, import_file])
        except Exception as e:
            logging.error(e)
            sys.exit(error_codes["SubprocessError"])

    logging.info("Done.")
