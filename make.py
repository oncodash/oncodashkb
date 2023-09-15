#!/usr/bin/env python3
import sys
import logging
import pandas as pd
from biocypher import BioCypher

import ontoweaver
import oncodashkb.adapters as od

if __name__ == "__main__":

    logging.basicConfig(level = logging.DEBUG, format = r"{levelname} -- {message}", style='{')

    bc = BioCypher(
        biocypher_config_path = "config/biocypher_config.yaml",
        schema_config_path = "config/schema_config.yaml"
    )
    # bc.show_ontology_structure()

    df = pd.read_csv(sys.argv[1])

    oncokb = od.oncokb.parse_all(df)

    for n in oncokb.nodes:
        print(n)
    bc.write_nodes( oncokb.nodes )

    for e in oncokb.edges:
        print(e)
    bc.write_edges( oncokb.edges )

    bc.write_import_call()

    bc.summary()
