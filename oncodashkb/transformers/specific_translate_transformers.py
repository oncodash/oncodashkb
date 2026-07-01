import logging
import pandas as pd
import re

import ontoweaver


class translate_cat_format(ontoweaver.base.Transformer):

    class ValueMaker(ontoweaver.make_value.ValueMaker):
        def __init__(self, 
                     column_to_translate,
                     translate, 
                     translate_from, 
                     translate_to, 
                     format_string: str = None,
                     raise_errors: bool = True
        ):
            self.column_to_translate = column_to_translate
            self.translate = translate
            self.translate_from = translate_from
            self.translate_to = translate_to
            self.format_string = format_string
            super().__init__(raise_errors)

        def __call__(self, columns, row, i):

            translated_row = row.copy()
            for key in self.column_to_translate:
                if key not in row:
                    self.error(f"Column '{key}' not found in data", section="translate", 
                               exception = ontoweaver.exceptions.TransformerDataError)
                if key not in columns:
                    logging.error(f"Column '{key}' not found in the column arguments: {columns}")
                cell = row[key]
                if cell in self.translate:
                    translated_val  = self.translate[cell]
                    translated_row[key] = translated_val
                else:
                    self.delay_warning(f"Row {i} does not contain something to be translated from `{self.translate_from}` to `{self.translate_to}` at column `{key}`.")

            formatted_translated_string = self.format_string.format_map(translated_row)
            yield formatted_translated_string

    def __init__(self,
        properties_of,
        label_maker = None,
        branching_properties = None,
        columns=None,
        output_validator = None,
        multi_type_dict = None,
        raise_errors = True,
        separator = None,
        **kwargs
    ):
        """
        FIXME doc
        """

        # self.map = map(properties_of, label_maker, branching_properties, columns, output_validator, multi_type_dict)

        lpf = ontoweaver.loader.LoadPandasFile()
        lpd = ontoweaver.loader.LoadPandasDataframe()
        lrf = ontoweaver.loader.LoadOWLFile()
        lrg = ontoweaver.loader.LoadOWLGraph()

        # Since we cannot expand kwargs, let's recover what we have inside.
        self.translations = kwargs.get("translations", None)
        self.translations_file = kwargs.get("translations_file", None)
        self.translate_from = kwargs.get("translate_from", None)
        self.translate_to = kwargs.get("translate_to", None)

        if self.translations and self.translations_file:
            self.error(f"Cannot have both `translations` (=`{self.translations}`) and `translations_file` (=`{self.translations_file}`) defined in a {type(self).__name__} transformer.", section="translate", exception = ontoweaver.exceptions.TransformerInterfaceError)

        if self.translations:
            self.translate = self.translations
            logging.debug(f"\t\t\tManual translations: `{self.translate}`")
        elif self.translations_file:
            logging.debug(f"\t\t\tGet translations from file: `{self.translations_file}`")
            if not self.translate_from:
                self.error(f"No translation source column declared for the `{type(self).__name__}` transformer using translations_file=`{self.translations_file}`, did you forget to add a `translate_from` keyword?", section="translate.init", exception = ontoweaver.exceptions.TransformerInterfaceError)
            if not self.translate_to:
                self.error(f"No translation target column declared for the `{type(self).__name__}` transformer using translations_file=`{self.translations_file}`, did you forget to add a `translate_to` keyword?", section="translate.init", exception = ontoweaver.exceptions.TransformerInterfaceError)
            else:

                # Possible arguments from the `translate` section.
                mapping_args = ["translations", "translations_file", "translate_from", "translate_to"]
                # Possible Python attributes.
                mapping_args += ["subclass"]
                # Discard match
                mapping_args += ["match"]
                # Discard columns to translate
                mapping_args += ["column_to_translate", "format_string"]
                # All possible arguments found in a YAML mapping.
                for attr in dir(ontoweaver.base.MappingParser):
                    if re.match("^k_", attr):
                        mapping_args += getattr(ontoweaver.base.MappingParser, attr)

                # Keep only the user-passed arguments that are not in possible YAML keywords.
                more_args = {k:v for k,v in kwargs.items() if k not in mapping_args}
                if more_args['sep'] == 'TAB': # FIXME why the fuck is this changed somehow?
                    more_args['sep'] = '\t'

                logging.debug(f"\t\t\tAdditional user-passed arguments for the load function: {more_args}")

                self.df = pd.DataFrame()
                for with_loader in [lpf, lpd, lrf, lrg]:
                    if with_loader.allows([self.translations_file]):
                        logging.debug(f"\t\t\tUsing loader: {type(with_loader).__name__}")
                        self.df = with_loader.load([self.translations_file], **more_args)
                        break

                if self.df.empty:
                    self.error(f"I was not able to load a valid translations_file from: `{self.translations_file}`")

                logging.debug(f"Loaded a DataFrame: {self.df}")

                if self.translate_from not in self.df.columns:
                    self.error(f"Source column `{self.translate_from}` not found in {type(self).__name__} transformer’s translations file `{self.translations_file}`, available headers: `{','.join(self.df.columns)}`.", section="translate.init", exception = ontoweaver.exceptions.TransformerDataError)

                if self.translate_to not in self.df.columns:
                    self.error(f"Target column `{self.translate_to}` not found in {type(self).__name__} transformer’s translations file `{self.translations_file}`, available headers: `{','.join(self.df.columns)}`.", section="translate.init", exception = ontoweaver.exceptions.TransformerDataError)

                self.translate = {}
                for i,row in self.df.iterrows():
                    frm = row[self.translate_from]
                    to = row[self.translate_to]
                    if frm in self.translate and self.translate[frm] != to:
                        self.delay_warning(f"The key `{frm}` already exists in the translation table, and translated to `{self.translate[frm]}`. It now translates to `{to}`. You may want to avoid such duplicates in translation tables.")
                    if frm and to:
                        self.translate[frm] = to
                    else:
                        self.delay_warning(f"Cannot translate frm `{self.translate_from}` to `{self.translate_to}`, invalid translations values at row {i} of file `{self.translations_file}`: `{frm}` => `{to}`. I will ignore this translation.")

        else:
            self.error(f"When using a {type(self).__name__} transformer, you must define either `translations` or `translations_file`.", section="translate.init", exception = ontoweaver.exceptions.TransformerInterfaceError)

        if not self.translate:
            self.error("No translation found, did you forget the `translations` keyword?", section="translate.init", exception = ontoweaver.exceptions.TransformerInterfaceError)
        
        format_string = kwargs.get("format_string", None)
        if not format_string:  # Neither empty string nor None.
            self.error(f"The `format_string` parameter of the `{self.__name__}` transformer cannot be an empty string.")
        self.format_string = format_string
        
        column_to_translate = kwargs.get("column_to_translate", None)
        if not column_to_translate:  # Neither empty string nor None.
            self.error(f"The `columns_to_translate` parameter of the `{self.__name__}` transformer cannot be an empty string.")
        self.column_to_translate = column_to_translate

        self.value_maker = self.ValueMaker(
            self.column_to_translate,
            self.translate, 
            self.translate_from, 
            self.translate_to, 
            self.format_string,
            raise_errors=raise_errors,
        )

        super().__init__(properties_of,
            self.value_maker,
            label_maker,
            branching_properties,
            columns,
            output_validator,
            multi_type_dict,
            raise_errors=raise_errors,
            **kwargs
        )

