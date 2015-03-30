#!/usr/bin/env python
#from grammar import Context, ListRule
from dom.grammar import symbol, string
from dom import metagrammar
from itertools import count
import ast
import dom
import imp
import os
import sys
import translator

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

def import_file_to_module(module_name, path):
    try:
        ast = file_to_ast(path)
        mod = imp.new_module(module_name)
        mod.__file__ = path
        mod.__dict__.update(default_env)
        eval(compile(ast, path, "exec"), mod.__dict__)
    except Exception:
        sys.modules.pop(module_name, None)
        raise
    return mod

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
        assert isinstance(box, translator.Box)
        for stmt in box.stmts:
            yield stmt
        yield box.expr

    def none(self):
        return self.new_node(ast.Name, "None", ast.Load(), lineno=0, col_offset=0)

class MetaLoader(object):
    def __init__(self, path, ispkg):
        self.path = path
        self.ispkg = ispkg

    def load_module(self, fullname):
        if fullname in sys.modules:
            return sys.modules[fullname]

        sys.modules[fullname] = None
        mod = import_file_to_module(fullname, self.path)

        mod.__file__ = self.path
        mod.__loader__ = self
        mod.__name__ = fullname

        if self.ispkg:
            mod.__path__ = []
            mod.__package__ = fullname
        else:
            mod.__package__ = fullname.rpartition('.')[0]

        sys.modules[fullname] = mod
        return mod

class MetaImporter(object):
    def find_on_path(self, fullname):
        files = [("{}/{}/__init__.t+", True), ("{}/{}.t+", False)]
        dirpath = "/".join(fullname.split("."))
        for path in sys.path:
            path = os.path.abspath(path)
            for fp, ispkg in files:
                fullpath = fp.format(path, dirpath)
                if os.path.exists(fullpath):
                    return fullpath, ispkg
        return None, None

    def find_module(self, fullname, path=None):
        path, ispkg = self.find_on_path(fullname)
        if path:
            return MetaLoader(path, ispkg)

def get_translator(name):
    return getattr(translator, "translate_" + name.replace('-', '_'))

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

sys.meta_path.append(MetaImporter())

def println(*args):
    print ' '.join(map(str, args))

default_env = {
    'println': println
}

if __name__=='__main__':
    local_environ = default_env.copy()
    path = sys.argv[1]
    code = forest_to_ast(dom.load(path))
    exec compile(code, path, 'exec') in local_environ
