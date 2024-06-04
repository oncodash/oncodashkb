import types as pytypes
import logging
import ontoweaver

from typing import Optional
from collections.abc import Iterable

import pandas as pd


class Gene_ontology(ontoweaver.tabular.PandasAdapter):

    def __init__(self,
                 df: pd.DataFrame,
                 ontology: str,
                 config: dict,
                 node_types: Optional[Iterable[ontoweaver.Node]] = None,
                 node_fields: Optional[list[str]] = None,
                 edge_types: Optional[Iterable[ontoweaver.Edge]] = None,
                 edge_fields: Optional[list[str]] = None,
                 ):

        self.ontology = ontology

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

        # create additional column with GO terms (mapped from GO_id)
        df['GO_term'] = df['GO_ID'].map(lambda go_id: dict_go_plus[go_id])

        # create new columns that depends on edge type
        df['GO_involved_in'] = None
        df['GO_enables'] = None
        df['GO_contributes_to'] = None

        # add the GO_term in GO_involved_in, GO_enables, GO_contributes_to columns depending on the edge type in
        # Qualifier column

        df = df.apply(self.separate_edges_types, axis=1)

        # list of genes presented in OncoKB database

        genes = ['MET', 'BRAF', 'EZH2', 'CDKN2A', 'ETV6', 'ETNK1', 'KRAS', 'NTRK3',
                 'IDH2', 'MAF', 'BRCA1', 'TP53', 'BCOR', 'FGFR1', 'MYC', 'JAK2',
                 'CD274', 'PDCD1LG2', 'PIK3CA', 'BCL6', 'TP63', 'IL7R', 'MDM2',
                 'SETBP1', 'FBXW7', 'ABL1', 'MAP2K1', 'TYK2', 'EPOR', 'ERCC2',
                 'SMARCB1', 'CHEK2', 'PDGFB', 'EP300', 'STAG2', 'PHF6', 'FGFR2',
                 'FGFR3', 'NRG1', 'GATA3', 'HRAS', 'ERBB2', 'BCL2', 'TCF3', 'CEBPA',
                 'CRLF2', 'ZRSR2', 'NOTCH1', 'TNFRSF14', 'BARD1', 'ESR1', 'PTCH1',
                 'FANCA', 'KLF2', 'MALT1', 'CALR', 'DNMT3A', 'ALK', 'SF3B1', 'IDH1',
                 'DUSP22', 'IRF4', 'BIRC3', 'ATM', 'ASXL1', 'ATRX']

        # cut df to include only edge type that we have chosen and annotations for genes from OncoKB
        df = df[((df['Qualifier'].isin(['enables', 'involved_in', 'contributes_to'])) &
                 (df['DB_Object_Symbol'].isin(genes)))]

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

        with open(self.ontology, 'r') as file:
            flag = 0
            saved_id = None
            saved_label = None

            # check each line
            for line in file:
                # cut "GO:11111111" (save as GO_11111111)
                if '<!-- http://purl.obolibrary.org/obo/GO_' in line:
                    saved_id = line.strip()
                    saved_id = saved_id.replace('<!-- http://purl.obolibrary.org/obo/', '').replace(' -->', '').replace(
                        '\n', '')
                    saved_id = saved_id.replace('GO_', 'GO:')
                    flag = 1
                # cut the term for this id
                elif flag == 1 and '   <rdfs:label>' in line:
                    saved_label = line.strip()
                    saved_label = saved_label.replace('<rdfs:label>', '').replace('</rdfs:label>', '')
                    flag = 0
                    # add in dictionary "id":"term"
                    dict_id_term[saved_id] = saved_label
                    # print(saved_line)
                    # print(saved_label, '\n')
            return dict_id_term

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
