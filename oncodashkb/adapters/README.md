# OncodashKB Adapters

## CGI adapter 

**Cancer Genome Interpreter** is the cancer database that contains information about various genetic alterations that can be associated with the patient, gene details, samples, disease type, and transcript information.

To launch CGI adapter, use `--cgi` option and path to the CSV file with the data that you want to integrate.

**Example of use:**
```
./weave.py –cgi /path_to_file/test_genomics_cgimutation.csv
```



## OncoKB adapter

**OncoKB** is the cancer database that contains information about various genetic alterations that can be associated with the patient, gene details, samples, and disease type, as well as treatment options with FDA, OncoKB evidence levels, and related publications. 

To launch OncoKB adapter, use `--oncokb` option and path to the CSV file with the data that you want to integrate.

**Example of use:**
```
./weave.py –oncokb /path_to_file/ test_genomics_oncokbannotation.csv
```

## Gene Ontology adapter

**Gene Ontology** is one of the biggest biomedical databases. The described adapter helps to integrate the data about the molecular function of the gene product, as well as the biological process in which these genes are involved.

- Molecular function: GO annotations that have relation type `enabled` or `contributes_to`.
- Biological process: GO annotations that have relation type `involved_in`.

**To integrate the data, three files are necessary:**
-	`--gene_ontology` option for GO annotations in GAF format  [Download GO annotations](http://current.geneontology.org/products/pages/downloads.html)
-	`--gene_ontology_owl` option for GO ontology in OWL format [Download GO ontology](https://geneontology.org/docs/download-ontology/)
-	`--gene_ontology_genes` option for the list of genes for which we want to integrate the GO annotations (example in adapters/GO_genes.conf file, by default = list of genes from OncoKB database).

**Example of use:**
```
./weave.py --gene_ontology /path_to_file/goa_human.gaf --gene_ontology_owl /path_to_file/go.owl --gene_ontology_genes /path_to_file/GO_genes.conf
```

If you want to integrate annotations with another type of relations, you can change the `adapters/gene_ontology.py` file by adding the next code in **class Gene_ontology** (example for `involved_in` edge type) and precise node and edge type in the `gene_ontology.yaml`:
```
# create new columns that depends on edge type
        df['GO_involved_in'] = None
        
# cut df to include only edge type that we have chosen and annotations for genes from OncoKB
        df = df[((df['Qualifier'].isin(['enables', 'involved_in', 'contributes_to'])) &
                 (df['DB_Object_Symbol'].isin(included_genes)))]
```

