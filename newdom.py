class Document(object):
    def __init__(self, contents):
        self.contents = contents

    def __getitem__(self, index):
        return self.contents[index]

    def __len__(self):
        return len(self.contents)

    def drop(self, start, stop):
        start = clamp(start, 0, len(self))
        stop = clamp(stop, 0, len(self))
        contents = self.contents[start:stop]
        self.contents = self.contents[:start] + self.contents[stop:]
        return contents

    def yank(self, start, stop):
        return self.contents[start:stop]

    def put(self, index, contents):
        assert isinstance(contents, list)
        index = clamp(index, 0, len(self))
        self.contents = self.contents[:index] + contents + self.contents[index:]

class Symbol(object):
    def __init__(self, string):
        self.string = string

    def __getitem__(self, index):
        return self.string[index]

    def __len__(self):
        return len(self.string)

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

def clamp(x, low, high):
    return min(max(x, low), high)

