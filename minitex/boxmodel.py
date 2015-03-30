
class Frame(object):
    parent = None
    quad = None
    hint = None
    subj = None
    index = -1
    offset = 0
    def traverse(self):
        yield self

    def set_subj(self, subj, index=0):
        if isinstance(subj, (str, unicode)):
            return self
        self.subj = subj
        self.index = index
        return self

    def get_hint(self, name, default=None):
        if self.hint is not None:
            return self.hint.get(name, default)
        return default

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
    def __init__(self, width, height, depth, font, texcoords, padding, color):
        Box.__init__(self, width, height, depth)
        self.font = font
        self.texcoords = texcoords
        self.padding = padding
        self.color = color
        assert isinstance(color, (tuple, list)) and len(color) == 4, repr(color)

class ImageBox(Box):
    def __init__(self, width, height, depth, source, color):
        Box.__init__(self, width, height, depth)
        self.source = source
        self.color = color

class Glue(Frame):
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
            height = max(height, node.height - node.shift)
            depth = max(depth, node.depth + node.shift)
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
    glue.computed = glue.width
    if expand.real > 0:
        if glue.stretch.imag == expand.imag:
            glue.computed = glue.width + expand.real * glue.stretch.real
    else:
        if glue.shrink.imag == expand.imag:
            glue.computed = glue.width + expand.real * glue.shrink.real
    return glue.computed

def pick_nearest(box, x, y):
    def nearest(node, maxdist):
        near, distance = None, maxdist
        if isinstance(node, Composite):
            dx, dy = delta_point_quad(x, y, node.quad)
            if dx**2 + dy**4 > maxdist:
                return near, distance
            for child in node:
                n, d = nearest(child, distance)
                if d < distance:
                    near = n
                    distance = d
            return near, distance
        elif node.subj is not None:
            dx, dy = delta_point_quad(x, y, node.quad)
            offset = (x - (node.quad[0] + node.quad[2])*0.5) > 0
            return (node.subj, node.index + offset), dx**2 + dy**4
        else:
            return None, float('inf')
    return nearest(box, 500**4)[0]

def delta_point_quad(x, y, quad):
    x0, y0, x1, y1 = quad
    return min(max(x0, x), x1) - x, min(max(y0, y), y1) - y
