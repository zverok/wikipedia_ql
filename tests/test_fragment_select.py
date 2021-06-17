import re

from bs4 import BeautifulSoup

from wikipedia_ql.fragment import Fragment
from wikipedia_ql.selectors import text, section, css

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
        return apply(make_fragment(html), text(selector))

    assert select("""
            <h2>Header</h2>
            <p>Paragraph with a <a href="foo">link</a>. And <b>bold</b> text.</p>
            """,
            'with a link') == ['<span>with a <a href="foo">link</a></span>']


def test_select_section():
    def select(fragment, **args):
        return apply(fragment, section(**args), simplify=True)

    fragment = make_fragment("""
        <h2>Section1</h2>
        <p>Text1</p>
        <h3>Section1.1</h3>
        <p>Text2</p>
        <h3>Section1.2</h3>
        <p>Text4</p>
        <h2>Section2</h2>
        <p>Text5</p>
        """)

    assert select(fragment, text='Section1') == [
        h("""
        <div>
            <h2>Section1</h2>
            <p>Text1</p>
            <h3>Section1.1</h3>
            <p>Text2</p>
            <h3>Section1.2</h3>
            <p>Text4</p>
        </div>
        """)
    ]

    assert select(fragment, text='Section1.1') == [
        h("""
        <div>
            <h3>Section1.1</h3>
            <p>Text2</p>
        </div>
        """)
    ]

    assert select(fragment, text='Section2') == [
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
        return apply(fragment, css(css_selector), simplify=True)

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

# TODO: sentence

def test_select_nested():
    def select(fragment, selector):
        return [str(f.soup) for f in fragment.select(selector)]

    fragment = make_fragment("""
        <h2>Section1</h2>
        <p>Text1</p>
        <ul>
            <li><a class="first">Link1</a></li>
            <li class="item"><a class="second">Link2</a>text</li>
        </ul>
        """)

    selector = section('Section1', nested=css('ul', nested=text('Li...')))
    assert select(fragment, selector) \
        == ['<a class="first">Link1</a>', '<a class="second">Link2</a>']

# TODO: nested
# TODO: any
# TODO: text-slice, wikitable, infobox, ...
