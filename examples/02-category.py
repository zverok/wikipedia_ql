# Fetching all pages in the category, using iquery (generator) to iterate through results

from pprint import pprint
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
