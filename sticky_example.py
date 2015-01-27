from ctypes import c_int, byref, c_char, POINTER, c_void_p
from sdl2 import *
from OpenGL.GL import *
import time
from math import sin, cos

def init():
    global window, context
    SDL_Init(SDL_INIT_VIDEO)
    SDL_GL_SetAttribute(SDL_GL_DOUBLEBUFFER, 1)
    window = SDL_CreateWindow(b"textended-edit",
        SDL_WINDOWPOS_CENTERED, SDL_WINDOWPOS_CENTERED,
        640, 480, SDL_WINDOW_SHOWN | SDL_WINDOW_OPENGL | SDL_WINDOW_RESIZABLE)
    context = SDL_GL_CreateContext(window)
    SDL_StartTextInput()

def main(respond):
    event = SDL_Event()
    running = True
    while running:
        respond()
        while SDL_PollEvent(byref(event)) != 0:
            if event.type == SDL_QUIT:
                running = False
        paint(time.time())
        SDL_GL_SwapWindow(window)

def paint(t):
    glClearColor(0.0, 0.0, sin(t)*0.2+0.5, 1.0)
    glClear(GL_COLOR_BUFFER_BIT)

def quit():
    SDL_GL_DeleteContext(context)
    SDL_DestroyWindow(window)
    SDL_Quit()

if __name__=='__main__':
    init()
    main(lambda: None)
