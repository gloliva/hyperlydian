"""
This module defines everything related to the Player, such as its movement and abilities.

Author: Gregg Oliva
"""

# stdlib imports
from math import sqrt
from typing import List, Set

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
import debug
from defs import ImageType
from events import Event
from sprites.base import CharacterSprite
import sprites.groups as groups
import sprites.projectiles as projectiles
from attacks import Weapon
from stats import stat_tracker
from settings_manager import settings_manager


class Player(CharacterSprite):
    """The player sprite. That's you!"""

    # Sprite
    DEFAULT_HEALTH = 10
    EASY_MODE_HEALTH = 15
    DEFAULT_SPEED = 5
    INITIAL_ROTATION = 90
    ROTATION_AMOUNT = 2

    # Menu
    MENU_SPEED = 6

    # Image
    IMAGE_SCALE = 1.5
    ANIMATION_TIMER_INCREMENT = 0.1

    def __init__(self, game_screen_rect: pg.Rect, weapons: List[Weapon]) -> None:
        spawn_location = (
            game_screen_rect.width / 2,
            game_screen_rect.height - 100,
        )

        image_types_to_files = {
            ImageType.DEFAULT: ["spaceships/player/player_ship.png"],
            ImageType.HIT: ["spaceships/player/player_ship_hit.png"],
            ImageType.HEAL: ["spaceships/player/player_ship_upgrade.png"],
            ImageType.COLLECT: ["spaceships/player/player_ship_collected.png"]
        }

        health = self.DEFAULT_HEALTH if not settings_manager.easy_mode else self.EASY_MODE_HEALTH

        super().__init__(
            image_types_to_files,
            health,
            self.DEFAULT_SPEED,
            spawn_location,
            weapons,
            image_scale=self.IMAGE_SCALE,
        )

        # Additional Player attributes
        self.max_health = health
        self.projectiles_in_range = set()
        self.overlapping_enemies: Set[CharacterSprite] = set()
        self.nearby_notes = set()
        self.last_time_hit = pg.time.get_ticks()
        self.last_time_note_collected = pg.time.get_ticks()

        # Menu attributes
        self.menu_direction = self.MENU_SPEED

    def move(self, pressed_keys, game_screen_rect: pg.Rect):
        """
        Determine how the player should move and rotate based on the user's keyboard input.
        Also tracks movement-based stats.
        """
        movement_vector = [0, 0]

        # check collided enemies
        enemy_collision_vector = self.get_enemy_collision_vector()

        # move player based on key input
        if pressed_keys[K_UP] and enemy_collision_vector[0] != 1:
            self.rect.move_ip(0, -self.movement_speed)
            movement_vector[1] -= self.movement_speed
        if pressed_keys[K_DOWN] and enemy_collision_vector[1] != 1:
            self.rect.move_ip(0, self.movement_speed)
            movement_vector[1] += self.movement_speed
        if pressed_keys[K_LEFT] and enemy_collision_vector[2] != 1:
            self.rect.move_ip(-self.movement_speed, 0)
            movement_vector[0] -= self.movement_speed
        if pressed_keys[K_RIGHT] and enemy_collision_vector[3] != 1:
            self.rect.move_ip(self.movement_speed, 0)
            movement_vector[0] += self.movement_speed

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
        rotation_amount = 0
        if pressed_keys[K_q]:
            rotation_amount = self.ROTATION_AMOUNT
            self.rotate(self.current_rotation + self.ROTATION_AMOUNT)
        if pressed_keys[K_e]:
            rotation_amount = -self.ROTATION_AMOUNT
            self.rotate(self.current_rotation - self.ROTATION_AMOUNT)

        # handle stats
        speed = sqrt(movement_vector[0]**2 + movement_vector[1]**2)
        stat_tracker.player__curr_velocity.update(*movement_vector)
        stat_tracker.player__curr_speed.update(speed)
        stat_tracker.player__angle.update(self.current_rotation)

        # rotating and moving
        if rotation_amount != 0 and speed > 0:
            stat_tracker.player__last_rotation_direction.update(rotation_amount)
            stat_tracker.player__frames__moving_and_rotating += 1
        # only rotating
        elif rotation_amount != 0:
            stat_tracker.player__last_rotation_direction.update(rotation_amount)
            stat_tracker.player__frames__rotating += 1
        # only moving
        elif speed > 0:
            stat_tracker.player__frames__moving += 1
        # completely still
        else:
            stat_tracker.player__frames__still += 1

        # calculate angle quadrant
        if self.current_rotation >= 0 and self.current_rotation < 90:
            stat_tracker.player__frames__per_angle_quadrant.add_at_index(0, 1)
        elif self.current_rotation >= 90 and self.current_rotation < 180:
            stat_tracker.player__frames__per_angle_quadrant.add_at_index(1, 1)
        elif self.current_rotation >= 180 and self.current_rotation < 270:
            stat_tracker.player__frames__per_angle_quadrant.add_at_index(2, 1)
        else:
            stat_tracker.player__frames__per_angle_quadrant.add_at_index(3, 1)

    def get_enemy_collision_vector(self):
        """
        Checks to see whether the Player is colliding with an enemy, and prevent it from moving
        if that's the case.
        """
        enemy_collision_vector = [0, 0, 0, 0]

        threshold = int(self.mask_size[0] * 0.45)

        for enemy in self.overlapping_enemies.copy():
            collide_point = pg.sprite.collide_mask(self, enemy)
            if enemy.is_dead or pg.sprite.collide_mask(self, enemy) is None:
                # No longer colliding
                self.overlapping_enemies.remove(enemy)
                continue

            horizontal, vertical = collide_point[0], collide_point[1]
            # check top
            if vertical < threshold:
                enemy_collision_vector[0] = 1

            # check bottom
            if vertical > (self.mask_size[1] - threshold):
                enemy_collision_vector[1] = 1

            # check left
            if horizontal < threshold:
                enemy_collision_vector[2] = 1

            # check right
            if horizontal > (self.mask_size[0] - threshold):
                enemy_collision_vector[3] = 1


        if len(self.overlapping_enemies) <= 0:
            return [0, 0, 0, 0]

        return enemy_collision_vector

    def move_in_menu(self, game_screen_rect: pg.Rect):
        """This defines how the Player moves in the CREDITS MENU."""
        self.rect.move_ip(self.menu_direction, 0)

        # don't move out of bounds
        if self.rect.left < 0:
            self.rect.left = 0
            self.menu_direction *= -1
        if self.rect.right > game_screen_rect.width:
            self.rect.right = game_screen_rect.width
            self.menu_direction *= -1

    def take_damage(self, damage: int) -> None:
        """
        When the Player gets hit by an enemy projectile, lose health based on the projectile's damage
        and show the damage animation.
        """
        if debug.PLAYER_INVINCIBLE:
            return

        curr_time = pg.time.get_ticks()
        stat_tracker.player__time__between_getting_hit.add(curr_time - self.last_time_hit)
        stat_tracker.player__health_lost += damage
        super().take_damage(damage)
        stat_tracker.player__curr_health.update(self.health)
        self.last_time_hit = curr_time
        if self.is_dead and not settings_manager.player_invincible:
            pg.event.post(Event.PLAYER_DEATH)

    def heal(self, health: int) -> None:
        """When the Player collides with a healh upgrade, gain health and show the heal animation"""
        self.health += health
        if self.health > self.max_health:
            self.health = self.max_health
        stat_tracker.player__curr_health.update(self.health)
        stat_tracker.player__health_gained += health

        self.animation_on = True
        self.image_type = ImageType.HEAL
        self.curr_image_id = 0
        self.show_animation()

    def collect_note(self) -> None:
        """When the Player collides with a Note show the collect animation"""
        self.animation_on = True
        self.image_type = ImageType.COLLECT
        self.curr_image_id = 0
        self.show_animation()

    def attack(self, in_menu: bool = False):
        """Attack with the equipped weapon"""
        attack_center = (self.rect.centerx, self.rect.centery)
        self.equipped_weapon.attack(
            projectile_center=attack_center,
            movement_angle=self.current_rotation,
        )
        if not in_menu:
            stat_tracker.player__frames__firing += 1

    def add_projectiles_in_range(self, projectiles: List[projectiles.Projectile]):
        """Keep track of projectiles that the Player is close to in order to track dodges"""
        for projectile in projectiles:
            if projectile not in self.projectiles_in_range:
                self.projectiles_in_range.add(projectile)
                stat_tracker.player__dodges += 1

    def update_dodges(self, projectile: projectiles.Projectile):
        """If the Player hits one of the projectiles that is nearby, remove it from being "dodged" """
        if projectile in self.projectiles_in_range:
            self.projectiles_in_range.remove(projectile)
            stat_tracker.player__dodges -= 1

    def add_notes_in_range(self, notes: List) -> None:
        """Keep track of notes that the Player is close to in order to track missed notes"""
        for note in notes:
            if note not in self.nearby_notes:
                self.nearby_notes.add(note)
                stat_tracker.player__missed_nearby_notes += 1

    def update_missed_notes(self, note) -> None:
        """If the Player hits one of the notes that is nearby, remove it from being "missed" """
        if note in self.nearby_notes:
            self.nearby_notes.remove(note)
            stat_tracker.player__missed_nearby_notes -= 1

    def update_enemies_collided(self, enemy: CharacterSprite) -> None:
        """Keep track of enemies the player is colliding with to not re-trigger the colliding logic"""
        if enemy not in self.overlapping_enemies:
            self.overlapping_enemies.add(enemy)
            stat_tracker.player__enemies_collided += 1

    def on_death(self):
        """Check to see if the Player should die or not, based on the settings"""
        if settings_manager.player_invincible:
            self.health = 1
            return

        super().on_death()


