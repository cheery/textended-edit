class Position(object):
    def __init__(self, subj, index):
        self.subj = subj
        self.index = index

    @property
    def above(self):
        parent = self.subj.parent
        if parent is not None:
            return Position(parent, parent.index(self.subj))

    @classmethod
    def top(cls, node):
        while node.islist() and len(node) > 0:
            node = node[0]
        return cls(node, 0)

    @classmethod
    def bottom(cls, node):
        while node.islist() and len(node) > 0:
            node = node[len(node) - 1]
        return cls(node, len(node))

    def __add__(self, number):
        return Position(self.subj, self.index+number)

    def __sub__(self, number):
        return Position(self.subj, self.index-number)

    def __eq__(self, other):
        return self.subj is other.subj and self.index == other.index

class Selection(object):
    def __init__(self, visual, head, tail=None):
        self.visual = visual
        self.set(head, tail)

    @property
    def document(self):
        return self.subj.document

    @property
    def start(self):
        return min(self.subj_head, self.subj_tail)

    @property
    def stop(self):
        return max(self.subj_head, self.subj_tail)

    def set(self, head, tail=None):
        tail = head if tail is None else tail
        if head.subj is tail.subj:
            self.subj = head.subj
            self.subj_head = head.index
            self.subj_tail = tail.index
        else:
            h0 = hierarchy_of(head.subj)
            h1 = hierarchy_of(tail.subj)
            i = 0
            for p0, p1 in zip(h0, h1):
                if p0 is not p1:
                    break
                i += 1
            if i == 0:
                return False
            self.subj = subj = h0[i-1]
            head_inc = i < len(h0)
            self.subj_head = subj.index(h0[i]) if head_inc else head.index
            tail_inc = i < len(h1)
            self.subj_tail = subj.index(h1[i]) if tail_inc else tail.index
            if self.subj_tail <= self.subj_head:
                self.subj_head += head_inc
            else:
                self.subj_tail += tail_inc
        self.head = head
        self.tail = tail
        self.x_anchor = None
        return True

    def drop(self):
        contents = self.subj.drop(self.start, self.stop)
        self.set(Position(self.subj, self.start))
        return contents

    def yank(self):
        contents = self.subj.yank(self.start, self.stop)
        return contents

    def put(self, contents):
        if self.head != self.tail:
            self.drop()
        self.subj.put(self.subj_head, contents)
        self.set(Position(self.subj, self.subj_head + len(contents)))
        return contents

def hierarchy_of(node):
    result = [node]
    while node.parent is not None:
        result.append(node.parent)
        node = node.parent
    result.reverse()
    return result
