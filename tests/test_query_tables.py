import re

import pytest

from wikipedia_ql.fragment import Fragment
from wikipedia_ql.selectors import text, section, css, alt, page, attr, table_data

def make_fragment(html, **kwargs):
    # Because fragment is Wikipedia-oriented and always looks for this div :shrug:
    return Fragment.parse(f'<div class="mw-parser-output">{html.strip()}</div>', **kwargs)

def test_simple():
    fragment = make_fragment("""
        <table>
            <tr><th></th><th>col1</th><th>col2</th></tr>
            <tr><th>row1</th><td>1.1</td><td>1.2</td></tr>
            <tr><th>row2</th><td>2.1</td><td>2.2</td></tr>
        </table>
        """)

    assert fragment.query(
            css(css_selector='table', nested=table_data(nested=css(css_selector='td[column="col1"]')))
        ) == ['1.1', '2.1']

# def test_complex():
#     fragment = make_fragment(open('tests/fixtures/tables/climate.html').read())

#     assert fragment.query(
#             css(css_selector='table', nested=table_data(nested=alt(css(css_selector='td[column="col1"]')))
#         ) == ['1.1', '2.1']
