import dom
import ast

class SemanticErrors(Exception):
    def __init__(self, document):
        self.document = document

def check_literal(node, label, type):
    return isinstance(node, dom.Literal) and node.label == label and isinstance(node.contents, type)

def expect_symbol(node, errors):
    if isinstance(node, dom.Symbol):
        return node[:].encode('utf-8')
    else:
        put_error_string(errors, node, "expected symbol")

def compile_expression(expr, errors):
    if expr.type == 'symbol':
        symbol = expr[:]
        if symbol[:1].isdigit():
            return ast.Num(int(symbol), lineno=0, col_offset=0)
        else:
            return ast.Name(symbol[:].encode('utf-8'), ast.Load(), lineno=0, col_offset=0)
    elif expr.type == 'string':
        return ast.Str(expr[:], lineno=0, col_offset=0)
    elif check_literal(expr, 'attr', list) and len(expr) == 2:
        subj = compile_expression(expr[0], errors)
        name = expect_symbol(expr[1], errors)
        return ast.Attribute(subj, name, ast.Load(), lineno=0, col_offset=0)
    else:
        put_error_string(errors, expr, "unknown semantics")

def compile_statement(stmt, errors):
    if check_literal(stmt, 'print', list):
        statement = ast.Print(None, [compile_expression(expr, errors) for expr in stmt], True, lineno=0, col_offset=0)
        yield statement
    elif check_literal(stmt, 'import', list):
        imports = []
        for node in stmt:
            if isinstance(node, dom.Symbol):
                imports.append(ast.alias(node[:].encode('utf-8'), None))
            else:
                put_error_string(errors, node, "unknown import semantics")
        yield ast.Import(imports, lineno=0, col_offset=0)
    else:
        yield ast.Expr(compile_expression(stmt, errors))

    def put_error_string(errors, node, message):
        if isinstance(node, dom.Literal):
            errors.append(
                dom.Literal("", u"reference", [
                    dom.Literal("", u"", node.ident),
                    dom.Literal("", u"", [dom.Literal("", u"", unicode(message))])]))

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
        else:
            statements.extend(compile_statement(item, errors))
    if errors:
        raise SemanticErrors(dom.Document(dom.Literal("", u"", errors)))
    exec compile(ast.Module(statements), "t+", 'exec')
