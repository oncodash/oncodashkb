import types as pytypes
import logging
import ontoweaver

from typing import Optional
from collections.abc import Iterable
import owlready2
import pandas as pd


class OpenTargetsEvidences(ontoweaver.tabular.PandasAdapter):

    def __init__(self,
                 df: pd.DataFrame,
                 config: dict,
                 ):

        df = df.reset_index(drop=True)

        df['urls'] = df['urls'].astype(str)

        df['urls'] = df['urls'].str.replace('[{', '', regex=False).str.replace('}]', '', regex=False).str.replace(',',
                                                                                                                  ' ',
                                                                                                                  regex=False).str.replace(
            '\'', ' ', regex=False)

        replacement_dict = {
            'LoF': 'Loss-of-function',
            'GoF': 'Gain-of-function'
        }

        # replace the values in the 'variantEffect' column to have the same values of functional effect as in the OncoKB
        df['variantEffect'] = df['variantEffect'].replace(replacement_dict)

        self.genes_list = 'oncodashkb/adapters/Ensembl_genes.conf'
        list_of_ensg = self.read_genes_list()

        df = df[df['targetId'].isin(list_of_ensg)]

        df = df.reset_index(drop=True)

        # Default mapping as a simple config.
        from . import types
        parser = ontoweaver.tabular.YamlParser(config, types)
        mapping = parser()

        # Declare types defined in the config.
        super().__init__(
            df,
            *mapping,
        )


    # method to recursively find all descendants
    @staticmethod
    def get_descendants(cls):
        set_descendants = set(cls.subclasses())
        for subclass in cls.subclasses():
            set_descendants.update(OpenTargetsEvidences.get_descendants(subclass))
        return set_descendants

    @staticmethod
    def remove_prefix(element):
        element_str = str(element)  # Ensure the element is a string
        if element_str.startswith("obo.") or element_str.startswith("efo."):
            return element_str.split(".", 1)[1]
        return element_str

    def source_type(self, row):
        from . import types
        logging.debug(f"Source type is `evidence`")
        return types.evidence


    def read_genes_list(self):
            with open(self.genes_list, 'r') as file:
                content = file.read()
                genes = content.replace('\n', '').split(',')
                genes = [gene.strip().strip("'") for gene in genes]
                genes = list(filter(None, genes))

            return genes


