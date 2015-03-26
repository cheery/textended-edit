import ast

def translate_call(env, func, argv):
    stmts = list(func.stmts)
    args = []
    for arg in argv:
        stmts.extend(arg.stmts)
        args.append(arg.expr)
    return Box(env.new_node(ast.Call, func.expr, args, [], None, None), stmts)

# Could use for vargs later..
def translate_argument_expr(env, expr):
    return expr
# #     args = []
# #     varg = None
# #     for style, expr in argv:
# #         if style == 'arg':
# #             args.append(expr)
# #         elif style == 'vararg':
# #             varg = expr
# #         else:
# #             assert False, "should not happen"
# #     return env.new_node(ast.Call, func, args, [], varg, None)
# 
#     print subj, args
# 
#     assert False

def translate_stmt_expr(env, ebox):
    return Box(env.new_node(ast.Expr, ebox.expr), ebox.stmts)

def translate_expr_symbol(env, name):
    if name == '':
        return Box(env.none())
    if name[:1].isdigit():
        if '.' in name:
            return Box(env.new_node(ast.Num, float(name)))
        return Box(env.new_node(ast.Num, int(name)))
    return Box(env.new_node(ast.Name, as_python_sym(name), ast.Load()))

def translate_lxpr_symbol(env, name):
    return Box(env.new_node(ast.Name, as_python_sym(name), ast.Store()))
 
def translate_expr_string(env, string):
    return Box(env.new_node(ast.Str, string))

def translate_return(env, ebox):
    return Box(env.new_node(ast.Return, ebox.expr), ebox.stmts)

def translate_import(env, *aliases):
    return Box(env.new_node(ast.Import, list(aliases)))

def translate_as(env, name, alias):
    return env.new_node(ast.alias, as_python_sym(name), as_python_sym(alias))

def translate_alias_symbol(env, name):
    return env.new_node(ast.alias, as_python_sym(name), None)

def translate_let(env, lbox, ebox):
    stmts = list(ebox.stmts) + list(lbox.stmts)
    stmts.append(env.new_node(ast.Assign, [lbox.expr], ebox.expr))
    # This is wrong return value for let, but I will fix it later.
    return Box(env.none(), stmts)

def translate_function(env, args, body):
    name = env.new_sym()
    body = []
    for expr in body:
        body.extend(env.statementify(expr))
    body.append(env.new_node(ast.Return, env.none()))
    return Box(
        env.new_node(ast.Name, name, ast.Load()),
        [env.new_node(ast.FunctionDef,
            name,
            ast.arguments([
                env.new_node(ast.Name, as_python_sym(a), ast.Param())
                for a in args], None, None, []),
            body,
            [])])

#def translate_from_import(env, name, aliases):
#    yield env.new_node(ast.ImportFrom, as_python_sym(name), aliases, 0)

def as_python_sym(name):
    return name.encode('utf-8')

