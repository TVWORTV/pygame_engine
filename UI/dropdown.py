import pygame
from scenes.sceneObject import SceneObject
from UI.button import Button
from UI.layoutGroup import LayoutGroup, LayoutType


class DropDownMenu(SceneObject):
    def __init__(self, optionList, font, pos, buttonSize,
                 onlyOne=True, spacing=2, headerLabel="Select...",
                 onSelectionChanged=None,
                 normalImage=None, hoverImage=None, selectedImage=None,
                 textColor=None):
        super().__init__()
        self.setPosition(pos)

        self.optionList = optionList
        self.font = font
        self.buttonSize = buttonSize
        self.onlyOne = onlyOne
        self.headerLabel = headerLabel
        self.onSelectionChanged = onSelectionChanged

        self.normalImage = normalImage
        self.hoverImage = hoverImage
        self.selectedImage = selectedImage
        self.textColor = textColor

        self.selected = set()
        self.isOpen = False

        self.headerButton = Button(
            pygame.Rect(0, 0, buttonSize[0], buttonSize[1]),
            self.headerLabel, font, self._toggleOpen,
            image=normalImage, hoverImage=hoverImage, textColor=textColor
        )
        self.addChild(self.headerButton)

        self.optionsGroup = LayoutGroup(LayoutType.vertical, spacing)
        self.optionsGroup.setPosition((0, buttonSize[1]))

        self.optionButtons = []
        self._buildOptions()

#region Options

    def _buildOptions(self):
        for btn in self.optionButtons:
            self.optionsGroup.removeFromGroup(btn)
        self.optionButtons.clear()

        for index, optionText in enumerate(self.optionList):
            btn = Button(
                pygame.Rect(0, 0, self.buttonSize[0], self.buttonSize[1]),
                optionText, self.font,
                lambda i=index: self.choose_option(i),
                image=self.normalImage, hoverImage=self.hoverImage,
                textColor=self.textColor
            )
            self.optionButtons.append(btn)

        self.optionsGroup.addToGroup(items=self.optionButtons)
        self._refreshOptionVisuals()

    def choose_option(self, index):
        if not (0 <= index < len(self.optionList)):
            return

        if self.onlyOne:
            self.selected = {index}
            self._setOpen(False)
        else:
            if index in self.selected:
                self.selected.discard(index)
            else:
                self.selected.add(index)

        self._refreshOptionVisuals()
        self._updateHeaderLabel()

        if self.onSelectionChanged is not None:
            self.onSelectionChanged(self.getSelectedOptions())

    def getSelectedOptions(self):
        return [self.optionList[i] for i in sorted(self.selected)]

    def getSelectedIndices(self):
        return sorted(self.selected)

    def _refreshOptionVisuals(self):
        for index, btn in enumerate(self.optionButtons):
            isSelected = index in self.selected
            if self.selectedImage is not None:
                btn.setSprite(self.selectedImage if isSelected else self.normalImage)
            else:
                marker = ("(o) " if isSelected else "( ) ") if self.onlyOne \
                    else ("[x] " if isSelected else "[ ] ")
                btn.setText(marker + self.optionList[index])

    def _updateHeaderLabel(self):
        if not self.selected:
            self.headerButton.setText(self.headerLabel)
        elif self.onlyOne:
            index = next(iter(self.selected))
            self.headerButton.setText(self.optionList[index])
        else:
            self.headerButton.setText(f"{len(self.selected)} selected")

#endregion

#region Open / close

    def _toggleOpen(self):
        self._setOpen(not self.isOpen)

    def _setOpen(self, isOpen):
        if isOpen == self.isOpen:
            return
        self.isOpen = isOpen
        if isOpen:
            self.addChild(self.optionsGroup)
        else:
            self.removeChild(self.optionsGroup)

#endregion

    def getSize(self):
        return self.headerButton.getSize()