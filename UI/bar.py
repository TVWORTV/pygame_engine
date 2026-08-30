from scenes.sceneObject import SceneObject
from UI.image import StaticImage
import pygame


class UIBar(SceneObject):
    def __init__(self, x, y, width, height, foregroundImage, border,
                 backgroundImage=None, bgNineSlicing=False,
                 currentValue=0.0, maxValue=1.0, worldSpace=False):
        super().__init__()

        self.setPosition((x, y))
        self.width = width
        self.height = height
        self.border = border
        self.worldSpace = worldSpace

        self.currentValue = currentValue
        self.maxValue = maxValue

        self.bgImage = None
        if backgroundImage is not None:
            self.bgImage = StaticImage(
                backgroundImage, (0, 0), size=(self.width, self.height),
                nineSliced=bgNineSlicing, border=self.border
            )
            self.addChild(self.bgImage)

        self.fillImage = StaticImage(
            foregroundImage, (0, 0), size=(self.width, self.height),
            nineSliced=True, border=self.border
        )
        self.addChild(self.fillImage)

#region Background / sizing

    def getRect(self):
        worldPos = self.getWorldPosition()
        return pygame.Rect(worldPos.x, worldPos.y, self.width, self.height)

    def setSize(self, width, height):
        self.width = width
        self.height = height
        if self.bgImage is not None:
            self.bgImage.setSize((width, height))
        self.fillImage.setSize((width, height))

#endregion

#region Value change

    def addValue(self, value):
        self.setValue(self.currentValue + value)

    def setValue(self, value):
        self.currentValue = max(0.0, min(value, self.maxValue))

    def getFillRatio(self):
        if self.maxValue <= 0:
            return 0.0
        return self.currentValue / self.maxValue

#endregion

    def draw(self, screen):
        if self.bgImage is not None:
            self.bgImage.draw(screen)

        ratio = self.getFillRatio()
        fillWidth = round(self.width * ratio)
        if fillWidth <= 0:
            return

        rect = self.getRect()
        # Clip is axis-aligned - see notes on rotation limitations.
        clipRect = pygame.Rect(rect.x, rect.y, fillWidth, rect.height)
        prevClip = screen.get_clip()
        screen.set_clip(clipRect)

        self.fillImage.draw(screen)

        screen.set_clip(prevClip)

        for child in self.children:
            if child is not self.bgImage and child is not self.fillImage:
                child.draw(screen)