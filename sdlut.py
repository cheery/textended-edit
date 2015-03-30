# Holds everything SDL I don't want to see elsewhere.
from sdl2 import *
from sdl2.sdlimage import *
from ctypes import c_int, byref
import os

modifiers = {
    KMOD_LSHIFT:  'left shift',
    KMOD_RSHIFT:  'right shift',
    KMOD_LCTRL:  'left ctrl',
    KMOD_RCTRL:  'right ctrl',
    KMOD_LALT:   'left alt',
    KMOD_RALT:   'right alt',
    KMOD_LGUI:  'left gui',
    KMOD_RGUI:  'right gui',
    KMOD_ALT:   'alt',
    KMOD_NUM:   'num',
    KMOD_CAPS:  'caps',
    KMOD_MODE:  'mode',
    KMOD_SHIFT: 'shift',
    KMOD_CTRL:  'ctrl',
    KMOD_GUI:   'gui',
}

# SDL keyboard handling sucks beyond recognition. This thing
# reassociates keyboard events with textinput events so it
# could be suppressed when responding to key macros.
class KeyboardStream(object):
    def __init__(self):
        self.name = None
        self.mods = None
        self.text = None
        self.pending = []

    def flush(self):
        if self.name is not None:
            self.pending.append((self.name, self.mods, self.text))
            self.name = None
            self.mods = None
            self.text = None

    def push_event(self, ev):
        if ev.type == SDL_TEXTINPUT:
            self.text = ev.text.text.decode('utf-8')
        if ev.type == SDL_KEYDOWN:
            sym = ev.key.keysym.sym
            mod = ev.key.keysym.mod
            self.flush()
            self.name = SDL_GetKeyName(sym).decode('utf-8').lower()
            self.mods = set(
                name for flag, name in modifiers.items()
                if mod & flag != 0)
            self.text = None

    def __iter__(self):
        self.flush()
        for key in self.pending:
            yield key
        self.pending[:] = ()

# Many image paths are relative to the file where it appears.
# The path is resolved before it ends up here.
class ImageResources(object):
    def __init__(self):
        self.cache = {}

    def get(self, path):
        if path in self.cache:
            return self.cache[path]
        self.cache[path] = image = IMG_Load(path.encode('utf-8'))
        return image

    def discard(self, path):
        if path in self.cache:
            image = self.cache.pop(path)
            SDL_FreeSurface(image)

# These remaining functions are mostly specialization to my
# use case. All this detail would be just dumb noise in edit.py
class Screen(object):
    def __init__(self, name, width, height):
        SDL_Init(SDL_INIT_VIDEO)
        SDL_GL_SetAttribute(SDL_GL_DOUBLEBUFFER, 1)
        self.window = SDL_CreateWindow(
            name.encode('utf-8'),
            SDL_WINDOWPOS_CENTERED,
            SDL_WINDOWPOS_CENTERED,
            width,
            height,
            (SDL_WINDOW_SHOWN |
                SDL_WINDOW_OPENGL |
                SDL_WINDOW_RESIZABLE))
        self.context = SDL_GL_CreateContext(self.window)
        SDL_StartTextInput()

    @property
    def width(self):
        return get_window_size(self.window)[0]

    @property
    def height(self):
        return get_window_size(self.window)[1]

    def swap(self):
        SDL_GL_SwapWindow(self.window)

def get_window_size(window):
    width = c_int()
    height = c_int()
    SDL_GetWindowSize(window, byref(width), byref(height))
    return width.value, height.value

def poll_events():
    event = SDL_Event()
    while SDL_PollEvent(byref(event)) != 0:
        yield event
