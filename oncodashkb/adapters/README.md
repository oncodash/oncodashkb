## Gene Ontology Data Preparation

**Gene Ontology** (GO) is one of the biggest biomedical databases for the annotation of genes and their products across different species. To integrate the data in the Semantic Knowledge Graph (SKG), we use the `GO Annotations file` for Homo Sapiens in `GAF format` [Download page](https://geneontology.org/docs/download-go-annotations/) . Each line in GAF file represents **one annotation** for a gene product and contains **17 columns** (you can read a detailed description of each column [here](https://geneontology.org/docs/go-annotation-file-gaf-format-2.2/])).

Compared to the integration of the CGI and OncoKB databases, where each column represents a concrete data type from Biolink ontology, the GO annotations file contains data type for each annotation (row) in the column 'Qualifier'. For further details regarding different types of relationships, please refer to the following [link](https://wiki.geneontology.org/Annotation_Relations).

To solve the issue concerning data types represented in one column and to make the integrated data in the SKG more clear and easy to understand, the following steps were implemented in the GO adapter:
- [Download](https://geneontology.org/docs/download-ontology/) the **GO ontology OWL file** to create a dictionary that can map **GO_ID** to **GO_term** cause there is only a **GO_ID** column in the GAF file. 
- Create a new column **GO_term** using a dictionary and `create_id_term_dict` method.
- For the chosen type of the relation from the **column 'Qualifier'** (in our case, `enables`, `involved_in`, `contributes_to` relation types) create an additional column (in our case, `GO_enables`, `GO_involved_in`, `GO_contributes_to` columns) and copy the **GO_term** in the related column (see illustration below)
  
![Schema_columns_GO_adapter](https://github.com/kgaydukova/oncodashkb/assets/23275374/37b23c98-17b6-45bd-ab34-bc4d7fdf72f9)


- Declare data type and relation type in the mapping file `gene_ontology.yaml` for each synthetic additional column (`GO_enables`, `GO_involved_in`, `GO_contributes_to`). 

```yaml
subject: annotation # Type for each entry (e.g. line).

columns:
    GO_enables:
        to_object: molecular_function
        via_relation: enables
    GO_involved_in:
        to_object: biological_process
        via_relation: involved_in
    GO_contributes_to:
        to_object: molecular_function
        via_relation: contributes_to
```
