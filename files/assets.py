import pygame

class Assets:
    _images = {}
    _sounds = {}
    _fonts = {}
    _sheets = {}
    _bgm_paths = {}

    @staticmethod
    def get_image(path):
        if path not in Assets._images:
            Assets._images[path] = pygame.image.load(path).convert_alpha()
        return Assets._images[path]


    @staticmethod
    def get_images_from_sheet(path, sprite_width, sprite_height):
        key = (path, sprite_width, sprite_height)
        if key not in Assets._sheets:
            sheet = Assets.get_image(path)
            sheet_width, sheet_height = sheet.get_size()

            cols = sheet_width // sprite_width
            rows = sheet_height // sprite_height

            sprites = []
            for row in range(rows):
                for col in range(cols):
                    rect = pygame.Rect(
                        col * sprite_width,
                        row * sprite_height,
                        sprite_width,
                        sprite_height
                    )
                    sprite = pygame.Surface((sprite_width, sprite_height), pygame.SRCALPHA)
                    sprite.blit(sheet, (0, 0), rect)
                    sprites.append(sprite)

            Assets._sheets[key] = sprites
        return Assets._sheets[key]
    
    @staticmethod
    def get_sound(path):
        if path not in Assets._sounds:
            Assets._sounds[path] = pygame.mixer.Sound(path)
        return Assets._sounds[path]

    @staticmethod
    def get_bgm(path):
        if path not in Assets._bgm_paths:
            import os
            if not os.path.exists(path):
                raise FileNotFoundError(f"BGM file not found: {path}")
            Assets._bgm_paths[path] = path
        return Assets._bgm_paths[path]

    @staticmethod
    def get_font(path, size):
        key = (path, size)  
        if key not in Assets._fonts:
            Assets._fonts[key] = pygame.font.Font(path, size)
        return Assets._fonts[key]