import boxmodel

class Mapping(object):
    __slots__ = ['mappings', 'subj', 'tokens', 'index']
    def __init__(self, mappings, subj, index):
        self.mappings = mappings
        self.subj = subj
        self.index = index
        self.tokens = ()

    def __len__(self):
        return len(self.subj)

    def __getitem__(self, index):
        assert self.subj.islist()
        return Mapping(self.mappings, self.subj[index], index)

    def update(self, func, *args):
        self.mappings[self.subj] = self
        self.tokens = list(func(self, *args))
        return self.tokens
