import pygame
from ..scenes.sceneObject import SceneObject
from ..camera.camera import Camera
from .color import *
from enum import Enum, auto

class Alignment(Enum):
    LEFT = auto()
    RIGHT = auto()
    CENTER = auto()

class TextBox(SceneObject):
    def __init__(self, text : str, font : pygame.font, pos, size, color : Color = Color(), antialias : bool = True, worldSpace : bool = False,
                 drawOrder : int = 0, align : Alignment = Alignment.CENTER, lineSpacing : int =0):
        super().__init__()
        self.setPosition(pos)
        self.text = text
        self.font = font
        self.size = tuple(size)
        self.color = color
        self.antialias = antialias
        self.worldSpace = worldSpace
        self.align = align
        self.lineSpacing = lineSpacing

        self.drawOrder = drawOrder

        self._cachedSurface = None
        self._rebuildCache()

    def setDrawOrder(self, drawOrder):
        self.drawOrder = drawOrder
        if self.scene is not None:
            self.scene.invalidateDrawOrder()

    def _wrapParagraph(self, paragraph, maxWidth):
        lines = []
        current = ""
        for word in paragraph.split(" "):
            candidate = word if not current else current + " " + word
            if self.font.size(candidate)[0] <= maxWidth:
                current = candidate
                continue

            if current:
                lines.append(current)
                current = ""

            if self.font.size(word)[0] <= maxWidth:
                current = word
                continue

            for char in word:
                candidate = current + char
                if not current or self.font.size(candidate)[0] <= maxWidth:
                    current = candidate
                else:
                    lines.append(current)
                    current = char

        lines.append(current)
        return lines

    def _wrapText(self):
        lines = []
        for paragraph in self.text.split("\n"):
            lines.extend(self._wrapParagraph(paragraph, self.size[0]))
        return lines

    def _rebuildCache(self):
        width = max(1, self.size[0])
        height = max(1, self.size[1])
        surface = pygame.Surface((width, height), pygame.SRCALPHA)

        lineHeight = self.font.get_linesize() + self.lineSpacing
        y = 0
        for line in self._wrapText():
            if y + self.font.get_linesize() > height:
                break

            if line:
                rendered = self.font.render(line, self.antialias, self.color.rgba)
                if self.align == Alignment.CENTER:
                    x = (width - rendered.get_width()) // 2
                elif self.align == Alignment.RIGHT: 
                    x = width - rendered.get_width()
                else:
                    x = 0
                surface.blit(rendered, (x, y))

            y += lineHeight

        self._cachedSurface = surface

    def setText(self, text):
        self.text = text
        self._rebuildCache()

    def setColor(self, color):
        self.color = color
        self._rebuildCache()

    def setFont(self, font):
        self.font = font
        self._rebuildCache()

    def setAlign(self, align):
        self.align = align
        self._rebuildCache()

    def setLineSpacing(self, lineSpacing):
        self.lineSpacing = lineSpacing
        self._rebuildCache()

    def setSize(self, size):
        self.size = tuple(size)
        self._rebuildCache()
        self._notifySizeChanged()

    def getSize(self):
        return self.size

    def getVertices(self):
        worldPos = self.getWorldPosition()
        width, height = self.size
        return [
            (worldPos.x, worldPos.y),
            (worldPos.x + width, worldPos.y),
            (worldPos.x + width, worldPos.y + height),
            (worldPos.x, worldPos.y + height),
        ]

    def draw(self, screen):
        if self._cachedSurface is None:
            return

        if self.worldSpace:
            self._drawWorldSpace(screen)
        else:
            self._drawScreenSpace(screen)

        super().draw(screen)

    def _drawScreenSpace(self, screen):
        worldPos = self.getWorldPosition()
        screen.blit(self._cachedSurface, (worldPos.x, worldPos.y))

    def _drawWorldSpace(self, screen):
        camera = Camera.get_instance()
        if camera is None:
            return

        worldPos = self.getWorldPosition()
        worldRect = pygame.Rect(worldPos.x, worldPos.y, self.size[0], self.size[1])
        screenRect = camera.apply(worldRect)

        scaled = pygame.transform.scale(self._cachedSurface, (screenRect.width, screenRect.height))
        screen.blit(scaled, (screenRect.x, screenRect.y))