from dom import Cell, TextCell, ListCell

class Grammar(object):
    def __init__(self, toplevel, rules, contexes, name):
        self.name = name
        self.contexes = contexes
        self.toplevel = toplevel
        self.rules = rules
        self.root = Star(toplevel)
        for label, rule in rules.iteritems():
            rule.label = label
        for name, context in contexes.iteritems():
            assert context.name == name
            context.update_indirect_rules()

    def recognize(self, cell):
        """
        Validation of every node is shallow.
        The construct should be recognized even if it were in a wrong context.
        """
        if turnip.validate(cell):
            return turnip
        if len(cell.label) > 0 and cell.label in self.rules:
            rule = self.rules[cell.label]
            if rule.validate(cell):
                return rule
        if cell.parent is None:
            return self.root
        rule = self.recognize(cell.parent)
        if isinstance(rule, ListRule):
            rule = rule.at(cell.parent.index(cell))
            if not isinstance(rule, Context):
                return rule

    def recognize_context(self, cell):
        if cell.parent is None:
            return self.toplevel
        rule = self.recognize(cell.parent)
        if isinstance(rule, ListRule):
            rule = rule.at(cell.parent.index(cell))
            return rule

class Rule(object):
    def match(self, cell):
        return [], (self if self.validate(cell) else None)

class ListRule(Rule):
    label = ""

class Group(ListRule):
    def __call__(self, builder, cell):
        return builder.build_group(self, cell)

    def __init__(self, contents, label=""):
        self.contents = contents
        self.label = label

    def __getitem__(self, index):
        return self.contents[index]

    def __len__(self):
        return len(self.contents)

    def __repr__(self):
        return '{{{}}}'.format(', '.join(map(repr, self)))

    def at(self, index):
        return self[index]

    def blank(self, grammar):
        return ListCell([r.blank(grammar) for r in self], self.label, grammar)

    def validate(self, cell):
        if not isinstance(cell, ListCell):
            return False
        if cell.label != self.label or len(cell) != len(self):
            return False
        return all(r.validate(c) for r, c in zip(self, cell))

class Star(ListRule):
    def __call__(self, builder, cell):
        return builder.build_star(self, cell)

    def __init__(self, rule, label=""):
        self.rule = rule
        self.label = label

    def __repr__(self):
        return '{}*'.format(self.rule)

    def at(self, index):
        return self.rule

    def blank(self, grammar):
        return ListCell([], self.label, grammar)

    def validate(self, cell):
        if not isinstance(cell, ListCell):
            return False
        if cell.label != self.label:
            return False
        return all(self.rule.validate(c) or cell.symbol or turnip.validate(cell) for c in cell)

class Plus(ListRule):
    def __call__(self, builder, cell):
        return builder.build_plus(self, cell)

    def __init__(self, rule, label=""):
        self.rule = rule
        self.label = label

    def __repr__(self):
        return '{}+'.format(self.rule)

    def at(self, index):
        return self.rule

    def blank(self, grammar):
        return ListCell([TextCell(u"")], self.label, grammar)

    def validate(self, cell):
        if not isinstance(cell, ListCell):
            return False
        if cell.is_external():
            return False
        if cell.label != self.label:
            return False
        return all(self.rule.validate(c) or cell.symbol or turnip.validate(cell) for c in cell)

class Context(Rule):
    def __call__(self, builder, cell):
        return builder.build_context(self, cell)

    def __init__(self, name):
        self.name = name
        self.rules = set()
        self.contexes = set()
        self.indirect_rules = []

    def __repr__(self):
        return "<{}>".format(self.name)

    def blank(self, grammar):
        return TextCell(u"")

    def match(self, cell):
        assert isinstance(cell, Cell)
        if self.name is None:
            return [], self
        for rule in self.rules:
            if rule.match(cell)[1]:
                return [], rule
        for pre, rule in self.indirect_rules:
            if rule.match(cell)[1]:
                return pre, rule
        return [], None

    def update_indirect_rules(self):
        visited = set(self.rules)
        self.indirect_rules = indirect_rules = []
        def visit(context, pre):
            if context not in visited:
                visited.add(context)
                for rule in context.rules:
                    if rule not in visited:
                        visited.add(rule)
                        indirect_rules.append((pre, rule))
                for subcontext in context.contexes:
                    visit(subcontext, pre + [subcontext])
        for context in self.contexes:
            visit(context, [context])

    def validate(self, cell):
        return True

class Symbol(Rule):
    def __call__(self, builder, cell):
        return builder.build_textcell(self, cell)

    def __repr__(self):
        return 'symbol'

    def blank(self, grammar):
        return TextCell(u"")

    def validate(self, cell):
        return isinstance(cell, TextCell) and cell.symbol

class Keyword(Rule):
    def __init__(self, keyword, precedence, precedence_bind):
        self.keyword = keyword
        self.precedence = precedence
        self.precedence_bind = precedence_bind

    def __call__(self, builder, cell):
        return builder.build_textcell(self, cell)

    def __repr__(self):
        return '<keyword {!r}>'.format(self.keyword)

    def blank(self, grammar):
        return TextCell(keyword)

    def validate(self, cell):
        return isinstance(cell, TextCell) and cell.symbol

    def match(self, cell):
        return [], (self if self.validate(cell) and cell[:] == self.keyword else None)

class String(Rule):
    def __call__(self, builder, cell):
        return builder.build_textcell(self, cell)

    def __repr__(self):
        return 'string'

    def blank(self, grammar):
        return TextCell(u"", symbol=False)

    def validate(self, cell):
        return isinstance(cell, TextCell) and not cell.symbol

symbol = Symbol()
string = String()
anything = Context(None)
turnip = Plus(anything, label='@')
