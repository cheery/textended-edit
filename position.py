class Position(object):
    @classmethod
    def top(cls, cell):
        while not cell.is_external():
            cell = cell[0]
        return cls(cell, 0)

    @classmethod
    def bottom(cls, cell):
        while not cell.is_external():
            cell = cell[len(cell) - 1]
        return cls(cell, len(cell))

    def __init__(self, cell, index):
        self.cell = cell
        self.index = index

    def __add__(self, number):
        return Position(self.cell, self.index+number)

    def __eq__(self, other):
        return self.cell is other.cell and self.index == other.index

    def __sub__(self, number):
        return Position(self.cell, self.index-number)

    @property
    def above(self):
        parent = self.cell.parent
        if parent is not None:
            return Position(parent, parent.index(self.cell))

    @property
    def on_left_boundary(self):
        if self.cell.parent is None:
            return False
        parent = self.cell.parent
        return parent.index(self.cell) == 0

    @property
    def on_right_boundary(self):
        if self.cell.parent is None:
            return False
        return parent.index(self.cell) == len(parent)
