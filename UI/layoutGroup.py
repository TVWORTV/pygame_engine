
from scenes.sceneObject import * 
from enum import Enum

class LayoutType(Enum):
    horizontal = 1
    vertical = 2

class LayoutGroup(SceneObject):

    def __init__(self, type, spacing):
        self.type = type 
        self.spacing = spacing
        self._childrenDirty = False

    def addChild(self, obj):
        super().addChild(obj)
        self._childrenDirty = True 

    def update(self, *args, **kwargs):
        return super().update(*args, **kwargs)