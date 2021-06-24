import json
import sys
import re
from pathlib import Path

sys.path.append(str(Path(__file__).parent.joinpath('..').resolve()))

from wikipedia_ql import fragment
from wikipedia_ql import media_wiki
from wikipedia_ql.selectors import *

wikipedia = media_wiki.Wikipedia()

# selected = w.get_page('Radiohead').select(css('.infobox'), all(css('.infobox-label'), css('.infobox-data > *')))
# selected = w.get_page('The Beatles').select(section('Discography'), css('li a'))

# print([f.text for f in selected.items])

# q = w.get_page('The Beatles').query(section('Discography').into('albums'), css('li'), css('a').into('title'))
# print(q)

# print(w.get_page('Bjork').soup.prettify())

# print(wikipedia.query(r'''
#     from "Nomadland (film)" {
#         section[heading="Critical response"] {
#             sentence["Rotten Tomatoes"] {
#                 text["\d+%"] as "percent";
#                 text["(\d+) (critics|reviews)"] >> text-slice[1] as "critics";
#                 text["[\d.]+/10"] as "overall"
#             };
#             text["consensus .+? \""(.+?)\""] as "consensus"
#         }
#     }
# '''))

print(wikipedia.query(r'''
    from "Nomadland (film)" {
        section[heading="Critical response"] {
            sentence["Rotten Tomatoes"] {
                text["\d+%"] as "percent";
                text["(\d+) (critic|review)"] >> text-slice[1] as "reviews";
                text["[\d.]+/10"] as "overall"
            }
        }
    }
'''))



print(wikipedia.query(r'''
    from "Bjork" {
        section[heading="Discography"] as "albums" {
            li {
                a as "title";
                text["\((.+?)\)"] >> text-slice[1] as "date";
                a@href as "link"
            }
        }
    }
'''))

print(wikipedia.query(r'''
    from "Bear" {
        section[heading="Feeding"] >> img@src as "image"
    }
'''))
