import pygame
import gate
import sys
import traceback
import math
import time
import font
import boxmodel
import textended
import renderers
import tempfile
import layout
import os
import defaultlayout
import ast
from OpenGL.GL import *
from OpenGL.GL import shaders
from ctypes import c_void_p
from collections import defaultdict
import dom
from dom import Position, Selection

class Editor(object):
    def __init__(self, document, selection, x=0, y=0, width=200, height=200):
        self.document = document
        self.selection = selection
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.children = []
        self.rootbox = None
        self.build_rootbox = None
        self.update_hook = lambda editor: None
        self.close_hook = lambda editor: None
        self.filename = None
        self.copybuf = None

module = sys.modules[__name__]
#poll   = gate.new(module)

def create_editor():
    contents = []
    for path in sys.argv[1:]:
        if os.path.exists(path):
            contents.extend(dom.load(path))
    body = dom.Literal("", u"", contents)

    document = dom.Document(body)
    if len(sys.argv) == 2:
        document.filename = sys.argv[1]

    selection = Selection.bottom(body)
    editor = Editor(document, selection)
    return editor

editor = create_editor()
focus = editor

editor.build_rootbox = defaultlayout.build_boxmodel

#    return boxmodel.vpack([
#        boxmodel.Caret(None, 0),
#        boxmodel.hpack(sans("Hello world") + [
#            boxmodel.Caret(None, 0),
#            boxmodel.vpack([
#                boxmodel.Caret(None, 0),
#                boxmodel.hpack(sans("t * r", 8)),
#                boxmodel.Caret(None, 1),
#                boxmodel.hpack(sans("t + r", 8)),
#                boxmodel.Caret(None, 2),
#            ]),
#            boxmodel.Caret(None, 1),
#        ] + sans("Abcd")),
#        boxmodel.Caret(None, 1),
#        boxmodel.hpack(sans("AbCD", 80)),
#        boxmodel.Caret(None, 2),
#        boxmodel.hpack(sans("Hello ^", 32)),
#        boxmodel.Caret(None, 3),
#    ])

#pygame.display.init()
#pygame.display.gl_set_attribute(pygame.GL_MULTISAMPLEBUFFERS, 1)
#pygame.display.gl_set_attribute(pygame.GL_MULTISAMPLESAMPLES, 8)

screen = pygame.display.set_mode((640, 480), pygame.DOUBLEBUF | pygame.OPENGL)
editor.width, editor.height = screen.get_size()
editor.x += 10
editor.y += 10
editor.width  -= 20
editor.height -= 20

visual = renderers.Visual()

glEnable(GL_TEXTURE_2D)
glEnable(GL_BLEND)
glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

sans = defaultlayout.sans#font.load('OpenSans.fnt')

data = pygame.image.tostring(sans.image, "RGBA", 1)
texture = glGenTextures(1)
glBindTexture(GL_TEXTURE_2D, texture)
glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, sans.width, sans.height, 0, GL_RGBA, GL_UNSIGNED_BYTE, data)

vertex = shaders.compileShader("""
attribute vec2 position;
attribute vec2 texcoord;

uniform vec2 resolution;

varying vec2 v_texcoord;
void main() {
    v_texcoord = texcoord;
    gl_Position = vec4(position / resolution * 2.0 - 1.0, 0.0, 1.0);
}""", GL_VERTEX_SHADER)
fragment = shaders.compileShader("""
uniform sampler2D texture;

varying vec2 v_texcoord;

uniform float smoothing;
uniform vec4 color;

void main() {
    float deriv = length(fwidth(v_texcoord));
    float distance = texture2D(texture, v_texcoord).a;
    float alpha = smoothstep(0.5 - smoothing*deriv, 0.5 + smoothing*deriv, distance);
    gl_FragColor = vec4(color.rgb, color.a*alpha);
}""", GL_FRAGMENT_SHADER)

shader = shaders.compileProgram(vertex, fragment)

vertexcount = 0
vbo = glGenBuffers(1)

