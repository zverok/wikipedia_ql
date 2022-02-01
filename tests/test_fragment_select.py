import re
import pytest

from bs4 import BeautifulSoup

from wikipedia_ql.fragment import Fragment
from wikipedia_ql.selectors import text, text_group, sentence, section, css, alt, page
from wikipedia_ql.parser import Parser

def make_fragment(html):
    # Because fragment is Wikipedia-oriented and always looks for this div :shrug:
    return Fragment.parse(f'<div class="mw-parser-output">{html.strip()}</div>')

def h(html):
    return re.sub(r'\s+<', '<', re.sub(r'>\s+', '>', html))

def sel(text):
    return Parser().parse_selector(text)

def apply(fragment, selector, simplify=False):
    selector = sel(selector)
    fragment = make_fragment(fragment)
    print(selector)
    if simplify:
        return [h(str(f.soup)) for f in fragment.select(selector)]
    else:
        return [str(f.soup) for f in fragment.select(selector)]

def test_select_text():
    assert apply("""
            <h2>Header</h2>
            <p>Paragraph with a <a href="foo">link</a>. And <b>bold</b> text.</p>
            """,
            'text:matches("with a link")') == ['<span>with a <a href="foo">link</a></span>']

def test_select_section():
    fragment = """
        <section>
            <h2>Section1</h2>
            <p>Text1</p>
            <section>
                <h3>Section1.1</h3>
                <p>Text2</p>
            </section>
            <section>
                <h3>Section1.2</h3>
                <p>Text4</p>
            </section>
        </section>
        <section>
            <h2>Section2</h2>
            <p>Text5</p>
        </section>
        """

    assert apply(fragment, 'section[heading="Section1"]', simplify=True) == [
        h("""
        <div>
            <h2>Section1</h2>
            <p>Text1</p>
            <section>
                <h3>Section1.1</h3>
                <p>Text2</p>
            </section>
            <section>
                <h3>Section1.2</h3>
                <p>Text4</p>
            </section>
        </div>
        """),
        h("""
        <div>
            <h3>Section1.1</h3>
            <p>Text2</p>
        </div>
        """),
        h("""
        <div>
            <h3>Section1.2</h3>
            <p>Text4</p>
        </div>
        """)
    ]

    assert apply(fragment, 'section[heading="Section1.1"]', simplify=True) == [
        h("""
        <div>
                <h3>Section1.1</h3>
                <p>Text2</p>
        </div>
        """)
    ]

    assert apply(fragment, 'section[heading="Section2"]', simplify=True) == [
        h("""
        <div>
        <h2>Section2</h2>
        <p>Text5</p>
        </div>
        """)
    ]

    assert apply(fragment, 'section:first', simplify=True) == [
        h("""
        <div>
            <h2>Section1</h2>
            <p>Text1</p>
            <section>
                <h3>Section1.1</h3>
                <p>Text2</p>
            </section>
            <section>
                <h3>Section1.2</h3>
                <p>Text4</p>
            </section>
        </div>
        """),
    ]
    # TODO:
    # all
    # by level
    # intersecting sections?..
    # text pattern (include, start/stop with, regexp)

def test_select_css():
    fragment = """
        <h2>Section1</h2>
        <p>Text1</p>
        <ul>
            <li><a class="first">Link1</a></li>
            <li class="item"><a class="second">Link2</a>text</li>
        </ul>
        """

    assert apply(fragment, '.item') == [
        h("""
        <li class="item"><a class="second">Link2</a>text</li>
        """)
    ]

def test_select_sentence():
    fragment = """
        <p>This is <b>sentence</b> one. This is phrase <a href="foo">two.</a> This is NOT</p>
        <p>sentence three, probably!</p>
        """

    assert apply(fragment, 'sentence:contains("one")') == ['<span>This is <b>sentence</b> one.</span>']
    assert apply(fragment, 'sentence:contains("This.+two")') == ['<span>This is phrase <a href="foo">two.</a></span>']
    assert apply(fragment, 'sentence:contains("This.+three")') == []
    assert apply(fragment, 'sentence') == [
        '<span>This is <b>sentence</b> one.</span>',
        '<span>This is phrase <a href="foo">two.</a></span>',
        'This is NOT',              # the whole text after </a>
        'sentence three, probably!' # takes the whole paragraph, that's why no span
    ]
    assert apply(fragment, 'sentence:first') == ['<span>This is <b>sentence</b> one.</span>']


def test_select_nested():
    fragment = """
        <section>
            <h2>Section1</h2>
            <p>Text1</p>
            <ul>
                <li><a class="first">Link1</a></li>
                <li class="item"><a class="second">Link2</a>text</li>
            </ul>
        </section>
        """

    selector = 'section[heading="Section1"] >> ul >> text:matches("Li...")'
    assert apply(fragment, selector) \
        == ['<a class="first">Link1</a>', '<a class="second">Link2</a>']

    # edge case: css selector of top-level node:
    assert apply(fragment, 'text:matches("Link1") >> a') == ['<a class="first">Link1</a>']

def test_select_alt():
    fragment = """
        <h2>Section1</h2>
        <p>Text1</p>
        <ul>
            <li><a class="first">Link1</a></li>
            <li class="item"><a class="second">Link2</a>text</li>
        </ul>
        """

    assert apply(fragment, '{ text:matches("Link1"); a.second }') == \
        ['<a class="first">Link1</a>', '<a class="second">Link2</a>']

def test_select_text_group():
    fragment = '<p>Some paragraph with <b>empasis</b> and <a href="#foo">link</a></p>'

    assert apply(fragment, r'text:matches("with (\S+ and) li(.*)") >> text-group[group=1]') == [
        '<span><b>empasis</b> and</span>'
    ]

    # When not after text
    with pytest.raises(ValueError, match='text-group is only allowed after text'):
        apply(fragment, 'text-group[group=1]')

    # When slice index is out of range
    assert apply(fragment, r'text:matches("with (\S+ and) li(.*)") >> text-group[group=10]') == []

    # Named groups
    assert apply(fragment, r'text:matches("with (?P<group1>\S+ and) li(.*)") >> text-group[group=group1]') == [
        '<span><b>empasis</b> and</span>'
    ]

    # Non-existent group:
    assert apply(fragment, r'text:matches("with (?P<group1>\S+ and) li(.*)") >> text-group[group=group2]') == []

def test_select_page():
    fragment = make_fragment("""
        <h2>Section1</h2>
        <p>Text1</p>
        <ul>
            <li><a class="first">Link1</a></li>
            <li class="item"><a class="second">Link2</a>text</li>
        </ul>
        """)

    assert str(fragment.select(sel('page')).items[0].soup) == str(fragment.soup)

    assert str(fragment.select(sel('li >> page')).items[0].soup) == str(fragment.soup)

# TODO: (laterz!) infobox, ...
