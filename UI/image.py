import pygame
from .nineSlicing import draw_nine_slice
from .draw import blit_rotated
from ..scenes.sceneObject import SceneObject
from ..camera.camera import Camera
from .color import *


class StaticImage(SceneObject):
    def __init__(self, 
                 image, 
                 pos, 
                 size=None, 
                 nineSliced=False, 
                 border=0, 
                 worldSpace=False,
                 color=None, 
                 drawOrder = 0 
                ):
        super().__init__()
        self.setPosition(pos)
        self.image = image
        self.size = size
        self.nineSliced = nineSliced
        self.border = border
        self.worldSpace = worldSpace
        self.color = color if color is not None else Color()
        self.drawOrder = drawOrder

        self._tintedImage = None
        self._cachedScaled = None
        self._rebuildCache()

    def _rebuildCache(self):
        self._tintedImage = self._applyTint(self.image)

        if self._tintedImage is not None and not self.nineSliced and self.size is not None:
            self._cachedScaled = pygame.transform.scale(self._tintedImage, self.size)
        else:
            self._cachedScaled = None

#region Visuals 

    def _applyTint(self, surface):
        if surface is None:
            return None
        if self.color.rgba == (255, 255, 255, 255):
            return surface

        tinted = surface.copy()
        tinted.fill(self.color.rgba, special_flags=pygame.BLEND_RGBA_MULT)
        return tinted
            
    def setDrawOrder(self, drawOrder):
        self.drawOrder = drawOrder
        if self.scene is not None:
            self.scene.invalidateDrawOrder()

    def setImage(self, image):
        self.image = image
        self._rebuildCache()

    def setColor(self, color):
        self.color = color
        self._rebuildCache()

#endregion 

#region Size 

    def setSize(self, size):
        self.size = size
        self._rebuildCache()
        self._notifySizeChanged()

    def getSize(self):
        if self.size is not None:
            return self.size
        if self._tintedImage is not None:
            return self._tintedImage.get_size()
        return (0, 0)

#endregion

#region Draw methods 

    def draw(self, screen):
        if self.image is None:
            return

        if self.worldSpace:
            self._drawWorldSpace(screen)
        else:
            self._drawScreenSpace(screen)

        super().draw(screen)

    def _drawScreenSpace(self, screen):
        worldPos = self.getWorldPosition()

        if self.nineSliced:
            w, h = self.size if self.size is not None else self._tintedImage.get_size()
            draw_nine_slice(screen, self._tintedImage, (worldPos.x, worldPos.y, w, h), self.border)
        else:
            surface = self._cachedScaled if self._cachedScaled is not None else self._tintedImage
            blit_rotated(screen, surface, worldPos, self.getWorldRotation())

    def _drawWorldSpace(self, screen):
        camera = Camera.get_instance()
        if camera is None:
            return

        worldPos = self.getWorldPosition()
        w, h = self.size if self.size is not None else self._tintedImage.get_size()
        worldRect = pygame.Rect(worldPos.x, worldPos.y, w, h)
        screenRect = camera.apply(worldRect)

        if self.nineSliced:
            scaledBorder = round(self.border * camera.zoom)
            draw_nine_slice(
                screen, self._tintedImage,
                (screenRect.x, screenRect.y, screenRect.width, screenRect.height),
                scaledBorder
            )
        else:
            scaled = pygame.transform.scale(self._tintedImage, (screenRect.width, screenRect.height))
            blit_rotated(screen, scaled, pygame.math.Vector2(screenRect.topleft), self.getWorldRotation())
#endregion

