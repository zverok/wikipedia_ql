import re

from bs4 import BeautifulSoup

from wikipedia_ql.fragment import Fragment
from wikipedia_ql.selectors import text, section, css

def make_fragment(html):
    # Because fragment is Wikipedia-oriented and always looks for this div :shrug:
    return Fragment.parse(f'<div class="mw-parser-output">{html.strip()}</div>')

def h(html):
    return re.sub(r'\s+<', '<', re.sub(r'>\s+', '>', html))

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

    assert slice(fragment, 20, 33) == '<span>th a <a href="foo">link</a>. An</span>'

    assert slice(fragment, 20, 27) == '<span>th a <a href="foo">li</a></span>'

    assert slice(fragment.slice(20, 33), 0, 6) == '<span>th a <a href="foo">l</a></span>'

    fragment = make_fragment("""
        <h2>Section1</h2>
        <p>Text1</p>
        <ul>
            <li><a class="first">First</a></li>
            <li class="item"><a class="second">Second</a> text</li>
        </ul>
        """)

    assert slice(fragment, 25, 31) == '<a class="second">Second</a>'


def test_slice_tags():
    pass
