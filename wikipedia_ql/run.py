import sys
from optparse import OptionParser
from pprint import pprint

import yaml
import json

import wikipedia_ql

def run():
    # TODO: Link to cheatsheet
    parser = OptionParser('Usage: %prog [options] query')
    parser.add_option("-p", "--page", dest="page",
                      help=r'''Wikipedia page name to query. If absent, query should have form `from "Page Name" { ... }`''')
    parser.add_option("-o", "--output-format", dest="output_format", default='yaml',
                      help='One of "yaml" (default), "json" or "pprint" (python pretty-print).')

    # TODO: cache folder
    # TODO: --time
    # TODO: force-cache-update

    options, args = parser.parse_args()
    if len(args) != 1:
      parser.print_help()
      exit()

    query = args[0]

    wikipedia = wikipedia_ql.media_wiki.Wikipedia(cache_folder='tmp/cache/')

    if options.page:
        result = wikipedia.query(query, page=options.page)
    else:
        result = wikipedia.query(query)

    print()

    if options.output_format == 'yaml':
      print(yaml.safe_dump(result, allow_unicode=True, width=1000, default_style='>'))
    elif options.output_format == 'json':
      print(json.dumps(result, ensure_ascii=False))
    else:
      pprint(result)
