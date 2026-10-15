import pygame
from scenes.sceneObject import SceneObject
from UI.image import StaticImage
from UI.bar import UIBar


class Handle(SceneObject):
    def __init__(self, image, size, worldSpace=False):
        super().__init__()

        self.size = tuple(size)
        self.dragging = False
        self.hovered = False
        self.worldSpace = worldSpace

        self.image = None
        if image is not None:
            self.image = StaticImage(image, (0, 0), size=self.size)
            self.addChild(self.image)

    def getSize(self):
        return self.size

    def getRect(self):
        worldPos = self.getWorldPosition()
        return pygame.Rect(worldPos.x, worldPos.y, self.size[0], self.size[1])

    def draw(self, screen):
        if self.image is None:
            color = (200, 200, 200) if self.hovered else (150, 150, 150)
            pygame.draw.rect(screen, color, self.getRect(), border_radius=4)

        super().draw(screen)


class UISlider(SceneObject):
    def __init__(self, pos, size, foregroundImage, border,
                 handleImage=None, handleSize=None,
                 backgroundImage=None, bgNineSlicing=False,
                 currentValue=0.0, maxValue=1.0, onChange=None, worldSpace=False):
        super().__init__()
        self.setPosition(pos)

        self.bar = UIBar(
            (0, 0), size, foregroundImage, border,
            backgroundImage=backgroundImage, bgNineSlicing=bgNineSlicing,
            currentValue=currentValue, maxValue=maxValue
        )

        if handleSize is None:
            handleSize = (16, size[1])

        self.handle = Handle(handleImage, handleSize)
        self.onChange = onChange

        self.addChild(self.bar)
        self.addChild(self.handle)

        self._updateHandlePosition()
        if self.onChange is not None:
            self.onChange(self.bar.currentValue)

    def getSize(self):
        return self.bar.getSize()

#region Value

    def _updateHandlePosition(self):
        ratio = self.bar.getFillRatio()
        travel = self.bar.getSize()[0]
        centerX = self.bar.position.x + ratio * travel
        barWidth, barHeight = self.bar.getSize()
        handleWidth, handleHeight = self.handle.getSize()
        newX = round(centerX - handleWidth / 2)
        newY = round(self.bar.position.y + barHeight / 2 - handleHeight / 2)
        self.handle.setPosition((newX, newY))

    def _setValueFromMouseX(self, mouseX):
        barRect = self.bar.getRect()
        ratio = (mouseX - barRect.x) / barRect.width
        ratio = max(0.0, min(1.0, ratio))
        self.bar.setValue(ratio * self.bar.maxValue)
        self._updateHandlePosition()
        if self.onChange is not None:
            self.onChange(self.bar.currentValue)

#endregion

#region input

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.handle.hovered = self.handle.getRect().collidepoint(event.pos)
            if self.handle.dragging:
                self._setValueFromMouseX(event.pos[0])

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.handle.getRect().collidepoint(event.pos):
                self.handle.dragging = True
            elif self.bar.getRect().collidepoint(event.pos):
                self._setValueFromMouseX(event.pos[0])
                self.handle.dragging = True

        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.handle.dragging = False

#endregion

#region output

    def setValue(self, value):
        self.bar.setValue(value)
        self._updateHandlePosition()

    def getValue(self):
        return self.bar.currentValue

#endregion