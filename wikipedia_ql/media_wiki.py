import json
from pathlib import Path
import re

import requests

from lark import Lark
import lark

from wikipedia_ql import fragment
from wikipedia_ql.parser import Parser

class Wikipedia:
    CACHE_DIR = Path('wikipedia/cache')
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

    def __init__(self):
        self.parser = Parser()

    def query(self, query_text):
        page, selector = self.parser.parse(query_text)
        return self.get_page(page).query(selector)

    def get_page(self, title):
        metadata = self.cache_get(title + '.props')
        if not metadata:
            response = requests.get(self.API_URI, params={'titles': title, **self.QUERY_PARAMS})
            metadata = [*json.loads(response.content.decode('utf-8'))['query']['pages'].values()][0]
            self.cache_put(title + '.props', json_data=metadata)

        real_title = metadata['title']
        # TODO: save metadata to cache under the real title, too!

        text_data = self.cache_get(title)
        if not text_data:
            response = requests.get(self.API_URI, params={'page': real_title, **self.PARSE_PARAMS})
            text_data = json.loads(response.content.decode('utf-8'))
            self.cache_put(title, json_data=text_data)

        return fragment.Fragment.parse(text_data['parse']['text']['*'], metadata=metadata)

    def cache_get(self, key):
        key = re.sub(r'[?\/&]', '-', key)
        path = self.CACHE_DIR.joinpath(f'{key}.json')
        if path.exists():
            return json.loads(path.read_text())

    def cache_put(self, key, *, text=None, json_data=None):
        key = re.sub(r'[?\/&]', '-', key)
        path = self.CACHE_DIR.joinpath(f'{key}.json')
        if json_data:
            text = json.dumps(json_data)
        path.write_text(text)

