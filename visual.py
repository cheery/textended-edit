import boxmodel
import defaultlayout
from mapping import Mapping
from compositor import Compositor

class Visual(object):
    def __init__(self, images, document, x=0, y=0, width=200, height=200):
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
        subeditor = Visual(self.images, document)
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
        cursor = x, y
        return boxmodel.pick_nearest(self.rootbox, x, y)

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
        self.mappings = {}
        self.mapping = Mapping(self.mappings, body, None)
        self.rootbox = None
