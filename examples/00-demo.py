# The main example from README: fetch multiple properties from the page

import sys
from pathlib import Path
from pprint import pprint

sys.path.append(str(Path(__file__).parent.joinpath('..').resolve()))

from wikipedia_ql import media_wiki

wikipedia = media_wiki.Wikipedia(cache_folder='tmp/cache')

pprint(wikipedia.query(r'''
    from "Guardians of the Galaxy (film)" {
        page@title as "title";
        section[heading="Cast"] as "cast" {
            li >> text["^(.+?) as (.+?):"] {
                text-group[1] as "actor";
                text-group[2] as "character"
            }
        };
        section[heading="Critical response"] {
            sentence["Rotten Tomatoes"] as "RT ratings" {
                text["\d+%"] as "percent";
                text["(\d+) (critic|review)"] >> text-group[1] as "reviews";
                text["[\d.]+/10"] as "overall"
            }
        }
    }
'''))
