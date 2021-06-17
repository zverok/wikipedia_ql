import re

from bs4 import BeautifulSoup

from wikipedia_ql.fragment import Fragment
from wikipedia_ql.selectors import text, section

def make_fragment(html):
    # Because fragment is Wikipedia-oriented and always looks for this div :shrug:
    return Fragment.parse(f'<div class="mw-parser-output">{html.strip()}</div>')

def test_build_tree():
    def tree(html):
        return make_fragment(html).text_tree

    assert tree("""
            <h2>Header</h2>
            <p>Paragraph with a <a href="foo">link</a>. And <b>bold</b> text.</p>
            """) == (0, 47,                                    # document itself
                        [
                            (0, 7,                              # h2
                                [(0, 6, [])]                    # "Header"
                            ),
                            (7, 8, []),                         # stray "\n"
                            (8, 46,                             # p
                                [
                                    (8, 25, []),                # "Paragraph with a "
                                    (25, 29,                    # a
                                        [(25, 29, [])]          # "link"
                                    ),
                                    (29, 35, []),               # ". And "
                                    (35, 39,                    # b
                                        [(35, 39, [])]          # "bold"
                                    ),
                                    (39, 45, [])                # " text."
                                ]
                            )
                        ]
                    )

def test_slice():
    fragment = make_fragment(
        """
        <h2>Header</h2>
        <p>Paragraph with a <a href="foo">link</a>. And <b>bold</b> text.</p>
        """)

    def slice(frag, start, end):
        return str(frag.slice(start, end).soup)

    assert slice(fragment, 20, 33) == '<span id="slice20_33">th a <a href="foo">link</a>. An</span>'

    assert slice(fragment, 20, 27) == '<span id="slice20_27">th a <a href="foo">li</a></span>'

    assert slice(fragment.slice(20, 33), 0, 6) == '<span id="slice20_26">th a <a href="foo">l</a></span>'

def test_select_text():
    def select(html, selector):
        fragment = make_fragment(html)
        selector = text(selector)
        return [str(f.soup) for f in fragment._select(selector)]

    assert select("""
            <h2>Header</h2>
            <p>Paragraph with a <a href="foo">link</a>. And <b>bold</b> text.</p>
            """,
            'with a link') == ['<span id="slice18_29">with a <a href="foo">link</a></span>']


def test_select_section():
    def select(fragment, **args):
        selector = section(**args)
        return [h(str(f.soup)) for f in fragment._select(selector)]

    def h(html):
        return re.sub(r'\s+', '', html)

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

    # all
    # by level
