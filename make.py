#!/usr/bin/env python3
import sys
import yaml
import logging
import pandas as pd
from biocypher import BioCypher

import ontoweaver
import oncodashkb.adapters as od

if __name__ == "__main__":

    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <CSV_filename> <YAML_mapping_config>")
        print(f"For example: {sys.argv[0]} ./tests/genomics_oncokbannotation.csv ./tests/oncokb_example.yaml")
        sys.exit(1)

    logging.basicConfig(level = logging.DEBUG, format = "{levelname} -- {message}\t\t{filename}:{lineno}", style='{')

    bc = BioCypher(
        biocypher_config_path = "config/biocypher_config.yaml",
        schema_config_path = "config/schema_config.yaml"
    )
    # bc.show_ontology_structure()

    # Taple input data.
    df = pd.read_csv(sys.argv[1])

    # Extraction mapping configuration.
    with open(sys.argv[2]) as fd:
        conf = yaml.full_load(fd)

    # Actully map the table to types with properties.
    oncokb = od.oncokb.extract_all(df, conf)

    # Write everything through Biocypher.
    logging.info(f"Extracted {len(list(oncokb.nodes))} nodes and {len(list(oncokb.edges))} edges.")

    logging.info("Write nodes...")
    for n in oncokb.nodes:
        logging.debug(n)
    bc.write_nodes( oncokb.nodes )

    logging.info("Write edges...")
    for e in oncokb.edges:
        logging.debug(e)
    bc.write_edges( oncokb.edges )

    import_file = bc.write_import_call()

    # bc.summary()

    print(import_file)
