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
        if 'text_align' not in values:
            env.values['text_align'] = line_justify
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

# Somewhat less clumsy implementation of minimum raggedness algorithm.
def line_break(paragraph, env):
    length = len(paragraph)
    page_width = env.page_width
    memo = []
    def penalty_of(index):
        return memo[length - index][0]

    def penalty(cut, width):
        # Adjustment to not penalize final line
        if cut == length and width*10 > page_width:
            return 0
        p = penalty_of(cut)
        if width <= page_width:
            return p + (page_width - width) ** 2
        return 2**10

    def cut_points(start):
        cut = start + 1
        width = paragraph[start].width
        none_yet = True
        while cut < length and (none_yet or width <= page_width):
            if paragraph[cut].get_hint('break'):
                yield width, cut
                none_yet = False
            width += paragraph[cut].width
            cut += 1
        if cut == length:
            yield width, cut

    def compute(start):
        if start == length:
            return (0, length)
        return min(
            (penalty(cut, width), cut)
            for width, cut in cut_points(start))

    index = length
    while index >= 0:
        memo.append(compute(index))
        index -= 1

    start = 0
    while start < length:
        cut = memo[length - start][1]
        yield env.text_align(env, paragraph[start:cut], cut==length)
        start = cut+1

def line_justify(env, line, is_last_line):
    if is_last_line:
        return hpack(line)
    return hpack(line, to_dimen=env.page_width)

def line_left(env, line, is_last_line):
    return hpack(line)

# paragraph break fold
def par(env):
    box = Glue(env.font_size)
    box.hint = {'vertical': True}
    yield box

def hfil(env):
    yield Glue(1, 0, 1+1j)

import math, time
# Table layouting
def table(rows, **values):
    def table_fold(env):
        env = Environ.let(env, values)
        tab = [[list(fold(cell, env)) for cell in row] for row in rows]
        col = [0 for i in range(max(map(len, tab)))]
        for row in tab:
            for i, cell in enumerate(row):
                col[i] = max(col[i], sum(x.width for x in cell))
        box = vpack([
            hpack([hpack(cell, to_dimen=w) for w, cell in zip(col, row)])
            for row in tab])
        if len(box) > 0:
            y = box[len(box)/2].offset
            if len(box)%2 == 0:
                y = (y + box[len(box)/2-1].offset) * 0.5
            box.height += y
            box.depth -= y
        yield box
    return table_fold
