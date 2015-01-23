import textended
import tempfile, os
from random import randint

class Document(object):
    def __init__(self, body, filename=None):
        self.body = body
        self.nodes = {}
        self.filename = filename
        self.ver = 1
        node_insert(self, body)

class Node(object):
    document = None
    parent = None

class Symbol(Node):
    type = 'symbol'
    def __init__(self, string):
        self.string = string

    def copy(self):
        return self.__class__(self.string)

    def __getitem__(self, index):
        return self.string[index]
    
    def __len__(self):
        return len(self.string)

    def drop(self, start, stop):
        text = self.string[start:stop]
        self.string = self.string[:start] + self.string[stop:]
        if self.document is not None:
            self.document.ver += 1
        return text

    def yank(self, start, stop):
        return self.string[start:stop]

    def put(self, index, string):
        assert isinstance(string, (str, unicode))
        self.string = self.string[:index] + string + self.string[index:]
        if self.document is not None:
            self.document.ver += 1

    def traverse(self):
        yield self

class Literal(Node):
    def __init__(self, ident, label, contents):
        self.contents = contents
        self.ident = ident
        self.label = label
        if isinstance(contents, list):
            self.type = 'list'
            for node in contents:
                assert isinstance(node, Node)
                assert node.parent is None
                node.parent = self
        elif isinstance(contents, str):
            self.type = 'binary'
        elif isinstance(contents, unicode):
            self.type = 'string'
    
    def __repr__(self):
        return "Literal({0.ident!r}, {0.label!r}, {0.type})".format(self)

    @property
    def label(self):
        return self._label

    @label.setter
    def label(self, label):
        self._label = label
        if self.document is not None:
            self.document.ver += 1
    
    def copy(self):
        return self.__class__(self.ident, self.label, self.yank(0, len(self)))

    def __getitem__(self, index):
        return self.contents[index]

    def index(self, obj):
        return self.contents.index(obj)
    
    def __len__(self):
        return len(self.contents)

    def drop(self, start, stop):
        contents = self.contents[start:stop]
        self.contents = self.contents[:start] + self.contents[stop:]
        if isinstance(contents, list):
            for node in contents:
                node.parent = None
                node_remove(self.document, node)
        if self.document is not None:
            self.document.ver += 1
        return contents

    def yank(self, start, stop):
        contents = self.contents[start:stop]
        if isinstance(contents, list):
            contents = [node.copy() for node in contents]
        return contents

    def put(self, index, contents):
        if self.type == 'binary' and isinstance(contents, unicode):
            contents = contents.encode('utf-8')
        self.contents = self.contents[:index] + contents + self.contents[index:]
        if self.type == 'list':
            for node in contents:
                assert isinstance(node, Node)
                assert node.parent is None
                node.parent = self
                node_insert(self.document, node)
        else:
            assert isinstance(contents, (str, unicode))
        if self.document is not None:
            self.document.ver += 1

    def traverse(self):
        yield self
        if not isinstance(self.contents, (str, unicode)):
            for node in self:
                for node in node.traverse():
                    yield node

def node_insert(document, node):
    if document is None:
        return
    assert node.document is None
    node.document = document
    if isinstance(node, Literal):
        if node.ident == "" or node.ident in document.nodes:
            ident = chr(randint(1, 255))
            while ident in document.nodes:
                ident += chr(randint(0, 255))
            node.ident = ident
        document.nodes[node.ident] = node
        if node.type == 'list':
            for subnode in node:
                node_insert(document, subnode)

def node_remove(document, node):
    assert node.document is document
    node.document = None
    if document is None:
        return
    if isinstance(node, Literal):
        del document.nodes[node.ident]
        if node.type == 'list':
            for subnode in node:
                node_remove(document, subnode)

def transform_enc(node):
    if isinstance(node, Symbol):
        return node.string
    if isinstance(node, Literal):
        return (node.ident, node.label, node.contents)

def transform_dec(obj):
    if isinstance(obj, tuple):
        return Literal(*obj)
    return Symbol(obj)

def load(path):
    with open(path, 'rb') as fd:
        contents = textended.load(fd, transform_dec)
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
    os.fdatasync(fd.fileno())
    fd.close()
    os.rename(fd.name, path)

class Position(object):
    def __init__(self, subj, index):
        self.subj = subj
        self.index = index

class Selection(object):
    def __init__(self, subj, head, tail):
        self.subj = subj
        self.head = head
        self.tail = tail
        self.x_anchor = None

    @property
    def start(self):
        return min(self.head, self.tail)
    
    @property
    def stop(self):
        return max(self.head, self.tail)

    @classmethod
    def top(cls, node):
        while node.type == 'list' and len(node) > 0:
            node = node[0]
        return cls(node, 0, 0)

    @classmethod
    def bottom(cls, node):
        while node.type == 'list' and len(node) > 0:
            node = node[len(node) - 1]
        return cls(node, len(node), len(node))

    def drop(self):
        contents = self.subj.drop(self.start, self.stop)
        self.head = self.tail = self.start
        return contents

    def yank(self):
        contents = self.subj.yank(self.start, self.stop)
        return contents

    def put(self, contents):
        if self.head != self.tail:
            self.drop()
        self.subj.put(self.head, contents)
        self.head = self.tail = self.head + len(contents)
        return contents
