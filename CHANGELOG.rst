Changelog
=========

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
