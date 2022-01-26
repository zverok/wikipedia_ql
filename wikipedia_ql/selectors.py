import re
import bs4
import soupsieve

from dataclasses import dataclass, field
from typing import Any, Union, Dict, List, Optional

import wikipedia_ql.tables

@dataclass
class selector_base:
    attrs: Dict = field(default_factory=dict)
    name: Optional[str] = None
    nested: Optional[Union['selector_base', 'alt']] = None

    def __init__(self, *, nested=None, name=None, **attrs):
        self.nested = nested
        self.name = name

        self.attrs = {key: val for key, val in attrs.items() if val != None}

    def __repr__(self):
        return type(self).__name__ + ''.join(f'[{name}={value!r}]' for name, value in self.attrs.items()) + \
            (f' as {self.name!r}' if self.name else '') + \
            (f' {{ {self.nested!r} }}' if self.nested else '')

class text(selector_base):
    @property
    def re(self):
        pat = self.attrs.get('pattern')
        if pat:
            return re.compile(pat, re.MULTILINE | re.DOTALL)

    def __call__(self, fragment):
        if self.re:
            yield from (fragment.slice(*m.span(0), context={'text': m}) for m in self.re.finditer(fragment.text))
        else:
            yield fragment

class text_group(selector_base):
    @property
    def group(self):
        return self.attrs['group']

    def __call__(self, page):
        if not 'text' in page.context:
            raise ValueError('text-group is only allowed after text')

        match = page.context['text']

        # TODO: fail if no group id? or just give the first?
        if isinstance(self.group, int) and len(match.groups()) < self.group or \
            isinstance(self.group, str) and not self.group in match.groupdict():
            return

        s, e = match.span(self.group)
        yield page.slice(s - match.start(), e - match.start())

class sentence(selector_base):
    @property
    def re(self):
        pat = self.attrs.get('pattern')
        if pat:
            return re.compile(pat)

    def __call__(self, fragment):
        yield from (
            fragment.slice(start, end)
            for (text, start, end) in fragment.sentences
            if not self.re or self.re.search(text)
        )

class section(selector_base):
    @property
    def heading(self):
        return self.attrs['heading']

    # TODO: Level as an optional filter; No filters at all (select all sections)
    def __call__(self, fragment):
        for section in fragment.soup.select('section'):
            # TODO: allow to fetch first section by special id, like /intro or something
            if section.get('data-mw-section-id') == '0':
                continue

            heading = section.select_one('h2, h3, h4')
            if self.heading in heading.get_text():
                yield fragment.slice_tags([*section.children])

    # This is more generic section fetching algo (relying on Wikipedia page structure with just hX at top level);
    # it doesn't work with Parsoid output (which made things easier), but might be useful if we'll parse other
    # MediaWiki instances not providing Parsoid API; that's why it left here but unused.
    def __old_section(self):
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
        # Handles the corner case when the current fragment's top node is the match, e.g.
        #   from ...<a>foo</a>...
        #    text["foo"] >> a
        # FIXME: Isn't there a way to ask bs to do this?..
        if soupsieve.match(self.css_selector, page.soup):
            yield page
        yield from (page.slice_tags([node]) for node in page.soup.select(self.css_selector))

# Quasi-fragment returned by attr() selector: it is only good for getting text out of it
@dataclass
class fragment_attribute:
    text: str

class attr(selector_base):
    @property
    def attr_name(self):
        return self.attrs['attr_name']

    def __call__(self, fragment):
        value = None

        # TODO:
        # * available attr depends on fragment's type
        # * not raise on not found attr
        if fragment.type == 'page':
            value = fragment.metadata.get(self.attr_name)
        elif self.attr_name.startswith('style-'):
            style = fragment.soup.get('style')
            if style:
                prop = self.attr_name.replace('style-', '')
                match = re.search(f'{prop}:\\s*(.+?)(;|$)', style)
                if match:
                    value = match.group(1)
        else:
            value = fragment.soup.get(self.attr_name)
            if value and (self.attr_name == 'href' or self.attr_name == 'src') and fragment.media_wiki:
                value = fragment.media_wiki.absoluteize_uri(value)

        if value:
            yield fragment_attribute(value)


class page(selector_base):
    def __call__(self, page):
        yield page.page

class follow_link(selector_base):
    def __call__(self, fragment):
        # TODO: Make it async (and have a queue of pages to fetch)?
        page_names = filter(None, [fragment.media_wiki.page_name_from_uri(href) for href in fragment.query('a@href')])
        yield from fragment.media_wiki.get_pages(page_names)

class table_data(selector_base):
    @property
    def force_row_headers(self):
        return self.attrs.get('force_row_headers')

    def __call__(self, fragment):
        if fragment.type == 'page' or fragment.soup.name != 'table':
            raise ValueError('table-data should be nested in a table directly')

        table = wikipedia_ql.tables.reflow(fragment.soup, force_row_headers=self.force_row_headers)
        yield fragment.slice_tags([table])

@dataclass
class alt:
    selectors: List[Union['selector_base', 'alt']]

    def __init__(self, *selectors):
        self.selectors = selectors

    def __call__(self, page):
        yield from (fragment for selector in self.selectors for fragment in selector(page))

    def __repr__(self):
        return '; '.join(sel.__repr__() for sel in self.selectors)
