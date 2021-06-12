import json
import sys
import re
from pathlib import Path

sys.path.append(str(Path(__file__).parent.joinpath('..').resolve()))

from wikipedia_ql import fragment
from wikipedia_ql.selectors import *

data = json.loads(open('nomadland.json').read())

page = fragment.Fragment.from_json(data)

selected = page.select(section('Critical'), sentence('Rotten'),
    all(text(re.compile(r'\d+%')), text(re.compile(r'\d+ (critic|review)')), text(re.compile(r'[\d\.]+/10')))
)

print([f.text for f in selected.items])
