from biocypher import BioCypher

# from weave import extract 

bc = BioCypher(
    biocypher_config_path="config/biocypher_config.yaml",
    schema_config_path="config/schema_config.yaml"
)

bc.show_ontology_structure(to_disk="/Users/mnajm/Documents/DECIDER/Oncodash_project/")