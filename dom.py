from random import randint
import os
import tempfile
import textended

class Document(object):
    def __init__(self, body, workspace):
        self.cells = {}
        self.body = self._insert(body)
        self.workspace = workspace
        self.unstaged = []
        self.undos = []

    def _insert(self, cell):
        assert self is not None
        assert cell.document is None or cell.document is self
        cell.document = self
        if cell.ident == "" or cell.ident in self.cells:
            ident = chr(randint(1, 255))
            while ident in self.cells:
                ident += chr(randint(0, 255))
            cell.ident = ident
        self.cells[cell.ident] = cell
        if isinstance(cell, ListCell):
            for subcell in cell:
                self._insert(subcell)
        return cell

    def _remove(self, cell):
        assert cell.document is self
        del self.cells[cell.ident]
        if isinstance(cell, ListCell):
            for subcell in cell:
                self._remove(subcell)

    def commit(self, head, tail):
        if len(self.unstaged) == 0:
            return
        self.undos.append((head, tail, self.unstaged))
        self.unstaged = []

    def rollback(self):
        if len(self.unstaged) == 0:
            return []
        reverted = reversed(self.unstaged) 
        self.unstaged = []
        for action in reverted:
            getattr(action[0], action[1])(*action[2:])
        inverse = self.unstaged
        self.unstaged = []
        return inverse

    def undo(self):
        self.rollback()
        head, tail, self.unstaged = self.undos.pop(-1)
        self.rollback()
        return head, tail

class Cell(object):
    document = None
    parent = None
    symbol = False
    label = ""

    @property
    def context(self):
        grammar = self.document.workspace.grammar_of(self)
        if grammar is not None:
            return grammar.recognize_context(self)

    # this may or may not be needed
    @property
    def grammar(self):
        return self.document.workspace.grammar_of(self)

    @property
    def hierarchy(self):
        this = self
        result = []
        while this is not None:
            result.append(this)
            this = this.parent
        return result

    def order(self, other):
        assert self is not other
        assert self.document is other.document
        h0 = self.hierarchy
        h1 = other.hierarchy
        assert h0[-1] is h1[-1], "cells in different documents"
        while h0[-1] is h1[-1]:
            common = h0.pop()
            common = h1.pop()
        c0 = h0.pop()
        c1 = h1.pop()
        if common.index(c0) < common.index(c1):
            return common, self, other
        else:
            return common, other, self

    @property
    def rule(self):
        grammar = self.document.workspace.grammar_of(self)
        if grammar is not None:
            return grammar.recognize(self)

    def is_leftmost(self):
        return self.parent and self.parent.index(self) == 0

    def is_rightmost(self):
        return self.parent and self.parent.index(self) == len(self.parent) - 1

    @property
    def top(self):
        while not self.is_external():
            self = self[0]
        return self

    @property
    def bottom(self):
        while not self.is_external():
            self = self[len(self) - 1]
        return self

    @property
    def previous_external(self):
        parent = self.parent
        if parent:
            index = parent.index(self)
            if index > 0:
                return parent[index-1].bottom
            else:
                return parent.previous_external

    @property
    def next_external(self):
        parent = self.parent
        if parent:
            index = parent.index(self)
            if index + 1 < len(parent):
                return parent[index+1].top
            else:
                return parent.next_external

class TextCell(Cell):
    def __init__(self, contents, ident='', symbol=True):
        self.contents = unicode(contents)
        self.ident = ident
        self.symbol = symbol

    def __getitem__(self, index):
        return self.contents[index]

    def __len__(self):
        return len(self.contents)

    def __repr__(self):
        if self.symbol:
            return "<TextCell {}>".format(self.contents)
        else:
            return "<TextCell {!r}>".format(self.contents)

    def copy(self):
        return self.__class__(self.contents, self.ident, self.symbol)

    def drop(self, start, stop):
        start = max(0, min(len(self), start))
        stop = max(0, min(len(self), stop))
        contents = self.contents[start:stop]
        self.contents = self.contents[:start] + self.contents[stop:]
        self.document.unstaged.append((self, 'put', start, contents))
        return contents

    def is_blank(self):
        return len(self.contents) == 0

    def is_external(self):
        return True

    def put(self, index, contents):
        assert isinstance(contents, (str, unicode))
        index = max(0, min(len(self), index))
        self.contents = self.contents[:index] + contents + self.contents[index:]
        self.document.unstaged.append((self, 'drop', index, index+len(contents)))

    def yank(self, start, stop):
        start = max(0, min(len(self), start))
        stop = max(0, min(len(self), stop))
        return self.contents[start:stop]

