import re

import pytest

from wikipedia_ql.fragment import Fragment
from wikipedia_ql.selectors import text, section, css, alt, page

def make_fragment(html, **kwargs):
    # Because fragment is Wikipedia-oriented and always looks for this div :shrug:
    return Fragment.parse(f'<div class="mw-parser-output">{html.strip()}</div>', **kwargs)

@pytest.fixture
def fragment():
    return make_fragment("""
        <h2>Section1</h2>
        <p><b>Text1</b></p>
        <ul>
            <li><a class="first">First</a></li>
            <li class="item"><a class="second" href="http://google.com">Second</a> text</li>
        </ul>
        <h2>Section2</h2>
        <p><b>Text2</b> Text3</p>
        """)

def test_fragment_query_simple(fragment):
    assert fragment.query(text(pattern='Fi.{3}')) == ['First']

def test_fragment_query_alt(fragment):
    assert fragment.query(alt(css(css_selector='a.second'), text(pattern='Fi.{3}'))) == ['Second', 'First']

def test_fragment_query_nested(fragment):
    assert fragment.query(
        section(heading='Section2',
            nested=css(css_selector='b', nested=text(pattern=r'Text\d'))
        )
    ) == ['Text2']

    assert fragment.query(
        text(pattern='Second text', nested=text(pattern='t.{3}'))
    ) == ['text']

def test_fragment_query_named(fragment):
    assert fragment.query(text(pattern='Fi.{3}').into('f')) == [{'f': 'First'}]

    assert fragment.query(alt(css(css_selector='a.second').into('a'), text(pattern='Fi.{3}').into('b'))) == \
        {'a': 'Second', 'b': 'First'}

    # section[heading=Section1] as "section" > ul as "list" > a as "link"
    assert fragment.query(
        section(heading='Section1', nested=css(css_selector='ul', nested=css(css_selector='a').into('link')).into('list')).into('section')
    ) == [{'section': [{'list': [{'link': 'First'}, {'link': 'Second'}]}]}]

    assert fragment.query(
        section(heading='Section1', nested=css(css_selector='ul', nested=css(css_selector='a'))).into('section')
    ) == [{'section': ['First', 'Second']}]

def test_fragment_query_attr(fragment):
    assert fragment.query(css(css_selector='a.second', attribute='href')) == ['http://google.com']
    assert fragment.query(css(css_selector='a.second', attribute='href').into('foo')) == [{'foo': 'http://google.com'}]

def test_fragment_query_attr_page():
    fragment = make_fragment('', metadata={'title': 'Bear'})

    assert fragment.query(page(attribute='title')) == ['Bear']
