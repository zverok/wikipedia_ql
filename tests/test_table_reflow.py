import re

from bs4 import BeautifulSoup

from wikipedia_ql.tables import reflow

def h(html):
    return re.sub(r'\s+<', '<', re.sub(r'>\s+', '>', html))

def reflow_test(html, **kwargs):
    soup = BeautifulSoup(html, 'html.parser').select_one('table')
    res = reflow(soup, **kwargs)
    return h(str(res))

def test_simple():
    # Nothing to do
    assert reflow_test("""
        <table>
            <tr><td>1.1</td><td>1.2</td></tr>
            <tr><td>2.1</td><td>2.2</td></tr>
        </table>
        """) == h("""
        <table>
            <tr><td>1.1</td><td>1.2</td></tr>
            <tr><td>2.1</td><td>2.2</td></tr>
        </table>
        """)

def test_simple_col_th():
    assert reflow_test("""
        <table>
            <tr><th>col1</th><th>col2</th></tr>
            <tr><td>1.1</td><td>1.2</td></tr>
            <tr><td>2.1</td><td>2.2</td></tr>
        </table>
        """) == h("""
        <table>
            <colgroup>
                <col title="col1"/>
                <col title="col2"/>
            </colgroup>
            <tr><td column="col1">1.1</td><td column="col2">1.2</td></tr>
            <tr><td column="col1">2.1</td><td column="col2">2.2</td></tr>
        </table>
        """)

def test_simple_row_th():
    assert reflow_test("""
        <table>
            <tr><th></th><th>col1</th><th>col2</th></tr>
            <tr><th>row1</th><td>1.1</td><td>1.2</td></tr>
            <tr><th>row2</th><td>2.1</td><td>2.2</td></tr>
        </table>
        """) == h("""
        <table>
            <colgroup>
                <col title="col1"/>
                <col title="col2"/>
            </colgroup>
            <tr title="row1"><td column="col1" row="row1">1.1</td><td column="col2" row="row1">1.2</td></tr>
            <tr title="row2"><td column="col1" row="row2">2.1</td><td column="col2" row="row2">2.2</td></tr>
        </table>
        """)

def test_colspan_td():
    assert reflow_test("""
        <table>
            <tr><th></th><th>col1</th><th>col2</th></tr>
            <tr><th>row1</th><td colspan="2">1.1-2</td></tr>
            <tr><th>row2</th><td>2.1</td><td>2.2</td></tr>
        </table>
        """) == h("""
        <table>
            <colgroup>
                <col title="col1"/>
                <col title="col2"/>
            </colgroup>
            <tr title="row1"><td column="col1" row="row1">1.1-2</td><td column="col2" row="row1">1.1-2</td></tr>
            <tr title="row2"><td column="col1" row="row2">2.1</td><td column="col2" row="row2">2.2</td></tr>
        </table>
        """)

def test_rowspan_td():
    assert reflow_test("""
        <table>
            <tr><th></th><th>col1</th><th>col2</th></tr>
            <tr><th>row1</th><td rowspan="2">1.*</td><td>1.2</td></tr>
            <tr><th>row2</th><td>2.2</td></tr>
        </table>
        """) == h("""
        <table>
            <colgroup>
                <col title="col1"/>
                <col title="col2"/>
            </colgroup>
            <tr title="row1"><td column="col1" row="row1">1.*</td><td column="col2" row="row1">1.2</td></tr>
            <tr title="row2"><td column="col1" row="row2">1.*</td><td column="col2" row="row2">2.2</td></tr>
        </table>
        """)

def test_span_complex():
    assert reflow_test("""
        <table>
            <tr><th></th><th>col1</th><th>col2</th><th>col3</th></tr>
            <tr><th>row1</th><td rowspan="2" colspan="2">1-2.1-2</td><td>1.3</td></tr>
            <tr><th>row2</th><td>2.3</td></tr>
        </table>
        """) == h("""
        <table>
            <colgroup><col title="col1"/><col title="col2"/><col title="col3"/></colgroup>
            <tr title="row1"><td column="col1" row="row1">1-2.1-2</td><td column="col2" row="row1">1-2.1-2</td><td column="col3" row="row1">1.3</td></tr>
            <tr title="row2"><td column="col1" row="row2">1-2.1-2</td><td column="col2" row="row2">1-2.1-2</td><td column="col3" row="row2">2.3</td></tr>
        </table>
        """)
    # TODO: more examples

def test_th_span():
    assert reflow_test("""
        <table>
            <tr><th></th><th colspan="2">col1-2</th></tr>
            <tr><th rowspan="2">row1-2</th><td>1.1</td><td>1.2</td></tr>
            <tr><td>2.1</td><td>2.2</td></tr>
        </table>
        """) == h("""
        <table>
            <colgroup>
                <col title="col1-2"/>
                <col title="col1-2"/>
            </colgroup>
            <tr title="row1-2"><td column="col1-2" row="row1-2">1.1</td><td column="col1-2" row="row1-2">1.2</td></tr>
            <tr title="row1-2"><td column="col1-2" row="row1-2">2.1</td><td column="col1-2" row="row1-2">2.2</td></tr>
        </table>
        """)