def burst(vertices, subj, x, y):
    global vertexcount
    subj.rect = x, y-subj.depth, subj.width, subj.height+subj.depth
    if isinstance(subj, boxmodel.HBox):
        x0 = x
        for node in subj.contents:
            if isinstance(node, boxmodel.Glue):
                x0 += node.width
            elif isinstance(node, boxmodel.LetterBox):
                x1 = x0 + node.width
                y1 = y + node.height
                y0 = y - node.depth
                s0, t0, s1, t1 = node.texcoords
                p0, p1, p2, p3 = node.padding
                vertices.extend([
                    x0-p0, y0-p1, s0, t0,
                    x0-p0, y1+p3, s0, t1,
                    x1+p2, y1+p3, s1, t1,
                    x1+p2, y0-p1, s1, t0,
                ])
                vertexcount += 4
                x0 = x1
            elif isinstance(node, (boxmodel.HBox, boxmodel.VBox)):
                burst(vertices, node, x0, y)
                x0 += node.width
            elif isinstance(node, boxmodel.Caret):
                node.rect = x0-0.5, y-subj.depth, 1, subj.height+subj.depth
                #visual.quad(node.rect, (255, 0, 0, 0.1))
    elif isinstance(subj, boxmodel.VBox):
        y0 = y + subj.height
        for node in subj.contents:
            if isinstance(node, boxmodel.Glue):
                y0 -= node.width
            elif isinstance(node, (boxmodel.HBox, boxmodel.VBox)):
                burst(vertices, node, x, y0 - node.height)
                y0 -= node.height + node.depth
            elif isinstance(node, boxmodel.Caret):
                node.rect = x, y0-0.5, subj.width, 1
                #visual.quad(node.rect, (0, 255, 0, 0.1))

def update_characters(t):
    global vertexcount
    vertexcount = 0
    vertices = []

    def layout_editor(editor, x, y):
        editor.rootbox = editor.build_rootbox(editor)
        burst(vertices, editor.rootbox, editor.x+x, editor.height - editor.y+y)
        for subeditor in editor.children:
            layout_editor(subeditor, x+editor.x, y+editor.y)
    layout_editor(editor, 0, 0)

    vertices = (GLfloat * len(vertices))(*vertices)
    glBindBuffer(GL_ARRAY_BUFFER, vbo)
    glBufferData(GL_ARRAY_BUFFER, vertices, GL_STREAM_DRAW)

def delta_point_rect(point, rect):
    x0, y0 = point
    x, y, w, h = rect
    x1 = min(max(x0, x), x+w)
    y1 = min(max(y0, y), y+h)
    return (x1-x0), (y1-y0)

def is_hcaret(node):
    if isinstance(node, boxmodel.Caret):
        if not isinstance(node.subj, dom.Node):
            return
        if node.subj.type != 'list' or len(node.subj) == 0:
            return isinstance(node.parent, boxmodel.HBox)

def hcarets_above(node):
    parent = node.parent
    success = False
    while parent is not None:
        if isinstance(parent, boxmodel.VBox):
            index = parent.index(node)
            for item in reversed(parent[:index]):
                for subnode in item.traverse():
                    if is_hcaret(subnode):
                        yield subnode
                        success = True
                if success:
                    return
        node   = parent
        parent = node.parent

def hcarets_below(node):
    parent = node.parent
    success = False
    while parent is not None:
        if isinstance(parent, boxmodel.VBox):
            index = parent.index(node)
            for item in parent[index+1:]:
                for subnode in item.traverse():
                    if is_hcaret(subnode):
                        yield subnode
                        success = True
                if success:
                    return
        node   = parent
        parent = node.parent

cursor = [0, 0]
def update_cursor(t):
    x, y = cursor

    if focus.rootbox is None:
        return
    
    document = focus.document
    cursors = defaultdict(list)
    for node in focus.rootbox.traverse():
        if not isinstance(node, boxmodel.Caret):
            continue
        if node.subj != focus.selection.subj:
            continue
        if node.index < focus.selection.start:
            continue
        if node.index > focus.selection.stop:
            continue
        cursors[node.parent].append(node.rect)

    color = (0, 0, 1.0, 0.5)
    if focus.selection.subj.type == 'list':
        color = (0, 1.0, 0.0, 0.5)
    if focus.selection.subj.type == 'string':
        color = (1.0, 1.0, 0.0, 0.5)
    if focus.selection.subj.type == 'binary':
        color = (0.5, 0.0, 1.0, 0.5)
    for container, cursorset in cursors.items():
        x0, y0, w0, h0 = cursorset[0]
        x2 = x0+w0
        y2 = y0+h0
        for x1, y1, w1, h1 in cursorset[1:]:
            x2 = max(x2, x1+w1)
            y2 = max(y2, y1+h1)
            x0 = min(x0, x1)
            y0 = min(y0, y1)
        visual.quad((x0, y0, x2-x0, y2-y0), color)

