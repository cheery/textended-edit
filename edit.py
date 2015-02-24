from compositor import Compositor
from ctypes import byref
from OpenGL.GL import *
from sdl2 import *
import boxmodel
import font
import sdl_backend
import sys
import time
import traceback

class Visual(object):
    def __init__(self, images, options):
        self.compositor = Compositor(images)
        self.images = images
        self.options = options
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
            if drag:
                pass # self.tail = self.head
            else:
                pass # self.head =

    def render(self, scroll_x, scroll_y, width, height):
        glClearColor(*self.options['background'])
        glClear(GL_COLOR_BUFFER_BIT)
        self.compositor.clear()
#        main, outboxes = layout.page(self.workspace, self.env, self.document.body)
#        self.rootboxes = [main]
#        self.compositor.compose(main, 10, 10)
#        min_y = 10
#        for anchor, outbox in outboxes:
#            y = max(anchor.quad[1], min_y)
#            self.compositor.compose(outbox, max(self.env.width, int(main.quad[2])+10), int(y))
#            self.rootboxes.append(outbox)
#            min_y = outbox.quad[3] + 10
#
#        if self.head.subj is self.tail.subj:
#            selection = set()
#        else:
#            selection = set(leaves(self.head, self.tail))
#
#        for rootbox in self.rootboxes:
#            for subbox in rootbox.traverse():
#                if subbox.subj is self.head.subj and subbox.index == self.head.index:
#                    x0, y0, x1, y1 = subbox.quad
#                    self.compositor.decor((x0, y0, x0+2, y1), None, (1, 0, 0, 1))
#                if subbox.subj is self.tail.subj and subbox.index == self.tail.index:
#                    x0, y0, x1, y1 = subbox.quad
#                    self.compositor.decor((x0, y0, x0+2, y1), None, (0, 1, 0, 1))
#
#                if subbox.subj in selection:
#                    self.compositor.decor(subbox.quad, None, (1, 0, 0, 0.2))
#
#        contextline = " -> ".join(textualcontext(self.head.subj, []))
#        contextline = boxmodel.hpack(self.env.font(contextline, 10))
#        self.compositor.compose(contextline, width - contextline.width, height - contextline.depth)
#
        self.compositor.render(scroll_x, scroll_y, width, height)

def init():
    global window, context, visual
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
        page_width=320)

    visual = Visual(images, options)

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
                pass
            else:
                keyboard.push_event(event)
        for key, mod, text in keyboard:
            try:
                print key, mod, text
            except Exception:
                traceback.print_exc()
        paint(time.time())
        SDL_GL_SwapWindow(window)

def paint(t):
    width, height = sdl_backend.get_window_size(window)
    glViewport(0, 0, width, height)
    visual.render(0, 0, width, height)

def clamp(x, low, high):
    return min(max(x, low), high)

if __name__=='__main__':
    init()
    main(lambda: None)
