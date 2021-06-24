import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.joinpath('..').resolve()))

from wikipedia_ql import media_wiki

wikipedia = media_wiki.Wikipedia()

print(wikipedia.query(r'''
    from "Nomadland (film)" {
        page@title as "title";
        section[heading="Critical response"] {
            sentence["Rotten Tomatoes"] {
                text["\d+%"] as "percent";
                text["(\d+) (critic|review)"] >> text-slice[1] as "reviews";
                text["[\d.]+/10"] as "overall"
            }
        }
    }
'''))
