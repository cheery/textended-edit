import ast
import sys
import textended

for filename in sys.argv[1:]:
    with open(filename) as fd:
        source = fd.read()
    root = ast.parse(source, filename)
    print root
    print root.body
