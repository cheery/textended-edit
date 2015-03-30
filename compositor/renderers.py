# Bit like in image manipulation program, the screen output
# consists of layers. We've got various different layers that
# are filled up by the compositor.
from OpenGL.GL import *
from OpenGL.GL import shaders
from ctypes import POINTER, cast, c_char, c_void_p, byref
import atlas

class ImageLayer(object):
    def __init__(self, images):
        self.images = images
        self.texture = glGenTextures(1)
        self.width = 64
        self.height = 64
        self.allocator = atlas.Allocator(self.width, self.height)
        self.subtextures = {}
        self.patch9_metrics = {}

        glEnable(GL_TEXTURE_2D)
        glBindTexture(GL_TEXTURE_2D, self.texture)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
        glTexImage2D(
            GL_TEXTURE_2D,
            0,
            GL_RGBA,
            self.width,
            self.height,
            0,
            GL_RGBA,
            GL_UNSIGNED_BYTE,
            c_void_p(0))

        self.vertexshader = shaders.compileShader("""
        attribute vec2 position;
        attribute vec4 color;
        attribute vec2 texcoord;

        uniform vec2 resolution;
        uniform vec2 scroll;

        varying vec2 v_texcoord;
        varying vec4 v_color;
        void main() {
            vec2 p = (position + scroll) / resolution * 2.0 - 1.0;
            gl_Position = vec4(p.x, -p.y, 0.0, 1.0);
            v_texcoord = texcoord;
            v_color = color;
        }""", GL_VERTEX_SHADER)
        self.fragmentshader = shaders.compileShader("""
        uniform sampler2D texture;

        varying vec2 v_texcoord;
        varying vec4 v_color;

        void main() {
            gl_FragColor = v_color * texture2D(texture, v_texcoord);
        }""", GL_FRAGMENT_SHADER)
        self.shader = shaders.compileProgram(
            self.vertexshader,
            self.fragmentshader)

        self.vbo = glGenBuffers(1)
        self.vertices = []
        self.vertexcount = 0
        self.dirty = True

    def close(self):
        glDeleteTextures(self.texture)
        glDeleteBuffers(1, [self.vbo])
        glDeleteShader(self.vertexshader)
        glDeleteShader(self.fragmentshader)
        glDeleteProgram(self.shader)

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

    def patch9(self,
            (x0, y0, x3, y3),
            (s0, t0, s1, t1, s2, t2, s3, t3),
            color):
        if x3 < x0:
            x0, x3 = x3, x0
        if y3 < y0:
            y0, y3 = y3, y0
        dx0 = (s1-s0)*self.width
        dx1 = (s3-s2)*self.height
        dy0 = (t1-t0)*self.width
        dy1 = (t3-t2)*self.height
        x1 = x0 + dx0
        y1 = y0 + dy0
        x2 = x3 - dx1
        y2 = y3 - dy1
        self.quad((x0, y0, x1, y1), (s0, t0, s1, t1), color)
        self.quad((x1, y0, x2, y1), (s1, t0, s2, t1), color)
        self.quad((x2, y0, x3, y1), (s2, t0, s3, t1), color)
        self.quad((x0, y1, x1, y2), (s0, t1, s1, t2), color)
        self.quad((x1, y1, x2, y2), (s1, t1, s2, t2), color)
        self.quad((x2, y1, x3, y2), (s2, t1, s3, t2), color)
        self.quad((x0, y2, x1, y3), (s0, t2, s1, t3), color)
        self.quad((x1, y2, x2, y3), (s1, t2, s2, t3), color)
        self.quad((x2, y2, x3, y3), (s2, t2, s3, t3), color)

    def patch9_texcoords(self, path):
        if path in self.patch9_metrics:
            return self.patch9_metrics[path]
        s0, t0, s3, t3 = self.texcoords(path)
        image = self.images.get(path)
        width = image.contents.w
        height = image.contents.h
        pixels = cast(c_void_p(image.contents.pixels), POINTER(c_char))
        x_stripe = [i for i in range(1, width)
            if pixels[i*4] == '\x00']
        y_stripe = [i for i in range(1, height)
            if pixels[i*4*width] == '\x00']
        s1 = s0 + float(x_stripe[0])  / self.width
        s2 = s0 + float(x_stripe[-1]) / self.width
        t1 = t0 + float(y_stripe[0]) / self.height
        t2 = t0 + float(y_stripe[-1]) / self.height
        s0 += 1.0 / self.width
        t0 += 1.0 / self.height
        self.patch9_metrics[path] = tx = s0, t0, s1, t1, s2, t2, s3, t3
        return tx

    def texcoords(self, path):
        if path in self.subtextures:
            return self.subtextures[path]
        if path is None:
            source = None
            width = 8
            height = 8
        else:
            source = self.images.get(path)
            width = source.contents.w
            height = source.contents.h
        item = self.allocator.allocate(width, height, source)
        self.subtextures[path] = tx = (
            float(item.x) / self.width,
            float(item.y) / self.height,
            float(item.x + item.width) / self.width,
            float(item.y + item.height) / self.height,
        )
        return tx

    def render(self, scroll_x, scroll_y, width, height):
        if len(self.vertices) == 0:
            return
        glEnable(GL_TEXTURE_2D)
        glBindTexture(GL_TEXTURE_2D, self.texture)
        for area in self.allocator.dirty:
            if area.source is None:
                data = '\xff'*(4*8*8)
            else:
                data = c_void_p(area.source.contents.pixels)
            glTexSubImage2D(
                GL_TEXTURE_2D,
                0,
                area.x,
                area.y,
                area.width,
                area.height,
                GL_RGBA,
                GL_UNSIGNED_BYTE,
                data)
        self.allocator.dirty[:] = ()

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
        a_texcoord = glGetAttribLocation(self.shader, "texcoord")
        a_color = glGetAttribLocation(self.shader, "color")

        glEnableVertexAttribArray(a_position)
        glVertexAttribPointer(
            a_position, 2, GL_FLOAT, GL_FALSE, 4*8, c_void_p(0))

        glEnableVertexAttribArray(a_texcoord)
        glVertexAttribPointer(
            a_texcoord, 2, GL_FLOAT, GL_FALSE, 4*8, c_void_p(4*2))

        glEnableVertexAttribArray(a_color)
        glVertexAttribPointer(
            a_color, 4, GL_FLOAT, GL_FALSE, 4*8, c_void_p(4*4))

        glDrawArrays(GL_QUADS, 0, self.vertexcount)
        glDisableVertexAttribArray(a_position)
        glDisableVertexAttribArray(a_texcoord)
        glDisableVertexAttribArray(a_color)

