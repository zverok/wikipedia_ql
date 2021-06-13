import json
from pathlib import Path
import re

import requests

from wikipedia_ql import fragment

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
        pass

    def get_page(self, title):
        filename = re.sub(r'[?\/&]', '-', title)
        path = self.CACHE_DIR.joinpath(f'{filename}.json')
        if not path.exists():
            response = requests.get(self.API_URI, params={'page': title, **self.DEFAULT_PARAMS})
            path.write_text(response.content.decode('utf-8'))

        data = json.loads(path.read_text())
        return fragment.Fragment.parse(data['parse']['text']['*'])
