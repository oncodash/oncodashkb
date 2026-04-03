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

# Importing OmniPath custom transformer and registering it.
from oncodashkb.transformers.networks import OmniPath_directed
ontoweaver.transformer.register(OmniPath_directed)

# Importing custom transformer for translating sample ids with publication code and registering it.
from oncodashkb.transformers.specific_translate_transformers import translate_sample_ids, translate_cat_format
ontoweaver.transformer.register(translate_sample_ids)
ontoweaver.transformer.register(translate_cat_format)

# Importing OpenTargets custom transformer and registering it.
from oncodashkb.transformers.ot_transformers import access_proteins, urls_to_prop
ontoweaver.transformer.register(access_proteins)
ontoweaver.transformer.register(urls_to_prop)

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
            for chunk in pd.read_table(filename, chunksize=chunksize, low_memory=False, **kwargs):
                chunks.append(chunk)
                progress()
    else:
        if "chunksize" not in kwargs:
            chunksize = 100

        with alive_bar(file=sys.stderr) as progress:
            for chunk in pd.read_table(filename, chunksize=chunksize, low_memory=False, **kwargs):
                chunks.append(chunk)
                progress()

    df = pd.concat(chunks, axis=0)

    return df


def process_OT(directory, name):
    logging.info(f" | Weave Open Targets {name}...")

    conf_filename = f"oncodashkb/adapters/{name}.yaml"

    logging.debug(f"DIRECTORY {directory}")

    #TODO check if reading directory is necessary, and the .* option.
    if os.path.isdir(directory):
        parquet_files = [os.path.join(directory, f) for f in os.listdir(directory) if f.endswith('.parquet')]
        logging.info(f" |  | Concatenating {len(parquet_files)} parquet files...")
        df = pd.concat([pd.read_parquet(file) for file in parquet_files])

        logging.debug(f"COLUMNS: {df.columns}")

        logging.info(f" |  | Read {name} mapping...")
        try:
            with open(conf_filename) as fd:
                ymapping = yaml.full_load(fd)
        except Exception as e:
            logging.error(e)
            sys.exit(error_codes["CannotAccessFile"])

        # with alive_bar(len(df), file=sys.stderr) as progress:
        #     for n,e in manager():
        #         progress()

        logging.info(f" |  | Process {conf_filename}...")

        yparser = ontoweaver.mapping.YamlParser(ymapping)
        mapping = yparser()

        adapter = ontoweaver.tabular.PandasAdapter(
            df,
            *mapping,
            type_affix="suffix",
            type_affix_sep=":",
            raise_errors = asked.debug
        )

        local_nodes = []
        local_edges = []
        with alive_bar(len(df), file=sys.stderr) as progress:
            for n,e in adapter():
                # NOTE: here, n & e are ontoweaver.base.Element, not BioCypher tuples.
                local_nodes += n
                local_edges += e
                progress()

    else:
        logging.error(f"`{directory}` is not a directory. I need a directory to be able to load the parquet files within it.")
        sys.exit(error_codes["FileError"])

    return local_nodes, local_edges

