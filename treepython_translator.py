import ast

def translate_print(env, *exprs):
    yield env.new_node(ast.Print, None, list(exprs), True)

def translate_expr_string(env, string):
    return env.new_node(ast.Str, string)


#def translate_expr_symbol(env, name):
#    return env.new_node(ast.

def as_python_sym(name):
    return name.encode('utf-8')
