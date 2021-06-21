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
    DEFAULT_PARAMS = {
        'action': 'parse',
        'format': 'json',
        'disablelimitreport': True,
        'disableeditsection': True,
        'disabletoc': True
    }

    def __init__(self):
        self.parser = Parser()

    def get_page(self, title):
        filename = re.sub(r'[?\/&]', '-', title)
        path = self.CACHE_DIR.joinpath(f'{filename}.json')
        if not path.exists():
            response = requests.get(self.API_URI, params={'page': title, **self.DEFAULT_PARAMS})
            path.write_text(response.content.decode('utf-8'))

        data = json.loads(path.read_text())
        return fragment.Fragment.parse(data['parse']['text']['*'])

    def query(self, query_text):
        page, selector = self.parser.parse(query_text)
        return self.get_page(page).query(selector)
