#!/usr/bin/env python3

import sys
import csv
import random
import subprocess

import faker
import pandas as pd

if len(sys.argv) != 4:
    print("Usage:",sys.argv[0],"<db.sqlite3> <table_name> <nb_lines>")
    sys.exit(1)

db = sys.argv[1]
table = sys.argv[2] # "genomics_oncokbannotation"
nb = int(sys.argv[3])

print(f"Parsing `{table}` from `{db}`")

lines = subprocess.check_output(f"sqlite3 {db} '.schema' | grep {table} | sed 's/,/,\\n/g' | grep '^\\s\\\"'", shell = True, universal_newlines=True)
print(len(lines.split('\n')),"columns:")

fields = {}
for line in lines.split("\n"):
    if not line.strip():
        continue
    a,b = line.split('" ')
    name = a.strip('" ')
    bl = b.split()
    type = bl[0]
    if "(" in type:
        c = "".join(bl)
        d = c.split("(")
        type = d[0]
        length = int(d[1].split(")")[0])
    else:
        length = 1
    print(f"`{name}`\t=>\t{type} ({length})")
    fields[name] = {"type": type, "length": length}

fake = faker.Faker()
rows = []
for i in range(nb):
    row = {}
    for h in fields:
        type = fields[h]["type"]
        length = fields[h]["length"]
        if type == "varchar":
            row[h] = fake.unique.text(max_nb_chars = min(length,64))
        elif type == "bool":
            row[h] = random.choice([True,False])
        elif type == "integer":
            row[h] = fake.unique.random_int(0,nb+100)
        elif type == "datetime":
            row[h] = fake.unique.date_time()
        else:
            print(f"Unknown field type: {type}")
            sys.exit(2)
    rows.append(row)

df = pd.DataFrame(rows)
print(df)
with open(table+".csv", "w") as fd:
    df.to_csv(fd,index=False, quoting=csv.QUOTE_NONNUMERIC)
print("Done")
