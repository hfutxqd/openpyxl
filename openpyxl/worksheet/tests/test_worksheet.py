# Copyright (c) 2010-2014 openpyxl

# tes imports
import pytest

# package imports
from openpyxl.workbook import Workbook
from openpyxl.worksheet import Worksheet, Relationship, flatten
from openpyxl.cell import Cell, coordinate_from_string
from openpyxl.comments import Comment
from openpyxl.exceptions import (
    CellCoordinatesException,
    SheetTitleException,
    InsufficientCoordinatesException,
    NamedRangeException
    )


class TestWorksheet(object):

    @classmethod
    def setup_class(cls):
        cls.wb = Workbook()

    def test_new_worksheet(self):
        ws = Worksheet(self.wb)
        assert self.wb == ws._parent

    def test_new_sheet_name(self):
        self.wb.worksheets = []
        ws = Worksheet(self.wb, title='')
        assert repr(ws) == '<Worksheet "Sheet1">'

    def test_get_cell(self):
        ws = Worksheet(self.wb)
        cell = ws.cell(row=1, column=1)
        assert cell.coordinate == 'A1'

    def test_set_bad_title(self):
        with pytest.raises(SheetTitleException):
            Worksheet(self.wb, 'X' * 50)

    def test_increment_title(self):
        ws1 = self.wb.create_sheet(title="Test")
        assert ws1.title == "Test"
        ws2 = self.wb.create_sheet(title="Test")
        assert ws2.title == "Test1"

    @pytest.mark.parametrize("value", ["[", "]", "*", ":", "?", "/", "\\"])
    def test_set_bad_title_character(self, value):
        with pytest.raises(SheetTitleException):
            Worksheet(self.wb, value)


    def test_unique_sheet_title(self):
        ws = self.wb.create_sheet(title="AGE")
        assert ws._unique_sheet_name("GE") == "GE"


    def test_worksheet_dimension(self):
        ws = Worksheet(self.wb)
        assert 'A1:A1' == ws.calculate_dimension()
        ws.cell('B12').value = 'AAA'
        assert 'A1:B12' == ws.calculate_dimension()


    @pytest.mark.parametrize('range_string, coords',
                             [
                                 ('C1:C4', (3, 1, 3, 4)),
                                 ('C1', (3, 1, 3, 1)),
                             ])
    def test_bounds(self, range_string, coords):
        ws = Worksheet(self.wb)
        assert ws._range_boundaries(range_string) == coords


    def test_worksheet_range(self):
        ws = Worksheet(self.wb)
        xlrange = ws.range('A1:C4')
        assert isinstance(xlrange, tuple)
        assert 4 == len(xlrange)
        assert 3 == len(xlrange[0])

    def test_worksheet_named_range(self):
        ws = Worksheet(self.wb)
        self.wb.create_named_range('test_range', ws, 'C5')
        xlrange = ws.range('test_range')
        cell = xlrange[0]
        assert isinstance(cell, Cell)
        assert cell.row == 5

    def test_bad_named_range(self):
        ws = Worksheet(self.wb)
        with pytest.raises(NamedRangeException):
            ws.range('bad_range')

    def test_named_range_wrong_sheet(self):
        ws1 = Worksheet(self.wb)
        ws2 = Worksheet(self.wb)
        self.wb.create_named_range('wrong_sheet_range', ws1, 'C5')
        with pytest.raises(NamedRangeException):
            ws2.range('wrong_sheet_range')

    def test_range_offset(self):
        ws = Worksheet(self.wb)
        xlrange = ws.range('A1:C4', 1, 3)
        assert isinstance(xlrange, tuple)
        assert 4 == len(xlrange)
        assert 3 == len(xlrange[0])
        assert 'D2' == xlrange[0][0].coordinate
        assert xlrange[-1][-1].coordinate == 'F5'

    def test_cell_alternate_coordinates(self):
        ws = Worksheet(self.wb)
        cell = ws.cell(row=8, column=4)
        assert 'D8' == cell.coordinate

    def test_cell_insufficient_coordinates(self):
        ws = Worksheet(self.wb)
        with pytest.raises(InsufficientCoordinatesException):
            ws.cell(row=8)

    def test_cell_range_name(self):
        ws = Worksheet(self.wb)
        self.wb.create_named_range('test_range_single', ws, 'B12')
        c_range_name = ws.range('test_range_single')
        c_range_coord = ws.range('B12')
        c_cell = ws.cell('B12')
        assert c_range_coord == ((c_cell,),)
        assert c_range_name == (c_cell,)


    def test_garbage_collect(self):
        ws = Worksheet(self.wb)
        ws.cell('A1').value = ''
        ws.cell('B2').value = '0'
        ws.cell('C4').value = 0
        ws.cell('D1').comment = Comment('Comment', 'Comment')
        ws._garbage_collect()
        assert set(ws.get_cell_collection()), set([ws.cell('B2'), ws.cell('C4') == ws.cell('D1')])


    def test_hyperlink_value(self):
        ws = Worksheet(self.wb)
        ws.cell('A1').hyperlink = "http://test.com"
        assert "http://test.com" == ws.cell('A1').value
        ws.cell('A1').value = "test"
        assert "test" == ws.cell('A1').value


    def test_hyperlink_relationships(self):
        ws = Worksheet(self.wb)
        assert len(ws.relationships) == 0

        ws.cell('A1').hyperlink = "http://test.com"
        assert len(ws.relationships) == 1
        assert "rId1" == ws.cell('A1').hyperlink_rel_id
        assert "rId1" == ws.relationships[0].id
        assert "http://test.com" == ws.relationships[0].target
        assert "External" == ws.relationships[0].target_mode

        ws.cell('A2').hyperlink = "http://test2.com"
        assert len(ws.relationships) == 2
        assert "rId2" == ws.cell('A2').hyperlink_rel_id
        assert "rId2" == ws.relationships[1].id
        assert "http://test2.com" == ws.relationships[1].target
        assert "External" == ws.relationships[1].target_mode

    def test_bad_relationship_type(self):
        with pytest.raises(ValueError):
            Relationship('bad_type')

    def test_append_list(self):
        ws = Worksheet(self.wb)

        ws.append(['This is A1', 'This is B1'])

        assert 'This is A1' == ws.cell('A1').value
        assert 'This is B1' == ws.cell('B1').value

    def test_append_dict_letter(self):
        ws = Worksheet(self.wb)

        ws.append({'A' : 'This is A1', 'C' : 'This is C1'})

        assert 'This is A1' == ws.cell('A1').value
        assert 'This is C1' == ws.cell('C1').value

    def test_append_dict_index(self):
        ws = Worksheet(self.wb)

        ws.append({1 : 'This is A1', 3 : 'This is C1'})

        assert 'This is A1' == ws.cell('A1').value
        assert 'This is C1' == ws.cell('C1').value

    def test_bad_append(self):
        ws = Worksheet(self.wb)
        assert ws.max_row == 0
        with pytest.raises(TypeError):
            ws.append("test")
        assert ws.max_row == 0


    def test_append_range(self):
        ws = Worksheet(self.wb)
        ws.append(range(30))
        assert ws['AD1'].value == 29


    def test_append_iterator(self):
        def itty():
            for i in range(30):
                yield i

        ws = Worksheet(self.wb)
        gen = itty()
        ws.append(gen)
        assert ws['AD1'].value == 29


    def test_append_2d_list(self):

        ws = Worksheet(self.wb)

        ws.append(['This is A1', 'This is B1'])
        ws.append(['This is A2', 'This is B2'])

        vals = ws.range('A1:B2')
        expected = (
            ('This is A1', 'This is B1'),
            ('This is A2', 'This is B2'),
        )
        for e, v in zip(expected, flatten(vals)):
            assert e == tuple(v)


    @pytest.mark.parametrize("row, column, coordinate",
                             [
                                 (1, 0, 'A1'),
                                 (9, 2, 'C9'),
                             ])
    def test_iter_rows(self, row, column, coordinate):
        from itertools import islice
        ws = Worksheet(self.wb)
        ws.cell('A1').value = 'first'
        ws.cell('C9').value = 'last'
        assert ws.calculate_dimension() == 'A1:C9'
        rows = ws.iter_rows()
        first_row = tuple(next(islice(rows, row-1, row)))
        assert first_row[column].coordinate == coordinate


    def test_rows(self):

        ws = Worksheet(self.wb)

        ws.cell('A1').value = 'first'
        ws.cell('C9').value = 'last'

        rows = ws.rows

        assert len(rows) == 9
        first_row = rows[0]
        last_row = rows[-1]

        assert first_row[0].value == 'first' and first_row[0].coordinate == 'A1'
        assert last_row[-1].value == 'last'


    def test_no_cols(self):
        ws = Worksheet(self.wb)
        assert ws.columns == ((),)


    def test_cols(self):

        ws = Worksheet(self.wb)

        ws.cell('A1').value = 'first'
        ws.cell('C9').value = 'last'

        cols = ws.columns

        assert len(cols) == 3

        assert cols[0][0].value == 'first'
        assert cols[-1][-1].value == 'last'

    def test_auto_filter(self):
        ws = Worksheet(self.wb)
        ws.auto_filter.ref = ws.range('a1:f1')
        assert ws.auto_filter.ref == 'A1:F1'

        ws.auto_filter.ref = ''
        assert ws.auto_filter.ref is None

        ws.auto_filter.ref = 'c1:g9'
        assert ws.auto_filter.ref == 'C1:G9'

    def test_getitem(self):
        ws = Worksheet(self.wb)
        c = ws['A1']
        assert isinstance(c, Cell)
        assert c.coordinate == "A1"
        assert ws['A1'].value is None

    def test_setitem(self):
        ws = Worksheet(self.wb)
        ws['A12'] = 5
        assert ws['A12'].value == 5

    def test_getslice(self):
        ws = Worksheet(self.wb)
        cell_range = ws['A1':'B2']
        assert isinstance(cell_range, tuple)
        assert (cell_range) == ((ws['A1'], ws['B1']), (ws['A2'], ws['B2']))


    def test_freeze(self):
        ws = Worksheet(self.wb)
        ws.freeze_panes = ws.cell('b2')
        assert ws.freeze_panes == 'B2'

        ws.freeze_panes = ''
        assert ws.freeze_panes is None

        ws.freeze_panes = 'c5'
        assert ws.freeze_panes == 'C5'

        ws.freeze_panes = ws.cell('A1')
        assert ws.freeze_panes is None

    def test_cells_from_range(self):
        ws = Worksheet(self.wb)
        cells = ws._cells_from_range("A1:D4")
        cells = [list(row) for row in cells]
        assert cells == [
           ['A1', 'B1', 'C1', 'D1'],
           ['A2', 'B2', 'C2', 'D2'],
           ['A3', 'B3', 'C3', 'D3'],
           ['A4', 'B4', 'C4', 'D4'],
                               ]

    def test_cells_from_range_offset(self):
        ws = Worksheet(self.wb)
        cells = ws._cells_from_range("A1:D4", 1, 2)
        cells = [list(row) for row in cells]
        assert cells == [
           ['C2', 'D2', 'E2', 'F2'],
           ['C3', 'D3', 'E3', 'F3'],
           ['C4', 'D4', 'E4', 'F4'],
           ['C5', 'D5', 'E5', 'F5'],
                               ]


    def test_merge_range_string(self):
        ws = Worksheet(self.wb)
        ws['A1'] = 1
        ws['D4'] = 16
        ws.merge_cells(range_string="A1:D4")
        assert ws._merged_cells == ["A1:D4"]
        assert 'D4' not in ws._cells


    def test_merge_coordinate(self):
        ws = Worksheet(self.wb)
        ws.merge_cells(start_row=1, start_column=1, end_row=4, end_column=4)
        assert ws._merged_cells == ["A1:D4"]


    def test_unmerge_range_string(self):
        ws = Worksheet(self.wb)
        ws._merged_cells = ["A1:D4"]
        ws.unmerge_cells("A1:D4")


    def test_unmerge_coordinate(self):
        ws = Worksheet(self.wb)
        ws._merged_cells = ["A1:D4"]
        ws.unmerge_cells(start_row=1, start_column=1, end_row=4, end_column=4)


class TestPositioning(object):
    def test_point(self):
        wb = Workbook()
        ws = wb.get_active_sheet()
        assert ws.point_pos(top=40, left=150), ('C' == 3)

    @pytest.mark.parametrize("value", ('A1', 'D52', 'X11'))
    def test_roundtrip(self, value):
        wb = Workbook()
        ws = wb.get_active_sheet()
        assert ws.point_pos(*ws.cell(value).anchor) == coordinate_from_string(value)
