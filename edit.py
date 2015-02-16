from compositor import Compositor
from ctypes import c_int, byref, c_char, POINTER, c_void_p
from OpenGL.GL import *
from selection import Position
from sdl2 import *
from workspace import Workspace
import dom
import font
import layout
import schema
import sdl_backend
import sys
import time
import traceback

class Visual(object):
    def __init__(self, images, workspace, document, env):
        self.images = images
        self.workspace = workspace
        self.document = document
        self.env = env
        self.compositor = Compositor(images)
        self.head = Position.bottom(document.body)
        self.tail = self.head
        self.rootboxes = []

    def pick(self, x, y, drag=False):
        nearest = None
        distance = 500**4
        for rootbox in self.rootboxes:
            for subbox in rootbox.traverse():
                if subbox.subj is not None:
                    x0, y0, x1, y1 = subbox.quad
                    dx = clamp(x, x0, x1) - x
                    dy = clamp(y, y0, y1) - y
                    d = dx**4 + dy**2
                    if d < distance:
                        distance = d
                        nearest = subbox
        if nearest is not None:
            self.head = Position(nearest.subj, nearest.index)
            if not drag:
                self.tail = self.head

    def render(self, scroll_x, scroll_y, width, height):
        glClearColor(*self.env.background)
        glClear(GL_COLOR_BUFFER_BIT)
        self.compositor.clear()
        main, outboxes = layout.page(self.workspace, self.env, self.document.body)
        self.rootboxes = [main]
        self.compositor.compose(main, 10, 10)
        min_y = 10
        for anchor, outbox in outboxes:
            y = max(anchor.quad[1], min_y)
            self.compositor.compose(outbox, max(320, int(main.quad[2])+10), int(y))
            self.rootboxes.append(outbox)
            min_y = outbox.quad[3] + 10

        if self.head.subj is self.tail.subj:
            selection = set()
        else:
            selection = set(leaves(self.head, self.tail))

        for rootbox in self.rootboxes:
            for subbox in rootbox.traverse():
                if subbox.subj is self.head.subj and subbox.index == self.head.index:
                    x0, y0, x1, y1 = subbox.quad
                    self.compositor.decor((x0, y0, x0+2, y1), None, (1, 0, 0, 1))
                if subbox.subj is self.tail.subj and subbox.index == self.tail.index:
                    x0, y0, x1, y1 = subbox.quad
                    self.compositor.decor((x0, y0, x0+2, y1), None, (0, 1, 0, 1))

                if subbox.subj in selection:
                    self.compositor.decor(subbox.quad, None, (1, 0, 0, 0.2))

        self.compositor.render(scroll_x, scroll_y, width, height)

def init():
    global window, context, images, workspace, visual
    SDL_Init(SDL_INIT_VIDEO)
    SDL_GL_SetAttribute(SDL_GL_DOUBLEBUFFER, 1)
    window = SDL_CreateWindow(b"textended-edit",
        SDL_WINDOWPOS_CENTERED, SDL_WINDOWPOS_CENTERED,
        640, 480, SDL_WINDOW_SHOWN | SDL_WINDOW_OPENGL | SDL_WINDOW_RESIZABLE)
    context = SDL_GL_CreateContext(window)
    images = sdl_backend.ImageResources()
    SDL_StartTextInput()

    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

    env = layout.Object(
        background=(0x27/255.0, 0x28/255.0, 0x22/255.0, 1), #272822
        white=(1.0, 1.0, 1.0, 1.0),
        blue=(0.5, 0.5, 1.0, 1.0),
        green=(1.0, 1.0, 0.0, 1.0),
        yellow=(1.0, 1.0, 0.0, 1.0),
        pink=(1.0, 0.0, 1.0, 1.0),
        gray=(0.5, 0.5, 0.5, 1.0),
        fontsize=12,
        font=font.load("OpenSans.fnt"))

    workspace = Workspace()
    document = workspace.get(sys.argv[1])
    visual = Visual(images, workspace, document, env)
    #subj = head.subj
    #if subj.islist():
    #    sym = dom.Symbol(u"")
    #    subj.put(len(subj), [sym])
    #    tail = head = Position.bottom(sym)

