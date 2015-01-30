import boxmodel
import defaultlayout
import importlib
from mapping import Mapping
from compositor import Compositor

class Visual(object):
    def __init__(self, env, images, document, x=0, y=0, width=200, height=200):
        self.env = env
        self.images = images
        self.compositor = Compositor(images)
        self.primary = VisualLayer(document)

        self.must_update = False
        self.mappings = {}
        self.mapping = Mapping(self.mappings, self.document.body, None)
        self.rootbox = None

        self.layers = []
        self.bridges = []

        self.position_hook = lambda editor: None
        self.update_hook = lambda editor: None
        self.close_hook = lambda editor: None

        self.parent = None
        self.children = []

        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.scroll_x = 0
        self.scroll_y = 0
        self.color = None
        self.background = None
        self.active = False

    @property
    def document(self):
        return self.primary.document

    def close(self):
        self.compositor.close()
        self.close_hook(self)
        if self.parent is not None:
            self.parent.children.remove(self)

    def get_rect(self, node):
        if node not in self.mappings:
            return
        obj = self.mappings[node].obj
        if isinstance(obj, list):
            return rect_enclosure([box.rect for box in obj if hasattr(box, 'rect')])
        elif obj is not None:
            return obj.rect

    def create_sub_editor(self, document):
        subeditor = Visual(self.env, self.images, document)
        subeditor.width = self.width
        subeditor.height = self.height
        self.children.append(subeditor)
        subeditor.parent = self
        return subeditor

    def create_layer(self, document):
        print 'layer created'
        layer = VisualLayer(document)
        self.layers.append(layer)
        self.ver = 0
        return layer

    def pick(self, x, y):
        for bridge in self.bridges:
            x0, y0, x1, y1 = bridge.rootbox.quad
            if x0 <= x < x1 and y0 <= y < y1:
                result = boxmodel.pick_nearest(bridge.rootbox, x, y)
                if result is not None:
                    return result
        return boxmodel.pick_nearest(self.rootbox, x, y)

    def update(self):
        must_update = self.must_update
        primary = self.primary
        if primary.document.body.islist():
            for directive in primary.document.body:
                if directive.isstring() and directive.label == 'language':
                    name = directive[:]
                    try:
                        primary.driver = importlib.import_module("extensions." + name)
                        if not hasattr(primary.driver, 'link_bridges'):
                            primary.driver.link_bridges = defaultlayout.link_bridges
                        must_update = True
                        break
                    except ImportError as error:
                        primary.driver = defaultlayout
        if primary.document.ver != primary.ver or must_update:
            self.mappings.clear()
            self.compositor.clear()
            self.rootbox = boxmodel.vpack(self.mapping.update(primary.driver.layout, self.env))
            self.inner_width = self.rootbox.width + 20
            self.inner_height = self.rootbox.vsize + 20
            self.position_hook(self)
            self.compositor.clear()
            self.compositor.decor((0, 0, self.width, self.height), self.background, self.color)
            self.compositor.compose(self.rootbox, 10, 10 + self.rootbox.height)
            primary.ver = primary.document.ver
            self.bridges = []
            for layer in self.layers:
                self.bridges.extend(layer.driver.link_bridges(primary, layer))
            sectors = []
            for bridge in self.bridges:
                bridge.mapping.mappings = self.mappings
                referenced = self.document.nodes.get(bridge.reference)
                if referenced not in self.mappings:
                    continue
                bridge.rootbox = boxmodel.vpack(bridge.mapping.update(bridge.layer.driver.layout, self.env))
                x0, y0, x1, y1 = self.mappings[referenced].tokens[0].quad
                self.compositor.decor((x0,y0,x1,y1), boxmodel.Patch9("assets/border-1px.png"), (1.0, 0.0, 0.0, 0.25))
                bridge.y = y0
                sectors.append(bridge)
            sectors.sort(key=lambda b: b.y)
            max_y = 0
            for bridge in sectors:
                y = max(bridge.y, max_y)
                self.compositor.compose(bridge.rootbox, self.rootbox.width + 50, y)
                max_y = y + bridge.rootbox.vsize
            self.must_update = False

        for subvisual in self.children:
            subvisual.update()

    def render(self, width, height):
        self.compositor.render(self.scroll_x - self.x, self.scroll_y - self.y, width, height)
        for subeditor in self.children:
            subeditor.render(width, height)

    def __str__(self):
        if self.document.name is None:
            return '[No Name]'
        else:
            return self.document.name

class VisualLayer(object):
    def __init__(self, document, driver=defaultlayout):
        self.document = document
        self.driver = driver
        self.ver = 0

class Bridge(object):
    def __init__(self, layer, reference, body):
        self.layer = layer
        self.reference = reference
        self.body = body
        self.mapping = Mapping({}, body, None)
        self.rootbox = None
