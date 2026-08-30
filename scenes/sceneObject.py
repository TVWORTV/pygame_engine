class SceneObject:
    def __init__(self):
        self.children = []
        self.parent = None
        self.scene = None
        self._sortedChildren = []
        self._drawOrderDirty = False

#region hierarchy

    def addChild(self, obj):
        if not isinstance(obj, SceneObject):
            raise TypeError(f"addChild expects a SceneObject, got {type(obj).__name__}")

        if obj.parent is not None:
            obj.parent.removeChild(obj)

        obj.parent = self
        self.children.append(obj)
        self._drawOrderDirty = True

        if self.scene is not None:
            obj.onAddedToScene(self.scene)

    def removeChild(self, obj):
        if obj not in self.children:
            return

        self.children.remove(obj)
        obj.parent = None
        self._drawOrderDirty = True

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