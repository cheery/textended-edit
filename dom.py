from random import randint
import textended

class Document(object):
    def __init__(self, body, workspace):
        self.nodes = {}
        self.body = self._insert(body)
        self.workspace = workspace

    def _insert(self, node):
        assert self is not None
        assert node.document is None
        node.document = self
        if node.ident == "" or node.ident in self.nodes:
            ident = chr(randint(1, 255))
            while ident in self.nodes:
                ident += chr(randint(0, 255))
            node.ident = ident
        self.nodes[node.ident] = node
        if isinstance(node, ListCell):
            for subnode in node:
                self._insert(subnode)
        return node

    def _remove(self, node):
        assert node.document is self
        node.document = None
        del self.nodes[node.ident]
        if isinstance(node, ListCell):
            for subnode in node:
                self._remove(subnode)

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
        result = []
        while self is not None:
            result.append(self)
            self = self.parent
        return result

    def order(self, other):
        assert self is not other
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
        return self.__class__(self.contents, self.mode, self.ident)

    def drop(self, start, stop):
        start = max(0, min(len(self), start))
        stop = max(0, min(len(self), stop))
        contents = self.contents[start:stop]
        self.contents = self.contents[:start] + self.contents[stop:]
        return contents

    def is_blank(self):
        return len(self.contents) == 0

    def is_external(self):
        return True

    def put(self, index, contents):
        assert isinstance(contents, (str, unicode))
        index = max(0, min(len(self), index))
        self.contents = self.contents[:index] + contents + self.contents[index:]

    def yank(self, start, stop):
        start = max(0, min(len(self), start))
        stop = max(0, min(len(self), stop))
        return self.contents[start:stop]

class ListCell(Cell):
    def __init__(self, label, contents, ident=""):
        self.ident = ident
        self.label = label
        self.contents = []
        for node in contents:
            assert isinstance(node, Cell)
            assert node.parent is None
            node.parent = self
            self.contents.append(node)

    def __getitem__(self, index):
        return self.contents[index]
    
    def __len__(self):
        return len(self.contents)

    def __repr__(self):
        return "<ListCell {}>".format(self.label)

    def copy(self):
        return self.__class__(self.label, self.yank(0, len(self)), self.ident)

    def drop(self, start, stop, undo=False):
        start = max(0, min(len(self), start))
        stop = max(0, min(len(self), stop))
        contents = self.contents[start:stop]
        self.contents = self.contents[:start] + self.contents[stop:]
        if isinstance(contents, list):
            for node in contents:
                assert node.parent is self
                node.parent = None
                node.document._remove(node)
        return contents

    def index(self, obj):
        return self.contents.index(obj)

    def is_blank(self):
        return self.is_external() or all(it.is_blank() for it in self) 

    def is_external(self):
        return len(self.contents) == 0

    def put(self, index, contents):
        index = max(0, min(len(self), index))
        self.contents = self.contents[:index] + contents + self.contents[index:]
        for node in contents:
            assert isinstance(node, Node)
            assert node.parent is None
            node.parent = self
            self.document._insert(node)

    def yank(self, start, stop):
        start = max(0, min(len(self), start))
        stop = max(0, min(len(self), stop))
        contents = self.contents[start:stop]
        contents = [node.copy() for node in contents]
        return contents


def transform_enc(node):
    print "warning: document format will change if the new document model turns out to be sufficient."
    assert isinstance(node, Cell), "{} not a cell".format(node)
    if node.symbol:
        return (node.contents, None, node.ident)
    elif isinstance(node, TextCell):
        return ("", node.contents, node.ident)
    else:
        return (node.label, node.contents, node.ident)

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
