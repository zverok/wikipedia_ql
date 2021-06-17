import re
import bs4

class selector_base:
    def __init__(self):
        self.name = None

    def into(self, name):
        self.name = name
        return self

    def is_named(self):
        return not self.name is None

class text(selector_base):
    def __init__(self, text):
        super().__init__()
        self.text = text
        self.re = re.compile(text)

    def __call__(self, page):
        yield from (page.slice(*m.span(0)) for m in self.re.finditer(page.text))

    def __repr__(self):
        return f"text[text=~{self.text!r}]"

class sentence(selector_base):
    def __init__(self, pattern):
        super().__init__()
        self.pattern = pattern

    def __call__(self, page):
        def matches(text):
            if isinstance(self.pattern, re.Pattern):
                return self.pattern.search(text)
            elif isinstance(self.pattern, str):
                return self.pattern in text

        yield from ((sent.start_char, sent.end_char) for sent in page.sentences if matches(sent.text))

    def __repr__(self):
        return f"sentence[{self.pattern}]"

class section(selector_base):
    # TODO: Level as an optional filter; No filters at all (select all sections)
    def __init__(self, text):
        super().__init__()
        self.text = text

    def __call__(self, page):
        first = None
        selected = []
        # FIXME: Currently only yields non-intersecting ones
        for child in page.soup.children:
            if first:
                if isinstance(child, bs4.element.Tag) and child.name.startswith('h') and child.name <= first.name:
                    yield page.slice_tags(selected)
                    first = None
                    selected = []
                else:
                    selected.append(child)
            else:
                if isinstance(child, bs4.element.Tag) and child.name.startswith('h') and self.text in child.get_text():
                    first = child
                    selected = [child]

    def __repr__(self):
        return f"section[{self.text}]"

class css(selector_base):
    def __init__(self, css_selector):
        super().__init__()
        self.css_selector = css_selector

    def __call__(self, page):
        yield from ((node.textstart, node.textend) for node in page.soup.select(self.css_selector))

    def __repr__(self):
        return f"css[{self.css_selector}]"

class all(selector_base):
    def __init__(self, *selectors):
        super().__init__()
        self.selectors = selectors

    def __call__(self, page):
        yield from (slice for selector in self.selectors for slice in selector(page))

    def is_named(self):
        return super().is_named() or any(sel.is_named() for sel in self.selectors)

    def __repr__(self):
        return 'all(' + ';'.join(sel.__repr__() for sel in self.selectors) + ')'
