from grammar import *

def new_metagrammar():
    contexes = {}

    contexes['stmt'] = stmt = Context('stmt')
    contexes['expr'] = expr = Context('expr')
    contexes['term'] = term = Context('term')

    expr.rules.update([symbol])
    term.rules.update([symbol, string])

    def group(context, group):
        rule = Group(group)
        context.rules.add(rule)
        return rule

    def star(context, rule):
        rule = Star(rule)
        context.rules.add(rule)
        return rule

    def plus(context, rule):
        rule = Plus(rule)
        context.rules.add(rule)
        return rule

    return Grammar(stmt, {
        'context': group(stmt, [symbol, Star(term)]),
        'group': star(expr, expr),
        'plus': group(expr, [expr]),
        'precedence': group(term, [string, symbol, symbol]),
        'rule': group(stmt, [symbol, Star(symbol), expr]),
        'star': group(expr, [expr]),
        'toplevel': group(stmt, [symbol]),
        }, contexes)

blank = Grammar(anything, {}, {})
grammar = new_metagrammar()

def load(forest):
    builder = Builder()
    for cell in forest:
        if modeline.validate(cell):
            continue
        builder.build_context(grammar.toplevel, cell)
    assert builder.toplevel is not None, "proper grammar must define a toplevel"
    return Grammar(builder.toplevel, builder.rules, builder.contexes)

class Builder(object):
    def __init__(self):
        self.contexes = {}
        self.rules = {}
        self.toplevel = None

    def context(self, name):
        if name not in self.contexes:
            self.contexes[name] = context = Context(name)
            return context
        return self.contexes[name]

    def build_context(self, context, cell):
        assert isinstance(cell, Cell), repr(cell)
        pre, rule = context.match(cell)
        if rule is None:
            raise Exception("syn error {!r}, expected {}".format(cell, context.name))
        elif rule is symbol:
            if cell[:] == 'symbol':
                return symbol
            if cell[:] == 'string':
                return string
            return self.context(cell[:])
        elif rule is string:
            return Keyword(cell[:])
        elif rule.label == 'rule':
            name, contexes, body = rule(self, cell)
            self.rules[name] = body
            for name in contexes:
                self.context(name).rules.add(body)
        elif rule.label == 'context':
            name, terms = rule(self, cell)
            context = self.context(name)
            for term in terms:
                if isinstance(term, Context):
                    context.contexes.add(term)
                else:
                    context.rules.add(term)
        elif rule.label == 'precedence':
            keyword, precedence, precedence_bind = rule(self, cell)
            return Keyword(keyword, int(precedence), precedence_bind)
        elif rule.label == 'toplevel':
            name, = rule(self, cell)
            self.toplevel = self.context(name)
        elif rule.label == 'group':
            return Group(rule(self, cell))
        elif rule.label == 'star':
            return Star(rule(self, cell)[0])
        elif rule.label == 'plus':
            return Plus(rule(self, cell)[0])
        else:
            raise Exception("not implemented {} label={}".format(rule, rule.label))

    def build_textcell(self, term, cell):
        return cell[:]

    def build_group(self, sequence, cell):
        print sequence, cell
        return [r(self, c) for r, c in zip(sequence, cell)]

    def build_star(self, star, cell):
        return [star.rule(self, c) for c in cell]

    def build_plus(self, plus, cell):
        return [plus.rule(self, c) for c in cell]
