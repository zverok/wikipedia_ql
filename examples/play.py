import json
import sys
import re
from pathlib import Path

sys.path.append(str(Path(__file__).parent.joinpath('..').resolve()))

from wikipedia_ql import fragment
from wikipedia_ql import media_wiki
from wikipedia_ql.selectors import *

w = media_wiki.Wikipedia()

page = w.get_page('Radiohead')

selected = page.select(css('.infobox'), all(css('.infobox-label'), css('.infobox-data > *')))

print([f.text for f in selected.items])
