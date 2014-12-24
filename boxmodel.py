class Frame(object):
    parent = None
    def traverse(self):
        yield self

class LetterBox(Frame):
    render = 1
    def __init__(self, width, height, depth, font, texcoords, padding):
        self.width  = width
        self.height = height
        self.depth  = depth
        self.font = font
        self.texcoords = texcoords
        self.padding = padding

class Glue(Frame):
    render = 2
    def __init__(self, width):
        self.width = width

class Caret(Frame):
    render = 0
    def __init__(self, subj, index):
        self.subj = subj
        self.index = index
        self.rect = None

class Composite(Frame):
    def index(self, obj):
        return self.contents.index(obj)

    def __getitem__(self, index):
        return self.contents[index]

    def __len__(self):
        return len(self.contents)

    def traverse(self):
        yield self
        for node in self:
            for node in node.traverse():
                yield node

class HBox(Composite):
    render = 1
    def __init__(self, width, height, depth, contents):
        self.width = width
        self.height = height
        self.depth = depth
        self.contents = contents
        self.rect = None
        _parent(self, contents)

class VBox(Composite):
    render = 1
    def __init__(self, width, height, depth, contents):
        self.width = width
        self.height = height
        self.depth = depth
        self.contents = contents
        self.rect = None
        _parent(self, contents)

def _parent(subj, contents):
    for node in contents:
        node.parent = subj

def hpack(contents):
    width = sum(node.width for node in contents if node.render > 0)
    height = max(node.height for node in contents if node.render == 1)
    depth = max(node.depth for node in contents if node.render == 1)
    return HBox(width, height, depth, contents)

def vpack(contents):
    width = max(node.width for node in contents if node.render == 1)
    vsize = sum(vsize_of(node) for node in contents if node.render > 0)
    return VBox(width, 0, vsize, contents)

def vsize_of(node):
    if node.render == 0:
        return 0
    if node.render == 1:
        return node.height + node.depth
    if node.render == 2:
        return node.width
