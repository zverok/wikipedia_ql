import copy
import re
import json
import bs4
from spacy.lang.en import English
from bs4 import BeautifulSoup

class Fragment:
    REMOVE = [
        '#toc',
        '.mw-editsection',
        'sup.reference',
        'div.reflist',
        'style'
    ]

    @classmethod
    def from_json(cls, data):
        return cls.parse(data['parse']['text']['*'])

    @classmethod
    def parse(cls, html):
        soup = BeautifulSoup(html, 'html.parser').select('.mw-parser-output')[0]
        for sel in cls.REMOVE:
            for tag in soup.select(sel):
                tag.extract()

        return cls(soup)

    def __init__(self, soup):
        self.soup = soup
        self.text = ''
        def attach_to_text(node):
            node.textstart = len(self.text)

            if isinstance(node, bs4.element.NavigableString):
                self.text += str(node)
            else:
                for child in node.children:
                    attach_to_text(child)
                if node.name in ['p', 'div', 'ul', 'ol', 'li', 'table', 'tbody', 'tr', 'br', 'h2', 'h3', 'h4', 'h5']:
                    self.text += "\n"
                elif node.name in ['td', 'th']:
                    self.text += " "
                else:
                    pass
                    # print(node.name)

            node.textend = len(self.text)

        for child in soup.children:
            attach_to_text(child)

        nlp = English()
        nlp.add_pipe(nlp.create_pipe("sentencizer"))
        doc = nlp(self.text)
        # FIXME: Newlines are ignored this way! Sentences include tables and hNs and whatnot
        self.sentences = [*doc.sents]

    def slice(self, start, end):
        def filter_children(node):
            if isinstance(node, bs4.element.NavigableString):
                s = start - node.textstart if node.textstart < start else 0
                e = end - node.textend if node.textend > end else -1
                text = str(node)[s:e]
                node.replace_with(text)
                return

            for child in [*node.children]:
                if child.textend < start or child.textstart > end:
                    child.extract()
                elif child.textstart < start or child.textend > end:
                    filter_children(child)
                else:
                    # Entirely inside the range
                    pass

        def copy_pos(from_node, to_node):
            to_node.textstart = from_node.textstart
            to_node.textend = from_node.textend

            if isinstance(to_node, bs4.element.Tag):
                for from_c, to_c in zip(from_node.children, to_node.children):
                    copy_pos(from_c, to_c)

        res = copy.copy(self.soup)
        for from_child, to_child in zip(self.soup.children, res.children):
            copy_pos(from_child, to_child)

        filter_children(res)

        return Fragment(res)

    def select(self, selector, *selectors):
        fragments = Fragments(self._select(selector))
        if selectors:
            return fragments.select(*selectors)
        else:
            return fragments

    def _select(self, selector):
        return [self.slice(f, t) for f, t in selector(self)]

    def query(self, selector, *selectors):
        fragments = Fragments(self._select(selector))

        return query(fragments, selector, selectors)

class Fragments:
    def __init__(self, items):
        self.items = items

    def select(self, selector, *selectors):
        fragments = Fragments([nested for item in self.items for nested in item._select(selector)])

        if selectors:
            return fragments.select(*selectors)
        else:
            return fragments

    def query(self, selector, *selectors):
        fragments = Fragments([nested for item in self.items for nested in item._select(selector)])

        return query(fragments, selector, selectors)

def query(fragments, selector, selectors):
    if selector.name:
        if selectors:
            return [{selector.name: fragment.query(*selectors)} for fragment in fragments.items]
        else:
            return [{selector.name: fragment.text} for fragment in fragments.items]
    else:
        if selectors:
            return [fragment.query(*selectors)]
        else:
            return [fragment.text for fragment in fragments.items]
