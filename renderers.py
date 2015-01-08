from OpenGL.GL import *
from OpenGL.GL import shaders
from ctypes import c_void_p

visual_vertex_shader = """
attribute vec2 position;
attribute vec4 color;

uniform vec2 resolution;

varying vec4 v_color;
void main() {
    v_color = color;
    gl_Position = vec4(position / resolution * 2.0 - 1.0, 0.0, 1.0);
}"""
visual_fragment_shader = """
varying vec4 v_color;

void main() {
    gl_FragColor = v_color;
}"""


class Visual(object):
    def __init__(self):
        vertex = shaders.compileShader(visual_vertex_shader, GL_VERTEX_SHADER)
        fragment = shaders.compileShader(visual_fragment_shader, GL_FRAGMENT_SHADER)
        self.shader = shaders.compileProgram(vertex, fragment)
        self.vbo = glGenBuffers(1)
        self.vertices = []

    def vertex(self, x, y, r, g, b, a):
        self.vertices.extend((x, y, r, g, b, a))

    def quad(self, (x, y, w, h), (r, g, b, a)):
        self.vertex(x, y, r, g, b, a)
        self.vertex(x+w, y, r, g, b, a)
        self.vertex(x+w, y+h, r, g, b, a)
        self.vertex(x, y+h, r, g, b, a)

    def render(self, width, height):
        if len(self.vertices) == 0:
            return
        glUseProgram(self.shader)

        glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
        vertexcount = len(self.vertices) / 6
        vertices = (GLfloat * len(self.vertices))(*self.vertices)
        glBufferData(GL_ARRAY_BUFFER, vertices, GL_STREAM_DRAW)

        loc = glGetUniformLocation(self.shader, "resolution")
        glUniform2f(loc, width, height)

        stride = 6*4

        i_position = glGetAttribLocation(self.shader, "position")
        glEnableVertexAttribArray(i_position)
        glVertexAttribPointer(i_position, 2, GL_FLOAT, GL_FALSE, stride, c_void_p(0))

        i_color = glGetAttribLocation(self.shader, "color")
        glEnableVertexAttribArray(i_color)
        glVertexAttribPointer(i_color, 4, GL_FLOAT, GL_FALSE, stride, c_void_p(4*2))

        glDrawArrays(GL_QUADS, 0, vertexcount)
        glDisableVertexAttribArray(i_position)
        glDisableVertexAttribArray(i_color)

        self.vertices = []
