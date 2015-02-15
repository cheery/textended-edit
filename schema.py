import dom

class Schema(object):
    def __init__(self, toplevel, rules, contexes):
        self.toplevel = toplevel
        self.rules = rules
        self.contexes = contexes
        for label, rule in rules.iteritems():
            rule.label = label

    def __getitem__(self, index):
        return self.rules[index]

    def recognize(self, node):
        if node.isblank():
            return 'blank'
        if node.issymbol():
            return 'symbol'
        if node.label == '##' and modeline.validate(node):
            return '##'
        elif node.label == '#' and modechange.validate(node):
            return '#'
        elif len(node.label) > 0 and node.label in self.rules:
            rule = self.rules[node.label]
            if rule.validate(node):
                return rule
        if node.isstring():
            return 'string'
        if node.isbinary():
            return 'binary'
        if node.islist():
            return 'list'
        raise Exception("panic")

class Context(object):
    def __init__(self, name):
        self.name = name
        self.valid_rules = set()
        self.valid_contexes = set()
        self.valid_terms = set()

    def validate(self, node):
        """
        Validation of every node is shallow.
        The construct should be recognized even if it were in a wrong context.
        """
        return True

    def build(self, function, node):
        return function(self, node)

    def __repr__(self):
        return "<{}>".format(self.name)

    def blank(self):
        return dom.Symbol(u"")

class Symbol(object):
    def validate(self, node):
        return node.issymbol()

    def build(self, function, node):
        return function(self, node)

    def __repr__(self):
        return "<symbol>"

    def blank(self):
        return dom.Symbol(u"")

class Rule(object):
    label = ''

    def __repr__(self):
        return "<{} {}>".format(self.__class__.__name__, self.label)

class ListRule(Rule):
    pass

class Sequence(ListRule):
    def __init__(self, sequence):
        self.sequence = sequence

    def __getitem__(self, index):
        return self.sequence[index]

    def __len__(self):
        return len(self.sequence)

    def __repr__(self):
        if self.label:
            return "{{:{} {}}}".format(self.label, ' '.join(map(repr, self.sequence)))
        return "{{{}}}".format(' '.join(map(repr, self.sequence)))

    def validate(self, node):
        if not node.islist():
            return False
        if len(node) <> len(self):
            return False
        return all(subrule.validate(subnode) for subrule, subnode in zip(self, node))

    def build(self, function, node):
        return [subrule.build(function, subnode) for subrule, subnode in zip(self, node)]

    def blank(self):
        return dom.Literal(self.label, [subrule.blank() for subrule in self])

class Star(ListRule):
    def __init__(self, rule):
        self.rule = rule

    def validate(self, node):
        if not node.islist():
            return False
        return all(self.rule.validate(subnode) for subnode in node)

    def build(self, function, node):
        return [self.rule.build(function, subnode) for subnode in node]

    def __repr__(self):
        return repr(self.rule) + '*'

    def blank(self):
        return dom.Literal(self.label, [])

class Plus(ListRule):
    def __init__(self, rule):
        self.rule = rule

    def validate(self, node):
        if not node.islist():
            return False
        if len(node) == 0:
            return False
        return all(self.rule.validate(subnode) for subnode in node)

    def build(self, function, node):
        return [self.rule.build(function, subnode) for subnode in node]

    def __repr__(self):
        return repr(self.rule) + '+'

    def blank(self):
        return dom.Literal(self.label, [self.rule.blank()])

class String(Rule):
    def validate(self, node):
        return node.isstring()

    def build(self, function, node):
        return function(self, node)

    def __repr__(self):
        return "<string>"

    def blank(self):
        return dom.Literal(self.label, u"")

class Binary(Rule):
    def validate(self, node):
        return node.isbinary()

    def build(self, function, node):
        return function(self, node)

    def __repr__(self):
        return "<binary>"

    def blank(self):
        return dom.Literal(self.label, "")

modeline = Plus(Symbol())
modeline.label = '##'
modechange = Sequence([Plus(Symbol()), Star(Context("*"))])
modechange.label = '#'
blankschema = Schema('*', {}, {})

def has_modeline(body):
    if len(body) > 0:
        return modeline.validate(body[0])
