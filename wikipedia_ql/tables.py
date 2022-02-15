import copy

from bs4 import BeautifulSoup

def reflow(source_table, *, force_row_headers=None):
    table = copy.copy(source_table)
    # TODO: handle if it is not a table
    if force_row_headers:
        force_row_headers = int(force_row_headers)

    soup = BeautifulSoup('', 'html.parser')

    columns = []
    rowspans = []

    look_for_columns = True

    row_title_size = 0
    prev_row = None
    row_title_prefix = None

    for row_num, row in enumerate(table.select('tr')):
        cells = []
        if rowspans:
            expanded = [False] * len(rowspans)

        row_cells = [*row.select('td,th')]

        # TODO: NAIVE!
        if len(row_cells) == 1:
            if row_num == 0 and row_cells[0].name == 'th':
                # Extract table header
                table['title'] = row_cells[0].text
                row.extract()
                continue
            elif row_cells[0].name == 'th':
                # Consider full-row th in the middle as a prefix to next rows title
                row_title_prefix = row_cells[0].get_text(" ", strip=True)
                row.extract()
                continue
            elif prev_row and row_cells[0].name == 'td':
                # Consider it "continuation" of a previous row
                td = row_cells[0]
                td.extract()
                if 'colspan' in td.attrs:
                    del td['colspan']
                prev_row.append(td)
                row.extract()
                continue

        # first, reflow possibe col- and row-spans:
        for cell in row_cells:
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
                columns = [soup.new_tag('col', title=cell.get_text(" ", strip=True)) for cell in cells]
            else:
                for column, cell, expanded in zip(columns, cells, expanded):
                    if not expanded:
                        column['title'] = column['title'] + "\n" + cell.get_text(" ", strip=True)
            row.extract()
        else:
            look_for_columns = False
            row_title = row_title_prefix
            look_for_title = not force_row_headers
            real_cells = []
            if not columns:
                columns = [None] * len(cells)
            for col_num, (cell, column) in enumerate(zip(cells, columns)):
                is_title = force_row_headers and col_num < force_row_headers or \
                            look_for_title and cell.name == 'th'
                if is_title:
                    if row_title:
                        row_title = row_title + "\n" + cell.get_text(" ", strip=True)
                    else:
                        row_title = cell.get_text(" ", strip=True)
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

            prev_row = row

    if columns and not all(c == None for c in columns):
        group = soup.new_tag('colgroup')
        # FIXME: Properly handle the fact that every row can have different number of TH! (But how?)
        columns = columns[row_title_size:]
        group.extend(columns)
        table.insert(1, group)

    return table
