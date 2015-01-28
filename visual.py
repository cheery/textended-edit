import defaultlayout
from mapping import Mapping
from compositor import Compositor

class Visual(object):
    def __init__(self, images, document, x=0, y=0, width=200, height=200):
        self.images = images
        self.compositor = Compositor(images)
        self.document = document
        self.layers = []
        self.children = []
        self.ver = 0
        self.mappings = {}
        self.mapping = Mapping(self.mappings, self.document.body, None)
        self.build_layout = defaultlayout.build
        self.rootbox = None
        self.bridges = []
        self.position_hook = lambda editor: None
        self.update_hook = lambda editor: None
        self.close_hook = lambda editor: None
        self.parent = None
        self.must_update = False

        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.scroll_x = 0
        self.scroll_y = 0
        self.color = None
        self.background = None

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
        subeditor = Editor(self.images, document)
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

class VisualLayer(object):
    def __init__(self, document):
        self.document = document
        self.ver = 0
        self.build_rootbox = None

class Bridge(object):
    def __init__(self, layer, reference, body):
        self.layer = layer
        self.reference = reference
        self.body = body
        self.mappings = {}
        self.mapping = Mapping(self.mappings, body, None)
        self.build_layout = defaultlayout.build
        self.rootbox = None