def main(respond):
    global head, tail
    keyboard = sdl_backend.KeyboardStream()
    event = SDL_Event()
    running = True
    while running:
        respond()
        while SDL_PollEvent(byref(event)) != 0:
            if event.type == SDL_QUIT:
                running = False
            elif event.type == SDL_MOUSEMOTION:
                if event.motion.state != 0:
                    visual.pick(event.motion.x, event.motion.y, True)
            elif event.type == SDL_MOUSEBUTTONDOWN:
                visual.pick(event.motion.x, event.motion.y)
            #elif event.type == SDL_MOUSEWHEEL:
                #selection.visual.scroll_x += event.wheel.x * 10.0
                #selection.visual.scroll_y += event.wheel.y * 10.0
            else:
                keyboard.push_event(event)
        for key, mod, text in keyboard:
            try:
                #print list(forest(head, tail))
                print key, mod, text
#                if key == 'escape':
#                    sys.exit(0)
#                if key == 'f10':
#                    syms = [Symbol(""), Symbol("")]
#                    Group(r_test, syms)
#                    document.put(head.pos+1, syms)
#                if key == 'tab':
#                    head = tail = trim_plant(document, head, tail)
                if key == 's' and 'ctrl' in mod:
                    print "saved", document.name
                    dom.save(document.name, document.body)
                if key == 'backspace' and 'ctrl' in mod:
                    subj = head.subj
                    parent = subj.parent
                    if parent is not None:
                        index = parent.index(subj)
                        parent.drop(index, index+1)
                        tail = head = Position.top(parent[index])
                if key == 'f1':
                    if schema.has_modeline(document.body):
                        tail = head = Position.bottom(document.body[0])
                    else:
                        modeline = schema.modeline.blank()
                        document.body.put(0, [modeline])
                        tail = head = Position.bottom(modeline)


                if key == 'f12':
                    compositor.debug = not compositor.debug
#                if key == 'a' and 'ctrl' in mod:
#                    head, tail = expand_selection(document, head, tail)
#                if key == 'f' and 'ctrl' in mod:
#                    print forestify(document, head, tail)
#                if key == 'e' and 'ctrl' in mod:
#                    print earley.parse(forestify(document, head, tail), c_expr.rules)
#                if key == 'i' and 'ctrl' in mod:
#                    results = earley.parse(forestify(document, head, tail), [r_and])
#                    if len(results) > 0:
#                        document.put(min(head, tail).pos, document.drop(min(head, tail).pos, max(head, tail).pos))
#                    assemble(results[0])
#                if key == 'backspace':
#                    head = tail = do_drop(document, head, tail)
#                elif key == 'space':
#                    symbol = document[head.pos]
#                    document.put(head.pos+1, [Symbol(symbol.drop(head.index, len(symbol)))])
#                    head = Position(head.pos+1, 0)
#                    tail = head
#                elif text is not None:
#                    symbol = document[head.pos]
#                    symbol.put(head.index, text)
#                    head = Position(head.pos, head.index + len(text))
#                    tail = head
                if text == ';':
                    subj = head.subj
                    above = head.above
                    if subj.issymbol() and above is not None:
                        head = above+1
                    above = head.above
                    if above is not None:
                        blank = dom.Symbol(u"")
                        (above+1).put([blank])
                        head = tail = Position(blank, 0)
                elif key == 'tab' and head.subj.issymbol():
                    result = []
                    active = workspace.active_schema(head.subj)
                    name = head.subj[:]
                    for rule in active.rules:
                        if rule.startswith(name):
                            result.append(rule)
                    block = active.rules[result.pop(0)].blank()
                    subj = head.subj
                    parent = subj.parent
                    index = parent.index(subj)
                    parent.drop(index, index+1)
                    parent.put(index, [block])
                    tail = head = Position.top(block)
                elif 'left alt' in mod and text != None and head.subj.isblank():
                    result = []
                    active = workspace.active_schema(head.subj)
                    for rule in active.rules:
                        if rule.startswith(text):
                            result.append(rule)
                    block = active.rules[result.pop(0)].blank()
                    subj = head.subj
                    parent = subj.parent
                    index = parent.index(subj)
                    parent.drop(index, index+1)
                    parent.put(index, [block])
                    tail = head = Position.top(block)
                elif key == 'backspace' and not head.subj.islist():
                    if head.index > 0:
                        head.subj.drop(head.index-1, head.index)
                        tail = head = Position(head.subj, head.index-1)
                elif key == 'delete' and not head.subj.islist():
                    if head.index < len(head.subj):
                        head.subj.drop(head.index, head.index+1)
                elif key == 'space' and visual.head.subj.issymbol():
                    subj = visual.head.subj
                    index = visual.head.index
                    above = visual.head.above
                    new_symbol = dom.Symbol(subj.drop(index, len(subj)))
                    rule = workspace.active_schema(above.subj).recognize_in_context(above.subj)
                    print "current rule", rule
                    (above+1).put([new_symbol])
                    visual.tail = visual.head = Position(new_symbol, 0)

                    #newsym = dom.Symbol(subj.drop(head.index, len(subj))
                    #subj = head.subj
                    #parent = subj.parent
                    #index = parent.index(subj)
                    #nsym = dom.Symbol(subj.drop(head.index, len(subj)))
                    #seq = parent.drop(index, index+1) + [nsym]
                    #if parent.label in ('@', '##'):
                    #    parent.put(index, seq)
                    #else:
                    #    parent.put(index, [dom.Literal(u'@', seq)])
                    #tail = head = Position(nsym, 0)
                elif text == ';' and head.subj.isstring():
                    subj = head.subj
                    parent = subj.parent
                    index = parent.index(subj)+1
                    sym = dom.Symbol(u"")
                    parent.put(index, [sym])
                    tail = head = Position(sym, 0)
                elif text == '"' and head.subj.isblank():
                    string = dom.Literal(u"", u"")
                    subj = head.subj
                    parent = subj.parent
                    index = parent.index(subj)
                    parent.drop(index, index+1)
                    parent.put(index, [string])
                    tail = head = Position(string, 0)
                elif text is not None:
                    if visual.head.subj.islist():
                        # should advance until this operation doesn't violate a schema.
                        blank = dom.Symbol(u"")
                        visual.head.put([blank])
                        visual.head = Position(blank, 0)
                    visual.head.put(text)
                    visual.tail = visual.head = visual.head+1
            except Exception:
                traceback.print_exc()
        paint(time.time())
        SDL_GL_SwapWindow(window)

