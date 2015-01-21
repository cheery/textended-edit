import boxmodel

class Mapping(object):
    __slots__ = ['mappings', 'func', 'subj', 'tokens', 'index']
    def __init__(self, mappings, func):
        self.mappings = mappings
        self.func = func
        self.tokens = ()

    def __len__(self):
        return len(self.subj)

    def __getitem__(self, index):
        assert self.subj.type == 'list'
        submapping = Mapping(self.mappings, self.func)
        return submapping.update(self.subj[index], index)

    def update(self, subj, index=None):
        self.mappings[subj] = self
        self.subj = subj
        self.index = index
        self.tokens = list(self.func(self))
        return self.tokens
