class Frame(object):
    parent = None
    quad = None
    clue = None
    subj = None
    index = -1
    def traverse(self):
        yield self

    def set_subj(self, subj, index=0):
        self.subj = subj
        self.index = index
        return self

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

class ImageBox(Box):
    clue = 'horizontal'
    def __init__(self, width, height, depth, source, color):
        Box.__init__(self, width, height, depth)
        self.source = source
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

    def with_expand(self, expand):
        if expand.real > 0:
            return self.width + expand.real * self.shrink.real
        else:
            return self.width + expand.real * self.stretch.real

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
    expand = 0

class HBox(Composite):
    expand = 0

class Padding(Composite):
    def __init__(self, box, padding, background=None, color=None):
        left, top, right, bottom = padding
        Composite.__init__(self, box.width + left + right, box.height + top, box.depth + bottom, [box])
        self.padding = padding
        self.background = background
        self.color = color

class Patch9(object):
    def __init__(self, source):
        self.source = source

def hpack(contents, to_dimen=None):
    width = 0
    height = 0
    depth  = 0
    shrink = 0
    stretch = 0
    for node in contents:
        if isinstance(node, Frame):
            width += node.width
        if isinstance(node, Box):
            height = max(height, node.height + node.shift)
            depth = max(depth, node.depth - node.shift)
        if isinstance(node, Glue):
            shrink = sum_dimen(shrink, node.shrink)
            stretch = sum_dimen(stretch, node.stretch)
    box = HBox(width, height, depth, contents)
    if to_dimen is not None:
        box.expand = apply_dimen(to_dimen - width, shrink, stretch)
        box.width = to_dimen
    return box

def vpack(contents, to_dimen=None):
    width = 0
    vsize = 0
    shrink = 0
    stretch = 0
    for node in contents:
        if isinstance(node, Frame):
            vsize += node.vsize
        if isinstance(node, Box):
            width = max(width, node.width + node.shift)
        if isinstance(node, Glue):
            shrink = sum_dimen(shrink, node.shrink)
            stretch = sum_dimen(stretch, node.stretch)
    box = VBox(width, 0, vsize, contents)
    if to_dimen is not None:
        box.expand = apply_dimen(to_dimen - vsize, shrink, stretch)
        box.depth = to_dimen
    return box

def sum_dimen(a, b):
    if a.imag == b.imag:
        return a + b.real
    elif a.imag < b.imag:
        return b
    else:
        return a

def apply_dimen(x, shrink, stretch):
    if x < 0 and shrink.real > 0:
        return (x / shrink.real) + (shrink.imag * 1j)
    if x > 0 and stretch.real > 0:
        return (x / stretch.real) + (stretch.imag * 1j)
    return x
