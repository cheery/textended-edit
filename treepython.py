#!/usr/bin/env python
from schema import Context, ListRule, Rule
import ast
import dom
import imp
import metaschema
import sys
import treepython_translator
import os

schema = metaschema.load(dom.load("schemas/treepython.t+"))

def file_to_ast(path):
    return forest_to_ast(dom.load(path))

def forest_to_ast(forest):
    env = Env()
    body = []
    for node in forest:
        if node.label == '##':
            continue
        body.extend(env(schema.toplevel, node))
    return ast.Module(body)

class Env(object):
    def __init__(self):
        self.subj = None
        self.context = None

    def __call__(self, slot, subj):
        result = schema.recognize(subj)
        if isinstance(slot, Context):
            match = slot.match(result)
            if len(match) > 0:
                self.subj = subj
                self.context = match.pop()
                if isinstance(result, str):
                    fn = get_translator(self.context.name + '_' + result)
                else:
                    fn = get_translator(result.label)
                if isinstance(result, ListRule):
                    result = fn(self, *result.build(self, subj))
                else:
                    result = fn(self, subj[:])
                for context in reversed(match):
                    result = get_translator(context.name + '_' + self.context.name)(self, result)
                    self.context = context
                return result
        elif slot.match_term(subj):
            return subj[:]
        raise Exception("syn error {}, expected {}".format(subj, slot))

    def new_node(self, cls, *args, **kwargs):
        node = cls(*args, **kwargs)
        node.lineno = ident_to_lineno(self.subj.ident)
        node.col_offset = 0
        return node

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

if __name__=='__main__':
    local_environ = dict()
    path = sys.argv[1]
    code = forest_to_ast(dom.load(path))
    exec compile(code, path, 'exec') in local_environ
