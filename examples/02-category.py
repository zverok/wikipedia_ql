# Fetching all pages in the category, using iquery (generator) to iterate through results

import sys
from pathlib import Path
from pprint import pprint

sys.path.append(str(Path(__file__).parent.joinpath('..').resolve()))

from wikipedia_ql import media_wiki

wikipedia = media_wiki.Wikipedia(cache_folder='tmp/cache')

query = r'''
    from category:"2020s American time travel television series" {
        page@title as "title";
        section[heading="External links"] >> li >> text["^(.+?) at IMDb"] >> text-group[1] >> a@href as "imdb"
    }
'''

for res in wikipedia.iquery(query):
    pprint(res)
