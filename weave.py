#!/usr/bin/env python3
import sys
import yaml
import logging
import argparse
import pandas as pd
from biocypher import BioCypher

import ontoweaver
import oncodashkb.adapters as od

def extract(bc, csv_filenames, manager_t, conf_filename):

    nodes = []
    edges = []

    for csv_filename in csv_filenames:

        # Taple input data.
        df = pd.read_csv(csv_filename)

        # Extraction mapping configuration.
        with open(conf_filename) as fd:
            conf = yaml.full_load(fd)

        manager = manager_t(df, conf)
        manager.run()

        nodes += manager.nodes
        edges += manager.edges

        logging.info(f"Extracted {len(list(manager.nodes))} nodes and {len(list(manager.edges))} edges.")

    return nodes, edges


if __name__ == "__main__":

    usage = f"Extract nodes and edges from Oncodash' CSV tables from OncoKB and/or CGI and prepare a knowledge graph import script."
    parser = argparse.ArgumentParser(
        description=usage)

    parser.add_argument("-o", "--oncokb", metavar="CSV", action="append",
            help="Extract from an OncoKB CSV file.")

    parser.add_argument("-c", "--cgi", metavar="CSV", action="append",
            help="Extract from a CGI CSV file.")

    parser.add_argument("-i", "--clinical", metavar="CSV", action="append",
            help="Extract from a clinical CSV file.")

    parser.add_argument("-g", "--gene_ontology", metavar="CSV", action="append",
            help="Extract from a Gene_Ontology_Annotation GAF file.")

    parser.add_argument("-g_owl", "--gene_ontology_owl", metavar="OWL", action="append",
            help="Download Gene_Ontology owl file.")

    levels = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL
    }

    parser.add_argument("-v", "--verbose", metavar="LEVEL",
            help="Set the verbose level ("+" ".join(l for l in levels.keys())+").")

    asked = parser.parse_args()

    #logging.basicConfig(level = levels[asked.verbose], format = "{levelname} -- {message}\t\t{filename}:{lineno}", style='{')

    bc = BioCypher(
        biocypher_config_path = "config/biocypher_config.yaml",
        schema_config_path = "config/schema_config.yaml"
    )
    # bc.show_ontology_structure()


    # Actually extract data.
    nodes = []
    edges = []

    # FIXME: allow passing several CSV files by parser.
    if asked.oncokb:
        n,e = extract(bc, asked.oncokb, od.oncokb.OncoKB, "./oncodashkb/adapters/oncokb.yaml")
        nodes += n
        edges += e

    if asked.cgi:
        n,e = extract(bc, asked.cgi, od.cgi.CGI, "./oncodashkb/adapters/cgi.yaml")
        nodes += n
        edges += e

    if asked.clinical:
        # TODO filter patients, keeping the ones already seen in cancer databases?
        n,e = extract(bc, asked.clinical, od.clinical.Clinical, "./oncodashkb/adapters/clinical.yaml")
        nodes += n
        edges += e

    if asked.gene_ontology:
        # TODO filter patients, keeping the ones already seen in cancer databases?
        # Table input data.
        df = pd.read_csv(asked.gene_ontology[0], sep='\t', comment='!', header=None)

        # Extraction mapping configuration.
        conf_filename = "./oncodashkb/adapters/gene_ontology.yaml"
        with open(conf_filename) as fd:
            conf = yaml.full_load(fd)

        manager = od.gene_ontology.Gene_ontology(df, asked.gene_ontology_owl[0], conf)
        manager.run()

        nodes += manager.nodes
        edges += manager.edges

    # Write everything.

    logging.info("Write nodes...")
    bc.write_nodes( nodes )

    logging.info("Write edges...")
    bc.write_edges( edges )

    import_file = bc.write_import_call()

    # bc.summary()

    print(import_file)