def create_player(game_screen_rect: pg.Rect, in_menu: bool = False) -> Player:
    """Creates a new Player object on every game start"""
    track_stat = True if not in_menu else False
    damage_increase = 2 if settings_manager.easy_mode else 0

    # Create player weapons
    energy_turret = Weapon(
        projectiles.PlayerMusicNote,
        groups.player_projectiles,
        groups.all_sprites,
        Weapon.INFINITE_AMMO,
        damage=1 + damage_increase,
        attack_speed=12,
        rate_of_fire=100,
        center_deltas=[(0, 24), (0, -24)],
        projectile_scale=0.15,
        track_stat=track_stat,
        weapon_index=0,
    )
    energy_beam = Weapon(
        projectiles.PlayerAccidental,
        groups.player_projectiles,
        groups.all_sprites,
        Weapon.INFINITE_AMMO,
        attack_speed=10,
        damage=5 + damage_increase,
        rate_of_fire=300,
        projectile_scale=0.5,
        track_stat=track_stat,
        weapon_index=1,
    )

    # Create player object
    player = Player(game_screen_rect, weapons=[energy_turret, energy_beam])

    # add to sprite group
    groups.all_sprites.add(player)

    # update stats
    if track_stat:
        stat_tracker.player__starting_position.update(player.rect.centerx, player.rect.centery)
        stat_tracker.player__starting_angle.update(player.INITIAL_ROTATION)
    return player
