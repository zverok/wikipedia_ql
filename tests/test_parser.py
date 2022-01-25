import pytest

from wikipedia_ql.selectors import text, text_group, sentence, section, css, alt, page, attr, table_data
from wikipedia_ql.parser import Parser

@pytest.fixture
def parser():
    return Parser()

def test_parse_selectors_base(parser):
    assert parser.parse_selector('text:matches("foo")') == text(pattern='foo')
    assert parser.parse_selector('text') == text()
    assert parser.parse_selector('sentence:contains("foo")') == sentence(pattern='foo')
    assert parser.parse_selector('sentence') == sentence()
    assert parser.parse_selector('section[heading="foo"]') == section(heading='foo')
    assert parser.parse_selector('section[heading="foo"][level="3"]') == section(heading='foo', level='3')
    assert parser.parse_selector('section') == section()

    assert parser.parse_selector('text-group[group=3]') == text_group(group=3)
    assert parser.parse_selector('text-group[group="good"]') == text_group(group='good')

    assert parser.parse_selector('page') == page()

    assert parser.parse_selector('table-data') == table_data()
    assert parser.parse_selector('table-data:force-row-headers(1)') == table_data(force_row_headers=1)

def test_parse_selectors_named(parser):
    assert parser.parse_selector('text:matches("foo") as "bar"') == text(pattern='foo', name="bar")

def test_parse_selectors_nested(parser):
    assert parser.parse_selector('text:matches("foo") >> { text-group[number=1] }') == \
        text(pattern='foo', nested=text_group(number=1))
    assert parser.parse_selector('text:matches("foo") >> text-group[number=1]') == \
        text(pattern='foo', nested=text_group(number=1))

    assert parser.parse_selector('text:matches("foo") >> { text-group[number=1]; text-group[number=2] }') == \
        text(pattern='foo', nested=alt(text_group(number=1), text_group(number=2)))

def test_parse_selectors_attribute(parser):
    assert parser.parse_selector('img@src') == css(css_selector='img', nested=attr(attr_name='src'))
    assert parser.parse_selector('img@src as "path"') == css(css_selector='img', nested=attr(attr_name='src', name='path'))

    assert parser.parse_selector('@src as "path"') == attr(attr_name='src', name='path')

def test_full_query(parser):
    assert parser.parse('from "Nomadland (film)" { text:matches("Rotten") }') == \
        ("page", "Nomadland (film)", text(pattern="Rotten"))

    assert parser.parse('from category:"Marvel Cinematic Universe films" { text:matches("Rotten") }') == \
        ("category", "Marvel Cinematic Universe films", text(pattern="Rotten"))
