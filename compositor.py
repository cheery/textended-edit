import renderers
import defaultlayout
import boxmodel

class Compositor(object):
    def __init__(self, images, debug=False):
        self.debug = debug
        self.images = images
        self.imglayer = renderers.ImageLayer(images)
        self.fontlayers = {}

    def get_fontlayer(self, font):
        if font not in self.fontlayers:
            self.fontlayers[font] = renderers.FontLayer(self.images, font)
        return self.fontlayers[font]

    def close(self):
        for fontlayer in self.fontlayers.values():
            fontlayer.close()
        self.imglayer.close()

    def clear(self):
        for fontlayer in self.fontlayers.values():
            fontlayer.clear()
        self.imglayer.clear()

    def decor(self, quad, source, color):
        if source is None and color is None:
            return
        if color is None:
            color = 1, 1, 1, 1
        if isinstance(source, boxmodel.Patch9):
            self.imglayer.patch9(quad, self.imglayer.patch9_texcoords(source.source), color)
        else:
            self.imglayer.quad(quad, self.imglayer.texcoords(source), color)

    def compose(self, subj, x, y):
        subj.quad = x, y-subj.height, x+subj.width, y+subj.depth
        if self.debug:
            self.imglayer.patch9(subj.quad, self.imglayer.patch9_texcoords("assets/border-1px.png"), (1.0, 1.0, 1.0, 0.1))
        if isinstance(subj, boxmodel.HBox):
            for node in subj.contents:
                if isinstance(node, boxmodel.Glue):
                    node.quad = x+node.offset, subj.quad[1], x+node.offset+node.computed, subj.quad[3]
                    if self.debug:
                        self.imglayer.quad(node.quad, self.imglayer.texcoords(None), (0.0, 1.0, 0.0, 0.2))
                else:
                    self.compose(node, x+node.offset, y+node.shift)
        elif isinstance(subj, boxmodel.VBox):
            y = y - subj.height
            for node in subj.contents:
                if isinstance(node, boxmodel.Glue):
                    node.quad = subj.quad[0], y+node.offset, subj.quad[2], y+node.offset+node.computed
                    if self.debug:
                        self.imglayer.quad(node.quad, self.imglayer.texcoords(None), (1.0, 1.0, 0.0, 0.2))
                else:
                    self.compose(node, x + node.shift, y + node.offset)
        elif isinstance(subj, boxmodel.Padding):
            left, top, right, bottom = subj.padding
            if subj.background is not None or subj.color is not None:
                self.decor(subj.quad, subj.background, subj.color)
            for node in subj.contents:
                if isinstance(node, (boxmodel.HBox, boxmodel.VBox)):
                    self.compose(node, x + node.offset, y + node.shift)
                else:
                    assert False
        elif isinstance(subj, boxmodel.ImageBox):
            self.decor(subj.quad, subj.source, subj.color)
        elif isinstance(subj, boxmodel.LetterBox):
            x0, y0, x1, y1 = subj.quad
            p0, p1, p2, p3 = subj.padding
            fontlayer = self.get_fontlayer(subj.font)
            fontlayer.quad((x0-p0, y0-p1, x1+p2, y1+p3), subj.texcoords, subj.color)

    def render(self, x, y, width, height):
        self.imglayer.render(x, y, width, height)
        for fontlayer in self.fontlayers.values():
            fontlayer.render(x, y, width, height)
