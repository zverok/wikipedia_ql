import copy

from bs4 import BeautifulSoup

def reflow(source_table):
    table = copy.copy(source_table)
    # TODO: handle if it is not a table

    soup = BeautifulSoup('', 'html.parser')

    columns = []
    rowspans = []

    look_for_columns = True

    row_title_size = 0

    for row_num, row in enumerate(table.select('tr')):
        cells = []
        if rowspans:
            expanded = [False] * len(rowspans)

        # Drop table header
        # TODO: NAIVE! and needs tests. And maybe embed in <table> tag as attr?
        if row_num == 0 and len([*row.select('td,th')]) == 1:
            continue

        # first, reflow possibe col- and row-spans:
        for cell in row.select('td,th'):
            if rowspans:
                while len(cells) < len(rowspans) and rowspans[len(cells)]:
                    expanded[len(cells)] = True
                    cells.append(rowspans[len(cells)].pop())

            colspan = None
            if 'colspan' in cell.attrs:
                colspan = int(cell['colspan']) # TODO: if it is converbible
                del cell['colspan']
            if colspan and colspan > 1:
                cells.extend([copy.copy(cell) for i in range(colspan)])
            else:
                cells.append(cell)

        if rowspans:
            while len(cells) < len(rowspans) and rowspans[len(cells)]:
                expanded[len(cells)] = True
                cells.append(rowspans[len(cells)].pop())

        if not rowspans:
            rowspans = [None] * len(cells) # TODO: reliable enough?


        for col, cell in enumerate(cells):
            if 'rowspan' in cell.attrs:
                rowspan = int(cell['rowspan']) # TODO: if it is converbible
                del cell['rowspan']
                if rowspan > 1:
                    # TODO: assert rowspans[col] is empty, otherwise tis bug!
                    rowspans[col] = [copy.copy(cell) for i in range(rowspan - 1)]

        if look_for_columns and all(cell.name == 'th' for cell in cells):
            if not columns:
                columns = [soup.new_tag('col', title=(cell.string or '').strip()) for cell in cells]
            else:
                for column, cell, expanded in zip(columns, cells, expanded):
                    if not expanded:
                        column['title'] = column['title'] + "\n" + (cell.string or '').strip()
            row.extract()
        else:
            look_for_columns = False
            row_title = None
            look_for_title = True
            real_cells = []
            for col_num, (cell, column) in enumerate(zip(cells, columns)):
                if cell.name == 'th':
                    if look_for_title:
                        row_title = row_title + "\n" + cell.string if row_title else cell.string
                        row_title_size = max(row_title_size, col_num + 1)
                else:
                    look_for_title = False
                    if column:
                        cell['column'] = column['title']
                    if row_title:
                        cell['row'] = row_title
                    real_cells.append(cell)

            row.clear()
            if row_title:
                row['title'] = row_title
            row.extend(real_cells)

    group = soup.new_tag('colgroup')
    # FIXME: Properly handle the fact that every row can have different number of TH! (But how?)
    columns = columns[row_title_size:]
    group.extend(columns)
    table.insert(1, group)

    return table
