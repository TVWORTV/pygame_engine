import pygame
from scenes.sceneObject import SceneObject
from UI.image import StaticImage
from UI.text import TextBox
from UI.color import *


class Button(SceneObject):
    def __init__(self, pos, size, text, font, on_click,
                 image=None, hoverImage=None, nineSliced=False, border=0,
                 textColor=None, worldSpace=False,
                 interactable=True
                 ):
        super().__init__()

        self.setPosition(pos)
        self.size = tuple(size)

        self.text = text
        self.font = font

        self.on_click = []
        self.on_click.append(on_click)

        self.hovered = False
        self.worldSpace = worldSpace

        self.normalImage = image
        self.hoverImage = hoverImage

        self.interactable = interactable

        self.bgImage = None
        if self.normalImage is not None:
            self.bgImage = StaticImage(
                self.normalImage, (0, 0),
                size=self.size,
                nineSliced=nineSliced, border=border
            )
            self.addChild(self.bgImage)

        self.labelText = TextBox(
            self.text, self.font, (0, 0), self._labelSize(),
            color=textColor if textColor is not None else Color()
        )
        self.addChild(self.labelText)
        self._centerLabel()

    def _labelSize(self):
        textWidth, textHeight = self.font.size(self.text)
        return (textWidth, max(textHeight, self.font.get_linesize()))

    def _centerLabel(self):
        textWidth, textHeight = self.font.size(self.text)
        self.labelText.setSize(self._labelSize())
        self.labelText.setPosition((
            round((self.size[0] - textWidth) / 2),
            round((self.size[1] - textHeight) / 2)
        ))

    def getRect(self):
        worldPos = self.getWorldPosition()
        return pygame.Rect(worldPos.x, worldPos.y, self.size[0], self.size[1])

    def setSprite(self, sprite):
        self.bgImage.setImage(sprite)

    def setText(self, text):
        self.text = text
        self.labelText.setText(text)
        self._centerLabel()

    def addEvent(self, event, overrideAll=False):
        if overrideAll:
            self.on_click.clear()
        self.on_click.append(event)
        
    def setSize(self, size):
        self.size = tuple(size)
        if self.bgImage is not None:
            self.bgImage.setSize(self.size)
        self._centerLabel()
        self._notifySizeChanged()

    def getSize(self):
        return self.size

    def handle_event(self, event):
        rect = self.getRect()
        if event.type == pygame.MOUSEMOTION:
            wasHovered = self.hovered
            self.hovered = rect.collidepoint(event.pos)
            if self.hovered != wasHovered and self.bgImage is not None and self.interactable:
                nextImage = self.hoverImage if (self.hovered and self.hoverImage) else self.normalImage
                self.bgImage.setImage(nextImage)

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.interactable:
            if rect.collidepoint(event.pos):
                for callback in self.on_click:
                    callback()

    def draw(self, screen):
        if self.bgImage is None:
            rect = self.getRect()
            color = Color((180, 180, 180, 255)) if self.hovered and self.interactable else Color((120, 120, 120, 255))
            pygame.draw.rect(screen, color.rgba, rect, border_radius=6)

        super().draw(screen)