class translate_sample_ids(ontoweaver.base.Transformer):
    """Translate the targeted cell value using a tabular mapping and yield a node with using the translated ID."""

    class ValueMaker(ontoweaver.make_value.ValueMaker):
        def __init__(self, translate, translate_from, translate_to, raise_errors: bool = True):
            self.translate = translate
            self.translate_from = translate_from
            self.translate_to = translate_to
            super().__init__(raise_errors)

        def __call__(self, columns, row, i):

            # here key will be sample_id
            for key in columns:
                if key not in row:
                    self.error(f"Column '{key}' not found in data", section="translate", 
                               exception = ontoweaver.exceptions.TransformerDataError)
                cell = row[key]
                patient_id_search = re.search("^([A-Z]+[0-9]+)", cell)
                if patient_id_search:
                    patient_id = patient_id_search.group(0)
                else:
                    logging.error(f"Row {i} does not contain something to be translated from `{self.translate_from}` to `{self.translate_to}` in the sample id `{key}`.")
                if patient_id in self.translate:
                    publication_patient_id = self.translate[patient_id]
                    yield re.sub(pattern = "^([A-Z]+[0-9]+)",
                                 repl = publication_patient_id,
                                 string = cell)
                else:
                    # logging.warning(f"VALUE TO TRANSLATE: {key}")
                    self.delay_warning(f"Row {i} does not contain something to be translated from `{self.translate_from}` to `{self.translate_to}` at column `{key}`.")

    def __init__(self,
            properties_of,
            label_maker = None,
            branching_properties = None,
            columns=None,
            output_validator: ontoweaver.validate.OutputValidator = None,
            multi_type_dict = None,
            raise_errors = True,
            **kwargs
        ):
        """
        Constructor.

        NOTE: The user should provide at least either `translations` or `translations_file`, but not both.

        Args:
            properties_of: Properties of the node.
            value_maker: the ValueMaker object used for the logic of cell value selection for each transformer.
            label_maker: the LabelMaker object used for handling the creation of the output of the transformer. Default is None.
            branching_properties: in case of branching on cell values, the dictionary holding the properties for each branch.
            columns: The columns to be processed.
            translations: A dictionary figuring what to replace (keys) with which string (values).
            translations_file: A filename pointing to a tabular file readable by Pandas' csv_read.
            translate_from: The column in the file containing what to replace.
            translate_to: The column in the file containing the replacement string.
            output_validator: the OutputValidator object used for validating transformer output.
            multi_type_dict: the dictionary holding regex patterns for node and edge type branching based on cell values.
            raise_errors: if True, the caller is asking for raising exceptions when an error occurs
            kwargs: Additional arguments to pass to a Loader function (e.g. if you want to load TSVs, "sep=TAB", reads the translations_file as tab-separated).
        """

        # self.map = map(properties_of, label_maker, branching_properties, columns, output_validator, multi_type_dict, **kwargs)

        lpf = ontoweaver.loader.LoadPandasFile()
        lpd = ontoweaver.loader.LoadPandasDataframe()
        lrf = ontoweaver.loader.LoadOWLFile()
        lrg = ontoweaver.loader.LoadOWLGraph()

        # Since we cannot expand kwargs, let's recover what we have inside.
        self.translations = kwargs.get("translations", None)
        self.translations_file = kwargs.get("translations_file", None)
        self.translate_from = kwargs.get("translate_from", None)
        self.translate_to = kwargs.get("translate_to", None)

        if self.translations and self.translations_file:
            self.error(f"Cannot have both `translations` (=`{self.translations}`) and `translations_file` (=`{self.translations_file}`) defined in a {type(self).__name__} transformer.", section="translate", exception = ontoweaver.exceptions.TransformerInterfaceError)

        if self.translations:
            self.translate = self.translations
            logging.debug(f"\t\t\tManual translations: `{self.translate}`")
        elif self.translations_file:
            logging.debug(f"\t\t\tGet translations from file: `{self.translations_file}`")
            if not self.translate_from:
                self.error(f"No translation source column declared for the `{type(self).__name__}` transformer using translations_file=`{self.translations_file}`, did you forget to add a `translate_from` keyword?", section="translate.init", exception = ontoweaver.exceptions.TransformerInterfaceError)
            if not self.translate_to:
                self.error(f"No translation target column declared for the `{type(self).__name__}` transformer using translations_file=`{self.translations_file}`, did you forget to add a `translate_to` keyword?", section="translate.init", exception = ontoweaver.exceptions.TransformerInterfaceError)
            else:
                # self.translations_file = translations_file
                # self.translate_from = translate_from
                # self.translate_to = translate_to

                # Possible arguments from the `translate` section.
                mapping_args = ["translations", "translations_file", "translate_from", "translate_to"]
                # Possible Python attributes.
                mapping_args += ["subclass"]
                # Discard match
                mapping_args += ["match"]
                # All possible arguments found in a YAML mapping.
                for attr in dir(ontoweaver.base.MappingParser):
                    if re.match("^k_", attr):
                        mapping_args += getattr(ontoweaver.base.MappingParser, attr)

                # Keep only the user-passed arguments that are not in possible YAML keywords.
                more_args = {k:v for k,v in kwargs.items() if k not in mapping_args}
                if 'sep' in  more_args and more_args['sep'] == 'TAB': # FIXME why the fuck is this changed somehow?
                    more_args['sep'] = '\t'

                logging.debug(f"\t\t\tAdditional user-passed arguments for the load function: {more_args}")

                self.df = pd.DataFrame()
                for with_loader in [lpf, lpd, lrf, lrg]:
                    if with_loader.allows([self.translations_file]):
                        logging.debug(f"\t\t\tUsing loader: {type(with_loader).__name__}")
                        self.df = with_loader.load([self.translations_file], **more_args)
                        break
                
                logging.debug(f"Columns in the translation file:{self.df.columns}")

                if self.df.empty:
                    self.error(f"I was not able to load a valid translations_file from: `{self.translations_file}`")

                logging.debug(f"Loaded a DataFrame: {self.df}")

                if self.translate_from not in self.df.columns:
                    self.error(f"Source column `{self.translate_from}` not found in {type(self).__name__} transformer’s translations file `{self.translations_file}`, available headers: `{','.join(self.df.columns)}`.", section="translate.init", exception = exceptions.TransformerDataError)

                if self.translate_to not in self.df.columns:
                    self.error(f"Target column `{self.translate_to}` not found in {type(self).__name__} transformer’s translations file `{self.translations_file}`, available headers: `{','.join(self.df.columns)}`.", section="translate.init", exception = exceptions.TransformerDataError)

                self.translate = {}
                for i,row in self.df.iterrows():
                    frm = row[self.translate_from]
                    to = row[self.translate_to]
                    if frm in self.translate and self.translate[frm] != to:
                        self.delay_warning(f"The key `{frm}` already exists in the translation table, and translated to `{self.translate[frm]}`. It now translates to `{to}`. You may want to avoid such duplicates in translation tables.")
                    if frm and to:
                        self.translate[frm] = to
                    else:
                        self.delay_warning(f"Cannot translate frm `{self.translate_from}` to `{self.translate_to}`, invalid translations values at row {i} of file `{self.translations_file}`: `{frm}` => `{to}`. I will ignore this translation.")

        else:
            self.error(f"When using a {type(self).__name__} transformer, you must define either `translations` or `translations_file`.", section="translate.init", exception = ontoweaver.exceptions.TransformerInterfaceError)


        if not self.translate:
            self.error("No translation found, did you forget the `translations` keyword?", section="translate.init", exception = ontoweaver.exceptions.TransformerInterfaceError)

        self.value_maker = self.ValueMaker(
            self.translate,
            self.translate_from,
            self.translate_to,
            raise_errors=raise_errors
        )

        super().__init__(properties_of,
            self.value_maker,
            label_maker,
            branching_properties,
            columns,
            output_validator,
            multi_type_dict,
            raise_errors=raise_errors,
            **kwargs
        )
        
    def __call__(self, row, i):
        """
        Process a row and yield cell values as node IDs.

        Args:
            row: The current row of the DataFrame.
            i: The index of the current row.

        Yields:
            str: The cell value if valid.

        Raises:
            Warning: If the cell value or the translation is invalid.
        """
        if not self.columns:
            self.error(f"No column declared for the {type(self).__name__} transformer, did you forgot to add a `columns` keyword?", section="translate", exception = exceptions.TransformerDataError)

        for item in super().__call__(row, i):
            yield item