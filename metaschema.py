from schema import Schema, Rule, ListRule, Context, Symbol, Sequence, Star, Plus, String, Binary

def rule(ctxs, body):
    for ctx in ctxs:
        ctx.valid_rules.add(body)
    return body

c_rule = Context("rule")
c_expr = Context("expr")
c_term = Context("term")

c_expr.valid_contexes.update([c_term])
c_expr.valid_terms.update([Symbol()])

schema = Schema(c_rule, {
    'language': rule([c_rule], String()),
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
        builder(schema.toplevel, node)
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

    def __call__(self, slot, node):
        result = schema.recognize(node)
        if slot is c_rule:
            if result is schema['rule']:
                name, contexes, body = result.build(self, node)
                self.rules[name] = body
                for context_name in contexes:
                    self.context(context_name).valid_rules.add(body)
                return
            elif result is schema['bind']:
                context_name, terms = result.build(self, node)
                ctx = self.context(context_name)
                for term in terms:
                    if isinstance(term, Context):
                        ctx.valid_contexes.add(term)
                    else:
                        ctx.valid_terms.add(term)
                return
            elif result is schema['language']:
                return
            elif result is schema['toplevel']:
                name, = result.build(self, node)
                self.toplevel = self.context(name)
                return
        if slot is c_expr:
            if result is schema['sequence']:
                return Sequence(result.build(self, node))
            if result == 'symbol':
                if node[:] == 'symbol':
                    return Symbol()
                if node[:] == 'string':
                    return String()
                if node[:] == 'binary':
                    return Binary()
                return self.context(node[:])
        if slot is c_term:
            if result == 'symbol':
                if node[:] == 'symbol':
                    return Symbol()
                if node[:] == 'string':
                    return String()
                if node[:] == 'binary':
                    return Binary()
        if isinstance(slot, Symbol) and result == 'symbol':
            return node[:]
        raise Exception("syn error {}, expected {}".format(node, slot))
