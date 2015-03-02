from dom import TextCell, ListCell

class Grammar(object):
    def __init__(self, toplevel, rules, contexes):
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
        if modeline.validate(cell):
            return modeline
        if modeblock.validate(cell):
            return modeblock
        if turnip.validate(cell) or cell.label == '@':
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
        rule = self.recognize(cell.parent)
        if isinstance(rule, ListRule):
            rule = rule.at(cell.parent.index(cell))
            if isinstance(rule, Context):
                return rule

class Rule(object):
    pass

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

    def at(self, index):
        return self[index]

    def blank(self):
        return ListCell(self.label, [r.blank() for r in self])

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

    def at(self, index):
        return self.rule

    def blank(self):
        return ListCell(self.label, [])

    def validate(self, cell):
        if not isinstance(cell, ListCell):
            return False
        if cell.label != self.label:
            return False
        return all(self.rule.validate(c) for c in cell)

class Plus(ListRule):
    def __call__(self, builder, cell):
        return builder.build_plus(self, cell)

    def __init__(self, rule, label=""):
        self.rule = rule
        self.label = label

    def at(self, index):
        return self.rule

    def blank(self):
        return ListCell(self.label, [self.rule.blank()])

    def validate(self, cell):
        if not isinstance(cell, ListCell):
            return False
        if cell.is_external():
            return False
        if cell.label != self.label:
            return False
        return all(self.rule.validate(c) for c in cell)

class Context(Rule):
    def __call__(self, builder, cell):
        return builder.build_context(self, cell)

    def __init__(self, name):
        self.name = name
        self.rules = set()
        self.contexes = set()
        self.indirect_rules = []

    def blank(self):
        return TextCell(u"")

    def match(self, cell):
        for rule in self.rules:
            if rule.validate(cell):
                return [], rule
        for pre, rule in self.indirect_rules:
            if rule.validate(cell):
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

    def blank(self):
        return TextCell(u"")

    def validate(self, cell):
        return isinstance(cell, TextCell) and cell.symbol

#class RegEx(Symbol):
#    pass

class String(Rule):
    def __call__(self, builder, cell):
        return builder.build_textcell(self, cell)

    def blank(self):
        return TextCell(u"", symbol=False)

    def validate(self, cell):
        return isinstance(cell, TextCell) and not cell.symbol

symbol = Symbol()
string = String()
anything = Context(None)
modeline = Plus(symbol, label='##')
modeblock = Group([Plus(symbol), Star(anything)], label='#')
turnip = Plus(anything, label='@')
