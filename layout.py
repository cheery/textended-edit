import boxmodel

class Mode(object):
    pass

class HMode(Mode):
    def __init__(self, subj):
        self.subj = subj
        self.contents = [boxmodel.Caret(subj, 0)]

    def append(self, frame):
        self.contents.append(frame)

    def extend(self, frame):
        self.contents.extend(frame)

    def __call__(self, func, node):
        index = self.subj.contents.index(node)
        resp = func(node)
        if isinstance(resp, Mode):
            resp = resp.freeze()
        self.contents.append(boxmodel.Caret(self.subj, index))
        if isinstance(resp, boxmodel.Frame):
            self.contents.append(resp)
        else:
            self.contents.extend(resp)
        self.contents.append(boxmodel.Caret(self.subj, index + 1))

    def freeze(self):
        self.contents.append(boxmodel.Caret(self.subj, len(self.subj)))
        return boxmodel.hpack(self.contents)

class VMode(Mode):
    def __init__(self, subj):
        self.subj = subj
        self.contents = [boxmodel.Caret(subj, 0)]
        self.indent = 0

    def append(self, frame):
        self.contents.append(frame)

    def extend(self, frame):
        self.contents.extend(frame)

    def __call__(self, func, node):
        index = self.subj.contents.index(node)
        resp = func(node)
        if isinstance(resp, Mode):
            resp = resp.freeze()
        self.contents.append(boxmodel.Caret(self.subj, index))
        if len(self.contents) > 2 and self.indent != 0:
            if isinstance(resp, boxmodel.Frame):
                resp = [resp]
            self.contents.append(boxmodel.hpack([boxmodel.Glue(self.indent)] + resp))
        else:
            if isinstance(resp, boxmodel.Frame):
                self.contents.append(resp)
            else:
                self.contents.append(boxmodel.hpack(resp))
        self.contents.append(boxmodel.Caret(self.subj, index + 1))

    def freeze(self):
        self.contents.append(boxmodel.Caret(self.subj, len(self.subj)))
        return boxmodel.vpack(self.contents)
