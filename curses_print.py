import textended
import sys

contents = textended.load(open(sys.argv[1]))

def print_out(node):
    if node.label != "":
        sys.stdout.write(node.label)
    if node.contents is None:
        pass
    elif isinstance(node.contents, str):
        sys.stdout.write(':binary ' + node.contents.encode('hex') + ';')
    elif isinstance(node.contents, unicode):
        sys.stdout.write(':string ' + node.contents + ';')
    else:
        sys.stdout.write('[ ')
        for subnode in node:
            print_out(subnode)
        sys.stdout.write(']')
    sys.stdout.write(' ')

for node in contents:
    print_out(node)
sys.stdout.write('\n')
