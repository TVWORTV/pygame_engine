import math
import random

import pygame

from physics import Falloff, ForceMode, GravityBody, GravityCenter, GravityMode, PhysicsWorld


def main():
    pygame.init()
    screen = pygame.display.set_mode((1000, 700))
    clock = pygame.time.Clock()
    world = PhysicsWorld.default()
    mid = pygame.Vector2(500, 350)
    GravityCenter(mid, strength=900.0, radius=900.0, falloff=Falloff.INVERSE_SQUARE, core_radius=40.0)
    bodies = []
    for i in range(12):
        angle = random.uniform(0, math.tau)
        distance = random.uniform(120, 300)
        offset = pygame.Vector2(math.cos(angle), math.sin(angle)) * distance
        speed = math.sqrt(900.0 * 40.0 ** 2 / distance)
        tangent = pygame.Vector2(-offset.y, offset.x).normalize() * speed
        body = GravityBody(position=mid + offset, gravity_mode=GravityMode.CENTERS)
        body.velocity = tangent
        bodies.append(body)
    running = True
    while running:
        dt = clock.tick(60) / 1000.0
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                for body in bodies:
                    body.add_explosion_force(60000.0, event.pos, 300.0)
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1:
                    for body in bodies:
                        body.gravity_mode = GravityMode.SIMPLE
                if event.key == pygame.K_2:
                    for body in bodies:
                        body.gravity_mode = GravityMode.DIRECTIONAL
                        body.gravity_direction = pygame.Vector2(1, -1)
                if event.key == pygame.K_3:
                    for body in bodies:
                        body.gravity_mode = GravityMode.CENTERS
        world.step(dt)
        screen.fill((10, 10, 20))
        pygame.draw.circle(screen, (255, 200, 60), mid, 14)
        for body in bodies:
            pygame.draw.circle(screen, (120, 200, 255), body.position, 6)
        pygame.display.flip()
    pygame.quit()


if __name__ == "__main__":
    main()
