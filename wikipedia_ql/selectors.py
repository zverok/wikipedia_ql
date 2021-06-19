import re
import bs4

class selector_base:
    def __init__(self, nested=None):
        self.name = None
        self.nested = nested

    def into(self, name):
        self.name = name
        return self

    def is_named(self):
        return not self.name is None

class text(selector_base):
    def __init__(self, text, nested=None):
        super().__init__(nested=nested)
        self.text = text
        self.re = re.compile(text)

    def __call__(self, page):
        yield from (page.slice(*m.span(0)) for m in self.re.finditer(page.text))

    def __repr__(self):
        return f"text[text=~{self.text!r}]"

class sentence(selector_base):
    def __init__(self, pattern, nested=None):
        super().__init__(nested=nested)
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
    def __init__(self, text, nested=None):
        super().__init__(nested=nested)
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

        if selected:
            yield page.slice_tags(selected)

    def __repr__(self):
        return f"section[{self.text}]"

class css(selector_base):
    def __init__(self, css_selector, nested=None):
        super().__init__(nested=nested)
        self.css_selector = css_selector

    def __call__(self, page):
        yield from (page.slice_tags([node]) for node in page.soup.select(self.css_selector))

    def __repr__(self):
        return f"css[{self.css_selector}]"

class alt(selector_base):
    def __init__(self, *selectors, nested=None):
        super().__init__(nested=nested)
        self.selectors = selectors

    def __call__(self, page):
        yield from (fragment for selector in self.selectors for fragment in selector(page))

    def is_named(self):
        return super().is_named() or any(sel.is_named() for sel in self.selectors)

    def into(self, name):
        raise RuntimeError("alt selector can't be named")

    def __repr__(self):
        return 'alt(' + ';'.join(sel.__repr__() for sel in self.selectors) + ')'
