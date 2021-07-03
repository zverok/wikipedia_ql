# Another example with fetching many pages from a category and finding some interesting attributes

from pprint import pprint
from wikipedia_ql import media_wiki

wikipedia = media_wiki.Wikipedia(cache_folder='tmp/cache')

# Note that some of the category links are not movies and wouldn't produce interesting results
for res in wikipedia.iquery(r'''
        from category:"Marvel Cinematic Universe films" {
            page@title as "title";
            .infobox-image as "image" { img@src as "url"; img@alt as "title" }
        }
    '''):
    pprint(res)
