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

def sel(text):
    return Parser().parse_selector(text)

def test_fragment_query_simple(fragment):
    assert fragment.query(sel('text:matches("Fi.{3}")')) == ['First']

def test_fragment_query_alt(fragment):
    assert fragment.query(sel('{ a.second; text:matches("Fi.{3}") }')) == ['Second', 'First']

def test_fragment_query_nested(fragment):
    assert fragment.query(sel(r'section[heading="Section2"] >> b >> text:matches("Text\d")')) == ['Text2']

    assert fragment.query(sel(r'section[heading="Section2"] >> b >> text')) == ['Text2']

    assert fragment.query(sel('text:matches("Second text") >> text:matches("t.{3}")')) == ['text']

    # Text of the entire fragment
    assert fragment.query(sel(r'section[heading="Section2"] >> text')) == ["Section2\n\nText2 Text3"]

def test_fragment_query_named(fragment):
    assert fragment.query(sel('text:matches("Fi.{3}") as "f"')) == [{'f': 'First'}]

    assert fragment.query(sel('{ a.second as "a"; text:matches("Fi.{3}") as "b" }')) == \
        {'a': 'Second', 'b': 'First'}

    #
    assert fragment.query(
        sel('section[heading="Section1"] as "section" >> ul as "list" >> a as "link"')
    ) == [{'section': [{'list': [{'link': 'First'}, {'link': 'Second'}]}]}]

    assert fragment.query(sel('section[heading="Section1"] as "section" >> ul >> a')) == \
        [{'section': ['First', 'Second']}]

def test_fragment_query_attr(fragment):
    assert fragment.query(sel('a.second@href')) == ['http://google.com']
    assert fragment.query(sel('a.second@href as "foo"')) == [{'foo': 'http://google.com'}]

    assert fragment.query(sel('a.second@nonexistent as "foo"')) == []

def test_fragment_query_attr_page():
    fragment = make_fragment('', metadata={'title': 'Bear'})

    assert fragment.query(sel('@title')) == ['Bear']

def test_fragment_query_merging(fragment):
    assert fragment.query(sel('ul >> { @id as "id"; li >> { text as "value" } }')) == \
        [{'id': 'list'}, {'value': 'First'}, {'value': 'Second text'}]

    assert fragment.query(sel('ul >> { @id as "id"; li >> { @id as "id"; text as "value" } }')) == \
        [{'id': 'list'}, {'id': 'li1', 'value': 'First'}, {'id': 'li2', 'value': 'Second text'}]