def paint(t):
    width, height = get_window_size()
    glViewport(0, 0, width, height)
    visual.render(0, 0, width, height)

def clamp(x, low, high):
    return min(max(x, low), high)

def get_window_size():
    width = c_int()
    height = c_int()
    SDL_GetWindowSize(window, byref(width), byref(height))
    return width.value, height.value

def forest(head, tail):
    subj, left, right = fingers(head, tail)
    while len(left) > 0 and leftmost(left[-1]):
        left.pop()
    while len(right) > 0 and rightmost(right[-1]):
        right.pop()
    complete = (len(left) == 0 and len(right) == 0)
    while complete and leftmost(subj) and rightmost(subj):
        subj = subj.parent
    if complete:
        yield subj
    else:
        if len(left) > 0:
            lsubj = left.pop()
            yield lsubj
            start = indexof(lsubj) + 1
        else:
            start = 0
        while len(left) > 0:
            lsubj = left.pop()
            for node in lsubj[start:]:
                yield node
            start = indexof(lsubj) + 1
        stop = indexof(right[0]) if len(right) > 0 else len(subj)
        for node in subj[start:stop]:
            yield node
        while len(right) > 1:
            rsubj = right.pop(0)
            for node in rsubj[0:indexof(right[0])]:
                yield node
        for node in right:
            yield node

def leftmost(node):
    parent = node.parent
    return parent is not None and parent.index(node) == 0

def rightmost(node):
    parent = node.parent
    return parent is not None and parent.index(node) == len(parent)-1

def indexof(node):
    return node.parent.index(node)

def leaves(head, tail):
    subj, left, right = fingers(head, tail)
    pivot = left.pop()
    yield pivot
    while len(left) > 0:
        lsubj = left.pop()
        for node in lsubj[lsubj.index(pivot)+1:]:
            for subnode in node.traverse():
                if not subnode.islist():
                    yield subnode
        pivot = lsubj
    rsubj = right.pop(0)
    for node in subj[subj.index(pivot)+1:subj.index(rsubj)]:
        for subnode in node.traverse():
            if not subnode.islist():
                yield subnode
    while len(right) > 0:
        for node in rsubj[:rsubj.index(right[0])]:
            for subnode in node.traverse():
                if not subnode.islist():
                    yield subnode
        rsubj = right.pop(0)
    yield rsubj

def fingers(head, tail):
    h0 = finger(head)
    h1 = finger(tail)
    index = 0
    for p0, p1 in zip(h0, h1):
        if p0 is not p1:
            break
        index += 1
    if index == 0 or len(h0) <= index >= len(h1):
        return
    subj = h0[index-1]
    i0 = subj.index(h0[index])
    i1 = subj.index(h1[index])
    if i0 < i1:
        return subj, h0[index:], h1[index:]
    else:
        return subj, h1[index:], h0[index:]

def finger(position):
    finger = []
    subj = position.subj
    while subj.parent is not None:
        finger.append(subj)
        subj = subj.parent
    finger.append(subj)
    finger.reverse()
    return finger

if __name__=='__main__':
    init()
    main(lambda: None)
