Changelog
=========

master - unreleased
-------------------

0.0.6 - 2022-02-16
------------------

- (internal) restructure custom WikipediaQL selectors internally into having "attrs" and "functions" (CSS pseudo-selectors), paving the way for more consistency;
- add ``sentence:first`` and ``section:first`` functions;
- improve default YAML output formatting;
- improve ``table-data`` quasi-selector behavior to handle mid-table full-row ``th`` (it gets attached as a prefix to subsequent rows).

0.0.5 - 2022-01-26
------------------

- Add executable script ``wikipedia_ql`` to run from command-line!
- Streamline and simplify the language.

  - There is now only one way of nesting: ``selector1 >> selector2``, ``{}`` is left only for grouping purposes;
  - Follow the CSS selectors intuition: ``text["pattern"]`` is now ``text:matches("pattern")``, ``sentence["pattern"]`` is ``sentence:contains("pattern")``, and ``text-group[1]`` is ``text-group[group=1]``

- A number of internal bugfixes and simplifications
- The further development is covered in near-the-realtime on my `Substack <https://zverok.substack.com/>`_


0.0.4 - 2021-11-30
------------------

- The **largest highlight** is ``table-data`` quasi-selector/filter, allowing to regularize tables and fetch data by columns/rows. See `Tables.md <https://github.com/zverok/wikipedia_ql/blob/main/docs/Tables.md>`_ for details;
- Improve results joining to be (a bit) more reasonable and allowing to fetch multiple hashes;
- Add support for fetching style attributes (naive!) with selectors like ``@style-background``;
- Support ``$=`` and ``^=`` attribute operators.


0.0.3 - 2021-10-08
------------------

The **largest highlight** of the release is links following: now you can go through pages graph in a single query!

.. code-block:: python

  from wikipedia_ql import media_wiki

  wikipedia = media_wiki.Wikipedia()

  pprint(wikipedia.query(r'''
      from "The Wachowskis" {
          section[heading="Films"] {
              table >> tr >> td:nth-child(2) {
                  a -> {
                      @title as "film";
                      section[heading="Critical response"]
                          >> sentence["Rotten Tomatoes"]
                          >> text["\d+%"] as "rotten-tomatoes";
                  }
              }
          }
      }
  '''))

This prints::

  [{'film': 'Assassins (1995 film)'},
   {'film': 'Bound (1996 film)', 'rotten-tomatoes': '89%'},
   {'film': 'The Matrix', 'rotten-tomatoes': '88%'},
   {'film': 'The Matrix Revisited'},
   {'film': 'The Animatrix'},
   {'film': 'V for Vendetta (film)', 'rotten-tomatoes': '73%'},
   {'film': 'The Invasion (film)'},
   {'film': 'Speed Racer (film)', 'rotten-tomatoes': '41%'},
   {'film': 'Ninja Assassin', 'rotten-tomatoes': '26%'},
   {'film': 'Cloud Atlas (film)', 'rotten-tomatoes': '66%'},
   {'film': 'Jupiter Ascending', 'rotten-tomatoes': '27%'},
   {'film': 'The Matrix Resurrections'}]

*(Yeah, not all movies are there... Table parsing is still to be enhanced)*

Other changes in query language:

- ``text`` without pattern (the text of entire element);
- ``text-group["group name"]`` named groups from text patterns;
- ``sentence`` without pattern (all sentences in the scope)
- standalone ``@attribute`` (attribute of the current selected element);
- for ``@href`` and ``img@src`` attributes URLs are now expanded to fully-qualified ones.

Changes to HTTP query engine:

- Using Parsoid API instead of default Wikipedia api.php to fetch HTML content — `#2 <https://github.com/zverok/wikipedia_ql/issues/2>`_;
- Providing sensible User-Agent string (and allow library user to rewrite it) — `#1 <https://github.com/zverok/wikipedia_ql/issues/1>`_.

0.0.2 - 2021-07-05
------------------

The release that actually works :)

0.0.1 - 2021-07-03
------------------

Initial release
