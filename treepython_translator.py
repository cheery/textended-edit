import ast

def translate_return(env, expr):
    yield env.new_node(ast.Return, expr)

def translate_assign(env, lhs, rhs):
    yield env.new_node(ast.Assign, [lhs], rhs)

def translate_import(env, *aliases):
    yield env.new_node(ast.Import, list(aliases))

def translate_from_import(env, name, aliases):
    yield env.new_node(ast.ImportFrom, as_python_sym(name), aliases, 0)

def translate_alias_symbol(env, name):
    return env.new_node(ast.alias, as_python_sym(name), None)

def translate_print(env, *exprs):
    yield env.new_node(ast.Print, None, list(exprs), True)

def translate_global(env, *globs):
    yield env.new_node(ast.Global, [as_python_sym(sym) for sym in globs])

def translate_expr_binary(env, string):
    return env.new_node(ast.Str, string)

def translate_expr_string(env, string):
    return env.new_node(ast.Str, string)

def translate_expr_blank(env, name):
    return translate_expr_symbol(env, name)

def translate_expr_symbol(env, name):
    if name[:1].isdigit():
        if '.' in name:
            return env.new_node(ast.Num, float(name))
        return env.new_node(ast.Num, int(name))
    return env.new_node(ast.Name, as_python_sym(name), ast.Load())

def translate_expr_store_symbol(env, name):
    return env.new_node(ast.Name, as_python_sym(name), ast.Store())

def translate_stmt_expr(env, expr):
    yield env.new_node(ast.Expr, expr)

def as_python_sym(name):
    return name.encode('utf-8')
