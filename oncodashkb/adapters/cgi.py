import types as pytypes
import logging
import ontoweaver

from typing import Optional
from collections.abc import Iterable

import pandas as pd


class CGI(ontoweaver.tabular.PandasAdapter):

    def __init__(self,
        df: pd.DataFrame,
        config: dict,
    ):
        # Default mapping as a simple config.
        from . import types
        parser = ontoweaver.tabular.YamlParser(config, types)
        mapping = parser()


        # Declare types defined in the config.
        super().__init__(
            df,
            *mapping,
        )

