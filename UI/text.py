

import pygame
from scenes.sceneObject import SceneObject
from camera.camera import Camera
from UI.color import * 

class StaticText(SceneObject):
    def __init__(self, text, font, pos, color=Color(), antialias=True, worldSpace=False, drawOrder = 0):
        super().__init__()
        self.text = text
        self.font = font
        self.pos = pos
        self.color = color
        self.antialias = antialias
        self.worldSpace = worldSpace

        self.drawOrder = drawOrder

        self._cachedSurface = None
        self._rebuildCache()

    def setDrawOrder(self, drawOrder):
        self.drawOrder = drawOrder
        if self.scene is not None:
            self.scene.invalidateDrawOrder()

    def _rebuildCache(self):
        self._cachedSurface = self.font.render(self.text, self.antialias, self.color.rgba)

    def setText(self, text):
        self.text = text
        self._rebuildCache()

    def setColor(self, color):
        self.color = color
        self._rebuildCache()

    def setFont(self, font):
        self.font = font
        self._rebuildCache()

    def setPos(self, pos):
        self.pos = pos

    def getSize(self):
        return self._cachedSurface.get_size()

    def draw(self, screen):
        if self._cachedSurface is None:
            return

        if self.worldSpace:
            self._drawWorldSpace(screen)
        else:
            self._drawScreenSpace(screen)

        super().draw(screen)

    def _drawScreenSpace(self, screen):
        screen.blit(self._cachedSurface, self.pos)

    def _drawWorldSpace(self, screen):
        camera = Camera.get_instance()
        if camera is None:
            return

        w, h = self._cachedSurface.get_size()
        worldRect = pygame.Rect(self.pos[0], self.pos[1], w, h)
        screenRect = camera.apply(worldRect)

        scaled = pygame.transform.scale(self._cachedSurface, (screenRect.width, screenRect.height))
        screen.blit(scaled, (screenRect.x, screenRect.y))