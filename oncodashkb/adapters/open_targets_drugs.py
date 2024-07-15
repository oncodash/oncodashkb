import types as pytypes
import logging
import ontoweaver

from typing import Optional
from collections.abc import Iterable
import owlready2
import pandas as pd


class OpenTargetsDrugs(ontoweaver.tabular.PandasAdapter):

    def __init__(self,
                 df: pd.DataFrame,
                 config: dict,
                 ):

        df = df.reset_index(drop=True)
        df = df[df['isApproved'] == True]
        df['name'] = df['name'].str.replace('\'', '', regex=False)

        # Default mapping as a simple config.
        from . import types
        parser = ontoweaver.tabular.YamlParser(config, types)
        mapping = parser()

        # Declare types defined in the config.
        super().__init__(
            df,
            *mapping,
        )


