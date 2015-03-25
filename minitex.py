# An attempt to provide combinators for constructing documents.
from boxmodel import *

# A convenience wrapper to form a scope from a dictionary.
class Environ(object):
    __slots__ = ('parent', 'values')
    def __init__(self, parent, values):
        self.parent = parent
        self.values = values

    def __getattr__(self, name):
        if name in self.values:
            return self.values[name]
        return getattr(self.parent, name)

    @classmethod
    def let(cls, parent, values):
        if len(values) > 0:
            return cls(parent, values)
        return parent

    @classmethod
    def root(cls, **values):
        env = cls(None, values)
        if 'line_break' not in values:
            env.values['line_break'] = line_break_greedy
        return env

def fold(item, env):
    if isinstance(item, Frame):
        return [item]
    elif callable(item):
        return item(env)
    else:
        return env.font(item, env.font_size, color=env.color)

def toplevel(contents, env, **values):
    env = Environ.let(env, values)
    return vpack(list(vbox(contents)(env)))

# These 'folding' -combinators take input and return a closure constructing boxes for environ.
def scope(contents, **values):
    def scope_fold(env):
        env = Environ.let(env, values)
        for item in contents:
            for box in fold(item, env):
                yield box
    return scope_fold

# imitates restricted horizontal mode
def hbox(contents, **values):
    def hbox_fold(env):
        env = Environ.let(env, values)
        boxes = []
        for item in contents:
            boxes.extend(fold(item, env))
        yield hpack(boxes)
    return hbox_fold

# imitates both vertical modes
def vbox(contents, **values):
    def vbox_fold(env):
        env = Environ.let(env, values)
        boxes = []
        paragraph = []
        for item in contents:
            for box in fold(item, env):
                if box.get_hint('vertical'):
                    if len(paragraph) > 0:
                        boxes.extend(env.line_break(paragraph, env))
                        paragraph = []
                    boxes.append(box)
                else:
                    paragraph.append(box)
        if len(paragraph) > 0:
            boxes.extend(env.line_break(paragraph, env))
        yield vpack(boxes)
    return vbox_fold

def no_line_break(paragraph, env):
    yield hpack(paragraph)

def line_break_greedy(paragraph, env):
    line = []
    remaining = env.page_width
    breakpoint = 0
    for box in paragraph:
        if remaining < box.width and breakpoint > 0:
            yield hpack(line[:breakpoint-1])
            line = line[breakpoint:]
            breakpoint = 0
            remaining = env.page_width - sum(box.width for box in line)
        line.append(box)
        remaining -= box.width
        if box.get_hint('break'):
            breakpoint = len(line)
    yield hpack(line)

def line_break_greedy_justify(paragraph, env):
    line = []
    remaining = env.page_width
    breakpoint = 0
    for box in paragraph:
        if remaining < box.width and breakpoint > 0:
            yield hpack(line[:breakpoint-1], to_dimen=env.page_width)
            line = line[breakpoint:]
            breakpoint = 0
            remaining = env.page_width - sum(box.width for box in line)
        line.append(box)
        remaining -= box.width
        if box.get_hint('break'):
            breakpoint = len(line)
    yield hpack(line)

#
def line_break(paragraph, env):
    memoized = {}
    page_width = env.page_width
    def calc(start):
        if start >= len(paragraph):
            return len(paragraph), 0
        if start in memoized:
            return memoized[start]
        width = paragraph[start].width
        stop = start + 1
        best = None
        while stop < len(paragraph) and (width < page_width and best is None):
            box = paragraph[stop] 
            if box.get_hint('break'):
                pen = calc(stop+1)[1] + penalty(page_width, width)
                if best and pen < best[1]:
                    best = stop+1, pen
            width += box.width
            stop += 1
        if best is None:
            best = len(paragraph), float('inf')
        memoized[start] = best
        return best
    index = 0
    while index < len(paragraph):
        jndex = calc(index)[0]
        yield hpack(paragraph[index:jndex])
        index = jndex

def penalty(page_width, width):
    #width = sum(box.width for box in line)
    if width <= page_width:
        return (page_width - width) ** 2
    return float('inf')

# paragraph break fold
def par(env):
    box = Glue(env.font_size)
    box.hint = {'vertical': True}
    yield box
