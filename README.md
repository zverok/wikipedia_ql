**WikipediaQL** is an experimental query language and Python library for querying structured data from Wikipedia. It looks like this:

```python
from wikipedia_ql import media_wiki

wikipedia = media_wiki.Wikipedia()

print(wikipedia.query(r'''
    from "Guardians of the Galaxy (film)" {
        page@title as "title";
        section[heading="Cast"] as "cast" {
            li >> text["^(.+?) as (.+?):"] {
                text-slice[1] as "actor";
                text-slice[2] as "character"
            }
        };
        section[heading="Critical response"] {
            sentence["Rotten Tomatoes"] as "RT ratings" {
                text["\d+%"] as "percent";
                text["(\d+) (critic|review)"] >> text-slice[1] as "reviews";
                text["[\d.]+/10"] as "overall"
            }
        }
    }
'''))

# {
#     'title': 'Guardians of the Galaxy (film)',
#     'cast': [{'actor': 'Chris Pratt', 'character': 'Peter Quill / Star-Lord'}, {'actor': 'Zoe Saldana', 'character': 'Gamora'}, {'actor': 'Dave Bautista', 'character': 'Drax the Destroyer'}, {'actor': 'Vin Diesel', 'character': 'Groot'}, {'actor': 'Bradley Cooper', 'character': 'Rocket'}, {'actor': 'Lee Pace', 'character': 'Ronan the Accuser'}, {'actor': 'Michael Rooker', 'character': 'Yondu Udonta'}, {'actor': 'Karen Gillan', 'character': 'Nebula'}, {'actor': 'Djimon Hounsou', 'character': 'Korath'}, {'actor': 'John C. Reilly', 'character': 'Rhomann Dey'}, {'actor': 'Glenn Close', 'character': 'Irani Rael'}, {'actor': 'Benicio del Toro', 'character': 'Taneleer Tivan / The Collector'}],
#     'RT ratings': {'percent': '92%', 'reviews': '328', 'overall': '7.82/10'}
# }
```

### How?

WikipediaQL-the-library does roughly this:

