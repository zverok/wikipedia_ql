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

    def __repr__(self):
        res = self.repr_impl()
        if self.name:
            res += f" as {self.name!r}"
        if self.nested:
            res += f" {{ {self.nested!r} }}"
        return res

class text(selector_base):
    def __init__(self, text, nested=None):
        super().__init__(nested=nested)
        self.text = text
        self.re = re.compile(text)

    def __call__(self, page):
        yield from (page.slice(*m.span(0)) for m in self.re.finditer(page.text))

    def repr_impl(self):
        return f"text[{self.text!r}]"

class sentence(selector_base):
    def __init__(self, pattern, nested=None):
        super().__init__(nested=nested)
        self.pattern_text = pattern
        self.pattern = re.compile(pattern)

    def __call__(self, page):
        yield from (page.slice(start, end) for (text, start, end) in page.sentences if self.pattern.search(text))

    def repr_impl(self):
        return f"sentence[{self.pattern_text!r}]"

class section(selector_base):
    # TODO: Level as an optional filter; No filters at all (select all sections)
    def __init__(self, heading, nested=None):
        super().__init__(nested=nested)
        self.heading = heading

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
                if isinstance(child, bs4.element.Tag) and child.name.startswith('h') and self.heading in child.get_text():
                    first = child
                    selected = [child]

        if selected:
            yield page.slice_tags(selected)

    def repr_impl(self):
        return f"section[heading={self.heading!r}]"

class css(selector_base):
    def __init__(self, css_selector, nested=None):
        super().__init__(nested=nested)
        self.css_selector = css_selector

    def __call__(self, page):
        yield from (page.slice_tags([node]) for node in page.soup.select(self.css_selector))

    def repr_impl(self):
        return f"css[{self.css_selector!r}]"

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

    def repr_impl(self):
        return ';'.join(sel.repr_impl() for sel in self.selectors)
