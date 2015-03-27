#!/usr/bin/env python
#from grammar import Context, ListRule
from grammar import symbol, string
from itertools import count
import ast
import dom
import metagrammar
import sys
import treepython_translator

#import ast
#import imp
#import os

grammar = metagrammar.load(dom.load("grammars/treepython.t+"), 'treepython')

def file_to_ast(path):
    return forest_to_ast(dom.load(path))

def forest_to_ast(forest):
    env = Env()
    body = []
    for cell in forest:
        if cell.label == '##':
            continue
        result = env.build_context(grammar.toplevel, cell)
        body.extend(env.statementify(result))
    return ast.Module(body)


class Env(object):
    def __init__(self):
        self.cell = None
        self.context = None
        self.newsym_counter = count(1)

    def new_sym(self):
        return "__anon{}".format(self.newsym_counter.next())

    def build_context(self, context, cell):
        self.cell = cell
        pre, rule = context.match(cell)
        pre = [context] + pre
        if rule is None:
            raise Exception("syn error {!r}, expected {}".format(cell, context.name))
        if rule is symbol:
            fn = get_translator(pre[-1].name + '_' + 'symbol')
            result = fn(self, cell[:])
        elif rule is string:
            fn = get_translator(pre[-1].name + '_' + 'string')
            result = fn(self, cell[:])
        else:
            label = rule.label
            fn = get_translator(rule.label)
            args = rule(self, cell)
            self.cell = cell
            result = fn(self, *args)
        top_ctx = pre.pop()
        for ctx in reversed(pre):
            result = get_translator(ctx.name + '_' + top_ctx.name)(self, result)
            top_ctx = ctx
        return result
#        result = schema.recognize(subj)
#        match = slot.match(result)
#        if len(match) > 0:
#            self.subj = subj
#            self.context = match.pop()
#            if isinstance(result, str):
#                fn = get_translator(self.context.name + '_' + result)
#                result = fn(self, subj[:])
#            else:
#                fn = get_translator(result.label)
#            for context in reversed(match):
#                result = get_translator(context.name + '_' + self.context.name)(self, result)
#                self.context = context
#            return result
#        else:
#            raise Exception("syn error {}, expected {}".format(subj, slot))
#
    def build_textcell(self, term, cell):
        if term.match(cell):
            return cell[:]
        raise Exception("syn error {}, expected {}".format(subj, slot))

    def build_group(self, group, cell):
        return [rule(self, subcell) for rule, subcell in zip(group, cell)]

    def build_star(self, star, cell):
        return [star.rule(self, subcell) for subcell in cell]

    def build_plus(self, plus, cell):
        return [plus.rule(self, subcell) for subcell in cell]

    def new_node(self, cls, *args, **kwargs):
        node = cls(*args, **kwargs)
        node.lineno = ident_to_lineno(self.cell.ident)
        node.col_offset = 0
        return node

    def statementify(self, box):
        assert isinstance(box, treepython_translator.Box)
        for stmt in box.stmts:
            yield stmt
        yield box.expr

    def none(self):
        return self.new_node(ast.Name, "None", ast.Load(), lineno=0, col_offset=0)


def get_translator(name):
    return getattr(treepython_translator, "translate_" + name.replace('-', '_'))

def ident_to_lineno(ident):
    lineno = 0
    for ch in ident:
        lineno <<= 8
        lineno |= ord(ch)
    return lineno

def lineno_to_ident(lineno):
    ident = ''
    while lineno > 0:
        ident = chr(lineno & 255) + ident
        lineno >>= 8
    return ident

def println(*args):
    print ' '.join(map(str, args))

if __name__=='__main__':
    local_environ = dict(
        println = println)
    path = sys.argv[1]
    code = forest_to_ast(dom.load(path))
    exec compile(code, path, 'exec') in local_environ
