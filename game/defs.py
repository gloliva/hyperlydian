# stdlib imports
from enum import Enum

# Game frames
FPS = 60


# Screen constants
SCREEN_TOP = 0
SCREEN_LEFT = 0
SCREEN_WIDTH = 1440
SCREEN_HEIGHT = 900


# Define game states
class GameState(Enum):
    MAIN_MENU = 0
    GAMEPLAY = 1
    DEATH_MENU = 3
    QUIT = 4


# OSC constants
ADDRESS = '127.0.0.1'  # localhost
PORT = 8001
INCOMING_PORT = 8002


# Projectile types
REST = 'rest'
SHARP = 'sharp'
FLAT = 'flat'
NATURAL = 'natural'

PROJECTILE_TYPES = [REST, SHARP, FLAT, NATURAL]


# Assets constants
PNG_PATH = 'assets/png'


# Max application constants
# MAX_APPLICATION_PATH = 'dist/max-hyperlydian.app'
MAX_APPLICATION_PATH = 'dist/max-hyperlydian.app/Contents/MacOS/max-hyperlydian'


# Music constants
NUM_VOICES = 3
