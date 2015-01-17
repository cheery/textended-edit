import dom

class SemanticErrors(Exception):
    def __init__(self, document):
        self.document = document

def compile_expression(expr):
    if expr.type == 'symbol':
        symbol = expr[:]
        if symbol[:1].isdigit():
            return ast.Num(int(symbol), lineno=0, col_offset=0)
        else:
            return ast.Name(symbol, ast.Load(), lineno=0, col_offset=0)
    else:
        assert False

def evaluate_document(document):
    for item in document.body:
        if item.label == 'language':
            language = item[:]
            break
    else:
        return
    if language != 'python':
        return
    statements = []
    errors = []
    for item in document.body:
        if item.label == 'language':
            assert item[:] == 'python'
        elif item.label == 'print' and item.type == 'list':
            statement = ast.Print(None, [compile_expression(expr) for expr in item], True, lineno=0, col_offset=0)
            statements.append(statement)
        else:
            if isinstance(item, dom.Literal):
                errors.append(
                    dom.Literal("", u"reference", [
                        dom.Literal("", u"", item.ident),
                        dom.Literal("", u"", [dom.Literal("", u"", u"unknown node")])]))
    if errors:
        raise SemanticErrors(dom.Document(dom.Literal("", u"", errors)))
    exec compile(ast.Module(statements), "t+", 'exec')
