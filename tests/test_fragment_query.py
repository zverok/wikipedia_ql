import re

import pytest

from wikipedia_ql.fragment import Fragment
from wikipedia_ql.selectors import text, section, css, alt, page, attr
from wikipedia_ql.parser import Parser

def make_fragment(html, **kwargs):
    # Because fragment is Wikipedia-oriented and always looks for this div :shrug:
    return Fragment.parse(f'<div class="mw-parser-output">{html.strip()}</div>', **kwargs)

@pytest.fixture
def fragment():
    return make_fragment("""
        <section>
            <h2>Section1</h2>
            <p><b>Text1</b></p>
            <ul id="list">
                <li id="li1"><a class="first">First</a></li>
                <li id="li2" class="item"><a class="second" href="http://google.com">Second</a> text</li>
            </ul>
        </section>
        <section>
            <h2>Section2</h2>
            <p><b>Text2</b> Text3</p>
        </section>
        """)

@pytest.fixture
def parser():
    return Parser()

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
        section(heading='Section2',
            nested=css(css_selector='b', nested=text())
        )
    ) == ['Text2']

    assert fragment.query(
        text(pattern='Second text', nested=text(pattern='t.{3}'))
    ) == ['text']

    assert fragment.query(
        section(heading='Section2', nested=text()) # Text of the entire fragment
    ) == ["Section2\n\nText2 Text3"]

def test_fragment_query_named(fragment):
    assert fragment.query(text(pattern='Fi.{3}', name='f')) == [{'f': 'First'}]

    assert fragment.query(alt(css(css_selector='a.second', name='a'), text(pattern='Fi.{3}', name='b'))) == \
        {'a': 'Second', 'b': 'First'}

    # section[heading=Section1] as "section" > ul as "list" > a as "link"
    assert fragment.query(
        section(heading='Section1', nested=css(css_selector='ul', nested=css(css_selector='a', name='link'), name='list'), name='section')
    ) == [{'section': [{'list': [{'link': 'First'}, {'link': 'Second'}]}]}]

    assert fragment.query(
        section(heading='Section1', nested=css(css_selector='ul', nested=css(css_selector='a')), name='section')
    ) == [{'section': ['First', 'Second']}]

def test_fragment_query_attr(fragment):
    assert fragment.query(css(css_selector='a.second', nested=attr(attr_name='href'))) == ['http://google.com']
    assert fragment.query(css(css_selector='a.second', nested=attr(attr_name='href', name='foo'))) == [{'foo': 'http://google.com'}]

    assert fragment.query(css(css_selector='a.second', nested=attr(attr_name='nonexistent', name='foo'))) == []

def test_fragment_query_attr_page():
    fragment = make_fragment('', metadata={'title': 'Bear'})

    assert fragment.query(attr(attr_name='title')) == ['Bear']

def test_fragment_query_merging(fragment, parser):
    assert fragment.query(parser.parse_selector('ul >> { @id as "id"; li >> { text as "value" } }')) == \
        [{'id': 'list'}, {'value': 'First'}, {'value': 'Second text'}]

    assert fragment.query(parser.parse_selector('ul >> { @id as "id"; li >> { @id as "id"; text as "value" } }')) == \
        [{'id': 'list'}, {'id': 'li1', 'value': 'First'}, {'id': 'li2', 'value': 'Second text'}]
