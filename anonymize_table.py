#!/usr/bin/env python3

import re
import random
import string
import logging
import numpy as np
from pathlib import Path

import ontoweaver

def write_table(df, fd, ext="csv", **kwargs):

    read_funcs = {
        'csv'    : df.to_csv,
        'tsv'    : df.to_csv,
        'txt'    : df.to_csv,

        'xls'    : df.to_excel,
        'xlsx'   : df.to_excel,
        'xlsm'   : df.to_excel,
        'xlsb'   : df.to_excel,
        'odf'    : df.to_excel,
        'ods'    : df.to_excel,
        'odt'    : df.to_excel,

        'json'   : df.to_json,
        'html'   : df.to_html,
        'xml'    : df.to_xml,
        'hdf'    : df.to_hdf,
        'feather': df.to_feather,
        'parquet': df.to_parquet,
        'pickle' : df.to_pickle,
        'orc'    : df.to_orc,
        'stata'  : df.to_stata,
    }

    if ext not in read_funcs:
        msg = f"File format '{ext}' of file '{filename}' is not supported (I can only write one of: {' ,'.join(read_funcs.keys())})"
        logger.error(msg)
        raise RuntimeError(msg)

    return read_funcs[ext](path_or_buf=fd, **kwargs)


def shuffle(df):
    # df.apply(np.random.shuffle, axis = 0) # columns
    return df.apply(lambda col: col.sample(frac=1).values)


def anonymize_value(value, remove_site = False):
    assert(";" not in str(value))
    if remove_site:
        value = re.sub("_DNA[1-2]*$", "", value)
    m = re.search("^([A-Z]{1,2}[0-9]{3})", value)
    if m:
        code = m.group(1)
        return re.sub(code, random_code(), value)
    else:
        return value


def anonymize_all(df, columns=None, remove_site = False):
    if not columns:
        columns = df.columns.values.tolist()
    for i,row in df.iterrows():
        for col in columns:
            value = row[col]
            if type(value) == str:
                if ";" in value:
                    vals = []
                    for val in value.split(";"):
                        new = anonymize_value(val, remove_site)
                        vals.append(new)
                    new_val = ";".join(vals)
                else:
                    new_val = anonymize_value(value, remove_site)

                if value and new_val:
                    df.loc[i,col] = new_val


def random_code():
    return "CC" + "".join(random.choices(string.digits, k=4))


if __name__ == "__main__":
    import argparse
    import os
    import sys

    do = argparse.ArgumentParser(
        formatter_class=argparse.RawTextHelpFormatter,
        description="""Anonymize or pseudonymize a data table.""",
        epilog=f"Example:\n\t./{os.path.basename(sys.argv[0])} data.csv --args index:False --remove-sample-site --format csv > data_anon.csv")

    do.add_argument("--log-level",
        default="INFO",
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
        help="Configure the log level (default: %(default)s).",
    )

    do.add_argument('-c', '--columns', nargs='+', default=None,
        help="Columns names in which to anonymize cohort codes (default: all).")

    do.add_argument('-s', '--remove-sample-site', action="store_true")

    do.add_argument('-S', '--no-shuffle', action="store_true")

    # do.add_argument('-c', '--eoc', help="Use the given (;-separated) mapping instead of generating a random one.", metavar="EOC_FILE")

    do.add_argument('-f', '--format', help="File format to export the altered data (default: same as input).", default=None, metavar="FMT")

    do.add_argument('-a', '--args', help="Additional argument to pass to the pandas.DataFrame.to_* write function (default: none).", default=None, nargs='+', metavar="KEY:VAL")


    do.add_argument("filename", metavar="DATABASE_FILE")

    asked = do.parse_args()

    logging.basicConfig(level = asked.log_level)

    if not asked.format:
        asked.format = Path(asked.filename).suffix[1:]

    more_args = {}
    if asked.args:
        for kv in asked.args:
            k,v = kv.split(":")

            if v == "False":
                v = False
            elif v == "True":
                v = True

            more_args[k] = v

    logging.info("Load file...")
    df = ontoweaver.read_file(asked.filename)
    print(df, file=sys.stderr)

    if not asked.no_shuffle:
        logging.info("Shuffle columns...")
        df = shuffle(df)

    logging.info("Alter cohort codes...")
    anonymize_all(df, columns = asked.columns, remove_site = asked.remove_sample_site)

    logging.info("Write data...")
    write_table(df, sys.stdout, ext=asked.format, **more_args)

