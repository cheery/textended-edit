from OpenGL.GL import *
from OpenGL.GL import shaders
from ctypes import c_void_p
from sdl2 import *
from sdl2.sdlimage import *

class ImageLayer(object):
    def __init__(self):
        self.atlas = glGenTextures(1)
        vertex = shaders.compileShader("""
        attribute vec2 position;
        attribute vec4 color;

        uniform vec2 resolution;
        uniform vec2 scroll;

        varying vec4 v_color;
        void main() {
            gl_Position = vec4((position - scroll) / resolution * 2.0 - 1.0, 0.0, 1.0);
            v_color = color;
        }""", GL_VERTEX_SHADER)
        fragment = shaders.compileShader("""
        uniform sampler2D texture;

        varying vec4 v_color;

        void main() {
            gl_FragColor = v_color;
        }""", GL_FRAGMENT_SHADER)
        self.shader = shaders.compileProgram(vertex, fragment)

        self.vbo = glGenBuffers(1)
        self.vertices = []
        self.vertexcount = 0
        self.dirty = True

    def clear(self):
        self.vertices[:] = []
        self.vertexcount = 0
        self.dirty = True

    def vertex(self, x, y, s, t, r, g, b, a):
        self.dirty = True
        self.vertices.extend((x, y, s, t, r, g, b, a))
        self.vertexcount += 1

    def quad(self, (x0, y0, x1, y1), (s0, t0, s1, t1), (r, g, b, a)):
        self.vertex(x0, y0, s0, t0, r, g, b, a)
        self.vertex(x0, y1, s0, t1, r, g, b, a)
        self.vertex(x1, y1, s1, t1, r, g, b, a)
        self.vertex(x1, y0, s1, t0, r, g, b, a)

    def render(self, scroll_x, scroll_y, width, height):
        if len(self.vertices) == 0:
            return
        glDisable(GL_TEXTURE_2D)
        #glEnable(GL_TEXTURE_2D)
        #glBindTexture(GL_TEXTURE_2D, self.texture)

        glUseProgram(self.shader)
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
        if self.dirty:
            vertices = (GLfloat * len(self.vertices))(*self.vertices)
            glBufferData(GL_ARRAY_BUFFER, vertices, GL_DYNAMIC_DRAW)
            self.dirty = False

        loc = glGetUniformLocation(self.shader, "resolution")
        glUniform2f(loc, width, height)

        loc = glGetUniformLocation(self.shader, "scroll")
        glUniform2f(loc, scroll_x, scroll_y)

        a_position = glGetAttribLocation(self.shader, "position")
        #a_texcoord = glGetAttribLocation(self.shader, "texcoord")
        a_color = glGetAttribLocation(self.shader, "color")

        glEnableVertexAttribArray(a_position)
        glVertexAttribPointer(a_position, 2, GL_FLOAT, GL_FALSE, 4*8, c_void_p(0))

        #glEnableVertexAttribArray(a_texcoord)
        #glVertexAttribPointer(a_texcoord, 2, GL_FLOAT, GL_FALSE, 4*8, c_void_p(4*2))

        glEnableVertexAttribArray(a_color)
        glVertexAttribPointer(a_color, 4, GL_FLOAT, GL_FALSE, 4*8, c_void_p(4*4))

        glDrawArrays(GL_QUADS, 0, self.vertexcount)
        glDisableVertexAttribArray(a_position)
        #glDisableVertexAttribArray(a_texcoord)
        glDisableVertexAttribArray(a_color)



