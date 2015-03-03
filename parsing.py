from dom import TextCell, ListCell
from grammar import *

class Match(object):
    def __init__(self, rule, start, values, reductions):
        self.rule = rule
        self.start = start
        self.values = values
        self.reductions = reductions

    @property
    def next_cat(self):
        return self.rule.at(len(self.values))

    @property
    def incomplete(self):
        return len(self.values) < len(self.rule)

    def shift(self, value):
        return Match(self.rule, self.start, self.values + [value], self.reductions)

    def __repr__(self):
        return '(' + self.rule.label + ' ' + ', '.join(map(repr, self.values)) + ')'

    def wrap(self):
        result = []
        for item in self.values:
            if isinstance(item, Match):
                result.append(item.build())
            else:
                result.append(item.copy())
        return ListCell(self.rule.label, result)

def parse(sequence, expects):
    nonterminals = [{} for i in range(len(sequence))]
    chart = [[] for i in range(len(sequence) + 1)]
 
    def scan(state, rule, index, visited):
        if rule in visited:
            return
        visited.add(rule)
        if match(rule, sequence[index]):
            chart[index+1].append(state.shift(sequence[index]))
        elif isinstance(rule, Group):
            if rule in nonterminals[index]:
                nonterminals[index][rule].append(state)
            else:
                nonterminals[index][rule] = reductions = [state]
                chart[index].append(Match(rule, index, [], reductions))
        elif isinstance(rule, Context):
            for subrule in rule.rules:
                scan(state, subrule, index, visited)
            for subrule in rule.contexes:
                scan(state, subrule, index, visited)
    for expect in expects:
        assert isinstance(expect, Rule)
        if isinstance(expect, Group):
            chart[0].append(Match(expect, 0, [], []))
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
    if isinstance(rule, Symbol) and token.symbol:
        return True
    if isinstance(rule, String) and isinstance(token, TextCell) and not token.symbol:
        return True
    if isinstance(rule, Rule):
        return rule.validate(token)
