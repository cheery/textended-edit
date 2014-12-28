import textended
import tempfile, os

class Symbol(object):
    def __init__(self, string):
        self.parent = None
        self.string = string
        self.type = 'symbol'

    def copy(self):
        return self.__class__(self.string)

    def __getitem__(self, index):
        return self.string[index]
    
    def __len__(self):
        return len(self.string)

    def drop(self, start, stop):
        text = self.string[start:stop]
        self.string = self.string[:start] + self.string[stop:]
        return text

    def yank(self, start, stop):
        return self.string[start:stop]

    def put(self, index, string):
        assert isinstance(string, (str, unicode))
        self.string = self.string[:index] + string + self.string[index:]

    def traverse(self):
        yield self

class Node(object):
    def __init__(self, ident, label, contents):
        self.parent = None
        self.contents = contents
        self.ident = ident
        self.label = label
        if isinstance(contents, list):
            self.type = 'list'
            for node in contents:
                assert isinstance(node, (Symbol, Node))
                assert node.parent is None
                node.parent = self
        elif isinstance(contents, str):
            self.type = 'binary'
        elif isinstance(contents, unicode):
            self.type = 'string'
    
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
        return contents

    def yank(self, start, stop):
        contents = self.contents[start:stop]
        if isinstance(contents, list):
            contents = [node.copy() for node in contents]

        return contents

    def put(self, index, contents):
        self.contents = self.contents[:index] + contents + self.contents[index:]
        if self.type == 'list':
            for node in contents:
                assert isinstance(node, (Symbol, Node))
                assert node.parent is None
                node.parent = self
        else:
            assert isinstance(contents, (str, unicode))

    def traverse(self):
        yield self
        if not isinstance(self.contents, (str, unicode)):
            for node in self:
                for node in node.traverse():
                    yield node

def transform_enc(node):
    if isinstance(node, Symbol):
        return node.string
    if isinstance(node, Node):
        return (node.ident, node.label, node.contents)

def transform_dec(obj):
    if isinstance(obj, tuple):
        return Node(*obj)
    return Symbol(obj)

def load(path):
    with open(path) as fd:
        contents = textended.load(fd, transform_dec)
    return contents

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
