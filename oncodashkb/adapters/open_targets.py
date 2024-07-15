import types as pytypes
import logging
import ontoweaver

from typing import Optional
from collections.abc import Iterable
import owlready2
import pandas as pd


class OpenTargets(ontoweaver.tabular.PandasAdapter):

    def __init__(self,
                 df: pd.DataFrame,
                 config: dict,
                 ):
        df = df.reset_index(drop=True)

        df['targetId'] = df['id']

        df['transcriptIds'] = df['transcriptIds'].astype(str)

        df['transcriptIds'] = df['transcriptIds'].apply(lambda x: x.replace(' ', ';'))
        df['transcriptIds'] = df['transcriptIds'].apply(lambda x: x.replace('\'', ''))
        df['transcriptIds'] = df['transcriptIds'].apply(lambda x: x.replace('[', ''))
        df['transcriptIds'] = df['transcriptIds'].apply(lambda x: x.replace(']', ''))


        self.genes_list = 'oncodashkb/adapters/Hugo_Symbol_genes.conf'

        our_genes = self.read_genes_list()

        df = df[df['approvedSymbol'].isin(our_genes)]

        # Default mapping as a simple config.
        from . import types
        parser = ontoweaver.tabular.YamlParser(config, types)
        mapping = parser()

        # Declare types defined in the config.
        super().__init__(
            df,
            *mapping,
        )
        self.add_edge(types.target, types.gene_hugo, types.ensemble_id_to_hugo_symbol)


    def read_genes_list(self):
            with open(self.genes_list, 'r') as file:
                content = file.read()
                genes = content.replace('\n', '').split(',')
                genes = [gene.strip().strip("'") for gene in genes]
                genes = list(filter(None, genes))

            return genes



