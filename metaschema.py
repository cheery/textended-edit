from schema import Schema, Rule, ListRule, Context, Symbol, Sequence, Star, Plus, String, Binary

def rule(ctxs, body):
    for ctx in ctxs:
        ctx.valid_rules.add(body)
    return body

c_rule = Context("rule")
c_expr = Context("expr")
c_term = Context("term")

c_expr.valid_contexes.update([c_term])
c_expr.valid_terms.update([Symbol(), String()])

schema = Schema(c_rule, {
    'toplevel': rule([c_rule], Sequence([Symbol()])),
    'rule': rule([c_rule], Sequence([
        Symbol(),
        Star(Symbol()),
        c_expr,
    ])),
    'sequence': rule([c_expr], Star(c_expr)),
    'star': rule([c_expr], Sequence([c_expr])),
    'plus': rule([c_expr], Sequence([c_expr])),
    'bind': rule([c_rule], Sequence([
        Symbol(),
        Star(c_term),
    ])),
}, {c_rule, c_expr, c_term})

def load(tree):
    builder = Builder()
    for node in tree:
        if node.label == '##':
            continue
        builder.build_context(schema.toplevel, node)
    return Schema(builder.toplevel, builder.rules, builder.contexes)

class Builder(object):
    def __init__(self):
        self.contexes = {}
        self.rules = {}
        self.toplevel = None

    def context(self, name):
        if name in self.contexes:
            return self.contexes[name]
        else:
            self.contexes[name] = context = Context(name)
            return context

    def build_context(self, slot, node):
        result = schema.recognize(node)
        if slot is c_rule:
            if result is schema['rule']:
                name, contexes, body = result.apply(self, node)
                self.rules[name] = body
                for context_name in contexes:
                    self.context(context_name).valid_rules.add(body)
                return
            elif result is schema['bind']:
                context_name, terms = result.apply(self, node)
                ctx = self.context(context_name)
                for term in terms:
                    if isinstance(term, Context):
                        ctx.valid_contexes.add(term)
                    else:
                        ctx.valid_terms.add(term)
                return
            elif result is schema['toplevel']:
                name, = result.apply(self, node)
                self.toplevel = self.context(name)
                return
        if slot is c_expr:
            if result is schema['sequence']:
                return Sequence(result.apply(self, node))
            if result is schema['star']:
                return Star(result.apply(self, node)[0])
            if result is schema['plus']:
                return Plus(result.apply(self, node)[0])
            if result == 'symbol':
                if node[:] == 'symbol':
                    return Symbol()
                if node[:] == 'string':
                    return String()
                if node[:] == 'binary':
                    return Binary()
                return self.context(node[:])
            if result == 'string':
                return Symbol(node[:])
        if slot is c_term:
            if result == 'symbol':
                if node[:] == 'symbol':
                    return Symbol()
                if node[:] == 'string':
                    return String()
                if node[:] == 'binary':
                    return Binary()
                return self.context(node[:])
            if result == 'string':
                return Symbol(node[:])
        raise Exception("syn error {}, expected {}".format(node, slot))

    def build_terminal(self, term, subj):
        return subj[:]

    def build_sequence(self, sequence, subj):
        return [rule.apply(self, node) for rule, node in zip(sequence, subj)]

    def build_star(self, star, subj):
        return [star.rule.apply(self, node) for node in subj]

    def build_plus(self, plus, subj):
        return [plus.rule.apply(self, node) for node in subj]
