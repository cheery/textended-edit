import dom

class Pattern(object):
    """
        Purpose of the recognizer is to substitute
        fixed if/elif/else -chains. These recognizers
        are extensible pattern matching grammars.

        The scan function of a pattern returns a reversed path of patterns that caused a match.
    """
    pre = None
    post = None

class Symbol(Pattern):
    def scan(self, grammar, subj):
        if isinstance(subj, dom.Symbol):
             return self, []

    def __repr__(self):
        return "Symbol()"
symbol = Symbol()

class Binary(Pattern):
    def __init__(self, label):
        self.label = label

    def scan(self, grammar, subj):
        if isinstance(subj, dom.Literal) and isinstance(subj.contents, str) and subj.label == self.label:
            return self, []

    def __repr__(self):
        return "Binary({0.label})".format(self)

class String(Pattern):
    def __init__(self, label):
        self.label = label

    def scan(self, grammar, subj):
        if isinstance(subj, dom.Literal) and isinstance(subj.contents, unicode) and subj.label == self.label:
            return self, []

    def __repr__(self):
        return "String({0.label})".format(self)

class Group(Pattern):
    def __init__(self, label, args, varg=None):
        self.label = label
        self.args = args
        self.varg = varg

    def scan(self, grammar, subj):
        if isinstance(subj, dom.Literal) and isinstance(subj.contents, list) and subj.label == self.label:
            if self.varg is not None and len(self.args) <= len(subj):
                return self, []
            elif len(self.args) == len(subj):
                return self, []

    def dissect(self, params):
        gen = iter(params)
        for arg in self.args:
            yield arg, gen.next()
        for rem in gen:
            yield self.varg, rem

    def __repr__(self):
        return "Group({0.label}, {0.args}, {0.varg})".format(self)

class AnyOf(Pattern):
    def __init__(self, args):
        self.args = args

    def scan(self, grammar, subj):
        matches = []
        for rule in self.args:
            match = rule.scan(grammar, subj)
            if match is not None:
                matches.append(match)
        if len(matches) > 1:
            raise AmbiguousGrammar(grammar, self, subj, matches)
        if len(matches) == 1:
            match, context = matches.pop(0)
            context.append(self)
            return match, context

    def __repr__(self):
        return "AnyOf({0.args})".format(self)

class Context(Pattern):
    def __init__(self, name):
        self.name = name

    def scan(self, grammar, subj):
        matches = []
        for rule in grammar[self.name]:
            match = rule.scan(grammar, subj)
            if match is not None:
                matches.append(match)
        if len(matches) > 1:
            raise AmbiguousGrammar(grammar, self, subj, matches)
        if len(matches) == 1:
            match, context = matches.pop(0)
            context.append(self)
            return match, context

    def __repr__(self):
        return "Context({0.name})".format(self)

class AmbiguousGrammar(Exception):
    def __init__(self, grammar, context, subj, matches):
        self.grammar = grammar
        self.context = context
        self.subj = subj
        self.matches = matches

    def __str__(self):
        return "AmbiguousGrammar(grammar, {0.context}, {0.subj}, {0.matches})".format(self)