# @semantic(stmt, Group('if', [expr], stmt))
# def def_statement(env, cond, body):
#     return env.new_node(ast.If, cond, body, [])
# 
# @semantic(stmt, Group('while', [expr], stmt))
# def def_statement(env, cond, body):
#     return env.new_node(ast.While, cond, body, [])
# 
# @semantic(expr, Group('attr', [expr, Symbol()]))
# def attr_expression(env, subj, name):
#     return env.new_node(ast.Attribute, subj, as_python_sym(name), ast.Load())
# 
# @semantic(expr, Group('cmp', [expr, Symbol(), expr]))
# def cmp_expr(env, lhs, op, rhs):
#     return env.new_node(ast.Compare, lhs, [cmp_operators[op]()], [rhs]) # fix later
# 
# @semantic(expr, Group('list', [], expr))
# def varg_argument(env, exprs):
#     return env.new_node(ast.List, exprs, ast.Load())
# 
# @semantic(expr, Group('tuple', [], expr))
# def varg_argument(env, exprs):
#     return env.new_node(ast.Tuple, exprs, ast.Load())
# 
# cmp_operators = {
#         '==': ast.Eq,
#         '!=': ast.NotEq,
#         '<': ast.Lt,
#         '<=': ast.LtE,
#         '>': ast.Gt,
#         '>=': ast.GtE,
#         'is': ast.Is,
#         'isnot': ast.IsNot,
#         'in': ast.In,
#         'notin': ast.NotIn,
# }
# 
# @semantic(expr, Group('infix', [Symbol(), expr]))
# def infix_expr(env, op, rhs):
#     if op not in unary_operators:
#         raise TranslationError(env.subj, expr)
#     return env.new_node(ast.UnaryOp, unary_operators[op](), rhs)
# 
# unary_operators = {
#         '+': ast.UAdd,
#         '-': ast.USub,
#         '~': ast.Invert,
#         'not': ast.Not,
# }
# 
# @semantic(expr, Group('infix', [expr, Symbol(), expr]))
# def infix_expr(env, lhs, op, rhs):
#     if op not in bin_operators:
#         raise TranslationError(env.subj, expr)
#     return env.new_node(ast.BinOp, lhs, bin_operators[op](), rhs)
# 
# bin_operators = {
#         '+': ast.Add,
#         '-': ast.Sub,
#         '*': ast.Mult,
#         '/': ast.Div,
#         '%': ast.Mod,
#         '**': ast.Pow,
#         '<<': ast.LShift,
#         '>>': ast.RShift,
#         '|': ast.BitOr,
#         '^': ast.BitXor,
#         '&': ast.BitAnd,
#         '//': ast.FloorDiv,
# }
# 
# @semantic(expr, Group('', [expr], argument))
# def call_expression(env, func, argv):
#     args = []
#     varg = None
#     for style, expr in argv:
#         if style == 'arg':
#             args.append(expr)
#         elif style == 'vararg':
#             varg = expr
#         else:
#             assert False, "should not happen"
#     return env.new_node(ast.Call, func, args, [], varg, None)
# 
# @semantic(expr, String("float-rgba"))
# def float_rgba_expression(env, hexdec):
#     channels = [c / 255.0 for c in hex_to_rgb(hexdec)] + [1.0]
#     return env.new_node(ast.Tuple,
#         [ast.Num(x, lineno=0, col_offset=0) for x in channels[:4]],
#         ast.Load())
# 
# def hex_to_rgb(value):
#     lv = len(value)
#     return tuple(int(value[i:i + lv // 3], 16) for i in range(0, lv, lv // 3))
# 
# @semantic(subscript, Context('expr'))
# def expr_subscript(env, expr):
#     return env.new_node(ast.Index, expr)
# 
# @semantic(expr, Group('sub', [expr, subscript]))
# def subscript_expr(env, value, slic):
#     return env.new_node(ast.Subscript, value, slic, ast.Load())
# 
# @semantic(expr_set, Group('sub', [expr, subscript]))
# def subscript_expr_set(env, value, slic):
#     return env.new_node(ast.Subscript, value, slic, ast.Store())
# 
# @semantic(expr_set, Group('attr', [expr, Symbol()]))
# def attr_expression(env, subj, name):
#     return env.new_node(ast.Attribute, subj, as_python_sym(name), ast.Store())
# 
# def put_error_string(errors, node, message):
#     if node.document.name is not None:
#         error = dom.Literal(u"reference", [
#             dom.Literal(u"", node.ident),
#             dom.Literal(u"", unicode(node.document.name)),
#             dom.Literal(u"", [dom.Literal(u"", unicode(message))])])
#     else:
#         error = dom.Literal(u"reference", [
#             dom.Literal(u"", node.ident),
#             dom.Literal(u"", [dom.Literal(u"", unicode(message))])])
#     errors.append(error)
# 
# class Env(object):
#     def __init__(self):
#         self.errors = []
#         self.subj = None
# 
# class SemanticErrors(Exception):
#     def __init__(self, document, name):
#         self.document = document
#         self.name = name
# 
#     def __str__(self):
#         return "{}".format(self.name)
# 
# def import_file_to_module(module_name, path):
#     try:
#         ast = file_as_ast(path)
#         mod = imp.new_module(module_name)
#         mod.__file__ = path
#         eval(ast_compile(ast, path, "exec"), mod.__dict__)
#     except Exception:
#         sys.modules.pop(module_name, None)
#         raise
#     return mod
# 
# def ast_compile(ast, filename, mode):
#     return compile(ast, filename, mode)
# 
# class MetaLoader(object):
#     def __init__(self, path, ispkg):
#         self.path = path
#         self.ispkg = ispkg
# 
#     def load_module(self, fullname):
#         if fullname in sys.modules:
#             return sys.modules[fullname]
# 
#         sys.modules[fullname] = None
#         mod = import_file_to_module(fullname, self.path)
# 
#         mod.__file__ = self.path
#         mod.__loader__ = self
#         mod.__name__ = fullname
# 
#         if self.ispkg:
#             mod.__path__ = []
#             mod.__package__ = fullname
#         else:
#             mod.__package__ = fullname.rpartition('.')[0]
# 
#         sys.modules[fullname] = mod
#         return mod
# 
# class MetaImporter(object):
#     def find_on_path(self, fullname):
#         files = [("{}/{}/__init__.t+", True), ("{}/{}.t+", False)]
#         dirpath = "/".join(fullname.split("."))
#         for path in sys.path:
#             path = os.path.abspath(path)
#             for fp, ispkg in files:
#                 fullpath = fp.format(path, dirpath)
#                 if os.path.exists(fullpath):
#                     return fullpath, ispkg
#         return None, None
# 
#     def find_module(self, fullname, path=None):
#         path, ispkg = self.find_on_path(fullname)
#         if path:
#             return MetaLoader(path, ispkg)
# 
# sys.meta_path.insert(0, MetaImporter())
# 
# if __name__=='__main__':
#     try:
#         sys.argv.pop(0)
#         if len(sys.argv) > 0:
#             sys.path.insert(0, os.path.dirname(sys.argv[0]))
#             import_file_to_module("__main__", sys.argv[0])
#             sys.exit(0)
#         else:
#             sys.stderr.write("usage: treepython.py FILE\n")
#             sys.exit(1)
#     except SemanticErrors as ser:
#         if not sys.stderr.isatty():
#             dom.dump(sys.stderr, ser.document)
#         else:
#             print "semantic errors, route stderr to file"
#         sys.exit(1)
#     except Exception:
#         if sys.stderr.isatty():
#             traceback.print_exc()
#             sys.stderr.write("Pipeline stderr to a file or invoke from an editor to get structured file.\n")
#         else:
#             errors = []
#             errors.append(dom.Literal(u'language', u"python_traceback"))
#             exc_type, exc_value, exc_traceback = sys.exc_info()
#             for filename, lineno, location, line in traceback.extract_tb(exc_traceback):
#                 if line is not None:
#                     errors.append(dom.Literal(u'tracerecord-text', [
#                         dom.Literal(u'', filename.decode('utf-8')),
#                         dom.Symbol(unicode(lineno)),
#                         dom.Literal(u'', location.decode('utf-8')),
#                         dom.Literal(u'', line.decode('utf-8')),
#                     ]))
#                 else:
#                     errors.append(dom.Literal(u'tracerecord', [
#                         dom.Literal(u'', filename.decode('utf-8')),
#                         dom.Literal(u'', lineno_to_ident(lineno)),
#                     ]))
#             errors.append(dom.Literal(u'tracemessage', [
#                 dom.Literal(u'', exc_type.__name__.decode('utf-8')),
#                 dom.Literal(u'', str(exc_value).decode('utf-8')),
#             ]))
#             document = dom.Document(dom.Literal(u'', errors))
#             dom.dump(sys.stderr, document)

class Box(object):
    def __init__(self, expr, stmts=()):
        self.expr = expr
        self.stmts = stmts
