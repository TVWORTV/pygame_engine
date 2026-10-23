import random

import pygame
from pygame.math import Vector2

from collision import (
    CapsuleCollider,
    CircleCollider,
    CollisionWorld,
    DetailLevel,
    FreeCollider,
    PhysicsMaterial,
    RectCollider,
)
from physics import GravityBody, PhysicsWorld

WIDTH = 1000
HEIGHT = 700


class Scene:
    def __init__(self):
        self.collision = CollisionWorld()
        self.world = PhysicsWorld(collision_world=self.collision)
        self.bodies = []
        self.inside = set()
        self.build_level()

    def build_level(self):
        cw = self.collision
        RectCollider((WIDTH, 40), position=(WIDTH / 2, HEIGHT - 20), world=cw)
        RectCollider((40, HEIGHT), position=(20, HEIGHT / 2), world=cw)
        RectCollider((40, HEIGHT), position=(WIDTH - 20, HEIGHT / 2), world=cw)
        FreeCollider(
            [(-150, -80), (-110, -80), (-70, 0), (70, 0), (110, -80), (150, -80), (150, 40), (-150, 40)],
            position=(300, 560),
            world=cw,
        )
        FreeCollider(
            [(0, 0), (180, 40), (320, 30), (420, 90)],
            closed=False,
            position=(520, 300),
            world=cw,
        )
        self.zone = RectCollider((160, 160), position=(800, 540), is_trigger=True, world=cw)
        self.zone.on_trigger_enter = lambda other: self.inside.add(other.id)
        self.zone.on_trigger_exit = lambda other: self.inside.discard(other.id)

    def spawn(self, position):
        kind = random.choice(["box", "circle", "capsule", "poly"])
        body = GravityBody(
            position=position,
            rotation=random.uniform(0, 360),
            use_auto_mass=True,
            world=self.world,
        )
        material = PhysicsMaterial(random.uniform(0.2, 0.7), random.choice([0.0, 0.3, 0.6]))
        common = {"world": self.collision, "density": 0.001, "material": material}
        if kind == "box":
            collider = RectCollider((random.randint(24, 56), random.randint(24, 56)), **common)
        elif kind == "circle":
            collider = CircleCollider(random.randint(10, 26), detail=DetailLevel.HIGH, **common)
        elif kind == "capsule":
            collider = CapsuleCollider((random.randint(16, 28), random.randint(40, 70)), **common)
        else:
            collider = FreeCollider(
                [(-20, 20), (0, -26), (22, 20), (0, 8)],
                **common,
            )
        body.add_collider(collider)
        self.bodies.append(body)

    def step(self, dt):
        self.world.step(dt)

    def draw(self, surface):
        surface.fill((14, 14, 24))
        for collider in self.collision.colliders:
            if collider is self.zone:
                color = (240, 200, 60) if self.inside else (90, 80, 30)
                collider.draw(surface, color, 2)
            elif collider.body is None:
                collider.draw(surface, (110, 110, 140), 2, fill=False)
            else:
                collider.draw(surface, (90, 170, 230), 1, fill=True)


def main(frames=None, screenshot=None):
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    clock = pygame.time.Clock()
    scene = Scene()
    count = 0
    running = True
    while running:
        dt = clock.tick(60) / 1000.0
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                scene.spawn(Vector2(event.pos))
        if pygame.mouse.get_pressed()[0] and count % 6 == 0:
            scene.spawn(Vector2(pygame.mouse.get_pos()))
        scene.step(dt)
        scene.draw(screen)
        pygame.display.flip()
        count += 1
        if frames is not None and count >= frames:
            if screenshot:
                pygame.image.save(screen, screenshot)
            running = False
    pygame.quit()


if __name__ == "__main__":
    main()
