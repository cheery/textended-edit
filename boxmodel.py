class Frame(object):
    parent = None
    rect = None
    clue = None
    def traverse(self):
        yield self

class Box(Frame):
    def __init__(self, width, height, depth):
        self.width = width
        self.height = height
        self.depth = depth
        self.shift = 0

    @property
    def vsize(self):
        return self.height + self.depth

class LetterBox(Box):
    clue = 'horizontal'
    def __init__(self, width, height, depth, font, texcoords, padding, color):
        Box.__init__(self, width, height, depth)
        self.font = font
        self.texcoords = texcoords
        self.padding = padding
        self.color = color

class Glue(Frame):
    clue = 'horizontal'
    def __init__(self, width, shrink=0, stretch=0):
        self.width = width
        self.shrink = shrink
        self.stretch = stretch

    @property
    def vsize(self):
        return self.width

class Caret(object):
    parent = None
    clue = 'hoist'
    def __init__(self, subj, index):
        self.subj = subj
        self.index = index
        self.rect = None

    def traverse(self):
        yield self

class Composite(Box):
    def __init__(self, width, height, depth, contents):
        Box.__init__(self, width, height, depth)
        self.contents = contents
        for node in contents:
            node.parent = self

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

class VBox(Composite):
    pass

class HBox(Composite):
    pass

def hpack(contents):
    width = 0
    height = 0
    depth  = 0
    for node in contents:
        if isinstance(node, Frame):
            width += node.width
        if isinstance(node, Box):
            height = max(height, node.height + node.shift)
            depth = max(depth, node.depth - node.shift)
    return HBox(width, height, depth, contents)

def vpack(contents):
    width = 0
    vsize = 0
    for node in contents:
        if isinstance(node, Frame):
            vsize += node.vsize
        if isinstance(node, Box):
            width = max(width, node.width + node.shift)
    return VBox(width, 0, vsize, contents)
