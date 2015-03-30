from collections import defaultdict
from dom import TextCell, ListCell
from dom.grammar import *
from Queue import PriorityQueue
from time import time

# This code has a flaw, which causes it to not produce best-scoring parsing results first.
# The precedence rule handling can suddenly rise the badness, but the reduction may still
# succeed, giving an insanely bad initial answer.

class Reduction(object): # Reduction represents found ListRules.
    def __init__(self, rule, values, badness):
        self.rule = rule
        self.values = values
        self.badness = 50 # Would fill up from the operator-assigned badness.
        self.precedence = None
        # On inconsistent operator precedence, we should add a penalty or ignore the precedence.
        # In reduction construct with precedence information, we should acknowledge
        # that information and penalize if it is inconsistent.
        if len(values) == 3 and isinstance(values[1], Operator):
            lhs, op, rhs = values
            precedence = op.keyword.precedence
            if precedence is not None:
                binding = op.keyword.precedence_bind
                if binding == 'left':
                    lhs_prec = precedence - 1
                    rhs_prec = precedence
                elif binding == 'right':
                    lhs_prec = precedence
                    rhs_prec = precedence - 1
                if isinstance(lhs, Reduction) and lhs.precedence is not None and lhs.precedence < lhs_prec:
                        self.badness = 1000
                elif isinstance(rhs, Reduction) and rhs.precedence is not None and rhs.precedence < rhs_prec:
                        self.badness = 1000
                else:
                    self.badness = 0
                self.precedence = precedence
        self.badness += badness

    def wrap(self):
        result = []
        for item in self.values:
            if isinstance(item, (Reduction, Operator)):
                result.append(item.wrap())
            else:
                result.append(item.copy())
        return ListCell(result, self.rule.label, self.rule.grammar.name)

# Parsing results with incorrect precedences aren't suppressed, instead they're
# penalized harshly.
# Operators are used to calculate badness of reductions, based on precedence rules.
class Operator(object):
    def __init__(self, keyword, value):
        self.keyword = keyword
        self.value = value

    def wrap(self):
        return self.value

    def __repr__(self):
        return "<Operator {} {}>".format(self.keyword, self.value)

# I have also considered to penalize results with symbols that match in the keyword
# list, but aren't parsed as those symbols.

# Penalizing in this parser isn't based on much of reasoning. Certain results are
# penalized with arbitrary values to accept smaller and more interesting parse
# trees to appear sooner than later.

# The parsing proceeds as in the http://en.wikipedia.org/wiki/Earley_parser
# with main difference that badness increases with the size of the parse.
# The least bad partial parses are visited first.
def parse(sequence, expects, timeout):
    q = PriorityQueue() # The unprocessed items end up into the queue
                        # Parsing constantly fills it up, and cannot
                        # progress after it becomes empty.
    wait = defaultdict(list) # Items that wait for reduction. (start, rule) -> [item]
    fini = defaultdict(list) # Items that have been finished at (start, rule) -> [(r_badness, stop, value)]
    halt = time() + timeout # When we should give up.

    for rule in expects: # The queue is populated with initial starting states.
        if valid_compound(rule):
            q.put((0, 0, 0, rule, []))
    while not q.empty():
        if halt < time():
            raise Exception("timeout")
        badness, start, index, rule, matches = q.get_nowait()
        # Queue is filled up from the results of shifting.
        if ((isinstance(rule, Group) and len(rule) == len(matches)) or
            (isinstance(rule, Plus) and len(matches) >= 1) or
            (isinstance(rule, Star))):
            # If shifting results in completely reduced construct, we want to reduce using it.
            # Reduction usually results in one or more shifts and it is stored
            # to allow worse reductions with the same rule again.
            if start == 0 and index == len(sequence):
                yield Reduction(rule, matches, badness)
                halt = time() + timeout # reset halt when we succeed.
                continue
            else:
                result = Reduction(rule, matches, badness)
                fini[(start, rule)].append((index, result))
                for g_badness, g_start, g_rule, g_matches in wait[(start, rule)]:
                    q.put((
                        g_badness + result.badness,
                        g_start,
                        index,
                        g_rule,
                        g_matches + [result]))
                if isinstance(rule, Group):
                    continue
        if index >= len(sequence): # Some rules may appear at positions where they cannot complete.
            continue
        subrule = rule.at(len(matches))
        subrules = ()
        match = subrule.match(sequence[index])
        if subrule.validate(sequence[index]) and match[1]:
            if isinstance(match[1], Keyword): # Operator inserted where Keyword matches.
                shift_badness = 1
                term = Operator(match[1], sequence[index])
            else:
                shift_badness = 10
                term = sequence[index]
            q.put((
                badness + shift_badness,
                start,
                index + 1,
                rule,
                matches + [term]))
        # Even if rule matched to a symbol or construct, it may match other ways too
        if isinstance(subrule, ListRule):
            subrules = [(10, subrule)]
        elif isinstance(subrule, Context): # Larger constructs with many indirections 
                                           # are treated as worse results.
            subrules = [(100, d_rule) for d_rule in subrule.rules if valid_compound(d_rule)]
            for pre, ind_rule in subrule.indirect_rules:
                if valid_compound(ind_rule):
                    subrules.append((100 + len(pre)*10, ind_rule))

        # If there are rules that can reduce, we shift with them.
        # Otherwise we add a blank shift to parse the rule and initiate fini to fill up.
        for b_badness, subrule in subrules:
            if fini.has_key((index, subrule)):
                for stop, result in fini[(index, subrule)]:
                    q.put((
                        b_badness + badness + result.badness,
                        start,
                        stop,
                        rule,
                        matches + [result]))
            elif isinstance(rule, ListRule):
                q.put((0, index, index, subrule, []))
                # Avoid recursion
                fini[(start, rule)] = []
            # Even if fini contained items, at this point we're not sure if
            # fini still fills up, so we need to add a wait every time.
            wait[(index, subrule)].append((b_badness+badness, start, rule, matches))


# The subrule.validate() takes care of other indirect rules
def valid_compound(rule):
    return isinstance(rule, (ListRule, Context))

