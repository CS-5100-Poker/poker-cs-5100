from enum import Enum, auto


class ComputerPlayingStyle(Enum):
    SAFE = auto()
    RISKY = auto()
    RANDOM = auto()
    HAND_AWARE = auto()
    MONTE_CARLO_TREE_SEARCH = 'MCTS'
