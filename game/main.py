"""
The Entrypoint to the application. The main loop calls functions that run additional loops, such
as menu loops and the main gameplay loop. Each function returns the next state to call. If a function returns
None, that indicates to the main loop to Quit the application.

This file is both the entrypoint and exit point of the application.

Summary of program logic:
    * Main loop
    * Menu loop(s)
    * Gameplay loop
    * Death menu loop
    * Gameplay / Death Menu loops repeat until Quit
    * Quit causes Main loop to exit
    * Application close (both Max and Python)

Author: Gregg Oliva
"""

#stdlib imports
import os
import sys

# 3rd-party imports
import pygame as pg
from pygame.locals import QUIT, RESIZABLE
import sounddevice as sd

# project imports
from defs import (
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
    GameState,
    PNG_PATH,
)
from debug import DISABLE_OPENING_MAX_APPLICATION
from exceptions import QuitOnLoadError
from menus.loading import loading_screen
from gameplay import run_gameplay
from menus.main_menu import run_main_menu
from menus.credits import run_credits_menu
from menus.death import run_death_menu
from menus.how_to_play import run_how_to_play_menu
from menus.settings import run_settings_menu
from stats import stat_tracker


# initial pygame setup
pg.init()


# set app icon; path changes depending on whether this is via Python or a Standalone build
try:
    base_path = sys._MEIPASS
except Exception:
    base_path = os.path.abspath(".")

game_icon_file = os.path.join(base_path, PNG_PATH, 'icons/icon_32x32@2x.png')
pg.display.set_icon(pg.image.load(game_icon_file))


# set up display
MAIN_SCREEN = pg.display.set_mode(
    (SCREEN_WIDTH, SCREEN_HEIGHT),
    flags=RESIZABLE,
)
pg.display.set_caption('HyperLydian')

# set up clock
CLOCK = pg.time.Clock()


def main():
    """
    Main Program Loop.

    Gets default audio output device then updates the initialization stats before
    entering the main application loop.

    Handles transitioning between different states.

    The first transition state is the Loading Screen while the Max Application is loading.
    """
    main_loop = True
    next_state = GameState.LOADING_SCREEN

    # init music
    output_device_name = get_default_audio_output_device()
    stat_tracker.control__output_device.update(output_device_name)
    stat_tracker.control__max_init += 1
    stat_tracker.send_stats()

    try:
        while main_loop:
            # event handler
            for event in pg.event.get():
                # Quit the game
                if event.type == QUIT:
                    main_loop = False

            # move to the next state
            next_state = transition_state(next_state, CLOCK, MAIN_SCREEN)
            if next_state is None:
                main_loop = False

            # lock FPS
            CLOCK.tick(60)
    except QuitOnLoadError:
        quit_game(CLOCK, MAIN_SCREEN)
    except Exception:
        # Catch all exception, close Max Application if anything errors out
        quit_game(CLOCK, MAIN_SCREEN)
        raise


def get_default_audio_output_device():
    """Get the default audio output device selected by the OS"""
    default_device_num = sd.default.device[1]
    devices = sd.query_devices()
    output_device_name = devices[default_device_num]['name']
    return output_device_name


def close_max_application():
    """Send Max a signal to close the application"""
    if not DISABLE_OPENING_MAX_APPLICATION:
        stat_tracker.control__max_quit.update(1)

    stat_tracker.control__record_music.update(0)


def quit_game(game_clock: pg.time.Clock, main_screen: pg.Surface):
    """Stop all game loops and quit game"""
    # turn off music
    stat_tracker.control__menu_init.update(0)
    stat_tracker.control__max_init -= 1
    # close Max/MSP
    close_max_application()
    # send closing stats to Max
    stat_tracker.send_stats()


# Game State transitions
GAME_STATE_TO_LOOP_MAP = {
    GameState.LOADING_SCREEN: loading_screen,
    GameState.MAIN_MENU: run_main_menu,
    GameState.CREDITS: run_credits_menu,
    GameState.HOW_TO_PLAY: run_how_to_play_menu,
    GameState.SETTINGS: run_settings_menu,
    GameState.GAMEPLAY: run_gameplay,
    GameState.DEATH_MENU: run_death_menu,
    GameState.QUIT: quit_game,
}


def transition_state(next_state: GameState, game_clock: pg.time.Clock, main_screen: pg.Surface):
    """Get a loop function from a GameState"""
    state_loop = GAME_STATE_TO_LOOP_MAP[next_state]
    return state_loop(game_clock, main_screen)


if __name__ == "__main__":
    main()
    pg.quit()
