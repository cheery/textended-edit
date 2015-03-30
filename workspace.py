from dom.grammar import *
from dom import metagrammar
import dom
import sys, os

class Workspace(object):
    def __init__(self):
        self.documents = {}
        self.grammars = {}
        self.clipboard = ""
        self.available_grammars = ['grammar'] + [
            g[:-3] for g in os.listdir('grammars') if g.endswith('.t+')]
        self.available_grammars.sort()
        self.current_grammar = self.get_grammar('grammar')

#        self.unbound = []
#        self.schema_cache = {}
#
#    def new(self):
#        body = dom.Literal(u"", [])
#        document = dom.Document(body, None)
#        self.unbound.append(document)
#        return document
#
#    def attach(self, document, name):
#        self.unbound.append(document)
#        document.name = name
#        return document
#

    def get(self, path, create=True):
        if path in self.documents:
            return self.documents[path]
        elif os.path.isfile(path):
            document = dom.Document(dom.ListCell(dom.load(path), "", ""), self)
            self.documents[path] = document
            return document
        elif not os.path.isdir(os.path.dirname(path)) and os.path.dirname(path) <> "":
            raise Exception("Not a directory: {}".format(os.path.dirname(path)))
        elif create:
            document = dom.Document(dom.ListCell([], u"", u""), self)
            self.documents[path] = document
            return document
        else:
            raise Exception("No such file: {}".format(path))

    def get_grammar(self, name):
        if name == '@':
            return self.current_grammar
        if name == 'grammar':
            return metagrammar.grammar
        path = os.path.join('grammars', name + '.t+')
        if os.path.isfile(path):
            if path not in self.grammars:
                self.grammars[path] = metagrammar.load(dom.load(path), name)
            return self.grammars[path]
        return metagrammar.blank

    def grammar_of(self, cell):
        while cell is not None:
            if cell.label == '@':
                return self.current_grammar
            if len(cell.label) > 0:
                return self.get_grammar(cell.grammar_name)
            cell = cell.parent
        return self.current_grammar

    def write(self, document):
        for path, item in self.documents.items():
            if item is document:
                return dom.save(path, document.body)
        raise Exception("Document doesn't have a filename.")
