from dataclasses import dataclass
from typing import Callable, Optional

class Animation:
    def __init__(self, frames, image, fps=8, onComplete=None, frameCallbacks=None, loop=True, autoplay=True):
        self.frames = frames
        self.image = image
        self.fps = fps
        self.loop = loop

        self.frameIndex = 0
        self.timer = 0.0
        self.playing = autoplay
        self.finished = False

        self.onComplete = onComplete
        self.frameCallbacks = frameCallbacks or []

        if self.frames:
            self.image.setImage(self.frames[0])

    @property
    def frameDuration(self):
        return 1.0 / self.fps if self.fps > 0 else 0

    def update(self, dt):
        if not self.playing or not self.frames or self.finished:
            return

        self.timer += dt

        while self.timer >= self.frameDuration:
            self.timer -= self.frameDuration
            self._advanceFrame()
            if self.finished:
                break

        self.image.setImage(self.frames[self.frameIndex])

    def _advanceFrame(self):
        self.frameIndex += 1

        if self.frameIndex >= len(self.frames):
            if self.loop:
                self.frameIndex = 0
            else:
                self.frameIndex = len(self.frames) - 1
                self.finished = True
                self.playing = False
                self._invokeFrameCallbacks(self.frameIndex)
                if self.onComplete:
                    self.onComplete()
                return

        self._invokeFrameCallbacks(self.frameIndex)

    def _invokeFrameCallbacks(self, frameIndex):
        for frameCallback in self.frameCallbacks:
            if frameCallback.frame == frameIndex and frameCallback.callback:
                frameCallback.callback()

    def play(self):
        self.playing = True
        self.finished = False
        self.frameIndex = 0
        self.timer = 0.0

    def pause(self):
        self.playing = False

    def stop(self):
        self.playing = False
        self.finished = False
        self.frameIndex = 0
        self.timer = 0.0
        if self.frames:
            self.image.setImage(self.frames[0])

    def setFrames(self, frames, resetIndex=True):
        self.frames = frames
        if resetIndex:
            self.frameIndex = 0
            self.timer = 0.0
        if self.frames:
            self.image.setImage(self.frames[min(self.frameIndex, len(self.frames) - 1)])

    def setFps(self, fps):
        self.fps = fps



@dataclass
class FrameAnimationCallback:
    frame: int
    callback: Optional[Callable[[], None]] = None