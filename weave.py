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

    for csv_filename in csv_filenames:

        # Taple input data.
        df = pd.read_csv(csv_filename)

        # Extraction mapping configuration.
        with open(conf_filename) as fd:
            conf = yaml.full_load(fd)

        manager = manager_t(df, conf)
        manager.run()

        # Write everything through Biocypher.
        logging.info(f"Extracted {len(list(manager.nodes))} nodes and {len(list(manager.edges))} edges.")

        logging.info("Write nodes...")
        for n in manager.nodes:
            logging.debug(n)
        bc.write_nodes( manager.nodes )

        logging.info("Write edges...")
        for e in manager.edges:
            logging.debug(e)
        bc.write_edges( manager.edges )


if __name__ == "__main__":

    usage = f"Extract nodes and edges from Oncodash' CSV tables from OncoKB and/or CGI and prepare a knowledge graph import script."
    parser = argparse.ArgumentParser(
        description=usage)

    parser.add_argument("-o", "--oncokb", metavar="CSV", action="append",
            help="Extract from an OncoKB CSV file.")

    parser.add_argument("-c", "--cgi", metavar="CSV", action="append",
            help="Extract from a CGI CSV file.")

    asked = parser.parse_args()


    logging.basicConfig(level = logging.DEBUG, format = "{levelname} -- {message}\t\t{filename}:{lineno}", style='{')

    bc = BioCypher(
        biocypher_config_path = "config/biocypher_config.yaml",
        schema_config_path = "config/schema_config.yaml"
    )
    # bc.show_ontology_structure()

    if asked.oncokb:
        extract(bc, asked.oncokb, od.oncokb.OncoKB, "./oncodashkb/adapters/oncokb.yaml")

    if asked.cgi:
        extract(bc, asked.cgi, od.cgi.CGI, "./oncodashkb/adapters/cgi.yaml")

    import_file = bc.write_import_call()

    bc.summary()

    print(import_file)
