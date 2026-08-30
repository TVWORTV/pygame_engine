import pygame
from engineStructures.singleton import *

class Camera(Singleton):

    def __init__(self, screen_width, screen_height, zoom=1.0):
        self.screen_width = screen_width
        self.screen_height = screen_height

        self.offset_x = 0.0
        self.offset_y = 0.0

        self.zoom = zoom

    def move(self, dx, dy):
        self.offset_x += dx
        self.offset_y += dy

    def world_to_screen(self, world_x, world_y):
        screen_x = (world_x - self.offset_x) * self.zoom
        screen_y = (world_y - self.offset_y) * self.zoom
        return screen_x, screen_y

    def apply(self, rect):
        screen_x, screen_y = self.world_to_screen(rect.x, rect.y)
        screen_w = rect.width * self.zoom
        screen_h = rect.height * self.zoom
        return pygame.Rect(screen_x, screen_y, screen_w, screen_h)

    def set_zoom(self, new_zoom, min_zoom=0.25, max_zoom=4.0):
        self.zoom = max(min_zoom, min(max_zoom, new_zoom))