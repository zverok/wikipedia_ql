import re
import bs4

from dataclasses import dataclass, field
from typing import Any, Union, Dict, Optional

@dataclass
class selector_base:
    attrs: Dict = field(default_factory=dict)
    name: Optional[str] = None
    nested: Optional[Union['selector_base', 'alt']] = None

    def __init__(self, *, nested=None, **attrs):
        self.nested = nested
        self.name = None
        self.attrs = attrs

    def into(self, name):
        self.name = name
        return self

    def __repr__(self):
        return type(self).__name__ + ''.join(f'[{name}={value!r}]' for name, value in self.attrs.items()) + \
            (f' as {self.name!r}' if self.name else '') + \
            (f' {{ {self.nested!r} }}' if self.nested else '')

class text(selector_base):
    @property
    def re(self):
        return re.compile(self.attrs['pattern'])

    def __call__(self, page):
        yield from (page.slice(*m.span(0), context={'text': m}) for m in self.re.finditer(page.text))

class text_slice(selector_base):
    @property
    def group_id(self):
        return self.attrs['group_id']

    def __call__(self, page):
        if not 'text' in page.context:
            raise ValueError('text-slice is only allowed after text')

        match = page.context['text']

        if len(match.groups()) < self.group_id:
            return

        s, e = match.span(self.group_id)
        yield page.slice(s - match.start(), e - match.start())

class sentence(selector_base):
    @property
    def re(self):
        return re.compile(self.attrs['pattern'])

    def __call__(self, page):
        yield from (page.slice(start, end) for (text, start, end) in page.sentences if self.re.search(text))

class section(selector_base):
    @property
    def heading(self):
        return self.attrs['heading']

    # TODO: Level as an optional filter; No filters at all (select all sections)
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

class css(selector_base):
    @property
    def css_selector(self):
        return self.attrs['css_selector']

    def __call__(self, page):
        yield from (page.slice_tags([node]) for node in page.soup.select(self.css_selector))

class alt:
    def __init__(self, *selectors):
        self.selectors = selectors

    def __call__(self, page):
        yield from (fragment for selector in self.selectors for fragment in selector(page))

    def __repr__(self):
        return '; '.join(sel.__repr__() for sel in self.selectors)
