import pytest

from wikipedia_ql.selectors import text, text_slice, sentence, section, css, alt
from wikipedia_ql.parser import Parser

@pytest.fixture
def parser():
    return Parser()

def test_parse_selectors_base(parser):
    assert parser.parse_selector('text["foo"]') == text(pattern='foo')
    assert parser.parse_selector('sentence["foo"]') == sentence(pattern='foo')
    assert parser.parse_selector('sentence') == sentence()
    assert parser.parse_selector('section[heading="foo"]') == section(heading='foo')
    assert parser.parse_selector('section[heading="foo"][level="3"]') == section(heading='foo', level='3')
    assert parser.parse_selector('section') == section()

    assert parser.parse_selector('text-slice[3]') == text_slice(group_id='3')
    assert parser.parse_selector('text-slice["good"]') == text_slice(group_id='good')

def test_parse_selectors_named(parser):
    assert parser.parse_selector('text["foo"] as "bar"') == text(pattern='foo').into("bar")

def test_parse_selectors_nested(parser):
    assert parser.parse_selector('text["foo"] { text-slice[1] }') == text(pattern='foo', nested=text_slice(group_id="1"))
    assert parser.parse_selector('text["foo"] >> text-slice[1]') == text(pattern='foo', nested=text_slice(group_id="1"))

    assert parser.parse_selector('text["foo"] { text-slice[1]; text-slice[2] }') == \
        text(pattern='foo', nested=alt(text_slice(group_id="1"), text_slice(group_id="2")))

def test_full_query(parser):
    assert parser.parse('from "Nomadland (film)" { text["Rotten"] }') == \
        ("Nomadland (film)", text(pattern="Rotten"))
