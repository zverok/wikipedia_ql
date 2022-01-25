import re
import pytest

from bs4 import BeautifulSoup

from wikipedia_ql.fragment import Fragment
from wikipedia_ql.selectors import text, text_group, sentence, section, css, alt, page

def make_fragment(html):
    # Because fragment is Wikipedia-oriented and always looks for this div :shrug:
    return Fragment.parse(f'<div class="mw-parser-output">{html.strip()}</div>')

def h(html):
    return re.sub(r'\s+<', '<', re.sub(r'>\s+', '>', html))

def apply(fragment, selector, simplify=False):
    if simplify:
        return [h(str(f.soup)) for f in fragment._select(selector)]
    else:
        return [str(f.soup) for f in fragment._select(selector)]

def test_select_text():
    def select(html, selector):
        return apply(make_fragment(html), text(pattern=selector))

    assert select("""
            <h2>Header</h2>
            <p>Paragraph with a <a href="foo">link</a>. And <b>bold</b> text.</p>
            """,
            'with a link') == ['<span>with a <a href="foo">link</a></span>']


def test_select_section():
    def select(fragment, **args):
        return apply(fragment, section(**args), simplify=True)

    fragment = make_fragment("""
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
        """)

    assert select(fragment, heading='Section1') == [
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

    assert select(fragment, heading='Section1.1') == [
        h("""
        <div>
                <h3>Section1.1</h3>
                <p>Text2</p>
        </div>
        """)
    ]

    assert select(fragment, heading='Section2') == [
        h("""
        <div>
        <h2>Section2</h2>
        <p>Text5</p>
        </div>
        """)
    ]
    # TODO:
    # all
    # by level
    # intersecting sections?..
    # text pattern (include, start/stop with, regexp)

def test_select_css():
    def select(fragment, css_selector):
        return apply(fragment, css(css_selector=css_selector), simplify=True)

    fragment = make_fragment("""
        <h2>Section1</h2>
        <p>Text1</p>
        <ul>
            <li><a class="first">Link1</a></li>
            <li class="item"><a class="second">Link2</a>text</li>
        </ul>
        """)

    assert select(fragment, '.item') == [
        h("""
        <li class="item"><a class="second">Link2</a>text</li>
        """)
    ]

def test_select_sentence():
    def select(fragment, pattern):
        return apply(fragment, sentence(pattern=pattern))

    fragment = make_fragment(
        """
        <p>This is <b>sentence</b> one. This is phrase <a href="foo">two.</a> This is NOT</p>
        <p>sentence three, probably!</p>
        """
    )

    assert select(fragment, 'one') == ['<span>This is <b>sentence</b> one.</span>']
    assert select(fragment, 'This.+two') == ['<span>This is phrase <a href="foo">two.</a></span>']
    assert select(fragment, 'This.+three') == []
    assert select(fragment, None) == [
        '<span>This is <b>sentence</b> one.</span>',
        '<span>This is phrase <a href="foo">two.</a></span>',
        'This is NOT',              # the whole text after </a>
        'sentence three, probably!' # takes the whole paragraph, that's why no span
    ]

def test_select_nested():
    def select(fragment, selector):
        return [str(f.soup) for f in fragment.select(selector)]

    fragment = make_fragment("""
        <section>
            <h2>Section1</h2>
            <p>Text1</p>
            <ul>
                <li><a class="first">Link1</a></li>
                <li class="item"><a class="second">Link2</a>text</li>
            </ul>
        </section>
        """)

    selector = section(heading='Section1', nested=css(css_selector='ul', nested=text(pattern='Li...')))
    assert select(fragment, selector) \
        == ['<a class="first">Link1</a>', '<a class="second">Link2</a>']

    # edge case: css selector of top-level node:
    selector = text(pattern='Link1', nested=css(css_selector='a'))
    assert select(fragment, selector) == ['<a class="first">Link1</a>']

def test_select_alt():
    def select(fragment, *selectors):
        return apply(fragment, alt(*selectors), simplify=True)

    fragment = make_fragment("""
        <h2>Section1</h2>
        <p>Text1</p>
        <ul>
            <li><a class="first">Link1</a></li>
            <li class="item"><a class="second">Link2</a>text</li>
        </ul>
        """)

    assert select(fragment, text(pattern='Link1'), css(css_selector='a.second')) == \
        ['<a class="first">Link1</a>', '<a class="second">Link2</a>']

def test_select_text_group():
    def select(fragment, group):
        return apply(fragment, text_group(group=group))

    fragment = make_fragment(
        '<p>Some paragraph with <b>empasis</b> and <a href="#foo">link</a></p>'
    )

    assert select(fragment.select(text(pattern=r'with (\S+ and) li(.*)')), 1) == [
        '<span><b>empasis</b> and</span>'
    ]

    # When not after text
    with pytest.raises(ValueError, match='text-group is only allowed after text'):
        select(fragment, 1)

    # When slice index is out of range
    assert select(fragment.select(text(pattern=r'with (\S+ and) li(.*)')), 10) == []

    # Named groups
    assert select(fragment.select(text(pattern=r'with (?P<group1>\S+ and) li(.*)')), 'group1') == [
        '<span><b>empasis</b> and</span>'
    ]

    # Non-existent group:
    assert select(fragment.select(text(pattern=r'with (?P<group1>\S+ and) li(.*)')), 'group2') == []

def test_select_page():
    fragment = make_fragment("""
        <h2>Section1</h2>
        <p>Text1</p>
        <ul>
            <li><a class="first">Link1</a></li>
            <li class="item"><a class="second">Link2</a>text</li>
        </ul>
        """)

    assert str(fragment.select(page()).items[0].soup) == str(fragment.soup)

    assert str(fragment.select(css(css_selector='li', nested=page())).items[0].soup) == str(fragment.soup)

# TODO: (laterz!) wikitable, infobox, ...
