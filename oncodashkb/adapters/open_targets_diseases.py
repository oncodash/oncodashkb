import types as pytypes
import logging
import ontoweaver

from typing import Optional
from collections.abc import Iterable
import owlready2
import pandas as pd


class OpenTargetsDiseases(ontoweaver.tabular.PandasAdapter):

    def __init__(self,
                 df: pd.DataFrame,
                 config: dict,
                 ):
        df = df.reset_index(drop=True)

        # Define the symbols you want to remove
        symbols_to_remove = "#$%^&*()@!~\"\'"

        # Replace each symbol in the 'description' column
        for symbol in symbols_to_remove:
            df['description'] = df['description'].str.replace(symbol, '')
            df['name'] = df['name'].str.replace(symbol, '')

        # Default mapping as a simple config.
        from . import types
        parser = ontoweaver.tabular.YamlParser(config, types)
        mapping = parser()

        # Declare types defined in the config.
        super().__init__(
            df,
            *mapping,
        )
