import pygame
from scenes.sceneObject import SceneObject
from UI.image import StaticImage
from UI.text import StaticText
from UI.color import *


class Button(SceneObject):
    def __init__(self, rect, text, font, on_click,
                 image=None, hoverImage=None, nineSliced=False, border=0,
                 textColor=None, worldSpace=False,
                 interactable=True
                 ):
        super().__init__()

        self.rect = pygame.Rect(rect)
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
                self.normalImage, (self.rect.x, self.rect.y),
                size=(self.rect.width, self.rect.height),
                nineSliced=nineSliced, border=border
            )
            self.addChild(self.bgImage)

        textWidth, textHeight = self.font.size(self.text)
        labelRect = pygame.Rect(0, 0, textWidth, textHeight)
        labelRect.center = self.rect.center
        self.labelText = StaticText(
            self.text, self.font, labelRect.topleft,
            color=textColor if textColor is not None else Color()
        )
        self.addChild(self.labelText)

    def setSprite(self, sprite):
        self.bgImage.setImage(sprite)

    def addEvent(self, event, overrideAll=False):
        if overrideAll:
            self.on_click.clear()
        self.on_click.append(event)

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            wasHovered = self.hovered
            self.hovered = self.rect.collidepoint(event.pos)
            if self.hovered != wasHovered and self.bgImage is not None and self.interactable:
                nextImage = self.hoverImage if (self.hovered and self.hoverImage) else self.normalImage
                self.bgImage.setImage(nextImage)

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.interactable:
            if self.rect.collidepoint(event.pos):
                for callback in self.on_click:
                    callback()

    def draw(self, screen):
        if self.bgImage is None:
            color = Color((180, 180, 180, 255)) if self.hovered and self.interactable else Color((120, 120, 120, 255))
            pygame.draw.rect(screen, color.rgba, self.rect, border_radius=6)

        super().draw(screen)