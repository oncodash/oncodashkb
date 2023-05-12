#!/usr/bin/env python3

from biocypher import BioCypher

import oncodashkb.adapters as od

if __name__ == "__main__":

    bc = BioCypher(
        biocypher_config_path = "config/biocypher_config.yaml",
        schema_config_path = "config/schema_config.yaml"
    )
    bc.show_ontology_structure()

    allowed_node_types  = [
        od.types.Patient,
        od.types.Target,
        od.types.Patient_has_target,
    ]
    allowed_node_fields = \
          od.types.Patient.fields() \
        + od.types.Target.fields() \
        + od.types.Patient_has_target.fields()
    allowed_edge_types  = [ ]

    oncokb = od.oncokb.OncoKB(
        allowed_node_types,
        allowed_node_fields,
        allowed_edge_types
    )

    # for n in oncokb.nodes():
    #     print(n)
    bc.write_nodes( oncokb.nodes() )

    # for e in oncokb.edges():
    #     print(e)
    bc.write_edges( oncokb.edges() )

    bc.write_import_call()

    bc.summary()