class FontLayer(object):
    def __init__(self, images, font):
        self.images = images
        self.font = font

        image = images.get(font.filename)
        texture = glGenTextures(1)

        glEnable(GL_TEXTURE_2D)
        glBindTexture(GL_TEXTURE_2D, texture)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        ptr = c_void_p(image.contents.pixels)
        glTexImage2D(
            GL_TEXTURE_2D,
            0,
            GL_RGBA,
            image.contents.w,
            image.contents.h,
            0,
            GL_RGBA,
            GL_UNSIGNED_BYTE,
            ptr)
        self.texture = texture

        self.vertexshader = shaders.compileShader("""
        attribute vec2 position;
        attribute vec2 texcoord;
        attribute vec4 color;

        uniform vec2 resolution;
        uniform vec2 scroll;

        varying vec2 v_texcoord;
        varying vec4 v_color;
        void main() {
            vec2 p = (position + scroll) / resolution * 2.0 - 1.0;
            gl_Position = vec4(p.x, -p.y, 0.0, 1.0);
            v_texcoord = texcoord;
            v_color = color;
        }""", GL_VERTEX_SHADER)
        self.fragmentshader = shaders.compileShader("""
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
        self.shader = shaders.compileProgram(
            self.vertexshader,
            self.fragmentshader)

        self.vbo = glGenBuffers(1)
        self.vertices = []
        self.vertexcount = 0
        self.dirty = True

    def close(self):
        glDeleteTextures(self.texture)
        glDeleteBuffers(1, [self.vbo])
        glDeleteShader(self.vertexshader)
        glDeleteShader(self.fragmentshader)
        glDeleteProgram(self.shader)

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
        glVertexAttribPointer(
            a_position, 2, GL_FLOAT, GL_FALSE, 4*8, c_void_p(0))

        glEnableVertexAttribArray(a_texcoord)
        glVertexAttribPointer(
            a_texcoord, 2, GL_FLOAT, GL_FALSE, 4*8, c_void_p(4*2))

        glEnableVertexAttribArray(a_color)
        glVertexAttribPointer(
            a_color, 4, GL_FLOAT, GL_FALSE, 4*8, c_void_p(4*4))

        glDrawArrays(GL_QUADS, 0, self.vertexcount)
        glDisableVertexAttribArray(a_position)
        glDisableVertexAttribArray(a_texcoord)
        glDisableVertexAttribArray(a_color)

class FlatLayer(object):
    def __init__(self):
        self.vertexshader = shaders.compileShader("""
        attribute vec2 position;
        attribute vec4 color;

        uniform vec2 resolution;
        uniform vec2 scroll;

        varying vec4 v_color;
        void main() {
            vec2 p = (position + scroll) / resolution * 2.0 - 1.0;
            gl_Position = vec4(p.x, -p.y, 0.0, 1.0);
            v_color = color;
        }""", GL_VERTEX_SHADER)
        self.fragmentshader = shaders.compileShader("""
        varying vec4 v_color;

        void main() {
            gl_FragColor = v_color;
        }""", GL_FRAGMENT_SHADER)
        self.shader = shaders.compileProgram(
            self.vertexshader,
            self.fragmentshader)
        self.vbo = glGenBuffers(1)
        self.vertices = []
        self.vertexcount = 0
        self.dirty = True

    def close(self):
        glDeleteBuffers(1, [self.vbo])
        glDeleteShader(self.vertexshader)
        glDeleteShader(self.fragmentshader)
        glDeleteProgram(self.shader)

    def clear(self):
        self.vertices[:] = []
        self.vertexcount = 0
        self.dirty = True

    def vertex(self, x, y, r, g, b, a):
        self.vertices.extend((x, y, r, g, b, a))
        self.vertexcount += 1
        self.dirty = True

    def quad(self, (x0, y0, x1, y1), (r, g, b, a)):
        self.vertex(x0, y0, r, g, b, a)
        self.vertex(x1, y0, r, g, b, a)
        self.vertex(x1, y1, r, g, b, a)
        self.vertex(x0, y1, r, g, b, a)

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
        glVertexAttribPointer(
            a_position, 2, GL_FLOAT, GL_FALSE, stride, c_void_p(0))

        glEnableVertexAttribArray(a_color)
        glVertexAttribPointer(
            a_color, 4, GL_FLOAT, GL_FALSE, stride, c_void_p(4*2))

        glDrawArrays(GL_QUADS, 0, self.vertexcount)
        glDisableVertexAttribArray(a_position)
        glDisableVertexAttribArray(a_color)
