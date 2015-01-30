from compositor import Compositor
from OpenGL.GL import *
import boxmodel

class Panels(object):
    def __init__(self, env, images, x, y, width, height):
        self.panes = []
        self.x = 0
        self.y = 0
        self.width = width
        self.height = height
        self.images = images
        self.compositor = Compositor(images)
        self.env = env

    def close(self):
        for pane in self.panes:
            pane.close()

    def update(self):
        self.compositor.clear()

        width = sum(pane.width for pane in self.panes)
        shift = float(self.width - width) / len(self.panes)
        x = self.x
        for pane in self.panes:
            pane.x = x
            pane.y = self.y
            pane.width += int(shift)
            pane.height = self.height - 16
            pane.update()
            x += pane.width


            loc_x0 = pane.x - self.x
            loc_y0 = pane.y - self.y
            loc_x1 = loc_x0 + pane.width - 5
            loc_y1 = loc_y0 + pane.height

            if pane.active:
                text_color = (1, 1, 1, 1)
            else:
                text_color = (0.75, 0.75, 0.75, 1)
            frame_color = (0.2, 0.2, 0.2, 1)
            self.compositor.decor((loc_x0, loc_y1, loc_x1, loc_y1+16), None, frame_color)
            self.compositor.decor((loc_x1, loc_y0, loc_x1+5, loc_y1+16), None, frame_color)
            text = boxmodel.hpack(self.env['font'](str(pane), 10, color=text_color))
            self.compositor.compose(text, loc_x0+2, loc_y1 + 16 - text.depth)

    def render(self, width, height):
        glEnable(GL_SCISSOR_TEST)
        for pane in self.panes:
            glScissor(pane.x, height-pane.y-pane.height, pane.width, pane.height)
            pane.render(width, height)
        glDisable(GL_SCISSOR_TEST)
        self.compositor.render(-self.x, -self.y, width, height)
