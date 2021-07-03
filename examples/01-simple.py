# Simple fetching of just a few properties from one pages

from pprint import pprint
from wikipedia_ql import media_wiki

wikipedia = media_wiki.Wikipedia(cache_folder='tmp/cache')

pprint(wikipedia.query(r'''
    from "Pink Floyd" {
        section[heading="Discography"] >> li {
            a as "title";
            text["\((.+)\)"] >> text-group[1] as "year";
        }
    }
'''))
