import pygame



"""

panel_image = Assets.get_image("assets/ui_panel.png")
border_size = 16 

    stretch/fit it into an area
button_rect = pygame.Rect(100, 100, 220, 60)

draw_nine_slice(screen, panel_image, button_rect, border_size)

"""

def draw_nine_slice(screen, image, dest_rect, border):
    w, h = image.get_size()
    b = border

    src = {
        "tl": pygame.Rect(0, 0, b, b),
        "tr": pygame.Rect(w-b, 0, b, b),
        "bl": pygame.Rect(0, h-b, b, b),
        "br": pygame.Rect(w-b, h-b, b, b),
        "top":    pygame.Rect(b, 0, w-2*b, b),
        "bottom": pygame.Rect(b, h-b, w-2*b, b),
        "left":   pygame.Rect(0, b, b, h-2*b),
        "right":  pygame.Rect(w-b, b, b, h-2*b),
        "center": pygame.Rect(b, b, w-2*b, h-2*b),
    }

    dx, dy, dw, dh = dest_rect
    mid_w, mid_h = dw - 2*b, dh - 2*b

    # corners
    screen.blit(image.subsurface(src["tl"]), (dx, dy))
    screen.blit(image.subsurface(src["tr"]), (dx+dw-b, dy))
    screen.blit(image.subsurface(src["bl"]), (dx, dy+dh-b))
    screen.blit(image.subsurface(src["br"]), (dx+dw-b, dy+dh-b))

    # edges
    screen.blit(pygame.transform.scale(image.subsurface(src["top"]), (mid_w, b)), (dx+b, dy))
    screen.blit(pygame.transform.scale(image.subsurface(src["bottom"]), (mid_w, b)), (dx+b, dy+dh-b))
    screen.blit(pygame.transform.scale(image.subsurface(src["left"]), (b, mid_h)), (dx, dy+b))
    screen.blit(pygame.transform.scale(image.subsurface(src["right"]), (b, mid_h)), (dx+dw-b, dy+b))

    # center
    screen.blit(pygame.transform.scale(image.subsurface(src["center"]), (mid_w, mid_h)), (dx+b, dy+b))