def test_multi_col_th():
    assert reflow_test("""
        <table>
            <tr><th>col1</th><th>col2</th></tr>
            <tr><th>colA</th><th>colB</th></tr>
            <tr><td>1.1</td><td>1.2</td></tr>
            <tr><td>2.1</td><td>2.2</td></tr>
        </table>
        """) == h("""
        <table>
            <colgroup>
                <col title="col1\ncolA"/>
                <col title="col2\ncolB"/>
            </colgroup>
            <tr><td column="col1\ncolA">1.1</td><td column="col2\ncolB">1.2</td></tr>
            <tr><td column="col1\ncolA">2.1</td><td column="col2\ncolB">2.2</td></tr>
        </table>
        """)

    assert reflow_test("""
        <table>
            <tr><th colspan="2">col1-2</th><th rowspan="2">col3</th></tr>
            <tr><th>colA</th><th>colB</th></tr>
            <tr><td>1.1</td><td>1.2</td><td>1.3</td></tr>
            <tr><td>2.1</td><td>2.2</td><td>2.3</td></tr>
        </table>
        """) == h("""
        <table>
            <colgroup>
                <col title="col1-2\ncolA"/>
                <col title="col1-2\ncolB"/>
                <col title="col3"/>
            </colgroup>
            <tr><td column="col1-2\ncolA">1.1</td><td column="col1-2\ncolB">1.2</td><td column="col3">1.3</td></tr>
            <tr><td column="col1-2\ncolA">2.1</td><td column="col1-2\ncolB">2.2</td><td column="col3">2.3</td></tr>
        </table>
        """)

def test_whole_row_header():
    assert reflow_test("""
        <table>
            <tr><th colspan="2">table title</th></tr>
            <tr><th>colA</th><th>colB</th></tr>
            <tr><td>1.1</td><td>1.2</td></tr>
            <tr><td>2.1</td><td>2.2</td></tr>
        </table>
        """) == h("""
        <table title="table title">
            <colgroup>
                <col title="colA"/>
                <col title="colB"/>
            </colgroup>
            <tr><td column="colA">1.1</td><td column="colB">1.2</td></tr>
            <tr><td column="colA">2.1</td><td column="colB">2.2</td></tr>
        </table>
        """)

def test_whole_row_middle_th():
    assert reflow_test("""
        <table>
            <tr><th>colA</th><th>colB</th></tr>
            <tr><td>1.1</td><td>1.2</td></tr>
            <tr><th colspan="2">row2title</th></tr>
            <tr><td>2.1</td><td>2.2</td></tr>
        </table>
        """) == h("""
        <table>
            <colgroup>
                <col title="colA"/>
                <col title="colB"/>
            </colgroup>
            <tr><td column="colA">1.1</td><td column="colB">1.2</td></tr>
            <tr title="row2title"><td column="colA" row="row2title">2.1</td><td column="colB" row="row2title">2.2</td></tr>
        </table>
        """)

def test_whole_row_td():
    assert reflow_test("""
        <table>
            <tr><th>colA</th><th>colB</th></tr>
            <tr><td>1.1</td><td>1.2</td></tr>
            <tr><td colspan="2">addendum1</td></tr>
            <tr><td>2.1</td><td>2.2</td></tr>
            <tr><td colspan="2">addendum2</td></tr>
        </table>
        """) == h("""
        <table>
            <colgroup>
                <col title="colA"/>
                <col title="colB"/>
            </colgroup>
            <tr><td column="colA">1.1</td><td column="colB">1.2</td><td>addendum1</td></tr>
            <tr><td column="colA">2.1</td><td column="colB">2.2</td><td>addendum2</td></tr>
        </table>
        """)

def test_force_rh():
    assert reflow_test("""
        <table>
            <tr><th></th><th>col1</th><th>col2</th></tr>
            <tr><td>row1</td><td>1.1</td><td>1.2</td></tr>
            <tr><td>row2</td><td>2.1</td><td>2.2</td></tr>
        </table>
        """, force_row_headers='1') == h("""
        <table>
            <colgroup>
                <col title="col1"/>
                <col title="col2"/>
            </colgroup>
            <tr title="row1"><td column="col1" row="row1">1.1</td><td column="col2" row="row1">1.2</td></tr>
            <tr title="row2"><td column="col1" row="row2">2.1</td><td column="col2" row="row2">2.2</td></tr>
        </table>
        """)

# TODO:
# * th in the middle
# * complex HTML in cells, or just "\n" and such stuff
# * broken tables
