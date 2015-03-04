from boxmodel import hpack
from compositor import Compositor
from ctypes import byref
from OpenGL.GL import *
from position import Position
from sdl2 import *
from workspace import Workspace
import actions
import font
import layout
import sdl_backend
import sys
import time
import traceback

class Visual(object):
    def __init__(self, images, document, options):
        self.images = images
        self.document = document
        self.options = options
        self.compositor = Compositor(images)
        self.rootboxes = []
        self.scroll_x = 0
        self.scroll_y = 0
        self.head = Position.bottom(document.body)
        self.tail = self.head
        self.action = None
        self.continuation = None

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
            if drag:
                self.head = Position(nearest.subj, nearest.index)
            else:
                self.head = Position(nearest.subj, nearest.index)
                self.tail = self.head

    def render(self, scroll_x, scroll_y, width, height):
        glClearColor(*self.options['background'])
        glClear(GL_COLOR_BUFFER_BIT)
        self.compositor.clear()

        options = self.options
        main, outboxes = layout.page(self.document, options)
        self.rootboxes = [main]
        self.compositor.compose(main, 10, 10)
        min_y = 10
        for anchor, outbox in outboxes:
            y = max(anchor.quad[1], min_y)
            self.compositor.compose(outbox, max(options['page_width'], int(main.quad[2])+10), int(y))
            self.rootboxes.append(outbox)
            min_y = outbox.quad[3] + 10

        if self.head.cell is self.tail.cell:
            selection = set()
            start = min(self.head.index, self.tail.index)
            stop = max(self.head.index, self.tail.index)
            common = self.head.cell
        else:
            common, left, right = self.head.cell.order(self.tail.cell)
            selection = scan_external(left, right, set())

        for rootbox in self.rootboxes:
            for subbox in rootbox.traverse():
                if subbox.subj is self.head.cell and subbox.index == self.head.index:
                    x0, y0, x1, y1 = subbox.quad
                    self.compositor.decor((x0, y0, x0+2, y1), None, (1, 0, 0, 1))
                if subbox.subj is self.tail.cell and subbox.index == self.tail.index:
                    x0, y0, x1, y1 = subbox.quad
                    self.compositor.decor((x0, y0, x0+2, y1), None, (1, 0, 0, 1))
                if subbox.subj in selection:
                    self.compositor.decor(subbox.quad, None, (1, 0, 0, 0.4))
                if subbox.subj is self.tail.cell and len(selection) == 0 and start <= subbox.index < stop:
                    self.compositor.decor(subbox.quad, None, (1, 0, 0, 0.4))

        contextline = " -> ".join(reversed([cell.label for cell in common.hierarchy if len(cell.label)]))
        contextline = hpack(options['font'](contextline, options['font_size']))
        self.compositor.compose(contextline, width - contextline.width, height - contextline.depth)

        self.compositor.render(scroll_x, scroll_y, width, height)

    def setpos(self, head, tail=None):
        self.head = head
        self.tail = head if tail is None else tail

def scan_external(left, right, selected):
    while left is not right:
        selected.add(left)
        while left.is_rightmost():
            left = left.parent
        left = left.parent[left.parent.index(left)+1]
        while not left.is_external():
            left = left[0]
    selected.add(right)
    return selected

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

    options = dict(
        background=(0x27/255.0, 0x28/255.0, 0x22/255.0, 1),
        font=font.load("OpenSans.fnt"),
        font_size=12,
        page_width=320,
        white=(1, 1, 1, 1),
        color_string=(1, 1, 0.5, 1.0),
        color_notation=(1.0, 1.0, 1.0, 0.2),
        color_notation_error=(1.0, 0.5, 0.5, 0.2),
        color_empty=(1.0, 1.0, 1.0, 0.5),
        )
    workspace = Workspace()
    document = workspace.get(sys.argv[1])
    visual = Visual(images, document, options)

def main(respond):
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
            elif event.type == SDL_MOUSEWHEEL:
                visual.scroll_x += event.wheel.x * 10.0
                visual.scroll_y += event.wheel.y * 10.0
            else:
                if event.type == SDL_KEYDOWN:
                    if event.key.keysym.sym == SDLK_PAUSE:
                        reload(actions)
                        print "actions table reloaded"

                keyboard.push_event(event)
        actions.interpret(visual, keyboard)
        paint(time.time())
        SDL_GL_SwapWindow(window)

def paint(t):
    width, height = sdl_backend.get_window_size(window)
    glViewport(0, 0, width, height)
    visual.render(visual.scroll_x, visual.scroll_y, width, height)

def clamp(x, low, high):
    return min(max(x, low), high)

if __name__=='__main__':
    init()
    main(lambda: None)
