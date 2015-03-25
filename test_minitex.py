from compositor import Compositor
from ctypes import byref
from minitex import *
from OpenGL.GL import *
from sdl2 import *
import font
import sdl_backend
import time

def main(respond):
    global window, compositor, env
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
    compositor = Compositor(images)
    env = Environ.root(
        font=font.load("OpenSans.fnt"),
        font_size=16,
        color=(0, 0, 0, 1.0))
    keyboard = sdl_backend.KeyboardStream()
    event = SDL_Event()
    running = True
    while running:
        respond()
        while SDL_PollEvent(byref(event)) != 0:
            if event.type == SDL_QUIT:
                running = False
            elif event.type == SDL_MOUSEBUTTONDOWN:
                compositor.debug = not compositor.debug
            else:
                pass #keyboard.push_event(event)
        paint(time.time())
        SDL_GL_SwapWindow(window)


def paint(t):
    width, height = sdl_backend.get_window_size(window)
    glViewport(0, 0, width, height)

    glClearColor(0.8, 0.8, 0.7, 1.0)
    glClear(GL_COLOR_BUFFER_BIT)
    compositor.clear()
    box = toplevel(page(), env, page_width=width-20)#, line_break=line_break)
    compositor.compose(box, 10, box.height + 10)
    compositor.render(0, 0, width, height)

def page():
    return [
        "Hi there, We have not been properly introduced, but I already know your name. You're the ",
        scope(["AMAZING Spiderman"], font_size=20), ". I am pleased to meet you!",
        par,
        scope(["- Bonzi"], font_size=10, color=(0.4, 0, 0, 1))
    ]

if __name__=='__main__':
    main(lambda: None)
