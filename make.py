from biocypher import BioCypher

import oncodashkb

if __name__ == "__main__":

    bc = BioCypher(biocypher_config_path = "config/biocypher_config.yaml")

    allowed ={
        "node_types"  = [ ],
        "node_fields" = [ ],
        "edge_types"  = [ ],
    }

    oncokb = OncoKB(*allowed)

    bc.write_nodes( oncokb.nodes() )
    bc.write_edges( oncokb.edges() )

    bc.write_import_call()

    bc.summary()
