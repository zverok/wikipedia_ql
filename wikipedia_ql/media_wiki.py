import json
from pathlib import Path
import re
import urllib.parse

import requests

from lark import Lark
import lark

from wikipedia_ql import fragment
from wikipedia_ql.parser import Parser

# TODO: Include version: wikipedia_ql/{version}
DEFAULT_UA = 'wikipedia_ql (https://github.com/zverok/wikipedia_ql; zverok.offline@gmail.com)'

class Wikipedia:
    API_URI = 'https://en.wikipedia.org/w/api.php'
    PARSOID_API_URI = 'https://en.wikipedia.org/api/rest_v1/page/html/'
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

    def __init__(self, cache_folder=None, user_agent=DEFAULT_UA):
        self.parser = Parser()
        if cache_folder:
            self.cache_folder = Path(cache_folder)
            self.cache_folder.mkdir(exist_ok=True, parents=True)
        else:
            self.cache_folder = None

        self.user_agent = user_agent

    def query(self, query_text, page=None):
        if page:
            type = 'page'
            selector = self.parser.parse_selector(query_text)
        else:
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
            response = self.__query_get(titles=title)
            metadata = [*json.loads(response.content.decode('utf-8'))['query']['pages'].values()][0]
            self.cache_put(title + '.props', json_data=metadata)

        # TODO: save metadata to cache under the real title, too!
        return self._parse_page(metadata)

    def get_pages(self, titles):
        # TODO: We can multi-fetch all pages metadata with one query; but before that we'll check if
        # some of it is in the cache already
        return filter(None, [self.get_page(title) for title in titles])

    def get_category(self, category):
        response = self.__query_get(
            generator = 'categorymembers',
            gcmtitle = f'Category:{category}',
            gcmnamespace = 0,
            gcmlimit = 100
        )
        # TODO: Continue if there is more than 100 pages in category
        # TODO: Distinguish nested category; go recursively by separate parameter
        metadata = [*json.loads(response.content.decode('utf-8'))['query']['pages'].values()]

        yield from (self._parse_page(m) for m in metadata)

    def _parse_page(self, metadata):
        if 'missing' in metadata:
            return None

        real_title = metadata['title']

        text_data = self.cache_get(real_title, format='html')
        if not text_data:
            response = self.__page_get(real_title)
            text_data = response.content.decode('utf-8')
            self.cache_put(real_title, text=text_data, format='html')

        return fragment.Fragment.parse(text_data, metadata=metadata, media_wiki=self)

    def cache_get(self, key, *, format='json'):
        if not self.cache_folder:
            return

        key = re.sub(r'[?\/&]', '-', key)
        path = self.cache_folder.joinpath(f'{key}.{format}')
        if path.exists():
            content = path.read_text()
            if format == 'json':
                return json.loads(content)
            else:
                return content

    def cache_put(self, key, *, text=None, json_data=None, format='json'):
        if not self.cache_folder:
            return

        key = re.sub(r'[?\/&]', '-', key)
        path = self.cache_folder.joinpath(f'{key}.{format}')
        if json_data:
            text = json.dumps(json_data)
        path.write_text(text)

    # URI services:
    def absoluteize_uri(self, uri):
        parsed = urllib.parse.urlparse(uri)
        if not parsed.netloc:
            # TODO: the real URL base should be taken from header > base@href of parsoid output!
            parsed = urllib.parse.urlparse(urllib.parse.urljoin('//en.wikipedia.org/wiki/', uri))
        if not parsed.scheme:
            parsed = parsed._replace(scheme='https') # TODO: Might want to take the scheme of the real Wiki we used

        return parsed.geturl()

    def page_name_from_uri(self, uri):
        if not uri.startswith('https://en.wikipedia.org/wiki/'): # TODO: Same as above, take real wiki URL!
            return None

        return urllib.parse.unquote(uri.replace('https://en.wikipedia.org/wiki/', ''))

    # Real fetching
    def __query_get(self, **params):
        return requests.get(
            self.API_URI,
            params={**params, **self.QUERY_PARAMS},
            headers={'User-Agent': self.user_agent})

    def __page_get(self, title):
        return requests.get(
            self.PARSOID_API_URI + urllib.parse.quote(title.replace(' ', '_')),
            headers={'User-Agent': self.user_agent})
