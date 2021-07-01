import sys
from pathlib import Path
from pprint import pprint
import time

sys.path.append(str(Path(__file__).parent.joinpath('..').resolve()))

from wikipedia_ql import media_wiki

wikipedia = media_wiki.Wikipedia()

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

# print(wikipedia.query(r'''
#     from category:"Best Drama Picture Golden Globe winners" {
#         page@title as "title";
#         section[heading="Critical response"] {
#             sentence["Rotten Tomatoes"] {
#                 text["\d+%"] as "percent";
#                 text["(\d+) (critic|review)"] >> text-group[1] as "reviews";
#                 text["[\d.]+/10"] as "overall"
#             }
#         }
#     }
# '''))

t = time.time()

for res in wikipedia.iquery(r'''
        from category:"Marvel Cinematic Universe films" {
            page@title as "title";
            .infobox-image as "image" { img@src as "url"; img@alt as "title" }
        }
    '''):
    print(f'after {time.time() - t:.2f}:')
    t = time.time()
    pprint(res)

