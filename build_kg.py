import biocypher

# start driver
driver = biocypher.Driver(
    user_schema_config_path='config/schema_config.yaml',
)

driver.show_ontology_structure()