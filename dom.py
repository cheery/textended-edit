import textended
import tempfile, os
from random import randint

class Document(object):
    def __init__(self, body, name=None):
        self.nodes = {}
        self.body = node_insert(self, body)
        self.name = name
        self.history = []

    @property
    def ver(self):
        return len(self.history) + 1

    def _update(self, change):
        self.history.append(change)

    def undo(self):
        if len(self.history) == 0:
            return
        change = self.history.pop(-1)
        return change.undo()

    def transaction(self, head, tail):
        transaction = Transaction(self, head, tail)
        self._update(transaction)
        return transaction

class Drop(object):
    def __init__(self, subj, index, dropped):
        self.subj = subj
        self.index = index
        self.dropped = dropped

    def undo(self):
        self.subj.put(self.index, self.dropped, undo=True)

class Put(object):
    def __init__(self, subj, index, inserted):
        self.subj = subj
        self.index = index
        self.inserted = inserted

    def undo(self):
        results = self.subj.drop(self.index, self.index + len(self.inserted), undo=True)
        assert len(results) == len(self.inserted)
        assert all(a is b for a, b in zip(self.inserted, results))

class Relabel(object):
    def __init__(self, subj, old_label, new_label):
        self.subj = subj
        self.old_label = old_label
        self.new_label = new_label

    def undo(self):
        self.subj._label = self.old_label

class Transaction(object):
    def __init__(self, document, head, tail):
        self.document = document
        self.head = head
        self.tail = tail

    def commit(self, head, tail):
        if self.document.history[-1] is self:
            self.document.history.pop(-1)
        else:
            self.document._update(Commit(self, head, tail))

    def rollback(self):
        index = self.document.history.index(self)
        while len(self.document.history) > index+1:
            change = self.document.history.pop(-1)
            change.undo()
        self.document.history.pop(-1)

class Commit(object):
    def __init__(self, transaction, head, tail):
        self.head = head
        self.tail = tail
        self.transaction = transaction

    def undo(self):
        self.transaction.rollback()
        return self.transaction

class Node(object):
    document = None
    parent = None

    def isblank(self):
        return False

    def issymbol(self):
        return False

    def isbinary(self):
        return False

    def isstring(self):
        return False

    def islist(self):
        return False

class Symbol(Node):
    def __init__(self, label, ident=''):
        self.label = label
        self.ident = ident

    def copy(self):
        return self.__class__(self.label, self.ident)

    def __getitem__(self, index):
        return self.label[index]
    
    def __len__(self):
        return len(self.label)

    def drop(self, start, stop, undo=False):
        start = max(0, min(len(self), start))
        stop = max(0, min(len(self), stop))
        text = self.label[start:stop]
        self.label = self.label[:start] + self.label[stop:]
        if not undo:
            self.document._update(Drop(self, start, text))
        return text

    def yank(self, start, stop, undo=False):
        return self.label[start:stop]

    def put(self, index, label, undo=False):
        index = max(0, min(len(self), index))
        assert isinstance(label, (str, unicode))
        self.label = self.label[:index] + label + self.label[index:]
        if not undo:
            self.document._update(Put(self, index, label))

    def traverse(self):
        yield self

    def isblank(self):
        return len(self.label) == 0

    def issymbol(self):
        return True

    def is_empty(self):
        return len(self) == 0

class Literal(Node):
    def __init__(self, label, contents, ident=""):
        self.ident = ident
        self._label = unicode(label)
        assert isinstance(ident, str), repr(ident)
        assert isinstance(self.label, unicode), repr(self.label)
        if isinstance(contents, (str, unicode)):
            self.contents = contents
        else:
            self.contents = []
            for node in contents:
                assert isinstance(node, Node)
                assert node.parent is None
                node.parent = self
                self.contents.append(node)
    
    def __repr__(self):
        type = 'list'
        if isinstance(self.contents, str):
            type = 'binary'
        if isinstance(self.contents, unicode):
            type = 'string'
        return "Literal({0.label!r}, {1}, {0.ident!r})".format(self, type)

    @property
    def label(self):
        return self._label

    @label.setter
    def label(self, new_label):
        old_label = self._label
        self._label = new_label
        if self.document is not None:
            self.document._update(Relabel(self, old_label, new_label))
    
    def copy(self):
        return self.__class__(self.label, self.yank(0, len(self)), self.ident)

    def __getitem__(self, index):
        return self.contents[index]

    def index(self, obj):
        return self.contents.index(obj)
    
    def __len__(self):
        return len(self.contents)

    def is_empty(self):
        if self.islist():
            return all(it.is_empty() for it in self)
        return len(self) == 0

    def drop(self, start, stop, undo=False):
        start = max(0, min(len(self), start))
        stop = max(0, min(len(self), stop))
        contents = self.contents[start:stop]
        self.contents = self.contents[:start] + self.contents[stop:]
        if isinstance(contents, list):
            for node in contents:
                node.parent = None
                node_remove(self.document, node)
        if not undo:
            self.document._update(Drop(self, start, contents))
            if self.islist():
                contents = [node.copy() for node in contents]
        return contents

    def yank(self, start, stop):
        contents = self.contents[start:stop]
        if isinstance(contents, list):
            contents = [node.copy() for node in contents]
        return contents

    def put(self, index, contents, undo=False):
        index = max(0, min(len(self), index))
        if self.isbinary() and isinstance(contents, unicode):
            contents = contents.encode('utf-8')
        self.contents = self.contents[:index] + contents + self.contents[index:]
        if self.islist():
            for node in contents:
                assert isinstance(node, Node)
                assert node.parent is None
                node.parent = self
                node_insert(self.document, node)
        else:
            assert isinstance(contents, (str, unicode))
        if not undo:
            self.document._update(Put(self, index, contents))

    def traverse(self):
        yield self
        if not isinstance(self.contents, (str, unicode)):
            for node in self:
                for node in node.traverse():
                    yield node

    def isbinary(self):
        return isinstance(self.contents, str)

    def isstring(self):
        return isinstance(self.contents, unicode)

    def islist(self):
        return isinstance(self.contents, list)

def node_insert(document, node):
    assert document is not None
    assert node.document is None
    node.document = document
    if node.ident == "" or node.ident in document.nodes:
        ident = chr(randint(1, 255))
        while ident in document.nodes:
            ident += chr(randint(0, 255))
        node.ident = ident
    document.nodes[node.ident] = node
    if node.islist():
        for subnode in node:
            node_insert(document, subnode)
    return node

def node_remove(document, node):
    assert node.document is document
    node.document = None
    if document is None:
        return
    del document.nodes[node.ident]
    if node.islist():
        for subnode in node:
            node_remove(document, subnode)

def transform_enc(node):
    if isinstance(node, Symbol):
        return (node.label, None, node.ident)
    if isinstance(node, Literal):
        return (node.label, node.contents, node.ident)

def transform_dec(label, contents, ident):
    if contents is None:
        return Symbol(label, ident)
    else:
        return Literal(label, contents, ident)

def load(path):
    with open(path, 'rb') as fd:
        contents = list(textended.load(fd, transform_dec))
    return contents

def dump(fd, document):
    textended.dump(document.body, fd, transform_enc)

def save(path, contents):
    fd = tempfile.NamedTemporaryFile(
        prefix=os.path.basename(path),
        dir=os.path.dirname(path),
        delete=False)
    textended.dump(contents, fd, transform_enc)
    fd.flush()
    #os.fdatasync(fd.fileno())
    fd.close()
    os.rename(fd.name, path)
