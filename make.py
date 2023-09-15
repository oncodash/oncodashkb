#!/usr/bin/env python3
import sys
import logging
import pandas as pd
from biocypher import BioCypher

import ontoweaver
import oncodashkb.adapters as od

if __name__ == "__main__":

    logging.basicConfig(level = logging.DEBUG, format = "{levelname} -- {message}\t\t{filename}:{lineno}", style='{')

    bc = BioCypher(
        biocypher_config_path = "config/biocypher_config.yaml",
        schema_config_path = "config/schema_config.yaml"
    )
    # bc.show_ontology_structure()

    df = pd.read_csv(sys.argv[1])

    oncokb = od.oncokb.extract_all(df)

    logging.info(f"Extracted {len(list(oncokb.nodes))} nodes and {len(list(oncokb.edges))} edges.")

    logging.info("Write nodes...")
    for n in oncokb.nodes:
        logging.debug(n)
    bc.write_nodes( oncokb.nodes )

    logging.info("Write edges...")
    for e in oncokb.edges:
        logging.debug(e)
    bc.write_edges( oncokb.edges )

    bc.write_import_call()

    bc.summary()
