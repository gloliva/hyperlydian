# stdlib imports
from typing import Any, Dict

# project imports
import debug
from defs import SCREEN_WIDTH, SCREEN_HEIGHT
from osc_client import osc, OSCHandler


class Stat:
    """A stat to be sent via OSC"""
    def __init__(self, value, send: bool = True) -> None:
        self.value = value
        self.send = send

    def __add__(self, other) -> "Stat":
        stat = Stat(self.value + other.value, self.send) \
            if isinstance(other, Stat) \
            else Stat(self.value + other, self.send)

        return stat

    def __sub__(self, other) -> "Stat":
        stat = Stat(self.value - other.value, self.send) \
            if isinstance(other, Stat) \
            else Stat(self.value - other, self.send)

        return stat

    def __mul__(self, other) -> "Stat":
        stat = Stat(self.value * other.value, self.send) \
            if isinstance(other, Stat) \
            else Stat(self.value * other, self.send)

        return stat

    def __div__(self, other) -> "Stat":
        stat = Stat(self.value / other.value, self.send) \
            if isinstance(other, Stat) \
            else Stat(self.value / other, self.send)

        return stat

    def __truediv__(self, other) -> "Stat":
        return self.__div__(other)

    def __lt__(self, other) -> bool:
        return self.value < other.value \
            if isinstance(other, Stat) \
            else self.value < other

    def __le__(self, other) -> bool:
        return self.value <= other.value \
            if isinstance(other, Stat) \
            else self.value <= other

    def __eq__(self, other) -> bool:
        return self.value == other.value \
            if isinstance(other, Stat) \
            else self.value == other

    def __ne__(self, other) -> bool:
        return self.value != other.value \
            if isinstance(other, Stat) \
            else self.value != other

    def __gt__(self, other) -> bool:
        return self.value > other.value \
            if isinstance(other, Stat) \
            else self.value > other

    def __ge__(self, other) -> bool:
        return self.value >= other.value \
            if isinstance(other, Stat) \
            else self.value >= other

    def __str__(self) -> str:
        return str(self.value)

    def __repr__(self) -> str:
        return str(f'Stat(Value={self.value}, OSC={self.send})')


class TimeStat:
    """A stat that tracks time in ms, seconds, minutes, and hours"""
    def __init__(self, total_ms, send: bool = True) -> None:
        self.total_ms = total_ms
        self.send = send

        seconds, self.ms = divmod(self.total_ms, 1000)
        minutes, self.seconds = divmod(seconds, 60)
        self.hours, self.minutes = divmod(minutes, 60)

    @property
    def time(self):
        return (self.hours, self.minutes, self.seconds, self.ms)

    def __sub__(self, other) -> "TimeStat":
        if isinstance(other, TimeStat):
            return TimeStat(self.total_ms - other.total_ms)
        elif isinstance(other, (int, float)):
            return TimeStat(self.total_ms - other)
        else:
            raise TypeError(f'{self.__class__} unable to perform subtraction with type: {type(other)}')

    def __str__(self) -> str:
        return str(self.total_ms)

    def __repr__(self) -> str:
        return str(f'TimeStat(Hours={self.hours}, Minutes={self.minutes}, Seconds={self.seconds}, Milliseconds={self.ms})')


class AvgStat:
    def __init__(self, send: bool = True) -> None:
        self.sum = 0
        self.count = 0
        self.send = send

    @property
    def avg(self) -> float:
        if self.count > 0:
            return self.sum / self.count
        else:
            return 0

    def add(self, val: float):
        self.sum += val
        self.count += 1

    def __str__(self) -> str:
        return str(self.avg)

    def __repr__(self) -> str:
        return str(f'AvgStat(Average={self.avg}, Count={self.count})')

class ListStat:
    def __init__(self, initial_length: int = 0, initial_fill: int = 0, send: bool = True) -> None:
        self.list = [initial_fill for _ in range(initial_length)]
        self.send = send

    def add_at_index(self, index: int, val: int):
        self.list[index] += val

    def update(self, *vals: int):
        for idx, val in enumerate(vals):
            self.list[idx] = val

    def __str__(self) -> str:
        return str(', '.join(self.list))

    def __repr__(self) -> str:
        return str(f'ListStat(List={self.list})')


