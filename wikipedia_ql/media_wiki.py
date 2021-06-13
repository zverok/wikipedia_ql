import json
from pathlib import Path
import re

import requests

from lark import Lark
import lark

from wikipedia_ql import fragment
from wikipedia_ql import selectors as s

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
        self.query_parser = Lark(open('wikipedia_ql/wikipedia_ql.lark').read(), start="query", propagate_positions=True)

    def get_page(self, title):
        filename = re.sub(r'[?\/&]', '-', title)
        path = self.CACHE_DIR.joinpath(f'{filename}.json')
        if not path.exists():
            response = requests.get(self.API_URI, params={'page': title, **self.DEFAULT_PARAMS})
            path.write_text(response.content.decode('utf-8'))

        data = json.loads(path.read_text())
        return fragment.Fragment.parse(data['parse']['text']['*'])

    def query(self, query_text):
        parsed = self.query_parser.parse(query_text)
        interpreter = QueryInterpreter(query_text)
        interpreter.visit(parsed)
        return interpreter.run(self)

class QueryInterpreter(lark.visitors.Interpreter):
    def __init__(self, query):
        super().__init__()

        self.query_str = query

        self.page = None
        self.selectors_list = None

    def query(self, tree):
        self.page = eval(tree.children[0].children[0])

        self.selectors_list = self.visit(tree.children[1])

    def nested_selectors(self, tree):
        return [nested for selector in tree.children for nested in self.visit(selector)]

    def selector(self, tree):
        sel = self.visit(tree.children[0])
        nested = []
        into = None
        if len(tree.children) > 1:
            if tree.children[1].data == 'as_named':
                into = eval(tree.children[1].children[0])
                if len(tree.children) > 2:
                    nested = self.visit(tree.children[2])
            else:
                nested = self.visit(tree.children[1])

        if into:
            sel.into(into)

        return [sel, *nested]

    def selectors(self, tree):
        return [s.all(*(sel for child in tree.children for sel in self.visit(child)))]

    def section_selector(self, tree):
        return s.section(eval(tree.children[0]))

    def sentence_selector(self, tree):
        return s.sentence(eval(tree.children[0]))

    def text_selector(self, tree):
        return s.text(re.compile(str(tree.children[0])[1:-1]))

    def css_selector(self, tree):
        source = self.query_str[tree.meta.start_pos:tree.meta.end_pos]
        return s.css(source)

    def run(self, w):
        # print(self.selectors_list)
        return w.get_page(self.page).query(*self.selectors_list)
