
#region Import

import pygame
import asyncio


from scenes.scene import *

from constants.consts import *

from tiles.tilemap import *
from tiles.tile import *
from tiles.ruleTile import *

from camera.camera import *

#endregion

#region Pygame default

pygame.mixer.pre_init(44100, -16, 2, 4096)  #  8192
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption(GAME_NAME)
clock = pygame.time.Clock()
FPS = 60

#endregion

#region Initialization

Camera(*screen.get_size())

TILE_SIZE = 32


def build_placeholder_tileset():
    colors = [
        (60, 60, 70),
        (200, 60, 60),
        (60, 180, 90),
        (60, 110, 200),
    ]
    tileset = []
    for color in colors:
        surface = pygame.Surface((TILE_SIZE, TILE_SIZE))
        surface.fill(color)
        pygame.draw.rect(surface, (0, 0, 0), surface.get_rect(), 1)
        tileset.append(surface)
    return tileset


def build_rule_tile():
    up = Neighbor(0, -1, NeighborCondition.ANY)
    down = Neighbor(0, 1, NeighborCondition.ANY)
    left = Neighbor(-1, 0, NeighborCondition.ANY)
    right = Neighbor(1, 0, NeighborCondition.ANY)
    up_empty = Neighbor(0, -1, NeighborCondition.EMPTY)
    down_empty = Neighbor(0, 1, NeighborCondition.EMPTY)
    left_empty = Neighbor(-1, 0, NeighborCondition.EMPTY)
    right_empty = Neighbor(1, 0, NeighborCondition.EMPTY)

    wads_rule = Rule(
        priority=0,
        result_tile_id=1,
        neighbors=[up, down, left, right],
    )

    ws_rule = Rule(
        priority=1,
        result_tile_id=2,
        neighbors=[up, down, left_empty, right_empty],
    )

    ad_rule = Rule(
        priority=1,
        result_tile_id=3,
        neighbors=[left, right, up_empty, down_empty],
    )

    return RuleTile(default_tile_id=0, rules=[wads_rule, ws_rule, ad_rule])


def place_cross(tilemap, rule_tile, center_x, center_y):
    tilemap.set_tile(center_x, center_y, rule_tile)
    tilemap.set_tile(center_x, center_y - 1, rule_tile)
    tilemap.set_tile(center_x, center_y + 1, rule_tile)
    tilemap.set_tile(center_x - 1, center_y, rule_tile)
    tilemap.set_tile(center_x + 1, center_y, rule_tile)


def place_vertical_pair(tilemap, rule_tile, center_x, center_y):
    tilemap.set_tile(center_x, center_y, rule_tile)
    tilemap.set_tile(center_x, center_y - 1, rule_tile)
    tilemap.set_tile(center_x, center_y + 1, rule_tile)


def place_horizontal_pair(tilemap, rule_tile, center_x, center_y):
    tilemap.set_tile(center_x, center_y, rule_tile)
    tilemap.set_tile(center_x - 1, center_y, rule_tile)
    tilemap.set_tile(center_x + 1, center_y, rule_tile)

#endregion

#region Scenes

class TestScene(Scene):
    def start(self):
        tileset = build_placeholder_tileset()
        rule_tile = build_rule_tile()

        self.tilemap = Tilemap(
            tileset=tileset,
            tile_width=TILE_SIZE,
            tile_height=TILE_SIZE,
            map_width=15,
            map_height=3,
            chunk_size=16,
        )

        place_cross(self.tilemap, rule_tile, 2, 1)
        place_vertical_pair(self.tilemap, rule_tile, 7, 1)
        place_horizontal_pair(self.tilemap, rule_tile, 12, 1)

        map_px_w = self.tilemap.map_width * TILE_SIZE
        map_px_h = self.tilemap.map_height * TILE_SIZE
        origin_x = (screen.get_width() - map_px_w) / 2
        origin_y = (screen.get_height() - map_px_h) / 2
        self.tilemap.setPosition((origin_x, origin_y))

        self.addobj(self.tilemap)


sceneManager = SceneManager(
    scene_classes={
        "test": TestScene,
    },
start_scene= "test"
)

#endregion


async def main():
    running = True

    while running:
        events = pygame.event.get()

        for event in events:
            if event.type == pygame.QUIT:
                running = False

        screen.fill((25, 25, 35))
        dt = clock.tick(FPS) / 1000.0

        sceneManager.handle_events(events)
        sceneManager.update(dt)
        sceneManager.draw(screen)

        pygame.display.flip()
        await asyncio.sleep(0)

    pygame.quit()

asyncio.run(main())