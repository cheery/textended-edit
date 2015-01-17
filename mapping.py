import boxmodel

class Mapping(object):
    __slots__ = ['mappings', 'subj', 'tokens', 'index']
    def __init__(self, mappings, subj, index=None):
        self.mappings = mappings
        self.subj = subj
        self.tokens = ()
        self.index = index
        mappings[subj] = self

    def __len__(self):
        return len(self.subj)

    def __getitem__(self, index):
        assert self.subj.type == 'list'
        return Mapping(self.mappings, self.subj[index], index)

    def apply(self, layoutfn, *args):
        self.tokens = list(layoutfn(self, *args))
        return self.tokens
