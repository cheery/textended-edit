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
            return modeline
        elif node.label == '#' and modechange.validate(node):
            return modechange
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

    def recognize_in_context(self, node):
        if node.parent is None:
            return Star(self.toplevel)
        if len(node.label) > 0 and node.label != '@':
            return self.recognize(node)
        rule = self.recognize_in_context(node.parent)
        if isinstance(rule, ListRule):
            return rule.descend(node.parent, node)
        return self.recognize(node)

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

    def match(self, result):
        if result in self.valid_rules:
            return [self]
        for term in self.valid_terms:
            if term.match_term(result):
                return [self]
        for ctx in self.valid_contexes:
            match = ctx.match(result)
            if len(match) > 0:
                return [self] + match
        return []

    @property
    def all_valid_rules(self):
        out = self.valid_rules.copy()
        for ctx in self.valid_contexes:
            out.update(ctx.all_valid_rules)
        return out
        
    def apply(self, builder, node):
        return builder.build_context(self, node)
 
class Symbol(object):
    def __init__(self, text=None, precedence=None, precedence_chaining='left'):
        self.text = text
        self.precedence = precedence
        self.precedence_chaining = 'left'

    def validate(self, node):
        return node.issymbol()

    def build(self, function, node):
        return function(self, node)

    def __repr__(self):
        if self.text is not None:
            return repr(self.text)
        return "<symbol>"

    def blank(self):
        return dom.Symbol(self.text or u"")

    def match_term(self, result):
        return result in ('symbol', 'blank')
        
    def apply(self, builder, node):
        return builder.build_terminal(self, node)

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

    def descend(self, subj, obj):
        return self.sequence[subj.index(obj)]
        
    def apply(self, builder, node):
        return builder.build_sequence(self, node)

class Star(ListRule):
    def __init__(self, rule):
        self.rule = rule

    def validate(self, node):
        if not node.islist():
            return False
        return all(self.rule.validate(subnode) for subnode in node)

    def build(self, function, node):
        if len(node) == 0 and hasattr(function, '__name__') and function.__name__ == '_layout':
            return [function(self, node)]
        return [self.rule.build(function, subnode) for subnode in node]

    def __repr__(self):
        return repr(self.rule) + '*'

    def blank(self):
        return dom.Literal(self.label, [])

    def descend(self, subj, obj):
        return self.rule
        
    def apply(self, builder, node):
        return builder.build_star(self, node)

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

    def descend(self, subj, obj):
        return self.rule
        
    def apply(self, builder, node):
        return builder.build_plus(self, node)

class String(Rule):
    def validate(self, node):
        return node.isstring()

    def build(self, function, node):
        return function(self, node)

    def __repr__(self):
        return "<string>"

    def blank(self):
        return dom.Literal(self.label, u"")

    def match_term(self, result):
        return result == 'string'
        
    def apply(self, builder, node):
        return builder.build_terminal(self, node)

class Binary(Rule):
    def validate(self, node):
        return node.isbinary()

    def build(self, function, node):
        return function(self, node)

    def __repr__(self):
        return "<binary>"

    def blank(self):
        return dom.Literal(self.label, "")

    def match_term(self, result):
        return result == 'binary'
        
    def apply(self, builder, node):
        return builder.build_terminal(self, node)

modeline = Plus(Symbol())
modeline.label = '##'
modechange = Sequence([Plus(Symbol()), Star(Context("*"))])
modechange.label = '#'
blankschema = Schema(Context('*'), {}, {})

def has_modeline(body):
    if len(body) > 0:
        return modeline.validate(body[0])