class FontLayer(object):
    def __init__(self, font):
        self.font = font
        image = IMG_Load(font.filename.encode('utf-8'))
        texture = glGenTextures(1)

        glEnable(GL_TEXTURE_2D)
        glBindTexture(GL_TEXTURE_2D, texture)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        ptr = c_void_p(image.contents.pixels)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, image.contents.w, image.contents.h, 0, GL_RGBA, GL_UNSIGNED_BYTE, ptr)
        SDL_FreeSurface(image)
        self.texture = texture

        vertex = shaders.compileShader("""
        attribute vec2 position;
        attribute vec2 texcoord;
        attribute vec4 color;

        uniform vec2 resolution;
        uniform vec2 scroll;

        varying vec2 v_texcoord;
        varying vec4 v_color;
        void main() {
            v_texcoord = texcoord;
            gl_Position = vec4((position - scroll) / resolution * 2.0 - 1.0, 0.0, 1.0);
            v_color = color;
        }""", GL_VERTEX_SHADER)
        fragment = shaders.compileShader("""
        uniform sampler2D texture;

        varying vec2 v_texcoord;
        varying vec4 v_color;

        uniform float smoothing;

        void main() {
            float deriv = length(fwidth(v_texcoord));
            float distance = texture2D(texture, v_texcoord).a;
            float alpha = smoothstep(0.5 - smoothing*deriv, 0.5 + smoothing*deriv, distance);
            gl_FragColor = vec4(v_color.rgb, v_color.a*alpha);
        }""", GL_FRAGMENT_SHADER)
        self.shader = shaders.compileProgram(vertex, fragment)

        self.vbo = glGenBuffers(1)
        self.vertices = []
        self.vertexcount = 0
        self.dirty = True

    def clear(self):
        self.vertices[:] = []
        self.vertexcount = 0
        self.dirty = True

    def vertex(self, x, y, s, t, r, g, b, a):
        self.dirty = True
        self.vertices.extend((x, y, s, t, r, g, b, a))
        self.vertexcount += 1

    def quad(self, (x0, y0, x1, y1), (s0, t0, s1, t1), (r, g, b, a)):
        self.vertex(x0, y0, s0, t0, r, g, b, a)
        self.vertex(x0, y1, s0, t1, r, g, b, a)
        self.vertex(x1, y1, s1, t1, r, g, b, a)
        self.vertex(x1, y0, s1, t0, r, g, b, a)

    def render(self, scroll_x, scroll_y, width, height):
        if len(self.vertices) == 0:
            return
        glEnable(GL_TEXTURE_2D)
        glBindTexture(GL_TEXTURE_2D, self.texture)

        glUseProgram(self.shader)
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
        if self.dirty:
            vertices = (GLfloat * len(self.vertices))(*self.vertices)
            glBufferData(GL_ARRAY_BUFFER, vertices, GL_DYNAMIC_DRAW)
            self.dirty = False

        loc = glGetUniformLocation(self.shader, "smoothing")
        glUniform1f(loc, self.font.size * 0.8)

        loc = glGetUniformLocation(self.shader, "resolution")
        glUniform2f(loc, width, height)

        loc = glGetUniformLocation(self.shader, "scroll")
        glUniform2f(loc, scroll_x, scroll_y)

        a_position = glGetAttribLocation(self.shader, "position")
        a_texcoord = glGetAttribLocation(self.shader, "texcoord")
        a_color = glGetAttribLocation(self.shader, "color")

        glEnableVertexAttribArray(a_position)
        glVertexAttribPointer(a_position, 2, GL_FLOAT, GL_FALSE, 4*8, c_void_p(0))

        glEnableVertexAttribArray(a_texcoord)
        glVertexAttribPointer(a_texcoord, 2, GL_FLOAT, GL_FALSE, 4*8, c_void_p(4*2))

        glEnableVertexAttribArray(a_color)
        glVertexAttribPointer(a_color, 4, GL_FLOAT, GL_FALSE, 4*8, c_void_p(4*4))

        glDrawArrays(GL_QUADS, 0, self.vertexcount)
        glDisableVertexAttribArray(a_position)
        glDisableVertexAttribArray(a_texcoord)
        glDisableVertexAttribArray(a_color)

class FlatLayer(object):
    def __init__(self):
        vertex = shaders.compileShader("""
        attribute vec2 position;
        attribute vec4 color;

        uniform vec2 resolution;
        uniform vec2 scroll;

        varying vec4 v_color;
        void main() {
            v_color = color;
            gl_Position = vec4((position - scroll) / resolution * 2.0 - 1.0, 0.0, 1.0);
        }""", GL_VERTEX_SHADER)
        fragment = shaders.compileShader("""
        varying vec4 v_color;

        void main() {
            gl_FragColor = v_color;
        }""", GL_FRAGMENT_SHADER)
        self.shader = shaders.compileProgram(vertex, fragment)
        self.vbo = glGenBuffers(1)
        self.vertices = []
        self.vertexcount = 0
        self.dirty = True

    def clear(self):
        self.vertices[:] = []
        self.vertexcount = 0
        self.dirty = True

    def vertex(self, x, y, r, g, b, a):
        self.vertices.extend((x, y, r, g, b, a))
        self.vertexcount += 1
        self.dirty = True

    def rect(self, (x, y, w, h), (r, g, b, a)):
        self.vertex(x, y, r, g, b, a)
        self.vertex(x+w, y, r, g, b, a)
        self.vertex(x+w, y+h, r, g, b, a)
        self.vertex(x, y+h, r, g, b, a)

    def render(self, scroll_x, scroll_y, width, height):
        if len(self.vertices) == 0:
            return
        glUseProgram(self.shader)
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
        if self.dirty:
            vertices = (GLfloat * len(self.vertices))(*self.vertices)
            glBufferData(GL_ARRAY_BUFFER, vertices, GL_STREAM_DRAW)
            self.dirty = False

        loc = glGetUniformLocation(self.shader, "resolution")
        glUniform2f(loc, width, height)

        loc = glGetUniformLocation(self.shader, "scroll")
        glUniform2f(loc, scroll_x, scroll_y)

        stride = 6*4

        a_position = glGetAttribLocation(self.shader, "position")
        a_color = glGetAttribLocation(self.shader, "color")

        glEnableVertexAttribArray(a_position)
        glVertexAttribPointer(a_position, 2, GL_FLOAT, GL_FALSE, stride, c_void_p(0))

        glEnableVertexAttribArray(a_color)
        glVertexAttribPointer(a_color, 4, GL_FLOAT, GL_FALSE, stride, c_void_p(4*2))

        glDrawArrays(GL_QUADS, 0, self.vertexcount)
        glDisableVertexAttribArray(a_position)
        glDisableVertexAttribArray(a_color)
