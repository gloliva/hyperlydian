# stdlib imports
from typing import Tuple

# 3rd-party impoarts
import pygame as pg


class Sprite(pg.sprite.Sprite):
    """Base Sprite class to be subclassed by player and enemy objects"""
    HIT_TIMER_INCREMENT = 0.2
    DRAW_LAYER = 2

    def __init__(
            self,
            image_files: str,
            health: int,
            movement_speed: int,
            spawn_location: Tuple[int, int],
            primary_attack,
            image_scale: float = 1.0,
            image_rotation: int = 0,
        ) -> None:
        super().__init__()

        # Load Sprite images
        self.images = [
            pg.transform.rotozoom(
                pg.image.load(image_file).convert_alpha(),
                image_rotation,
                image_scale
            ) for image_file in image_files
        ]
        self.num_images = len(image_files)
        self.curr_image_id = 0

        # Select sprite image to display
        self.surf = self.images[self.curr_image_id]

        # Get sprite rect
        self.rect = self.surf.get_rect(center=spawn_location)

        # Create sprite mask
        self.mask = pg.mask.from_surface(self.surf)

        # Set layer sprite is drawn to
        self._layer = self.DRAW_LAYER

        # Hit animation attributes
        self.hit_animation_on = False

        # Sprite attributes
        self.health = health
        self.movement_speed = movement_speed
        self.primary_attack = primary_attack

    def update(self, *args, **kwargs):
        if self.hit_animation_on:
            self.show_hit_animation()

        self.move(*args, **kwargs)

    def move(self, *args, **kwargs):
        raise NotImplementedError(
            'Each Sprite subclass must override their update method.'
        )

    def attack(self):
        raise NotImplementedError(
            'Each Sprite subclass must override their attack method.'
        )

    def take_damage(self, damage: int) -> None:
        self.health -= damage
        self.hit_animation_on = True
        # TODO: setting this to 1 uses the hit sprite png
        # will need to change this later if working with multiple sprites for animation
        self.curr_image_id = 1
        self.show_hit_animation()
        if self.is_dead():
            self.kill()

    def show_hit_animation(self):
        self.curr_image_id = (self.curr_image_id + self.HIT_TIMER_INCREMENT) % self.num_images
        image_id = int(self.curr_image_id)
        self.surf = self.images[image_id]
        if image_id == 0:
            self.curr_image_id = 0
            self.hit_animation_on = False

    def is_dead(self):
        return self.health <= 0
