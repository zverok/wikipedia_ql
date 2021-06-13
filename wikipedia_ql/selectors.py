import re
import bs4

class text:
    def __init__(self, re):
        self.re = re

    def __call__(self, page):
        yield from (m.span(0) for m in self.re.finditer(page.text))

class sentence:
    def __init__(self, pattern):
        self.pattern = pattern

    def __call__(self, page):
        def matches(text):
            if isinstance(self.pattern, re.Pattern):
                return self.pattern.search(text)
            elif isinstance(self.pattern, str):
                return self.pattern in text

        yield from ((sent.start_char, sent.end_char) for sent in page.sentences if matches(sent.text))

class section:
    # TODO: Level as an optional filter
    def __init__(self, text):
        self.text = text

    def __call__(self, page):
        first = None
        last = None
        # FIXME: Currently only yields non-intersecting ones
        for child in page.soup.children:
            if first:
                if isinstance(child, bs4.element.Tag) and child.name.startswith('h') and child.name <= first.name:
                    yield (first.textstart, last.textend)
                    first = None
                    last = None
                else:
                    last = child
            else:
                if isinstance(child, bs4.element.Tag) and child.name.startswith('h') and self.text in child.get_text():
                    first = child

class css:
    def __init__(self, selector):
        self.selector = selector

    def __call__(self, page):
        yield from ((node.textstart, node.textend) for node in page.soup.select(self.selector))

class all:
    def __init__(self, *selectors):
        self.selectors = selectors

    def __call__(self, page):
        yield from (slice for selector in self.selectors for slice in selector(page))
