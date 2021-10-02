import json
from pathlib import Path
import re
import urllib.parse

import requests

from lark import Lark
import lark

from wikipedia_ql import fragment
from wikipedia_ql.parser import Parser

class Wikipedia:
    API_URI = 'https://en.wikipedia.org/w/api.php'
    PARSE_PARAMS = {
        'action': 'parse',
        'format': 'json',
        'disablelimitreport': True,
        'disableeditsection': True,
        'disabletoc': True
    }
    QUERY_PARAMS = {
        'action': 'query',
        'format': 'json',
        'redirects': 1
    }

    def __init__(self, cache_folder=None):
        self.parser = Parser()
        if cache_folder:
            self.cache_folder = Path(cache_folder)
            self.cache_folder.mkdir(exist_ok=True)
        else:
            self.cache_folder = None

    def query(self, query_text):
        type, page, selector = self.parser.parse(query_text)
        if type == 'page':
            return self.get_page(page).query(selector)
        elif type == 'category':
            return [fragment.query(selector) for fragment in self.get_category(page)]

    def iquery(self, query_text):
        type, page, selector = self.parser.parse(query_text)
        if type == 'page':
            yield self.get_page(page).query(selector)
        elif type == 'category':
            yield from (fragment.query(selector) for fragment in self.get_category(page))

    def get_page(self, title):
        metadata = self.cache_get(title + '.props')
        if not metadata:
            response = requests.get(self.API_URI, params={'titles': title, **self.QUERY_PARAMS})
            metadata = [*json.loads(response.content.decode('utf-8'))['query']['pages'].values()][0]
            self.cache_put(title + '.props', json_data=metadata)

        # TODO: save metadata to cache under the real title, too!
        return self._parse_page(metadata)

    def get_pages(self, titles):
        # TODO: We can multi-fetch all pages metadata with one query; but before that we'll check if
        # some of it is in the cache already
        return filter(None, [self.get_page(title) for title in titles])

    def get_category(self, category):
        response = requests.get(self.API_URI,
            params={
                'generator': 'categorymembers',
                'gcmtitle': f'Category:{category}',
                'gcmnamespace': 0,
                'gcmlimit': 100,
                **self.QUERY_PARAMS
            }
        )
        # TODO: Continue if there is more than 100 pages in category
        # TODO: Distinguish nested category; go recursively by separate parameter
        metadata = [*json.loads(response.content.decode('utf-8'))['query']['pages'].values()]

        yield from (self._parse_page(m) for m in metadata)

    def _parse_page(self, metadata):
        if 'missing' in metadata:
            return None

        real_title = metadata['title']

        text_data = self.cache_get(real_title)
        if not text_data:
            response = requests.get(self.API_URI, params={'page': real_title, **self.PARSE_PARAMS})
            text_data = json.loads(response.content.decode('utf-8'))
            self.cache_put(real_title, json_data=text_data)

        return fragment.Fragment.parse(text_data['parse']['text']['*'], metadata=metadata, media_wiki=self)

    def cache_get(self, key):
        if not self.cache_folder:
            return

        key = re.sub(r'[?\/&]', '-', key)
        path = self.cache_folder.joinpath(f'{key}.json')
        if path.exists():
            return json.loads(path.read_text())

    def cache_put(self, key, *, text=None, json_data=None):
        if not self.cache_folder:
            return

        key = re.sub(r'[?\/&]', '-', key)
        path = self.cache_folder.joinpath(f'{key}.json')
        if json_data:
            text = json.dumps(json_data)
        path.write_text(text)

    # URI services:
    def absoluteize_uri(self, uri):
        parsed = urllib.parse.urlparse(uri)
        if not parsed.scheme:
            parsed = parsed._replace(scheme='https') # TODO: Might want to take the scheme of the real Wiki we used
        if not parsed.netloc:
            parsed = parsed._replace(netloc='en.wikipedia.org') # TODO: take the real Wiki domain we are using

        return parsed.geturl()

    def page_name_from_uri(self, uri):
        if not uri.startswith('https://en.wikipedia.org/wiki/'): # TODO: Same as above, take real wiki URL!
            return None

        return urllib.parse.unquote(uri.replace('https://en.wikipedia.org/wiki/', ''))