def slit(sel):
    if sel.subj.type == 'list':
        return
    if sel.subj.parent is None:
        return
    parent = sel.subj.parent
    pos = parent.index(sel.subj)
    if sel.head != sel.tail:
        sel.drop()
    if sel.head == 0:
        sel.subj = parent
        sel.head = sel.tail = pos
    if sel.head == len(sel.subj):
        sel.subj = parent
        sel.head = sel.tail = pos + 1
    else:
        contents = sel.subj.drop(sel.head, len(sel.subj))
        type = sel.subj.type
        sel.subj = parent
        sel.head = sel.tail = pos + 1
        if type == 'symbol':
            sel.subj.put(sel.head, [dom.Symbol(contents)])
        else:
            sel.subj.put(sel.head, [dom.Literal("", u"", contents)])

def fall_before(sel):
    type = sel.subj.type
    parent = sel.subj.parent
    if parent is None:
        return
    pos = parent.index(sel.subj)
    sel.subj = parent
    sel.head = sel.tail = pos
    if type != 'list':
        fall_before(sel)

def fall_after(sel):
    type = sel.subj.type
    parent = sel.subj.parent
    if parent is None:
        return
    pos = parent.index(sel.subj) + 1
    sel.subj = parent
    sel.head = sel.tail = pos
    if type != 'list':
        fall_after(sel)

def fall_left_leaf(node):
    if node.parent is None:
        return Selection.top(node)
    index = node.parent.index(node)
    if index > 0:
        return Selection.bottom(node.parent[index - 1])
    else:
        return fall_left_leaf(node.parent)

def fall_right_leaf(node):
    if node.parent is None:
        return Selection.bottom(node)
    index = node.parent.index(node) + 1
    if index < len(node.parent):
        return Selection.top(node.parent[index])
    else:
        return fall_right_leaf(node.parent)

def find_caret(editor, subj, index):
    for frame in editor.rootbox.traverse():
        if isinstance(frame, boxmodel.Caret):
            if frame.subj == subj and frame.index == index:
                return frame

def navigate(editor, sel, hcarets_fn):
    caret = find_caret(editor, sel.subj, sel.head)
    if caret is None:
        return
    if sel.x_anchor is None:
        sel.x_anchor = caret.rect[0]
    def nearest(node):
        x,y,w,h = node.rect
        return abs(x - sel.x_anchor)
    try:
        node = min(hcarets_fn(caret), key=nearest)
    except ValueError as v:
        return
    else:
        sel.subj = node.subj
        sel.head = sel.tail = node.index

def hierarchy_of(node):
    result = [node]
    while node.parent is not None:
        result.append(node.parent)
        node = node.parent
    result.reverse()
    return result

def simplify_selection(headpos, tailpos):
    if headpos.subj is tailpos.subj:
        return Selection(headpos.subj, headpos.index, tailpos.index)
    hh = hierarchy_of(headpos.subj)
    th = hierarchy_of(tailpos.subj)
    i = 0
    for c_a, c_b in zip(hh, th):
        if c_a is c_b:
            i += 1
        else:
            break
    assert i > 0
    subj = hh[i-1]
    head_inc = i < len(hh)
    head = subj.index(hh[i]) if head_inc else headpos.index
    tail_inc = i < len(th)
    tail = subj.index(th[i]) if tail_inc else tailpos.index
    if tail <= head:
        head += head_inc
    else:
        tail += tail_inc
    return Selection(subj, head, tail)

def label_editor(editor, sel):
    global focus
    if sel.subj.type == 'symbol':
        subj = sel.subj.parent
    else:
        subj = sel.subj
    if subj is None:
        return

    body = dom.Symbol(subj.label)

    document = dom.Document(body)
    selection = Selection.bottom(body)
    label_editor = Editor(document, selection, x=0, y=0)
    label_editor.build_rootbox = editor.build_rootbox
    editor.children.append(label_editor)
    focus = label_editor

    def hook(editor):
        subj.label = label_editor.document.body[:]
    label_editor.close_hook  = hook
    label_editor.update_hook = hook

