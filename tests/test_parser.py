import pytest

from wikipedia_ql.selectors import text, text_group, sentence, section, css, alt, page, attr
from wikipedia_ql.parser import Parser

@pytest.fixture
def parser():
    return Parser()

def test_parse_selectors_base(parser):
    assert parser.parse_selector('text["foo"]') == text(pattern='foo')
    assert parser.parse_selector('text') == text()
    assert parser.parse_selector('sentence["foo"]') == sentence(pattern='foo')
    assert parser.parse_selector('sentence') == sentence()
    assert parser.parse_selector('section[heading="foo"]') == section(heading='foo')
    assert parser.parse_selector('section[heading="foo"][level="3"]') == section(heading='foo', level='3')
    assert parser.parse_selector('section') == section()

    assert parser.parse_selector('text-group[3]') == text_group(group_id=3)
    assert parser.parse_selector('text-group["good"]') == text_group(group_id='good')

    assert parser.parse_selector('page') == page()

def test_parse_selectors_named(parser):
    assert parser.parse_selector('text["foo"] as "bar"') == text(pattern='foo', name="bar")

def test_parse_selectors_nested(parser):
    assert parser.parse_selector('text["foo"] { text-group[1] }') == \
        text(pattern='foo', nested=text_group(group_id=1))
    assert parser.parse_selector('text["foo"] >> text-group[1]') == \
        text(pattern='foo', nested=text_group(group_id=1))

    assert parser.parse_selector('text["foo"] { text-group[1]; text-group[2] }') == \
        text(pattern='foo', nested=alt(text_group(group_id=1), text_group(group_id=2)))

def test_parse_selectors_attribute(parser):
    assert parser.parse_selector('img@src') == css(css_selector='img', nested=attr(attr_name='src'))
    assert parser.parse_selector('img@src as "path"') == css(css_selector='img', nested=attr(attr_name='src', name='path'))

    assert parser.parse_selector('@src as "path"') == attr(attr_name='src', name='path')

def test_full_query(parser):
    assert parser.parse('from "Nomadland (film)" { text["Rotten"] }') == \
        ("page", "Nomadland (film)", text(pattern="Rotten"))

    assert parser.parse('from category:"Marvel Cinematic Universe films" { text["Rotten"] }') == \
        ("category", "Marvel Cinematic Universe films", text(pattern="Rotten"))
