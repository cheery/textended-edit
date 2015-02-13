from compositor import Compositor
from ctypes import c_int, byref, c_char, POINTER, c_void_p
from OpenGL.GL import *
from selection import Position
from sdl2 import *
import dom
import font
import sdl_backend
import time
import schema_layout
import sys

def init():
    global window, context, images, env, document, compositor, head #back, middle, front, document, env, head, tail
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

    env = Object(
        background=(0x27/255.0, 0x28/255.0, 0x22/255.0, 1), #272822
        white=(1.0, 1.0, 1.0, 1.0),
        blue=(0.5, 0.5, 1.0, 1.0),
        green=(1.0, 1.0, 0.0, 1.0),
        yellow=(1.0, 1.0, 0.0, 1.0),
        pink=(1.0, 0.0, 1.0, 1.0),
        gray=(0.5, 0.5, 0.5, 1.0),
        fontsize=12,
        font=font.load("OpenSans.fnt"))

    document = dom.Document(dom.Literal(u"", dom.load(sys.argv[1])))
    compositor = Compositor(images)
    head = Position.bottom(document.body)

    #head = Position(len(document)-1, len(document[-1]))
    #tail = Position(len(document)-1, len(document[-1]))

def main(respond):
    #global head, tail
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
                    pick(event.motion.x, event.motion.y, True)
            elif event.type == SDL_MOUSEBUTTONDOWN:
                pick(event.motion.x, event.motion.y)
            #elif event.type == SDL_MOUSEWHEEL:
            #    selection.visual.scroll_x -= event.wheel.x * 10.0
            #    selection.visual.scroll_y -= event.wheel.y * 10.0
            else:
                keyboard.push_event(event)
        for key, mod, text in keyboard:
            try:
                print key, mod, text
#                if key == 'escape':
#                    sys.exit(0)
#                if key == 'f10':
#                    syms = [Symbol(""), Symbol("")]
#                    Group(r_test, syms)
#                    document.put(head.pos+1, syms)
#                if key == 'tab':
#                    head = tail = trim_plant(document, head, tail)
                if key == 'f12':
                    compositor.debug = not compositor.debug
#                    back.debug = not back.debug
#                    middle.debug = not middle.debug
#                    front.debug = not front.debug
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
            except Exception:
                traceback.print_exc()
        paint(time.time())
        SDL_GL_SwapWindow(window)

def pick(x, y, drag=False):
    global head
    nearest = None
    distance = 500**4
    for rootbox in rootboxes:
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
        head = Position(nearest.subj, nearest.index)

def paint(t):
    global rootboxes
    width, height = get_window_size()
    glViewport(0, 0, width, height)
    glClearColor(*env.background)
    glClear(GL_COLOR_BUFFER_BIT)
    compositor.clear()
    rootbox = schema_layout.page(env, document.body)
    rootboxes = [rootbox]
    compositor.compose(rootbox, 10, 10)

    for rootbox in rootboxes:
        for subbox in rootbox.traverse():
            if subbox.subj is head.subj and subbox.index == head.index:
                x0, y0, x1, y1 = subbox.quad
                compositor.decor((x0, y0, x0+2, y1), None, (1, 0, 0, 1))

    compositor.render(0, 0, width, height)

def clamp(x, low, high):
    return min(max(x, low), high)

class Object(object):
    def __init__(self, **kw):
        for k in kw:
            setattr(self, k, kw[k])

def get_window_size():
    width = c_int()
    height = c_int()
    SDL_GetWindowSize(window, byref(width), byref(height))
    return width.value, height.value

if __name__=='__main__':
    init()
    main(lambda: None)
