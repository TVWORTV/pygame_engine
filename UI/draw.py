

import pygame


def blit_rotated(screen, surface, topleft, rotation):
    if rotation == 0:
        screen.blit(surface, topleft)
        return

    rect = surface.get_rect(topleft=topleft)
    rotated = pygame.transform.rotate(surface, -rotation)  
    rotatedRect = rotated.get_rect(center=rect.center)
    screen.blit(rotated, rotatedRect.topleft)