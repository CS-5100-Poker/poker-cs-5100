"""
#####################################################################################
TEXAS HOLD 'EM POKER

Source for rules: Wikipedia - "Texas Hold em"
#####################################################################################
"""

from src.poker.pokergamestate import Game


# TODO: Continue major refactor for readability, including smaller functions
# TODO: Repair functionality that broke with refactor
# TODO: Write more unit tests to ensure functionality is there
# TODO: More type hints
# TODO: Get all docstring styles consistent
# TODO: Look for bugs
# TODO: Expand on current functionality
def main():
    game = Game(3, True)  # number of 'rounds' in a game (before resetting coins)
    game.play(2)  # number or 'rounds' (times that betting is reset)
    print(game.net_wins)


if __name__ == '__main__':
    main()
