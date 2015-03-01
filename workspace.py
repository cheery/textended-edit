from grammar import *
import dom
import metagrammar
import sys, os

class Workspace(object):
    def __init__(self):
        self.documents = {}
        self.grammars = {}
        self.clipboard = None
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
            document = dom.Document(dom.ListCell("", dom.load(path)), self)
            self.documents[path] = document
            return document
        elif not os.path.isdir(os.path.dirname(path)) and os.path.dirname(path) <> "":
            raise Exception("Not a directory: {}".format(os.path.dirname(path)))
        elif create:
            document = dom.Document(dom.ListCell("", []), self)
            self.documents[path] = document
            return document
        else:
            raise Exception("No such file: {}".format(path))

    def get_grammar(self, name):
        if name == 'grammar':
            return metagrammar.grammar
        path = os.path.join('grammars', name + '.t+')
        if os.path.isfile(path):
            if path not in self.grammars:
                self.grammars[path] = metagrammar.load(dom.load(path))
            return self.grammars[path]

    def grammar_of(self, cell):
        while cell.parent is not None:
            cell = cell.parent
            if modeblock.validate(cell):
                return self.get_grammar(cell[0][0][:])
        if len(cell) > 0 and modeline.validate(cell[0]):
            return self.get_grammar(cell[0][0][:])
