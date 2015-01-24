class Frame(object):
    parent = None
    quad = None
    clue = None
    subj = None
    index = -1
    offset = 0
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
        self.computed = 0

    @property
    def vsize(self):
        return self.width

class Composite(Box):
    def __init__(self, width, height, depth, contents):
        Box.__init__(self, width, height, depth)
        self.contents = contents
        for node in contents:
            assert isinstance(node, Frame)
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

class Padding(Composite):
    def __init__(self, box, padding, background=None, color=None):
        left, top, right, bottom = padding
        box.offset = left
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
    expand, width = apply_dimen(to_dimen, width, shrink, stretch)
    x = 0
    for node in contents:
        node.offset = x
        if isinstance(node, Glue):
            x += set_dimen(node, expand)
        else:
            x += node.width
    return HBox(width, height, depth, contents)

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
    expand, vsize = apply_dimen(to_dimen, vsize, shrink, stretch)
    y = 0
    for node in contents:
        if isinstance(node, Glue):
            node.offset = y
            y += set_dimen(node, expand)
        else:
            node.offset = y + node.height
            y += node.vsize
    return VBox(width, 0, vsize, contents)

def sum_dimen(a, b):
    if a.imag == b.imag:
        return a + b.real
    elif a.imag < b.imag:
        return b
    else:
        return a

def apply_dimen(to_dimen, size, shrink, stretch):
    if to_dimen is None:
        return 0, size
    x = to_dimen - size
    if x < 0 and shrink.real > 0:
        x = (x / shrink.real) + (shrink.imag * 1j)
    elif x > 0 and stretch.real > 0:
        x = (x / stretch.real) + (stretch.imag * 1j)
    return x, to_dimen

def set_dimen(glue, expand):
    if expand.real > 0:
        glue.computed = glue.width + expand.real * glue.shrink.real
    else:
        glue.computed = glue.width + expand.real * glue.stretch.real
    return glue.computed