def compile_expression(expr):
    if expr.type == 'symbol':
        symbol = expr[:]
        if symbol[:1].isdigit():
            return ast.Num(int(symbol), lineno=0, col_offset=0)
        else:
            return ast.Name(symbol, ast.Load(), lineno=0, col_offset=0)
    else:
        assert False

def evaluate_document(document):
    for item in document.body:
        if item.label == 'language':
            language = item[:]
            break
    else:
        return
    if language != 'python':
        return
    statements = []
    for item in document.body:
        if item.label == 'language':
            assert item[:] == 'python'
        elif item.label == 'print' and item.type == 'list':
            statement = ast.Print(None, [compile_expression(expr) for expr in item], True, lineno=0, col_offset=0)
            statements.append(statement)
        else:
            if isinstance(item, dom.Literal):
                print "error at ", repr(item.ident)
            print "should present the error in the editor"
            print document.nodes
            return
    exec compile(ast.Module(statements), "t+", 'exec')

cursor_tail = None
alt_pressed = False
def process_event(ev):
    global live, cursor_tail, alt_pressed, focus
    document = focus.document
    sel = focus.selection

    if ev.type == pygame.KEYDOWN:
        if alt_pressed and ev.key == pygame.K_LALT:
            label_editor(focus, sel)
        alt_pressed = False

        ctrl = (ev.mod & pygame.KMOD_CTRL) != 0
        shift = (ev.mod & pygame.KMOD_SHIFT) != 0
        if ev.key == pygame.K_ESCAPE:
            if focus != editor:
                focus.close_hook(focus)
                editor.children.remove(focus)
                focus = editor
            else:
                live = False
        elif ev.key == pygame.K_F5:
            evaluate_document(document)
        elif ev.key == pygame.K_LEFT:
            if sel.head > 0:
                if sel.subj.type == 'list':
                    sel = focus.selection = Selection.bottom(sel.subj[sel.head-1])
                else:
                    sel.head -= 1
                    sel.tail = sel.head
                    sel.x_anchor = None
            else:
                sel = focus.selection = fall_left_leaf(sel.subj)
        elif ev.key == pygame.K_RIGHT:
            if sel.head < len(sel.subj):
                if sel.subj.type == 'list':
                    sel = focus.selection = Selection.top(sel.subj[sel.head])
                else:
                    sel.head += 1
                    sel.tail = sel.head
                    sel.x_anchor = None
            else:
                sel = focus.selection = fall_right_leaf(sel.subj)
        elif ev.key == pygame.K_UP:
            navigate(focus, sel, hcarets_above)
        elif ev.key == pygame.K_DOWN:
            navigate(focus, sel, hcarets_below)
        elif ev.key == pygame.K_LALT:
            alt_pressed = True
        elif ctrl and ev.key == pygame.K_s and (document.filename is not None):
            dom.save(document.filename, document.body)
        elif ctrl and ev.key == pygame.K_x:
            document.copybuf = sel.drop()
        elif ctrl and ev.key == pygame.K_c:
            document.copybuf = sel.yank()
        elif ctrl and ev.key == pygame.K_v and (document.copybuf is not None):
            if sel.subj.type == 'list' and isinstance(document.copybuf, list):
                sel.put(document.copybuf)
            if sel.subj.type == 'symbol' and isinstance(document.copybuf, unicode):
                sel.put(document.copybuf)
            if sel.subj.type == 'string' and isinstance(document.copybuf, unicode):
                sel.put(document.copybuf)
            if sel.subj.type == 'binary' and isinstance(document.copybuf, str):
                sel.put(document.copybuf)
        elif ev.unicode == '\x08':
            if sel.head == sel.tail and sel.head > 0:
                sel.head -= 1
            sel.drop()
        elif ev.unicode == '\x7f':
            if sel.head == sel.tail and sel.head < len(sel.subj):
                sel.head += 1
            sel.drop()
        elif ev.unicode == ' ' and sel.subj.type not in ('string', 'binary'):
            if sel.subj.type == 'symbol':
                slit(sel)
        elif ev.unicode == "'":
            slit(sel)
            subj = dom.Literal("", u"", [])
            sel.put([subj])
            sel.subj = subj
            sel.head = sel.tail = 0
            sel.x_anchor = None
        elif ev.unicode == '"':
            slit(sel)
            subj = dom.Literal("", u"", u"")
            sel.put([subj])
            sel.subj = subj
            sel.head = sel.tail = 0
            sel.x_anchor = None
        elif ev.unicode == '#':
            slit(sel)
            subj = dom.Literal("", u"", "")
            sel.put([subj])
            sel.subj = subj
            sel.head = sel.tail = 0
            sel.x_anchor = None
        elif ev.unicode == '(':
            fall_before(sel)
        elif ev.unicode == ')':
            fall_after(sel)
        elif len(ev.unicode) > 0:
            if sel.subj.type in ('string', 'symbol', 'binary'):
                sel.put(ev.unicode)
            elif sel.subj.type == 'list':
                node = dom.Symbol(ev.unicode)
                sel.put([node])
                sel = focus.selection = Selection.bottom(node)
    if ev.type == pygame.MOUSEMOTION:
        cursor[0] = ev.pos[0]
        cursor[1] = screen.get_height() - ev.pos[1]
        if not any(ev.buttons):
            cursor_tail = None
        if cursor_tail is not None:
            node = pick_nearest(focus, *ev.pos)
            if node is not None:
                focus.headpos = Position(node.subj, node.index)
                focus.selection = simplify_selection(focus.headpos, focus.tailpos)
    if ev.type == pygame.MOUSEBUTTONDOWN:
        node = pick_nearest(focus, *ev.pos)
        if node is not None:
            sel.subj = node.subj
            sel.head = sel.tail = node.index
            sel.x_anchor = None
            cursor_tail = Position(node.subj, node.index)
            focus.headpos = focus.tailpos = cursor_tail
            focus.selection = simplify_selection(focus.headpos, focus.tailpos)
    focus.update_hook(focus)

