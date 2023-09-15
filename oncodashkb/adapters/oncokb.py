import logging
import ontoweaver

from typing import Optional
from collections.abc import Iterable

import pandas as pd

from . import types

class OncoKB(ontoweaver.tabular.PandasAdapter):

    def __init__(self,
        df: pd.DataFrame,
        node_types : Optional[Iterable[ontoweaver.Node]] = None,
        node_fields: Optional[list[str]] = None,
        edge_types : Optional[Iterable[ontoweaver.Edge]] = None,
        edge_fields: Optional[list[str]] = None,
    ):

        # Type of the node created for each row.
        row_type = types.Target

        # Column name in table => relation type in KG.
        type_of = {
            "patient_id": types.Patient_has_target,
            "referenceGenome": types.Reference_genome,
        }

        # Any Element type in KB => list of columns to extract as properties.
        properties_of = {
            types.Patient: {"lastUpdate": "timestamp"},
            types.Target:  {"lastUpdate": "timestamp"},
            types.Genome:  {"lastUpdate": "timestamp"},
            types.Reference_genome:   {},
            types.Patient_has_target: {},
        }

        super().__init__(df, row_type, type_of, properties_of, node_types, node_fields, edge_types, edge_fields)

        self.run()
