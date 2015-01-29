import textended
import sys
import pyttsx

engine = pyttsx.init()
engine.setProperty('rate', 70)
voices = engine.getProperty('voices')

contents = textended.load(open(sys.argv[1]))

def print_out(node):
    if node.contents is None:
        pass
    elif isinstance(node.contents, str):
        engine.say(node.label + " binary" + node.contents.encode('hex'))
    elif isinstance(node.contents, unicode):
        engine.say(node.label + " string " + node.contents)
    else:
        engine.say(node.label + " begin")
        for subnode in node:
            print_out(subnode)
        engine.say("done")

for node in contents:
    print_out(node)

engine.runAndWait()
