"""
This module defines projectiles that are fired from weapons.
Projectiles have a speed and damage associated with them.

Author: Gregg Oliva
"""

# stdlib
import math
from typing import Tuple

# 3rd-party imports
import pygame as pg

# project imports
from defs import REST, SHARP, FLAT, NATURAL
from exceptions import AssetLoadError
from sprites.base import construct_asset_full_path

class Projectile(pg.sprite.Sprite):
    """Projectile base class. Projectiles are what actually do damage and are associated with a Weapon instance"""
    # Default attrs
    DEFAULT_DAMAGE = 1
    DEFAULT_SPEED = 1
    DEFAULT_ANGLE = 0

    # Image
    IMAGE_FILE = None

    # Layers
    DRAW_LAYER = 4

    # Colors
    AVAILABLE_COLORS = None
    COLOR = None

    # Variants
    AVAILABLE_VARIANTS = None
    NUM_VARIANTS = 1

    def __init__(
            self,
            center_position: Tuple[int, int],
            damage: int,
            speed: int,
            movement_angle: int,
            image_scale: float = 1.0,
            variant_number: int = 0,
        ) -> None:
        super().__init__()

        # Handle sprite color, if needed
        if self.COLOR is not None:
            if self.COLOR not in self.AVAILABLE_COLORS:
                raise AssetLoadError(
                    f'Passed in color "{self.COLOR}" not in available Projectile colors: {self.AVAILABLE_COLORS}'
                )

        # Handle variants
        self.variant_number = variant_number
        self.variant = ''
        if self.AVAILABLE_VARIANTS is not None:
            self.variant = self.AVAILABLE_VARIANTS[variant_number]

        image_file = self.IMAGE_FILE.format(color=self.COLOR, variant=self.variant, variant_number=variant_number)

        # Sprite attributes
        image = pg.image.load(construct_asset_full_path(image_file)).convert_alpha()
        self.surf = pg.transform.rotozoom(image, movement_angle, image_scale)

        # Set projectile rect
        self.rect = self.surf.get_rect(center=center_position)
        self.starting_position = self.rect.center

        # Create sprite mask
        self.mask = pg.mask.from_surface(self.surf)

        # Update the drawing layer
        self._layer = self.DRAW_LAYER

        # Weapon attributes
        self.damage = damage if damage is not None else self.DEFAULT_DAMAGE
        self.movement_speed = speed if speed is not None else self.DEFAULT_SPEED
        self.movement_angle = movement_angle if movement_angle is not None else self.DEFAULT_ANGLE

    def update(self, game_screen_rect: pg.Rect):
        # Calculate new position based on the angle of fire
        # We negate Y since the top of the screen is negative, and the bottom is positive
        x = self.movement_speed * math.cos(math.radians(self.movement_angle))
        y = -1 * self.movement_speed * math.sin(math.radians(self.movement_angle))

        self.rect.move_ip(x, y)
        out_of_bounds = (
            self.rect.left > game_screen_rect.right or
            self.rect.right < game_screen_rect.left or
            self.rect.top > game_screen_rect.bottom or
            self.rect.bottom < game_screen_rect.top
        )

        if out_of_bounds:
            self.kill()

    def get_distance_traveled(self) -> float:
        x_delta = self.rect.centerx - self.starting_position[0]
        y_delta = self.rect.centery - self.starting_position[1]
        return math.sqrt((x_delta)**2 + (y_delta)**2)


# The following classes define specific projectiles that are used by Player and Enemy weapons
class PlayerMusicNote(Projectile):
    """Fast, low-damage projectile used by the Player's first weapon"""
    DEFAULT_DAMAGE = 1
    DEFAULT_SPEED = 1
    DEFAULT_ANGLE = 180
    IMAGE_FILE = "projectiles/player/notes/note_{variant_number}.png"
    AVAILABLE_COLORS = ('blue', 'red')
    NUM_VARIANTS = 6


class PlayerAccidental(Projectile):
    """Slow, high-damage projectile used by the Player's second weapon"""
    DEFAULT_DAMAGE = 5
    DEFAULT_SPEED = 8
    IMAGE_FILE = "projectiles/player/accidentals/{variant}.png"
    AVAILABLE_VARIANTS = (NATURAL, SHARP, FLAT)
    NUM_VARIANTS = 3


class EnemyQuarterRest(Projectile):
    """Enemy projectile used by Strafer Grunt enemies"""
    DEFAULT_DAMAGE = 1
    DEFAULT_SPEED = 10
    DEFAULT_ANGLE = 180
    IMAGE_FILE = "projectiles/enemy/rests/rest.png"
    AVAILABLE_VARIANTS = (REST,)


class EnemyAccidental(Projectile):
    """Enemy projectile used by Spinner Grunt enemies"""
    DEFAULT_DAMAGE = 1
    DEFAULT_SPEED = 1
    IMAGE_FILE = "projectiles/enemy/accidentals/{variant}.png"
    AVAILABLE_VARIANTS = (NATURAL, SHARP, FLAT)
    NUM_VARIANTS = 3