if __name__ == "__main__":
    # TODO add adapter for parquet, one for csv and one that automatically checks filetype.

    usage = f"Extract nodes and edges from Oncodash' CSV tables from OncoKB and/or CGI and prepare a knowledge graph import script."
    parser = argparse.ArgumentParser(
        description=usage)

    parser.add_argument("-C", "--config", metavar="FILE", default=["config/neo4j.yaml"],
                        action="append",
                        help="The BioCypher configuration to load [default: config/neo4j.yaml].")

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

    parser.add_argument("-sv", "--structural-variants", metavar="CSV", nargs="+",
                        help="Extract from a CSV file with short mutations' local annotations.")

    parser.add_argument("-o", "--oncokb", metavar="CSV", nargs="+",
                        help="Extract from an OncoKB CSV file.")

    parser.add_argument("-on", "--omnipath-networks", metavar="TSV", nargs="+",
                        help="Extract from the Omnipath networks TSV file.")

    parser.add_argument("-ott", "--open-targets-target", metavar="PARQUET", nargs="+",
                        help="Extract parquet files containing targets from the given directory.")

    parser.add_argument("-otmao", "--open-targets-drug_mechanism_of_action", metavar="PARQUET", nargs="+",
                        help="Extract parquet files containing evidences from the given directory.")

    parser.add_argument("-otdm", "--open-targets-drug-molecule", metavar="PARQUET", nargs="+",
                        help="Extract parquet files containing molecule from the given directory.")

    parser.add_argument("-c", "--cgi", metavar="CSV", nargs="+",
                        help="Extract from a CGI CSV file.")

    parser.add_argument("-s", "--separator", metavar="STRING", default=", ",
                        help="Separator in exported data files.")

    parser.add_argument("-im", "--import-script-run", action="store_true",
                        help=f"If passed, it will call the import scripts created byBioCypher for you. ")

    parser.add_argument("--debug", action="store_true",
                        help=f"If passed, stops on any error.")


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
        "structural_variants",
        "oncokb",
        "omnipath_networks",
        "open_targets_target",
        "open_targets_drug_mechanism_of_action",
        "open_targets_drug_molecule",
        "cgi",
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
            raise_errors = asked.debug
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

    if asked.structural_variants:
        opt_loaded += 1
        logging.info(f"########## Adapter #{opt_loaded}/{opt_total} ##########")
        data_file = asked.structural_variants[0]
        mapping_file = "./oncodashkb/adapters/structural_variants.yaml"

        # logging.info(f"Weave structural variants...")
        logging.info(f" | Weave `{data_file}:{mapping_file}`...")
        logging.info(f" |  | Load data `{data_file}`...")
        table = pd.read_excel(data_file)

        table = table.rename(columns={"Gene.type":"Gene_type"})
        table["mutation"] = table.mutation.str.replace(r';', ',', regex=True)

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

    if asked.cgi:
        opt_loaded += 1
        logging.info(f"########## Adapter #{opt_loaded}/{opt_total} ##########")
        data_file = asked.cgi[0]
        mapping_file = "./oncodashkb/adapters/cgi.yaml"

        # logging.info(f"Weave structural variants...")
        logging.info(f" | Weave `{data_file}:{mapping_file}`...")
        logging.info(f" |  | Load data `{data_file}`...")
        table = progress_read(data_file, hint=72648)

        table["treatment"] = table.treatment.str.upper().str.replace(r'\([^()]*\)', '', regex=True)

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

    if asked.omnipath_networks:
        opt_loaded += 1
        logging.info(f"########## Adapter #{opt_loaded}/{opt_total} ##########")
        data_file = asked.omnipath_networks[0]
        mapping_file = "./oncodashkb/adapters/omnipath_networks.yaml"

        # logging.info(f"Weave OmniPath networks data...")
        logging.info(f" | Weave `{data_file}:{mapping_file}`...")
        logging.info(f" |  | Load data `{data_file}`...")
        table = progress_read(data_file, hint=890699)

        translations_file = "./data/HGNC/hgnc_complete_set.txt"
        translations_table = pd.read_table(translations_file, sep="\t")

        table['source_genesymbol'] = table['source_genesymbol'].str.upper()
        table['target_genesymbol'] = table['target_genesymbol'].str.upper()

        filtered_table = table[
            ((table['source_genesymbol'].isin(translations_table.symbol)) | (table.entity_type_source!="protein")) & 
            ((table['target_genesymbol'].isin(translations_table.symbol)) | (table.entity_type_target!="protein"))
        ]

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
            filtered_table,
            *mapping,
            type_affix="suffix",
            type_affix_sep=":",
            raise_errors = asked.debug
        )

        local_nodes = []
        local_edges = []
        with alive_bar(len(filtered_table), file=sys.stderr) as progress:
            for n,e in adapter():
                # NOTE: here, n & e are ontoweaver.base.Element, not BioCypher tuples.
                local_nodes += n
                local_edges += e
                progress()

        logging.info(f" |  | OK, wove: {len(local_nodes)} nodes, {len(local_edges)} edges.")
        nodes += local_nodes
        edges += local_edges
        logging.info(f"Done adapter {opt_loaded}/{opt_total}")

    ## DECIDER Patient Clinical Data

    ## OpenTarget

    ### OpenTargets Drug Molecule
    if asked.open_targets_drug_molecule:
        opt_loaded += 1
        logging.info(f"########## Adapter #{opt_loaded}/{opt_total} ##########")
        directory = asked.open_targets_drug_molecule[0]
        # columns = ["id", "approvedSymbol", "approvedName", 'transcriptIds']
        name = "open_targets_drug_molecule"

        local_nodes, local_edges = process_OT(
            directory,
            name,
        )

        logging.info(f"OK, wove {name}: {len(local_nodes)} nodes and {len(local_edges)} edges.")
        nodes += local_nodes
        edges += local_edges
        logging.info(f"Done adapter {opt_loaded}/{opt_total}")

    ### OpenTargets Drug Mechanims of Action
    if asked.open_targets_drug_mechanism_of_action:
        opt_loaded += 1
        logging.info(f"########## Adapter #{opt_loaded}/{opt_total} ##########")
        directory = asked.open_targets_drug_mechanism_of_action[0]
        # columns = ["id", "approvedSymbol", "approvedName", 'transcriptIds']
        name = "open_targets_drug_mechanism_of_action"

        local_nodes, local_edges = process_OT(
            directory,
            name,
        )

        logging.info(f"OK, wove {name}: {len(local_nodes)} nodes and {len(local_edges)} edges.")
        nodes += local_nodes
        edges += local_edges
        logging.info(f"Done adapter {opt_loaded}/{opt_total}")

    ### OpenTargets targets
    if asked.open_targets_target:
        opt_loaded += 1
        logging.info(f"########## Adapter #{opt_loaded}/{opt_total} ##########")
        directory = asked.open_targets_target[0]
        # columns = ["id", "approvedSymbol", "approvedName", 'transcriptIds']
        name = "open_targets_target"

        local_nodes, local_edges = process_OT(
            directory,
            name,
        )

        logging.info(f"OK, wove {name}: {len(local_nodes)} nodes and {len(local_edges)} edges.")
        nodes += local_nodes
        edges += local_edges
        logging.info(f"Done adapter {opt_loaded}/{opt_total}")

    ###################################################
    # Map the data not requiring special loadings.    #
    ###################################################

    ## DECIDER Patient molecular Data
    ### Short mutations
    ### Copy number amplifications

    ## Other
    ### OmniPath Networks
    ### OncoKB
    ### CGI

    direct_mappings = [
        "short_mutations_local",
        "short_mutations_external",
        "copy_number_amplifications_local",
        "copy_number_amplifications_external",
        # "structural_variants",
        "oncokb",
        # "cgi",
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
            raise_errors = asked.debug
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

    configs = asked.config

    for config in configs:
        logging.info(f"Write the final SKG into {config} files...")
        
        bc = biocypher.BioCypher(
            biocypher_config_path = config,
            schema_config_path = "config/schema.yaml"
        )
        
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
