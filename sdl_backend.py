from sdl2 import *
from sdl2.sdlimage import *
from ctypes import c_int, byref

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
            self.mods = set(name for flag, name in modifiers.items() if mod & flag != 0)
            self.text = None

    def __iter__(self):
        self.flush()
        for key in self.pending:
            yield key
        self.pending[:] = ()

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

def get_window_size(window):
    width = c_int()
    height = c_int()
    SDL_GetWindowSize(window, byref(width), byref(height))
    return width.value, height.value
