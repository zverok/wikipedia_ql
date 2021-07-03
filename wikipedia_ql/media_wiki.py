import json
from pathlib import Path
import re

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
        metadata = [*json.loads(response.content.decode('utf-8'))['query']['pages'].values()]

        yield from (self._parse_page(m) for m in metadata)

    def _parse_page(self, metadata):
        real_title = metadata['title']

        text_data = self.cache_get(real_title)
        if not text_data:
            response = requests.get(self.API_URI, params={'page': real_title, **self.PARSE_PARAMS})
            text_data = json.loads(response.content.decode('utf-8'))
            self.cache_put(real_title, json_data=text_data)

        return fragment.Fragment.parse(text_data['parse']['text']['*'], metadata=metadata)

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