* Parses query in WikipediaQL-the-language;
* Uses [MediaWiki API](https://en.wikipedia.org/w/api.php) to fetch pages' metadata;
* Uses [`action=parse` API](https://en.wikipedia.org/w/api.php?action=help&modules=parse) to fetch each page's content HTML;
* Applies selectors from the query to page to extract structured data.

### Why?

Wikipedia is the most important open knowledge project: basically, the ToC of all the human data. While it might be incomplete or misleading in details, the amount of data is incredible, and its organization makes all the data fairly accessible to humans.

OTOH, the data is semi-structured, and quite hard to extract automatically. This project is an experiment in making this data accessible to machines—or, rather, to humans with programming languages. The main goal is to develop an easy to use and remember, unambigous and powerful query language, and back it by a reference implementation.

_See [FAQ](#faq) below for justifications of parsing Wikipedia instead of just using already formalized Wikidata (and of  parsing HTML instead of Wikipedia markup)._

## Usage

`pip install wikipedia_ql`

```python
from wikipedia_ql import media_wiki

wikipedia = media_wiki.Wikipedia()

data = wikipedia.query(query_text)
```

Each WikipediaQL query looks like this:
```
from <source> {
  <selectors>
}
```

_Source_ is wikipedia article name, or category name, or (in the future) other ways of specifying multiple pages. _Selectors_ are CSS-alike, and nested in one another with `selector { other; selectors }`, or (shortcut) `selector >> other_selector`. All terminal selectors (e.g. doesn't having others nested) produce values in the output; which can be named with `as "valuename`.

See below for a list of selectors and sources currently supported, and the future ones.

### Examples

Simple query for some info from the page:

```python
wikipedia.query(r'''
from "Pink Floyd" {
    section[heading="Discography"] >> li {
        a as "title";
        text["\((.+)\)"] >> text-group[1] as "year";
    }
}
''')
# => [{'title': 'The Piper at the Gates of Dawn', 'year': '1967'}, {'title': 'A Saucerful of Secrets', 'year': '1968'}, {'title': 'More', 'year': '1969'}, {'title': 'Ummagumma', 'year': '1969'}, {'title': 'Atom Heart Mother', 'year': '1970'}, {'title': 'Meddle', 'year': '1971'}, {'title': 'Obscured by Clouds', 'year': '1972'}, {'title': 'The Dark Side of the Moon', 'year': '1973'}, {'title': 'Wish You Were Here', 'year': '1975'}, {'title': 'Animals', 'year': '1977'}, {'title': 'The Wall', 'year': '1979'}, {'title': 'The Final Cut', 'year': '1983'}, {'title': 'A Momentary Lapse of Reason', 'year': '1987'}, {'title': 'The Division Bell', 'year': '1994'}, {'title': 'The Endless River', 'year': '2014'}]
```

Multi-page query from pages of some category:
```python
query = r'''
from category:"2020s American time travel television series" {
    page@title as "title";
    section[heading="External links"] {
      li >> text["^(.+?) at IMDb"] >> text-group[1] >> a@href as "imdb"
    }
}
'''

# iquery returns generator, fetching pages as you go
for row in wikipedia.iquery(query):
  print(row)
# {'title': 'Agents of S.H.I.E.L.D.', 'imdb': 'https://www.imdb.com/title/tt2364582/'}
# {'title': 'The Flash (2014 TV series)', 'imdb': 'https://www.imdb.com/title/tt3107288/'}
# {'title': 'Legends of Tomorrow', 'imdb': 'https://www.imdb.com/title/tt4532368/'}
# ....
```

TODO: caching

## Current state & Planned features

### Query language

```
from <source> {
  <selectors>
}
```

**Source** can be:

* [x] `"Page title"`
* [x] `category:"Category title"`
* [ ] `"Page title","Other page title"` (several pages at once)
* [ ] `geo:"<lat>, <lng>"`
* [ ] `prefix:"Page title prefix"`
* [ ] `search:"Search string"`
  * _Maybe several search types, as Wikipedia has several search APIs_

**Selectors** are CSS-alike selectors, `type.class[attr="value"][otherattr="othervalue"]`. Note, that **unlike CSS**, nesting (any `child` inside `parent`) is performed not with spaces (`parent child`), but with `parent >> child` or `parent { child }`.

* Singular selectors:
  * [x] regular CSS selectors, like `a` or `table.wikitable`
    * _Note again, that `selector nested_selector` is **not** supported, so you need to `li { a }` to say "all links inside the list items"_
  * [ ] `section`
    * [x] `section[heading="Section heading"]`: fetch everything inside section with the specified heading (full heading text must match);
    * [ ] `section`: all sections;
    * [ ] `section[level=3]`: all sections of particular level
    * [ ] more powerful `heading` value patterns would be supported (probably in CSS-alike manner: `heading^="Starts from"` and so on)
  * [ ] `text`
    * [x] `text["pattern"]`: part of the document matching pattern (Python's regexp); document's structure would be preserved, so you can nest CSS and other WikipediaQL selectors inside: `li >> text["^(.+?) as"] { a@href as "link" }`
    * [ ] `text`: without pattern specification, just selects entire text of the parent element;
    * [ ] pattern flags, like `text["pattern"i]` (case-insensitive)
    * [ ] handle inline images `alt` attribute as text
  * [ ] `text-group`: should be directly nested in `text` pattern, refers to capture group of the regexp; see first example in the README;
    * [x] `text-group[1]`: group by number
    * [ ] `text-group["name"]`: named groups
  * [ ] `sentence`
    * [x] `sentence["pattern"]`: find sentence where pattern matches (whole sentence is selected)
    * [ ] `sentence`: all sentences in the scope
    * [ ] pattern flags (same as for text)
    * [ ] _more suitable sentence tokenizer will be used, probably: currently we are relying on nltk, which is too powerful (and large dependency) for our simplistic needs_
  * [x] `page`: refers (from any scope) to entire current page; useful for re-nesting fetched data in a logical way, and to include metadata attributes in output (see below)
  * [ ] `<selector>@<attribute>`:
      * [x] `<css_selector>@<tag_attribute>`
        * [ ] expand URLs
      * [ ] `page@<page_attribute>`
        * [x] `title`
        * [ ] other
        * [ ] smart fetching metadata
      * [ ] as a free-standing selector (`@title` on the top level to fetch "current page's title" instead of `page@title`, and so on)
  * [ ] `infobox` and `infobox-*`: logical selectors for data from infoboxes (formalized data at the top right corner), something like `from "City name" { infobox >> infobox-value[field="Population"] }`
  * [ ] `wikitable` and `wikitable-*`: same for data tables: `from "City name" { section[heading="Climate"] >> wikitable >> wikitable-row["Average high"] }`
  * [ ] `hatnote` to fetch and process [Hatnotes](https://en.wikipedia.org/wiki/Wikipedia:Hatnote) (special links at the top of the page/section, saying "for more information, see [here]", "this page is about X, if you want Y, go [there]" and so on)
  * [ ] `:has`: like [CSS `:has` pseudo-class](https://developer.mozilla.org/en-US/docs/Web/CSS/:has) but support all the WikipediaQL selectors, so one might say `from category:"Marvel Cinematic Universe films" { :has(@category*="films") { ...work with pages... } }` to drop from the result-set pages of the [category](https://en.wikipedia.org/wiki/Category:Marvel_Cinematic_Universe_films) which aren't movies.
  * [ ] (?) `:primary` or something like that (maybe `:largest`), to select the most important thing in the scope (for example, `section[heading="Discography"] >> ul:primary` will probably fetch the list of albums, while the section might have other, smaller lists, like enumeration of studios where recordings were done)
  * _TBC on "as-good-examples-found" basis_
* Selector operations:
  * [x] sequence: `parent { children }` or `parent >> child`
  * [x] group: `{ selector1; selector2; selector3 }` fetch all the selectors in the result set
  * [ ] immediate child: `parent > child`; maybe (come good reasons) other CSS relations like `sibling1 + sibling2`
  * [ ] **follow link**: I am not sure about the syntax yet, but something like `section["Discography"] >> li >> a => { selectors working inside the fetched page }`, to allow expressing page navigation in a singular query
* Marking information to extract:
  * [x] extract unnamed data: every terminal selector puts extracted value in resultset (the resultset then will look like several nested arrays)
  * [x] `as "variablename"`: every terminal selector with associated name puts extracted value as `{"name": value}`; there are still some uncertainty on how it all should be structured, but mostly the right thing is done
  * [ ] `as :type` and `as "name":type` for typecasting values
    * [ ] (?) simpe types (`as "year":int`) maybe wouldn't be that necessary, as the conversion can be easily done in the client
    * [ ] `as :html` (as opposed to current "content text only" extraction) might be useful in many cases
    * [ ] converting a large section of document into composite type should shine. Things like `infobox as :hash` or `wikitable as :dataframe` will change usability of data extraction significantly

### Other features/problems

* **Speed** is not stellar now (roughly, a few seconds per page). This is due to a) `parse` API doesn't support batch-fetching pages, so each page, and b) this is unoptimized prototype (so parsing takes a lot more than it could). To fix this, we plan to implement:
  * [ ] Less naive page caching
  * [ ] Profiling and optimizations (like probably using naked `lxml` instead of `BeautifulSoup`, and simpler sentence tokenizer)
  * [ ] Support for async/parallel processing (as far as I can understand, _in Python_ async I/O would be the most useful optimization; but multi-trheaded selectors processing will bring no gain due to GIL?)
* [ ] More robust edge case handling is planned, like links to absent pages, redirects (including redirect to a middle of another page), disambiguation pages etc.
* [ ] Exposing HTTP client dependency to the client code, allowing request logging, custom caching strategies etc.
* Some potential farther-future features:
  * [ ] using other languages Wikipedias: nothing in WikipediaQL makes it bound to English Wikipedia only
  * [ ] (maybe?) other MediaWiki-based sites (like Wikvoyage, Wiktionary etc): more high-level selectors (like `infobox` and `wikitable`) would be irrelevant though, and may need a replacement with site-specific ones
  * [ ] (?) Request analyzer (e.g. prediction of efficience and number of requests)

## Rough near roadmap

* **0.0.2** links following + some low-hanging optimizations and enhancements
* **0.0.3** `infobox`, `wikitable` and related selectors
* **0.0.4** more Wikipedia API support (page metadata, page lists etc.)
* **0.1.0** efficiency & robustness of existing features
* **0.2.0** documentation and principal portability to other languages
* (maybe) online client-side demo, using [Pyodide](https://pyodide.org/en/stable/)?..

## FAQ

### Why not use [Wikidata](https://www.wikidata.org/) (or other structured Wikipedia-based data source, like [DBPedia](https://www.dbpedia.org/))?

Wikidata is a massive effort for representing Wikipedia in a computable form. But currently, it contains much less data than Wikipedia itself; and much less accessible for _investigatory_ data extraction (TODO: good examples!) While it gets improved constantly, I wanted to go from the other angle, and see how accessible we can make the Wikipedia itself, with all of its semi-structuredness.

## Why not fetch and parse page sources in Wikitext?

Some of similar projects (say, [wtf_wikipedia](https://github.com/spencermountain/wtf_wikipedia)) are working by fetching page source in Wikitext form, and parsing it for data extraction. This road looks pretty tempting (and for a several years I went it myself with the previous iteration: [infoboxer Ruby project](https://github.com/molybdenum-99/infoboxer)). The problem here is at the first sight, Wikitext is better structured: large chunks of data are represented by [templates](https://en.wikipedia.org/wiki/Wikipedia:Templates) like `{{Infobox; field=value, ...}}` so it really _seems_ like a better source for data extraction. There are two huge problems with this approach, though:

1. The list of the templates is infinite and unpredictable. While ten city-related pages would have `{{Infobox city` in a pretty similar form, the eleventh will have `{{Geobox capital` with all the different fields and conventions—but in HTML they would render to the similarly-looking `<table class="infobox"`. Or, some TV series will represent list of episodes with just a plain table markup, while the other will use sophisticated `{{Episode list` template. And it all might change with time (some spring cleanup replacing all the template names, or converting some regular text to template). The HTML version is _much_ more stable and predictable.
2. To library/QL user, having Wikitext&templates as the base would mean that writing queries requires intimate knowledge of Wikitext format and conventions, and frequently looking into page's source (via "Edit") to find out how something is represented in Wikitext. OTOH, HTML/CSS-based approach relies on widely known elements like headers, lists, links, tables, and simple relatable grouping objects, like sections and sentences. Most of it is unambiguously deduced by looking at the page in the browser, or, worst case, by "inspect element" (to know its particular class/id).

## License

MIT
