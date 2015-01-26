import sys, os
import dom

class Workspace(object):
    def __init__(self):
        self.documents = {}
        self.unbound = []

    def new(self):
        body = dom.Literal("", u"", [])
        document = dom.Document(body, None)
        self.unbound.append(document)
        return document

    def attach(self, document, name):
        self.unbound.append(document)
        document.filename = name
        return document

    def get(self, path, create=True):
        if path in self.documents:
            return self.documents[path]
        elif os.path.exists(path):
            body = dom.Literal("", u"", dom.load(path))
            self.documents[path] = document = dom.Document(body, path)
            return document
        elif create:
            body = dom.Document("", u"", [])
            self.documents[path] = document = dom.Document(body, path)
            return document
        else:
            raise Exception("No such file: {}".format(path))