class StatTracker:
    """Tracks game information"""
    def __init__(self, osc: OSCHandler) -> None:
        self.osc = osc

        # Stats that track throughout each playthrough
        self.control__max_init = Stat(0)
        self.control__game_init = Stat(0)
        self.control__screen_width = Stat(SCREEN_WIDTH)
        self.control__screen_height = Stat(SCREEN_HEIGHT)

        self.game__play_count = Stat(0)
        self.game__time__total_played = TimeStat(0)

    def init_new_playthrough(self, start_time_ms: int = 0, player_max_health: int = 0):
        self.start_time = start_time_ms
        self.time_last_enemy_killed = start_time_ms

        self.control__game_init = Stat(0)

        self.game__score = Stat(0)
        self.game__time__current_playthrough = TimeStat(0)

        self.player__position = ListStat(initial_length=2)
        self.player__curr_speed = Stat(0)
        self.player__angle = Stat(0)
        self.player__rotation_amount = Stat(0)
        self.player__avg_shots_per_second = AvgStat()
        self.player__accuracy = Stat(0.0)
        self.player__avg_time_between_kills = AvgStat()
        self.player__max_health = Stat(player_max_health)
        self.player__curr_health = Stat(player_max_health)
        self.player__health_lost = Stat(0)
        self.player__near_misses = Stat(0)

        self.weapon__selected = Stat(0)
        self.weapon__total_shots_fired = Stat(0)
        self.weapon__shots_per_weapon = ListStat(initial_length=2)

        self.enemies__num_on_screen = Stat(0)
        self.enemies__hit = Stat(0)
        self.enemies__killed = Stat(0)

        self.game__play_count += 1

    def send_stats(self):
        osc_stats = self.convert_osc_stats_to_dict()
        self.osc.union_bundle(osc_stats)
        if not debug.DISABLE_OSC_SEND:
            self.osc.send_full_bundle()

    def update_stats(self):
        if self.weapon__total_shots_fired > 0:
            self.player__accuracy = (self.enemies__hit / self.weapon__total_shots_fired) * 100

    def convert_osc_stats_to_dict(self) -> Dict[str, Any]:
        stat_dict = {}

        for stat_name, stat in self.__dict__.items():
            if not hasattr(stat, 'send') or not stat.send:
                continue

            if isinstance(stat, Stat):
                stat_dict[stat_name] = stat.value
            elif isinstance(stat, TimeStat):
                stat_dict[stat_name] = stat.time
            elif isinstance(stat, AvgStat):
                stat_dict[stat_name] = stat.avg
            elif isinstance(stat, ListStat):
                stat_dict[stat_name] = stat.list

        return stat_dict

    def set_game_time(self, total_time_elapsed_ms: int):
        # calculate playthrough time
        playthrough_time_elapsed = total_time_elapsed_ms - self.start_time
        self.game__time__current_playthrough = TimeStat(playthrough_time_elapsed)

        # calculate total time
        self.game__time__total_played = TimeStat(total_time_elapsed_ms)

    def print_stats(self):
        print(f'---- Game {self.game__play_count} ----')
        print(f'Score: {self.game__score}')
        print(f'Enemies Killed: {self.enemies__killed}')
        print(f'Enemy shots dodged: {self.player__near_misses}')
        print(f'Avg time to kill an Enemy: {self.player__avg_time_between_kills.avg / 1000}')
        print(f'Total Shots Fired: {self.weapon__total_shots_fired}')
        print(f'Enemies Hit: {self.enemies__hit}')
        print(f'Player Shot Accuracy: {self.player__accuracy}%')
        print(
            f'Time Survived: {self.game__time__current_playthrough.hours} Hours, '
            f'{self.game__time__current_playthrough.minutes} Minutes, '
            f'{self.game__time__current_playthrough.seconds} Seconds'
        )
        print(
            f'Total Time Played: {self.game__time__total_played.hours} Hours, '
            f'{self.game__time__total_played.minutes} Minutes, '
            f'{self.game__time__total_played.seconds} Seconds'
        )
        print()


stat_tracker = StatTracker(osc=osc)
