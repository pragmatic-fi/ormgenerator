import json
from pprint import pp

from ormgenerator.main import _process_schema

with open("schemas/user.json") as f:
    d = json.load(f)

pp(_process_schema(d), width=1000)