class ListCell(Cell):
    def __init__(self, label, contents, ident=""):
        self.ident = ident
        self.label = label
        self.contents = []
        for cell in contents:
            assert isinstance(cell, Cell)
            assert cell.parent is None
            cell.parent = self
            self.contents.append(cell)

    def __getitem__(self, index):
        return self.contents[index]
    
    def __len__(self):
        return len(self.contents)

    def __repr__(self):
        return "<ListCell {}>".format(self.label)

    def copy(self):
        return self.__class__(self.label, self.yank(0, len(self)), self.ident)

    def dissolve(self):
        assert self.document is None and self.parent is None
        for cell in self.contents:
            assert cell.parent is self
            cell.parent = None
        return self.contents

    def drop(self, start, stop, undo=False):
        start = max(0, min(len(self), start))
        stop = max(0, min(len(self), stop))
        contents = self.contents[start:stop]
        self.contents = self.contents[:start] + self.contents[stop:]
        if isinstance(contents, list):
            for cell in contents:
                assert cell.parent is self
                cell.parent = None
                cell.document._remove(cell)
        self.document.unstaged.append((self, 'put', start, contents))
        return contents

    def index(self, obj):
        return self.contents.index(obj)

    def is_blank(self):
        return self.is_external() or all(it.is_blank() for it in self) 

    def is_external(self):
        return len(self.contents) == 0

    def put(self, index, contents):
        index = max(0, min(len(self), index))
        for cell in contents:
            assert isinstance(cell, Cell)
            assert cell.parent is None
            cell.parent = self
            self.document._insert(cell)
        self.contents = self.contents[:index] + contents + self.contents[index:]
        self.document.unstaged.append((self, 'drop', index, index+len(contents)))

    def yank(self, start, stop):
        start = max(0, min(len(self), start))
        stop = max(0, min(len(self), stop))
        contents = self.contents[start:stop]
        contents = [c.copy() for c in contents]
        return contents

    def unwrap(self):
        parent = self.parent
        index = parent.index(self)
        length = len(self.contents)
        parent.contents[index:index+1] = self.contents
        for cell in self.contents:
            assert cell.parent is self
            cell.parent = parent
        self.contents = []
        self.parent = None
        self.document.unstaged.append((parent, 'wrap', index, index+length, self))
        self.document._remove(self)
        return parent, index, index+length

    def wrap(self, start, stop, cell):
        assert len(cell.contents) == 0 and cell.parent is None
        cell.parent = self
        self.document._insert(cell)
        cell.contents = self.contents[start:stop]
        self.contents[start:stop] = [cell]
        for subcell in cell.contents:
            assert subcell.parent is self
            subcell.parent = cell
        self.document.unstaged.append((cell, 'unwrap'))
        return cell

def transform_enc(cell):
    "warning: document format will change if the new document model turns out to be sufficient."
    assert isinstance(cell, Cell), "{} not a cell".format(cell)
    if cell.symbol:
        return (cell.contents, None, cell.ident)
    elif isinstance(cell, TextCell):
        return ("", cell.contents, cell.ident)
    else:
        return (cell.label, cell.contents, cell.ident)

def transform_dec(label, contents, ident):
    if contents is None:
        return TextCell(label, ident, symbol=True)
    elif isinstance(contents, list):
        return ListCell(label, contents, ident)
    else:
        return TextCell(contents, ident, symbol=False)

def dump(fd, forest):
    textended.dump(forest, fd, transform_enc)

def load(path):
    with open(path, 'rb') as fd:
        forest = list(textended.load(fd, transform_dec))
    return forest

def save(path, forest):
    fd = tempfile.NamedTemporaryFile(
        prefix=os.path.basename(path),
        dir=os.path.dirname(path),
        delete=False)
    textended.dump(forest, fd, transform_enc)
    fd.flush()
    if hasattr(os, 'fdatasync'):
        os.fdatasync(fd.fileno())
    fd.close()
    os.rename(fd.name, path)
