import schema
import dom

class Result(object):
    def __init__(self, rule, start, values, reductions):
        self.rule = rule
        self.start = start
        self.values = values
        self.reductions = reductions

    @property
    def next_cat(self):
        return self.rule[len(self.values)]

    @property
    def incomplete(self):
        return len(self.values) < len(self.rule)

    def shift(self, value):
        return Result(self.rule, self.start, self.values + [value], self.reductions)

    def __repr__(self):
        return '(' + self.rule.label + ' ' + ', '.join(map(repr, self.values)) + ')'

    def build(self):
        result = []
        for item in self.values:
            if isinstance(item, Result):
                result.append(item.build())
            else:
                result.append(item.copy())
        return dom.Literal(self.rule.label, result)

def parse(sequence, expects):
    nonterminals = [{} for i in range(len(sequence))]
    chart = [[] for i in range(len(sequence) + 1)]

    def scan(state, rule, index, visited):
        if rule in visited:
            return
        visited.add(rule)
        if match(rule, sequence[index]):
            chart[index+1].append(state.shift(sequence[index]))
        elif isinstance(rule, schema.Sequence):
            if rule in nonterminals[index]:
                nonterminals[index][rule].append(state)
            else:
                nonterminals[index][rule] = reductions = [state]
                chart[index].append(Result(rule, index, [], reductions))
        elif isinstance(rule, schema.Context):
            for subrule in rule.valid_rules:
                scan(state, subrule, index, visited)
            for subrule in rule.valid_contexes:
                scan(state, subrule, index, visited)
            for subrule in rule.valid_terms:
                scan(state, subrule, index, visited)

    for expect in expects:
        assert isinstance(expect, schema.Rule)
        if isinstance(expect, schema.Sequence):
            chart[0].append(Result(expect, 0, [], []))
    for index in range(0, len(sequence)):
        for state in chart[index]:
            if state.incomplete:
                scan(state, state.next_cat, index, set())
            else:
                for st in state.reductions:
                    chart[index].append(st.shift(state))
    completed = []
    for state in chart[len(sequence)]:
        if not state.incomplete:
            if state.rule in expects and len(state.reductions) == 0:
                completed.append(state)
            for st in state.reductions:
                chart[index].append(st.shift(state))
    return completed

def match(rule, token):
    if isinstance(rule, schema.Symbol) and token.issymbol():
        return True
    if isinstance(rule, schema.String) and token.isstring():
        return True
    if isinstance(rule, schema.Binary) and token.isbinary():
        return True
    if isinstance(rule, schema.ListRule) and token.islist():
        return token.label == rule.label


# from schema import Sequence, Plus, Star, Context, Symbol, String, Binary
# from collections import defaultdict
# 
# class Reduction(object):
#     def __init__(self, lhs=None, star=False):
#         self.lhs = lhs
#         self.star = star
# 
# def cyk(schema):
#     bgrammar = []
#     ugrammar = []
#     visited = {}
# 
#     symbols = set()
#     strings = set()
#     binaries = set()
#     def visit(rule):
#         if isinstance(rule, Reduction):
#             return rule
#         if rule in visited:
#             return visited[rule]
#         visited[rule] = lhs = Reduction(rule, isinstance(rule, Star))
#         if isinstance(rule, Sequence):
#             pairs = list(rule)
#             while len(pairs) > 2:
#                 mhs = Reduction()
#                 n1 = visit(pairs.pop())
#                 n0 = visit(pairs.pop())
#                 bgrammar.append((mhs, n0, n1))
#             if len(pairs) == 2:
#                 n1 = visit(pairs.pop())
#                 n0 = visit(pairs.pop())
#                 bgrammar.append((lhs, n0, n1))
#             elif len(pairs) == 1:
#                 ugrammar.append((lhs, visit(pairs[0])))
#         elif isinstance(rule, (Plus, Star)):
#             n0 = visit(rule.rule)
#             ugrammar.append((lhs, n0))
#             bgrammar.append((lhs, n0, lhs))
#         elif isinstance(rule, Context):
#             for subrule in rule.valid_rules:
#                 ugrammar.append((lhs, visit(subrule)))
#             for ctx in rule.valid_contexes:
#                 ugrammar.append((lhs, visit(ctx)))
#             for term in rule.valid_terms:
#                 ugrammar.append((lhs, visit(term)))
#         elif isinstance(rule, Symbol):
#             symbols.add(rule)
#         elif isinstance(rule, String):
#             strings.add(rule)
#         elif isinstance(rule, Binary):
#             binaries.add(rule)
#         else:
#             assert False, repr(rule)
#         return lhs
#     # split all rules
#     for rule in schema.rules.values():
#         visit(rule)
#     print bgrammar
#     print ugrammar
#     print symbols
#     print strings
#     print binaries
