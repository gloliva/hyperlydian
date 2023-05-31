# 3rd-party imports
import pygame as pg
from pygame.locals import (
    K_q,
    K_e,
    K_UP,
    K_DOWN,
    K_LEFT,
    K_RIGHT,
)

# project imports
from events import Event


class Player(pg.sprite.Sprite):
    DEFAULT_HEALTH = 3
    DEFAULT_SPEED = 5
    ROTATION_AMOUNT = 2
    DRAW_LAYER = 2

    def __init__(self, game_screen_rect: pg.Rect, primary_attack) -> None:
        super().__init__()

        # Create sprite surface
        image_file = "assets/spaceships/player_ship.png"
        self.original_image = pg.transform.scale_by(pg.image.load(image_file), 1.5).convert_alpha()
        self.surf = self.original_image

        # Get sprite rect
        spawn_location = (game_screen_rect.width / 2, game_screen_rect.height - 100)
        self.rect = self.surf.get_rect(center=spawn_location)

        # Create sprite mask
        self.mask = pg.mask.from_surface(self.surf)

        # Set layer sprite is drawn to
        self._layer = self.DRAW_LAYER

        # rotation
        self.current_rotation = 0

        # Player attributes
        self.max_health = self.DEFAULT_HEALTH
        self.curr_health = self.max_health
        self.movement_speed = self.DEFAULT_SPEED
        self.primary_attack = primary_attack

    def update(self, pressed_keys, game_screen_rect: pg.Rect):
        # move player based on key input
        if pressed_keys[K_UP]:
            self.rect.move_ip(0, -self.movement_speed)
        if pressed_keys[K_DOWN]:
            self.rect.move_ip(0, self.movement_speed)
        if pressed_keys[K_LEFT]:
            self.rect.move_ip(-self.movement_speed, 0)
        if pressed_keys[K_RIGHT]:
            self.rect.move_ip(self.movement_speed, 0)

        # don't move out of bounds
        if self.rect.left < 0:
            self.rect.left = 0
        if self.rect.right > game_screen_rect.width:
            self.rect.right = game_screen_rect.width
        if self.rect.top <= 0:
            self.rect.top = 0
        if self.rect.bottom > game_screen_rect.height:
            self.rect.bottom = game_screen_rect.height

        # handle rotation
        if pressed_keys[K_q]:
            self.rotate(self.current_rotation + self.ROTATION_AMOUNT)
        if pressed_keys[K_e]:
            self.rotate(self.current_rotation - self.ROTATION_AMOUNT)

    def rotate(self, rotation_angle: int):
        self.current_rotation = rotation_angle
        self.surf = pg.transform.rotate(self.original_image, rotation_angle)

        # make sure image retains its previous center
        current_image_center = self.rect.center
        self.rect = self.surf.get_rect()
        self.rect.center = current_image_center

        # generate new mask
        self.mask = pg.mask.from_surface(self.surf)

    def take_damage(self, damage: int) -> None:
        self.curr_health -= damage
        if self.is_dead():
            self.kill()
            pg.event.post(Event.PLAYER_DEATH)

    def is_dead(self):
        return self.curr_health <= 0

    def light_attack(self):
        attack_center = (self.rect.centerx, self.rect.centery)
        movement_angle = 180 + self.current_rotation
        rotation_angle = self.current_rotation

        self.primary_attack.attack(
            projectile_center_position=attack_center,
            movement_angle=movement_angle,
            rotation_angle=rotation_angle
        )

    def heavy_attack(self):
        pass

    def special_ability(self):
        pass
