import pygame


class SceneObject:
    def __init__(self):
        self.children = []
        self.parent = None
        self.scene = None
        self._sortedChildren = []
        self._drawOrderDirty = False

        self.position = pygame.math.Vector2(0, 0)   
        self.rotation = 0.0                           

        self._worldPosition = pygame.math.Vector2(0, 0)
        self._worldRotation = 0.0
        self._worldDirty = True

#region notification 

    def onChildTransformChanged(self, child):
        pass

    def onChildSizeChanged(self, child):
        pass

    def _notifySizeChanged(self):
        if self.parent is not None:
            self.parent.onChildSizeChanged(self)

    def _notifyPositionChanged(self):
        if self.parent is not None:
            self.parent.onChildTransformChanged(self) 

#endregion 

#region size 

    def getSize(self):
        return (0, 0)

#endregion 

#region Positioning

    def setPosition(self, pos):
        self.position = pygame.math.Vector2(pos)
        self._invalidateWorldTransform()
        if self.parent is not None:
            self.parent.onChildTransformChanged(self)

    def setRotation(self, rotation):
        self.rotation = rotation
        self._invalidateWorldTransform()
        if self.parent is not None:
            self.parent.onChildTransformChanged(self)

    def translate(self, delta):
        self.position += pygame.math.Vector2(delta)
        self._invalidateWorldTransform()

    def rotate(self, deltaDegrees):
        self.rotation += deltaDegrees
        self._invalidateWorldTransform()

    def getWorldPosition(self):
        self._updateWorldTransform()
        return self._worldPosition

    def getWorldRotation(self):
        self._updateWorldTransform()
        return self._worldRotation

    def _updateWorldTransform(self):
        if not self._worldDirty:
            return

        if self.parent is None:
            self._worldPosition = pygame.math.Vector2(self.position)
            self._worldRotation = self.rotation
        else:
            parentPos = self.parent.getWorldPosition()
            parentRot = self.parent.getWorldRotation()
            self._worldPosition = parentPos + self.position.rotate(parentRot)
            self._worldRotation = parentRot + self.rotation

        self._worldDirty = False

    def _invalidateWorldTransform(self):
        self._worldDirty = True
        for child in self.children:
            child._invalidateWorldTransform()

#endregion

#region hierarchy

    def addChild(self, obj):
        if not isinstance(obj, SceneObject):
            raise TypeError(f"addChild expects a SceneObject, got {type(obj).__name__}")

        if obj.parent is not None:
            obj.parent.removeChild(obj)

        obj.parent = self
        self.children.append(obj)
        self._drawOrderDirty = True
        obj._invalidateWorldTransform()

        if self.scene is not None:
            obj.onAddedToScene(self.scene)

    def removeChild(self, obj):
        if obj not in self.children:
            return

        self.children.remove(obj)
        obj.parent = None
        self._drawOrderDirty = True
        obj._invalidateWorldTransform()

        if self.scene is not None:
            obj.onRemovedFromScene(self.scene)

#endregion

#region scene lifecycle

    def onAddedToScene(self, scene):
        self.scene = scene
        for child in self.children:
            child.onAddedToScene(scene)

    def onRemovedFromScene(self, scene):
        self.scene = None
        for child in self.children:
            child.onRemovedFromScene(scene)

#endregion

#region draw order

    def invalidateDrawOrder(self):
        self._drawOrderDirty = True
        if self.parent is not None:
            self.parent.invalidateDrawOrder()
        elif self.scene is not None:
            self.scene.invalidateDrawOrder()

#endregion

#region loop

    def update(self, *args, **kwargs):
        for child in self.children:
            child.update(*args, **kwargs)

    def handle_event(self, event):
        for child in self.children:
            child.handle_event(event)

    def draw(self, screen):
        if self._drawOrderDirty:
            self._sortedChildren = sorted(self.children, key=lambda o: getattr(o, "drawOrder", 0))
            self._drawOrderDirty = False

        for child in self._sortedChildren:
            child.draw(screen)

#endregion