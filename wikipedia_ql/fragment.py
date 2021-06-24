import copy
import re
import json
import bs4
from bs4 import BeautifulSoup
import nltk
import nltk.data

import wikipedia_ql

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
    def parse(cls, html, *, metadata=None):
        soup = BeautifulSoup(html, 'html.parser').select('.mw-parser-output')[0]
        for sel in cls.REMOVE:
            for tag in soup.select(sel):
                tag.extract()

        return cls(soup, metadata=metadata, type='page')

    def __init__(self, soup, text=None, text_tree=None, *, context=None, parent=None, metadata=None, type=None):
        self.context = context or {}
        self.soup = soup
        self.parent = parent
        self.metadata = metadata
        self.type = type

        def build_tree(node):
            start = len(self.text)
            if isinstance(node, bs4.element.NavigableString):
                self.text += str(node)
                children = []
            else:
                children = [build_tree(child) for child in node.children]
                if node.name in ['p', 'div', 'ul', 'ol', 'li', 'table', 'tbody', 'tr', 'br', 'h2', 'h3', 'h4', 'h5']:
                    self.text += "\n"
                elif node.name in ['td', 'th']:
                    self.text += " "
                else:
                    pass

            end = len(self.text)

            return (start, end, children)

        if text is None:
            self.text = ''
            self.text_tree = build_tree(soup)
        else:
            self.text = text
            self.text_tree = text_tree

        # nlp = English()
        # nlp.add_pipe(nlp.create_pipe("sentencizer"))
        # doc = nlp(self.text)
        # # FIXME: Newlines are ignored this way! Sentences include tables and hNs and whatnot
        # self.sentences = [*doc.sents]

        sent_detector = nltk.data.load('tokenizers/punkt/english.pickle')
        self.sentences = []
        start = 0
        for line in self.text.split("\n"):
            for s, e in sent_detector.span_tokenize(line):
                self.sentences.append((line[s:e], start + s, start +e))
            start += len(line) + 1 # \n

        # print(self.sentences)

    @property
    def page(self):
        return self if self.parent is None else self.parent.page

    def slice(self, start, end, *, context=None):
        def make_slice(node, text_tree):
            s, e, children = text_tree
            if e < start or s > end:
                return None

            if s >= start and e <= end:
                return (copy.copy(node), text_tree)

            s1 = start - s if s < start else 0
            e1 = end - e if e > end else None

            new_s = s + s1
            new_e = e + e1 + 1 if e1 else e

            if new_e and new_e <= new_s + 1: # empty
                return None

            if isinstance(node, bs4.element.NavigableString):
                text = str(node)[s1:e1]
                return (bs4.element.NavigableString(text), (new_s, new_e, []))

            sliced_children = list(filter(
                None,
                [make_slice(child, tchild) for child, tchild in zip(node.children, children)]
            ))
            node_children = [n for n, t in sliced_children]
            tree_children = [t for n, t in sliced_children]

            if s > start or e < end:
                new_node = copy.copy(node)
                new_node.clear()
                new_node.extend(node_children)
            elif len(node_children) == 1:
                new_node = node_children[0]
                tree_children = tree_children[0][2]
            else:
                new_node = BeautifulSoup().new_tag('span')
                new_node.extend(node_children)

            return (new_node, (new_s, new_e, tree_children))

        tstart, tend = start, end
        start += self.text_tree[0]
        end += self.text_tree[0]

        res_node, res_tree = make_slice(self.soup, self.text_tree)

        return Fragment(res_node, self.text[tstart:tend], res_tree, context=context, parent=self)

    def slice_tags(self, tags):
        if len(tags) == 1:
            return Fragment(tags[0], parent=self)
        else:
            new_node = BeautifulSoup().new_tag('div')
            new_node.extend([copy.copy(tag) for tag in tags])
            return Fragment(new_node, parent=self)

    def select(self, selector):
        fragments = Fragments(self._select(selector))
        if selector.nested:
            return fragments.select(selector.nested)
        else:
            return fragments

    def _select(self, selector):
        return [*selector(self)]

    def query(self, selector):
        return query(self, selector)

    def attribute(self, name):
        # TODO:
        # * available attr depends on fragment's type
        if self.type == 'page':
            return self.metadata.get(name)
        else:
            return self.soup[name]

class Fragments:
    def __init__(self, items):
        self.items = items

    def select(self, selector):
        fragments = Fragments([nested for item in self.items for nested in item._select(selector)])

        if selector.nested:
            return fragments.select(selector.nested)
        else:
            return fragments

    def query(self, selector):
        return query(self, selector)

    def _select(self, selector):
        return [nested for item in self.items for nested in item._select(selector)]

    def __iter__(self):
        return self.items.__iter__()

# FIXME: Base class queriable?..
def query(subject, selector):
    if isinstance(selector, wikipedia_ql.selectors.alt):
        return flatten_and_merge([subject.query(sel) for sel in selector.selectors])

    fragments = Fragments(subject._select(selector))

    if selector.name:
        if selector.nested:
            return [{selector.name: fragment.query(selector.nested)} for fragment in fragments.items]
        else:
            return [{selector.name: query_value(fragment, selector)} for fragment in fragments.items]
    else:
        if selector.nested:
            return flatten([fragment.query(selector.nested) for fragment in fragments.items])
        else:
            return [query_value(fragment, selector) for fragment in fragments.items]

def query_value(fragment, selector):
    if selector.attribute:
        return fragment.attribute(selector.attribute)
    else:
        return fragment.text

def flatten(items):
    return [subitem for item in items for subitem in (flatten(item) if isinstance(item, list) else [item])]

def flatten_and_merge(items):
    res = flatten(items)
    if all(isinstance(item, dict) for item in res):
        return merge(*res)
    else:
        return res

def merge(*dicts):
    result = {}
    for dict in dicts:
        result.update(dict)
    return result
