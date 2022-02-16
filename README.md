# WikipediaQL: querying structured data from Wikipedia

**WikipediaQL** is an _experimental query language_ and Python library for querying structured data from Wikipedia. It looks like this:

```
$ wikipedia_ql --page "Guardians of the Galaxy (film)" \
    '{
      page@title as "title";
      section[heading="Cast"] as "cast" >> {
          li >> text:matches("^(.+?) as (.+?):") >> {
              text-group[group=1] as "actor";
              text-group[group=2] as "character"
          }
      };
      section[heading="Critical response"] >> {
          sentence:contains("Rotten Tomatoes") as "RT ratings" >> {
              text:matches("\d+%") as "percent";
              text:matches("(\d+) (critic|review)") >> text-group[group=1] as "reviews";
              text:matches("[\d.]+/10") as "overall"
          }
      }
    }'

RT ratings:
  overall: 7.8/10
  percent: 92%
  reviews: '334'
cast:
- actor: Chris Pratt
  character: Peter Quill / Star-Lord
- actor: Zoe Saldaña
  character: Gamora
- actor: Dave Bautista
  character: Drax the Destroyer
- actor: Vin Diesel
  character: Groot
- actor: Bradley Cooper
  character: Rocket CREDITED ONLY AS "Rocket" PER OFFICIAL SYNOPSIS!
- actor: Lee Pace
  character: Ronan the Accuser
- actor: Michael Rooker
  character: Yondu Udonta
- actor: Karen Gillan
  character: Nebula
- actor: Djimon Hounsou
  character: Korath
- actor: John C. Reilly
  character: Rhomann Dey
- actor: Glenn Close
  character: Irani Rael
- actor: Benicio del Toro
  character: Taneleer Tivan / The Collector
title: Guardians of the Galaxy (film)
```

### How?

WikipediaQL-the-tool does roughly this:

* Parses query in WikipediaQL-the-language;
* Uses [MediaWiki API](https://en.wikipedia.org/w/api.php) to fetch pages' metadata;
* Uses [Parsoid API](https://www.mediawiki.org/wiki/Parsoid/API) to fetch each page's content semantic HTML;
* Applies selectors from the query to page to extract structured data.

**The WikipediaQL development is covered in ongoing series of articles:** (newest first)

* Jan'22: [Wikipedia and irregular data: how much can you fetch in one expression?](https://zverok.substack.com/p/wikipedia-and-irregular-data-how)
* Dec'21: [Wikipedia as the data source: taming the irregular](https://zverok.substack.com/p/wikipediaql-1)
* Oct'21: [Why Wikipedia matters, and how to make sense of it (programmatically)](https://zverok.substack.com/p/wikipedia)

[Subscribe to follow](https://zverok.substack.com/)

### Why?

> “Sometimes magic is just someone spending more time on something than anyone else might reasonably expect.” — Raymond Joseph Teller

Wikipedia is the most important open knowledge project: basically, the "table of contents" of all the human data. While it might be incomplete or misleading in details, the amount of data is incredible, and its organization makes all the data accessible to humans.

OTOH, the data is semi-structured and quite hard to extract automatically. This project is an experiment in making this data accessible to machines—or, rather, to humans with programming languages. The main goal is to develop an easy to use and memorize, unambiguous and powerful query language and support it by the reference implementation.

_See [FAQ](#faq) below for justifications of parsing Wikipedia instead of just using already formalized Wikidata (and of parsing HTML instead of Wikipedia markup)._

## Usage

`$ pip install wikipedia_ql`

```
$ wikipedia_ql --page "Page name" query_text
# or
$ wikipedia_ql query_text_with_page
```

Usage as Python library:

```python
from wikipedia_ql import media_wiki

wikipedia = media_wiki.Wikipedia()

data = wikipedia.query(query_text)
```

Full WikipediaQL query looks like this:
```
from <source> {
  <selectors>
}
```

When using `--page` parameter to the executable, you need only to pass selectors in the query text.

_Source_ is Wikipedia article name, or category name, or (in the future) other ways of specifying multiple pages. _Selectors_ are similar to CSS; they are nested in one another with `selector { other; selectors }`, or (shortcut) `selector >> other_selector`. All terminal selectors (e.g., doesn't having others nested) produce values in the output; the value can be associated with a name with `as "valuename"`.

See below for a list of selectors and sources currently supported and the future ones.

### Examples

Simple query for some info from the page:

```
$ wikipedia_ql --page "Pink Floyd" \
    'section[heading="Discography"] >> li >> {
        a as "title";
        text:matches("\((.+)\)") >> text-group[group=1] as "year";
    }'

- title: The Piper at the Gates of Dawn
  year: '1967'
- title: A Saucerful of Secrets
  year: '1968'
- title: More
  year: '1969'
- title: Ummagumma
  year: '1969'
#     ...and so on...
```

Multi-page query from pages of some category (only from inside Python):
```python
query = r'''
from category:"2020s American time travel television series" {
    page@title as "title";
    section[heading="External links"] >> {
      li >> text:matches("^(.+?) at IMDb") >> text-group[group=1] >> a@href as "imdb"
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

Navigating through pages in one query (note the `->` which means "perform subquery in the page by link"):
```
$ wikipedia_ql --page Björk \
    'section[heading="Discography"] >> li >> a -> {
        page@title as "title";
        .infobox-image >> img >> @src as "cover"
    }'

- cover: https://upload.wikimedia.org/wikipedia/en/thumb/7/77/Bj%C3%B6rk-Debut-1993.png/220px-Bj%C3%B6rk-Debut-1993.png
  title: Debut (Björk album)
- cover: https://upload.wikimedia.org/wikipedia/en/thumb/3/3f/Bjork_Post.png/220px-Bjork_Post.png
  title: Post (Björk album)
- cover: https://upload.wikimedia.org/wikipedia/en/thumb/a/af/Bj%C3%B6rk_-_Homogenic.png/220px-Bj%C3%B6rk_-_Homogenic.png
  title: Homogenic
...
```

As the page source should be fetched from Wikipedia every time, and it can be a major slowdown when experimenting, `wikipedia_ql` implements super-naive caching:

```py
wikipedia = media_wiki.Wikipedia(cache_folder='some/folder')
wikipedia.query('from "Pink Floyd" { page@title }') # fetches page from Wikipedia, then runs query
wikipedia.query('from "Pink Floyd" { page@title }') # gets the cached by prev.request contents from some/folder
```

_(**Caution!** as it was said, for now, the cache is super-naive: it just stores page contents in the specified folder forever. You might delete it from the cache manually, though: there are just `PageName.meta.json` and `PageName.json` files.)_

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

**Selectors** are CSS-alike selectors, `type.class[attr="value"][otherattr="othervalue"]`. Note, that **unlike CSS**, nesting (any `child` inside `parent`) is performed not with spaces (`parent child`), but with `parent >> child`.

* Singular selectors:
  * [x] regular CSS selectors, like `a` or `table.wikitable`
    * _Note again, that `selector nested_selector` is **not** supported, so you need to `li >> a` to say "all links inside the list items"_
  * [ ] `section`
    * [x] `section[heading="Section heading"]`: fetch everything inside section with the specified heading (full heading text must match);
    * [x] `section:first` (useful to fetch article intro)
    * [ ] `section`: all sections;
    * [ ] `section[level=3]`: all sections of particular level
    * [ ] more powerful `heading` value patterns would be supported (probably in CSS-alike manner: `heading^="Starts from"` and so on)
  * [ ] `text`
    * [x] `text:matches("pattern")`: part of the document matching pattern (Python's regexp); document's structure would be preserved, so you can nest CSS and other WikipediaQL selectors inside: `li >> text:matches("^(.+?) as") >> a@href as "link"`
    * [x] `text`: without pattern specification, just selects the entire text of the parent element;
    * [ ] pattern flags, like `text:imatches("pattern")` (case-insensitive)
    * [ ] handle inline images `alt` attribute as text
  * [x] `text-group`: should be directly nested in `text` pattern, refers to capture a group of the regexp; see the first example in the README;
    * [x] `text-group[group=1]`: group by number
    * [x] `text-group[group="name"]`: named groups
  * [ ] `sentence`
    * [x] `sentence:contains("pattern")`: find sentence where pattern matches (whole sentence is selected)
    * [x] `sentence`: all sentences in the scope
    * [x] `sentence:first`
    * [ ] other CSS pseudo-selectors for `sentence`
    * [ ] pattern flags (same as for text)
    * [ ] _more suitable sentence tokenizer will be used, probably: currently we are relying on nltk, which is too powerful (and large dependency) for our simplistic needs_
  * [x] `page`: refers (from any scope) to the entire current page; useful for re-nesting fetched data in a logical way and to include metadata attributes in output (see below)
  * [ ] `<selector>@<attribute>`:
      * [x] `<css_selector>@<tag_attribute>`
        * [x] expand URLs
      * [ ] `page@<page_attribute>`
        * [x] `title`
        * [ ] other
        * [ ] smart fetching metadata
      * [x] as a free-standing selector (`@title` on the top level to fetch "current page's title" instead of `page@title`, and so on)
  * [x] `table-data` for data tables: `from "Kharkiv" { section[heading="Climate"] >> table >> table-data >> tr[title^="Average high"] >> td[column="Jan"] }`; see [docs](https://github.com/zverok/wikipedia_ql/blob/main/docs/Tables.md)
  * [x] _infoboxes_ are covered with the same `table-data` quasi-selector, see [showcase](https://github.com/zverok/wikipedia_ql/blob/main/docs/showcase/Infoboxes.md)
  * [ ] `hatnote` to fetch and process [Hatnotes](https://en.wikipedia.org/wiki/Wikipedia:Hatnote) (special links at the top of the page/section, saying "for more information, see [here]", "this page is about X, if you want Y, go [there]" and so on)
  * [ ] `:has`: like [CSS `:has` pseudo-class](https://developer.mozilla.org/en-US/docs/Web/CSS/:has) but support all the WikipediaQL selectors, so one might say `from category:"Marvel Cinematic Universe films" { :has(@category*="films") { ...work with pages... } }` to drop from the result-set pages of the [category](https://en.wikipedia.org/wiki/Category:Marvel_Cinematic_Universe_films) which aren't movies.
  * [ ] (?) `:primary` or something like that (maybe `:largest`), to select the most important thing in the scope (for example, `section[heading="Discography"] >> ul:primary` will probably fetch the list of albums, while the section might have other, smaller lists, like the enumeration of studios where recordings were done)
  * _TBC on "as-good-examples-found" basis_
* Selector operations:
  * [x] sequence: `parent >> child`
  * [x] group: `{ selector1; selector2; selector3 }` fetch all the selectors in the result set
  * [ ] immediate child: `parent > child`; maybe (come good reasons) other CSS relations like `sibling1 + sibling2`
  * [x] **follow link**: `section["Discography"] >> li >> a -> { selectors working inside the fetched page }`, to allow expressing page navigation in a singular query
* Marking information to extract:
  * [x] extract unnamed data: every terminal selector puts extracted value in resultset (the resultset then will look like several nested arrays)
  * [x] `as "variablename"`: every terminal selector with associated name puts extracted value as `{"name": value}`; there is still some uncertainty on how it all should be structured, but mostly the right thing is done
  * [ ] `as :type` and `as "name":type` for typecasting values
    * [ ] (?) simpe types (`as "year":int`) maybe wouldn't be that necessary, as the conversion can be easily done in the client
    * [ ] `as :html` (as opposed to current "content text only" extraction) might be useful in many cases
    * [ ] converting a large section of the document into composite type should shine. Things like `infobox as :hash` or `wikitable as :dataframe` will change the usability of data extraction significantly
* Other query language features:
  * [ ] comments (probably `// text`, as `#` can be a start of valid CSS selector)
  * [ ] (maybe?) named/reusable subquires

### Other features/problems

* **Speed** is not stellar now (roughly, a few seconds per page). This is due to a) Parsoid API doesn't support batch-fetching pages, so each page is fetched with a separate HTTP request, and b) this is an unoptimized prototype (so parsing takes a lot more than it could). To fix this, we plan to implement:
  * [ ] Less naive page caching
  * [ ] Profiling and optimizations (like probably using naked `lxml` instead of `BeautifulSoup`, and simpler sentence tokenizer)
  * [ ] Support for async/parallel processing (as far as I can understand, _in Python_ async I/O would be the most useful optimization; but multi-threaded selectors processing will bring no gain due to GIL?)
* [ ] More robust edge case handling is planned, like links to absent pages, redirects (including redirecting to the middle of another page), disambiguation pages, etc.
* [ ] Exposing HTTP client dependency to the client code, allowing request logging, custom caching strategies, etc.
* Some potential far-future features:
  * [ ] using other languages Wikipedias: nothing in WikipediaQL makes it bound to English Wikipedia only
  * [ ] (maybe?) other MediaWiki-based sites (like Wikvoyage, Wiktionary, etc.): more high-level selectors (like `infobox` and `wikitable`) would be irrelevant though, and may need a replacement with site-specific ones
  * [ ] (?) Request analyzer (e.g., prediction of efficiency and number of requests)

## Roadmap

* **0.0.7** more Wikipedia API support (page metadata, page lists etc.)
* **0.1.0** efficiency & robustness of existing features
* **0.2.0** documentation and principal portability to other languages
* (maybe) online client-side demo, using [Pyodide](https://pyodide.org/en/stable/)?..

## FAQ

### Why not use [Wikidata](https://www.wikidata.org/) (or other structured Wikipedia-based data source, like [DBPedia](https://www.dbpedia.org/))?

Wikidata is a massive effort to represent Wikipedia in a computable form. But currently, it contains much less data than Wikipedia itself; and much less accessible for _investigatory_ data extraction (TODO: good examples!) While it gets improved constantly, I wanted to tackle the problem from a different angle and see how accessible we can make Wikipedia itself, with all of its semi-structuredness.

### Why not fetch and parse page sources in Wikitext?

Some similar projects (say, [wtf_wikipedia](https://github.com/spencermountain/wtf_wikipedia)) work by fetching page source in Wikitext form, and parsing it for data extraction. This road looks pretty tempting (and for several years, I went it myself with the previous iteration: [infoboxer Ruby project](https://github.com/molybdenum-99/infoboxer)). The problem here is that at first sight, Wikitext is better structured: large chunks of data are represented by [templates](https://en.wikipedia.org/wiki/Wikipedia:Templates) like `{{Infobox; field=value, ...}}` so it really _seems_ like a better source for data extraction. There are two huge problems with this approach, though:

1. The list of templates is infinite and unpredictable. While ten city-related pages would have `{{Infobox city` in a pretty similar form, the eleventh will have `{{Geobox capital` with all the different fields and conventions—but in HTML they would render to the similarly-looking `<table class="infobox"`. Or, some TV series will represent a list of episodes with just a plain table markup, while the other will use a sophisticated `{{Episode list` template. And it all might change with time (some spring cleanup replacing all the template names or converting some regular text to a template). The HTML version is _much_ more stable and predictable.
2. To library/QL users, having Wikitext&templates as the base would mean that writing queries requires intimate knowledge of Wikitext format and conventions and frequently looking at the page's source (via "Edit") to find out how something is represented in Wikitext. OTOH, HTML/CSS-based approach relies on widely known elements like headers, lists, links, tables, and simple grouping objects, like sections and sentences. Most of them are unambiguously deduced by looking at the page in the browser or, in the worst case, by "inspect element" (to find out its particular class/id).

## Prior work

This project is the N-th iteration of the ideas about providing "common knowledge" in a computable form. Most of the previous work was done in Ruby and centered around **[Reality](https://github.com/molybdenum-99/reality)** project; and included, amongst other things, **[Infoboxer](https://github.com/molybdenum-99/infoboxer)** the Wikipedia parser/high-level client, and [MediaWiktory](https://github.com/molybdenum-99/mediawiktory) the idiomatic low-level MediaWiki client. Some of that work still to be incorporated into WikipediaQL and sister projects.

That project was once inspired by ["integrated knowledge"](https://www.wolfram.com/knowledgebase/) feature of Wolfram Language, I've talked about it (and other topics leading to this project) in a [Twitter thread](https://twitter.com/zverok/status/1397651367909629953) (yes).

The WikipediaQL syntax seems to be subconsciously inspired by [qsx](https://github.com/danburzo/qsx) selectors language. (By _subconsciously_ I mean I don't remember thinking "Oh, I should do something similar", but the day I've published WikipediQL, [past.codes](https://past.codes/) service have reminded me I starred `qsx` in December 2020. I started to think about WikipediaQL syntax in June 2021, but there are striking similarities, so it should be related to some indirect inspiration by that project.)

## License

MIT
