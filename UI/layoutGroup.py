import pygame
from enum import Enum
from scenes.sceneObject import SceneObject


class LayoutType(Enum):
    horizontal = 1
    vertical = 2


class LayoutGroup(SceneObject):
    def __init__(self, layoutType, spacing, padding=(0, 0)):
        super().__init__()
        self.layoutType = layoutType
        self.spacing = spacing
        self.padding = pygame.math.Vector2(padding)

        self._childrenDirty = False
        self._contentSize = (0, 0)

#region Children

    def addToGroup(self, item=None, items=None, insertAt=None):
        toAdd = list(items) if items is not None else []
        if item is not None:
            toAdd.insert(0, item)

        for child in toAdd:
            self.addChild(child)
            if insertAt is not None:
                self.children.remove(child)
                clampedIndex = max(0, min(insertAt, len(self.children)))
                self.children.insert(clampedIndex, child)
                self._drawOrderDirty = True

        self._childrenDirty = True

    def removeFromGroup(self, item):
        self.removeChild(item)
        self._childrenDirty = True

    def markDirty(self):
        self._childrenDirty = True

#endregion

#region Notifications

    def onChildSizeChanged(self, child):
        self._childrenDirty = True

#endregion

#region Layout

    def _arrangeHorizontal(self):
        cursorX = self.padding.x
        maxHeight = 0

        for child in self.children:
            width, height = child.getSize()
            child.setPosition((cursorX, self.padding.y))
            cursorX += width + self.spacing
            maxHeight = max(maxHeight, height)

        totalWidth = (cursorX - self.spacing if self.children else 0) + self.padding.x
        totalHeight = maxHeight + 2 * self.padding.y
        self._contentSize = (totalWidth, totalHeight)

    def _arrangeVertical(self):
        cursorY = self.padding.y
        maxWidth = 0

        for child in self.children:
            width, height = child.getSize()
            child.setPosition((self.padding.x, cursorY))
            cursorY += height + self.spacing
            maxWidth = max(maxWidth, width)

        totalHeight = (cursorY - self.spacing if self.children else 0) + self.padding.y
        totalWidth = maxWidth + 2 * self.padding.x
        self._contentSize = (totalWidth, totalHeight)

    def arrange(self):
        if self.layoutType == LayoutType.horizontal:
            self._arrangeHorizontal()
        else:
            self._arrangeVertical()
        self._childrenDirty = False

    def setSpacing(self, spacing):
        self.spacing = spacing
        self._childrenDirty = True

    def setPadding(self, padding):
        self.padding = pygame.math.Vector2(padding)
        self._childrenDirty = True

    def getSize(self):
        if self._childrenDirty:
            self.arrange()
        return self._contentSize

#endregion

#region loop

    def draw(self, screen):
        if self._childrenDirty:
            self.arrange()
        super().draw(screen)

#endregion