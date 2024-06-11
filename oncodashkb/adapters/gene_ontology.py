import types as pytypes
import logging
import ontoweaver

from typing import Optional
from collections.abc import Iterable

import pandas as pd

from owlready2 import get_ontology


class Gene_ontology(ontoweaver.tabular.PandasAdapter):

    def __init__(self,
                 df: pd.DataFrame,
                 ontology: str,
                 genes_list: str,
                 config: dict,
                 node_types: Optional[Iterable[ontoweaver.Node]] = None,
                 node_fields: Optional[list[str]] = None,
                 edge_types: Optional[Iterable[ontoweaver.Edge]] = None,
                 edge_fields: Optional[list[str]] = None,
                 ):

        self.ontology = ontology
        self.genes_list = genes_list

        # define column names based on the GAF specification
        columns = ['DB', 'DB_Object_ID', 'DB_Object_Symbol', 'Qualifier', 'GO_ID', 'DB_Reference', 'Evidence_Code',
                   'With_or_From', 'Aspect', 'DB_Object_Name', 'DB_Object_Synonym', 'DB_Object_Type', 'Taxon', 'Date',
                   'Assigned_By', 'Annotation_Extension', 'Gene_Product_Form_ID']

        # assign column names to the DataFrame
        df.columns = columns

        # create dict with GO_id:GO_term
        dict_go_plus = self.create_id_term_dict()

        # DELETE ; and , from terms (values in dictionary) to avoid future errors in CSV for neo4j import
        for key in dict_go_plus.keys():
            if ',' in dict_go_plus[key]:
                dict_go_plus[key] = dict_go_plus[key].replace(',', '')
            if ';' in dict_go_plus[key]:
                dict_go_plus[key] = dict_go_plus[key].replace(';', '')
            if '\'' in dict_go_plus[key]:
                dict_go_plus[key] = dict_go_plus[key].replace('\'', '')

        # create additional column with GO terms (mapped from GO_id)
        df['GO_term'] = df['GO_ID'].map(lambda go_id: dict_go_plus[go_id])

        # create new columns that depends on edge type
        df['GO_involved_in'] = None
        df['GO_enables'] = None
        df['GO_contributes_to'] = None

        # add the GO_term in GO_involved_in, GO_enables, GO_contributes_to columns depending on the edge type in
        # Qualifier column

        df = df.apply(self.separate_edges_types, axis=1)

        '''
        List of genes the annotation for which we will integrate from Gene Ontology data,
        Reading from GO_genes.conf file 
        By default = genes from OncoKB database
        '''
        included_genes = self.read_genes_list()

        # cut df to include only edge type that we have chosen and annotations for genes from OncoKB
        df = df[((df['Qualifier'].isin(['enables', 'involved_in', 'contributes_to'])) &
                 (df['DB_Object_Symbol'].isin(included_genes)))]

        # Default mapping as a simple config.
        from . import types
        mapping = self.configure(config, types)

        if not node_types:
            node_types = types.all.nodes()
            logging.debug(f"node_types: {node_types}")

        if not node_fields:
            node_fields = types.all.node_fields()
            logging.debug(f"node_fields: {node_fields}")

        if not edge_types:
            edge_types = types.all.edges()
            logging.debug(f"edge_types: {edge_types}")

        if not edge_fields:
            edge_fields = types.all.edge_fields()
            logging.debug(f"edge_fields: {edge_fields}")

        # Declare types defined in the config.
        super().__init__(
            df,
            *mapping,
            node_types,
            node_fields,
            edge_types,
            edge_fields,
        )

    # function to create a dictionary with GO_id:GO_term for gene ontology, input - OWL file, output - dictionary
    def create_id_term_dict(self):
        dict_id_term = {}

        ont = get_ontology(self.ontology).load()

        # iterate through all classes in the ontology
        for cls in ont.classes():
            # get the class ID and label (term)
            class_id = cls.iri # read class_id like http://purl.obolibrary.org/obo/GO_0003674'
            class_label = cls.label.first() if cls.label else cls.name

            # make the same key as we have in GO annotation files
            class_id_key = class_id.replace("http://purl.obolibrary.org/obo/GO_", "GO:")
            # add to dictionary like GO:0003674': 'molecular_function'
            dict_id_term[class_id_key] = class_label

        return dict_id_term

    def read_genes_list(self):

        with open(self.genes_list, 'r') as file:

            content = file.read()
            genes = content.replace('\n', '').split(',')
            genes = [gene.strip().strip("'") for gene in genes]
            genes = list(filter(None, genes))

        return genes

    # function to copy GO_term to related column for future ontoweaver mapping based on Qualifier column (relation type)

    @staticmethod
    def separate_edges_types(row):
        if row['Qualifier'] == 'enables':
            row['GO_enables'] = row['GO_term']
        elif row['Qualifier'] == 'involved_in':
            row['GO_involved_in'] = row['GO_term']
        elif row['Qualifier'] == 'contributes_to':
            row['GO_contributes_to'] = row['GO_term']
        return row

    def source_type(self, row):
        from . import types
        logging.debug(f"Source type is `annotation`")
        return types.annotation

    def end(self):
        from . import types
        # Manual extraction of an additional edge between sample and patient.
        # Because so far the PandasAdapter only allow to declare one mapping for each column.
        # FIXME comment indicating that we should find a way to handle the type suffix/prefix through a make_id function in the next refactoring of OntoWeaver.
        for i, row in self.df.iterrows():
            separator = ":"

            sid = f"{row['DB_Object_Symbol']}:gene_hugo"
            pid1 = f"{row['GO_involved_in']}:biological_process"
            pid2 = f"{row['GO_enables']}:molecular_function"

            logging.debug(f"Add a `gene_to_biological_process` edge between `{sid}` and `{pid1}`")
            self.edges_append(self.make_edge(
                types.gene_to_biological_process, id=None,
                id_source=sid, id_target=pid1
            ))
            logging.debug(f"Add a `gene_to_molecular_function` edge between `{sid}` and `{pid2}`")
            self.edges_append(self.make_edge(
                types.gene_to_molecular_function, id=None,
                id_source=sid, id_target=pid2
            ))
