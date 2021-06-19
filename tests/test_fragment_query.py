import re

import pytest

from wikipedia_ql.fragment import Fragment
from wikipedia_ql.selectors import text, section, css, alt

def make_fragment(html):
    # Because fragment is Wikipedia-oriented and always looks for this div :shrug:
    return Fragment.parse(f'<div class="mw-parser-output">{html.strip()}</div>')

@pytest.fixture
def fragment():
    return make_fragment("""
        <h2>Section1</h2>
        <p><b>Text1</b></p>
        <ul>
            <li><a class="first">First</a></li>
            <li class="item"><a class="second">Second</a> text</li>
        </ul>
        <h2>Section2</h2>
        <p><b>Text2</b> Text3</p>
        """)

def test_fragment_query_simple(fragment):
    assert fragment.query(text('Fi.{3}')) == ['First']

def test_fragment_query_alt(fragment):
    assert fragment.query(alt(css('a.second'), text('Fi.{3}'))) == ['Second', 'First']

def test_fragment_query_nested(fragment):
    assert fragment.query(section('Section2', nested=css('b', nested=text(r'Text\d')))) == ['Text2']

def test_fragment_query_named(fragment):
    assert fragment.query(text('Fi.{3}').into('f')) == [{'f': 'First'}]

    assert fragment.query(alt(css('a.second').into('a'), text('Fi.{3}').into('b'))) == \
        [{'a': 'Second'}, {'b': 'First'}]

    assert fragment.query(
        section('Section1', nested=css('ul', nested=css('a').into('link')).into('list')).into('section')
    ) == [{'section': [{'list': [{'link': 'First'}, {'link': 'Second'}]}]}]

    assert fragment.query(
        section('Section1', nested=css('ul', nested=css('a'))).into('section')
    ) == [{'section': ['First', 'Second']}]
