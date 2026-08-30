class Scene:
    def __init__(self, manager):
        self.manager = manager
        self._objects = []
        self._sortedObjects = []
        self._drawOrderDirty = False

#region loop


    def handle_events(self, events):
        for event in events:
            for obj in self._objects:
                obj.handle_event(event)

    def update(self, *args, **kwargs):
        for obj in self._objects:
            obj.update(*args, **kwargs)

    def draw(self, screen):
        if self._drawOrderDirty:
            self._sortedObjects = sorted(self._objects, key=lambda o: getattr(o, "drawOrder", 0))
            self._drawOrderDirty = False

        for obj in self._sortedObjects:
            obj.draw(screen)

    def addobj(self, obj):
        if obj not in self._objects:
            self._objects.append(obj)
            self._drawOrderDirty = True
            obj.onAddedToScene(self)

    def removeobj(self, obj):
        if obj in self._objects:
            self._objects.remove(obj)
            self._drawOrderDirty = True
            obj.onRemovedFromScene(self)

    def invalidateDrawOrder(self):
        self._drawOrderDirty = True

    def __contains__(self, item):
        return item in self._objects

#endregion

#region initialization

    def start(self): pass
    def end(self): pass

#endregion


class SceneManager:
    def __init__(self, scene_classes, start_scene):
        self.scene_classes = scene_classes
        self.current_scene = None
        self.change_scene(start_scene)

    def change_scene(self, scene_name):
        if scene_name not in self.scene_classes:
            return

        if self.current_scene is not None:
            self.current_scene.end()

        scene_class = self.scene_classes[scene_name]
        self.current_scene = scene_class(self)
        self.current_scene.start()

    def handle_events(self, events):
        if self.current_scene is not None:
            self.current_scene.handle_events(events)

    def update(self, dt):
        if self.current_scene is not None:
            self.current_scene.update(dt)

    def draw(self, screen):
        if self.current_scene is not None:
            self.current_scene.draw(screen)