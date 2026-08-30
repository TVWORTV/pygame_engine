import pygame
from scenes.sceneObject import SceneObject
from UI.image import StaticImage
from UI.bar import UIBar


class Handle(SceneObject):
    def __init__(self, image, width, height, worldSpace=False):
        super().__init__()

        self.width = width
        self.height = height
        self.x = 0
        self.y = 0
        self.dragging = False
        self.hovered = False
        self.worldSpace = worldSpace

        self.image = None
        if image is not None:
            self.image = StaticImage(image, (self.x, self.y), size=(self.width, self.height))
            self.addChild(self.image)

    def getRect(self):
        return pygame.Rect(self.x, self.y, self.width, self.height)

    def setPosition(self, x, y):
        self.x = x
        self.y = y
        if self.image is not None:
            self.image.setPos((x, y))

    def draw(self, screen):
        if self.image is None:
            color = (200, 200, 200) if self.hovered else (150, 150, 150)
            pygame.draw.rect(screen, color, self.getRect(), border_radius=4)

        super().draw(screen)


class UISlider(SceneObject):
    def __init__(self, x, y, width, height, foregroundImage, border,
                 handleImage=None, handleWidth=16, handleHeight=None,
                 backgroundImage=None, bgNineSlicing=False,
                 currentValue=0.0, maxValue=1.0, onChange=None, worldSpace=False):
        super().__init__()

        self.bar = UIBar(
            x, y, width, height, foregroundImage, border,
            backgroundImage=backgroundImage, bgNineSlicing=bgNineSlicing,
            currentValue=currentValue, maxValue=maxValue
        )

        if handleHeight is None:
            handleHeight = height

        self.handle = Handle(handleImage, handleWidth, handleHeight)
        self.onChange = onChange

        self.addChild(self.bar)
        self.addChild(self.handle)

        self._updateHandlePosition()
        if self.onChange is not None:
            self.onChange(self.bar.currentValue)

#region Value

    def _updateHandlePosition(self):
        ratio = self.bar.getFillRatio()
        travel = self.bar.width
        centerX = self.bar.x + ratio * travel
        newX = round(centerX - self.handle.width / 2)
        newY = round(self.bar.y + self.bar.height / 2 - self.handle.height / 2)
        self.handle.setPosition(newX, newY)

    def _setValueFromMouseX(self, mouseX):
        ratio = (mouseX - self.bar.x) / self.bar.width
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
            elif pygame.Rect(self.bar.x, self.bar.y, self.bar.width, self.bar.height).collidepoint(event.pos):
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