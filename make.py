#!/usr/bin/env python3
import sys
import logging
import pandas as pd
from biocypher import BioCypher

import oncodashkb.adapters as od

if __name__ == "__main__":

    logging.basicConfig(level = logging.DEBUG)

    bc = BioCypher(
        biocypher_config_path = "config/biocypher_config.yaml",
        schema_config_path = "config/schema_config.yaml"
    )
    # bc.show_ontology_structure()

    allowed_node_types  = od.types.all.nodes()
    # print("allowed_node_types:", allowed_node_types)

    allowed_node_fields = od.types.all.node_fields()
    # print("allowed_node_fields:", allowed_node_fields)

    allowed_edge_types  = od.types.all.edges()
    # print("allowed_edge_types:", allowed_edge_types)

    allowed_edge_fields = od.types.all.edge_fields()
    # print("allowed_edge_fields:", allowed_edge_fields)

    df = pd.read_csv(sys.argv[1])

    # Using empty list or no argument would also select everything,
    # but explicit is better than implicit.
    oncokb = od.oncokb.OncoKB(
        df,
        allowed_node_types,
        allowed_node_fields,
        allowed_edge_types,
        allowed_edge_fields,
    )

    # for n in oncokb.nodes():
    #     print(n)
    bc.write_nodes( oncokb.nodes )

    # for e in oncokb.edges():
    #     print(e)
    bc.write_edges( oncokb.edges )

    bc.write_import_call()

    bc.summary()
