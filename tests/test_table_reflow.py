import re

from bs4 import BeautifulSoup

from wikipedia_ql.tables import reflow

def h(html):
    return re.sub(r'\s+<', '<', re.sub(r'>\s+', '>', html))

def test(html):
    soup = BeautifulSoup(html, 'html.parser').select_one('table')
    res = reflow(soup)
    return h(str(res))

def test_simple():
    # Nothing to do
    # FIXME: Or add col/row num to metadata?
    assert test("""
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
    assert test("""
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
    assert test("""
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
    assert test("""
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
    assert test("""
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
    assert test("""
        <table>
            <tr><th></th><th>col1</th><th>col2</th></tr>
            <tr><th>row1</th><td rowspan="2" colspan="2">1-2.1-2</td></tr>
            <tr><th>row2</th></tr>
        </table>
        """) == h("""
        <table>
            <tr><th></th><th>col1</th><th>col2</th></tr>
            <tr><th>row1</th><td column="col1" row="row1">1-2.1-2</td><td column="col2" row="row1">1-2.1-2</td></tr>
            <tr><th>row2</th><td column="col1" row="row2">1-2.1-2</td><td column="col2" row="row2">1-2.1-2</td></tr>
        </table>
        """)
    # TODO: more examples

def test_th_span():
    assert test("""
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
    assert test("""
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

    assert test("""
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

def test_whole_rows():
    pass

# TODO:
# * th in the middle
# * complex HTML in cells, or just "\n" and such stuff
# * broken tables