def pick_nearest(editor, x, y):
    def nearest(node):
        dx, dy = delta_point_rect(cursor, node.rect)
        return dx**2 + dy**4
    try:
        node = min((node for node in editor.rootbox.traverse() if is_hcaret(node)), key=nearest)
    except ValueError as v:
        return
    return node

def paint(t):
    glClearColor(0.8, 0.8, 0.8, 1)
    glClear(GL_COLOR_BUFFER_BIT)

    update_characters(t)

    glUseProgram(shader)
    loc = glGetUniformLocation(shader, "smoothing")
    glUniform1f(loc, sans.size * 0.8)

    loc = glGetUniformLocation(shader, "resolution")
    glUniform2f(loc, *screen.get_size())

    loc = glGetUniformLocation(shader, "color")
    glUniform4f(loc, 0, 0, 0, 0.9)

    glBindBuffer(GL_ARRAY_BUFFER, vbo)

    i_position = glGetAttribLocation(shader, "position")
    glEnableVertexAttribArray(i_position)
    glVertexAttribPointer(i_position, 2, GL_FLOAT, GL_FALSE, 4*4, c_void_p(0))

    i_texcoord = glGetAttribLocation(shader, "texcoord")
    glEnableVertexAttribArray(i_texcoord)
    glVertexAttribPointer(i_texcoord, 2, GL_FLOAT, GL_FALSE, 4*4, c_void_p(4*2))

    glDrawArrays(GL_QUADS, 0, vertexcount)
    glDisableVertexAttribArray(i_position)
    glDisableVertexAttribArray(i_texcoord)

    #visual.quad((150+90*math.sin(t), 300, 50, 30), (0, 0.4, 0.9, 0.2))
    #visual.quad((155, 290, 50, 30), (0, 0.4, 0.9, 0.2))
    #visual.quad((150, 280, 50, 30), (0, 0.4, 0.9, 0.2))

    update_cursor(t)

    visual.render(screen)

live = True
while live:
    for ev in pygame.event.get():
        process_event(ev)
        if ev.type == pygame.QUIT:
            live = False
    paint(time.time())
    pygame.display.flip()

#live = True
#crash = False
#while live:
#    try:
#        poll(crash)
#        for ev in pygame.event.get():
#            process_event(ev)
#            if ev.type == pygame.QUIT:
#                live = False
#        paint(time.time())
#        pygame.display.flip()
#        crash = False
#    except Exception as exc:
#        traceback.print_exc()
#        crash = True
