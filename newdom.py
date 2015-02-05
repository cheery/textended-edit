import schema

class Document(object):
    def __init__(self, contents):
        self.contents = contents
        for i, node in enumerate(contents):
            node.index = i

    def __getitem__(self, index):
        return self.contents[index]

    def __len__(self):
        return len(self.contents)

    def drop(self, start, stop):
        start = clamp(start, 0, len(self))
        stop = clamp(stop, 0, len(self))
        contents = self.contents[start:stop]
        blanks = []
        for node in contents:
            blanks.extend(node.detach(start, stop))
        self.contents = self.contents[:start] + blanks + self.contents[stop:]

        for i, node in enumerate(self.contents):
            node.index = i
        return contents

    def yank(self, start, stop):
        return self.contents[start:stop]

    def put(self, index, contents):
        assert isinstance(contents, list)
        index = clamp(index, 0, len(self))
        self.contents = self.contents[:index] + contents + self.contents[index:]
        for i, node in enumerate(self.contents):
            node.index = i

class Node(object):
    parent = None

    @property
    def root(self):
        root = self
        while root.parent is not None:
            root = root.parent
        return root

class Group(Node):
    def __init__(self, rule, contents):
        assert isinstance(rule, schema.Rule) and len(contents) == len(rule.slots)
        self.rule = rule
        self.contents = contents
        for node in contents:
            node.parent = self

    def __getitem__(self, index):
        return self.contents[index]

    def __len__(self):
        return len(self.contents)

    @property
    def left(self):
        return self.contents[0].left

    @property
    def right(self):
        return self.contents[-1].right

    def detach(self, start, stop, item):
        if start <= self.left and self.right < stop:
            if self.parent is None:
                return []
            else:
                return self.parent.detach(start, stop, self)
        else:
            blank = Symbol(u"")
            index = self.contents.index(item)
            self.contents[index] = blank
            item.parent = None
            blank.parent = self
            return [blank]

    def plant(self, document, place, root, block):
        self.contents[self.contents.index(place)] = root
        root.parent = self
        place.parent = None
        index = place.index
        document.drop(index, index+1)
        document.put(index, block)

class Symbol(Node):
    def __init__(self, string):
        self.string = string
        self.index = None

    def __getitem__(self, index):
        return self.string[index]

    def __len__(self):
        return len(self.string)

    def detach(self, start, stop):
        if self.parent is None:
            return []
        else:
            return self.parent.detach(start, stop, self)

    def drop(self, start, stop):
        start = clamp(start, 0, len(self))
        stop = clamp(stop, 0, len(self))
        string = self.string[start:stop]
        self.string = self.string[:start] + self.string[stop:]
        return string

    def yank(self, start, stop):
        return self.string[start:stop]

    def put(self, index, string):
        assert isinstance(string, (str, unicode))
        index = clamp(index, 0, len(self))
        self.string = self.string[:index] + string + self.string[index:]

    @property
    def left(self):
        return self.index

    @property
    def right(self):
        return self.index

def clamp(x, low, high):
    return min(max(x, low), high)

