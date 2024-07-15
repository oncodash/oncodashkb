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
        Reading from Hugo_Symbol_genes.conf file 
        By default = genes from OncoKB database
        '''
        included_genes = self.read_genes_list()

        # cut df to include only edge type that we have chosen and annotations for genes from OncoKB
        df = df[((df['Qualifier'].isin(['enables', 'involved_in', 'contributes_to'])) &
                 (df['DB_Object_Symbol'].isin(included_genes)))]

        # Default mapping as a simple config.
        from . import types
        parser = ontoweaver.tabular.YamlParser(config, types)
        mapping = parser()

        # Declare types defined in the config.
        super().__init__(
            df,
            *mapping,
        )

        self.add_edge(types.gene_hugo, types.biological_process, types.gene_to_biological_process)
        self.add_edge(types.gene_hugo, types.molecular_function, types.gene_to_molecular_function)


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
