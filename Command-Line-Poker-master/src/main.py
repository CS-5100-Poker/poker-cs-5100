"""
#####################################################################################
TEXAS HOLD 'EM POKER

Source for rules: Wikipedia - "Texas Hold em"
#####################################################################################
"""

from .poker.game import Game


# TODO: Continue major refactor for readability, including smaller functions
# TODO: Repair functionality that broke with refactor
# TODO: Write more unit tests to ensure functionality is there
# TODO: More type hints
# TODO: Get all docstring styles consistent
# TODO: Look for bugs
# TODO: Expand on current functionality
def main():
    all_winnings = []
    while len(all_winnings) < 10:
        game = Game()
        while len(game.agent_winnings) < 1:
            game.play()
        print(f"AGENT CHIPS {game.agent_winnings}")
        all_winnings = all_winnings + game.agent_winnings
    print(f"all winnings {all_winnings}")
    for w in all_winnings:
        print(f"{w}")



if __name__ == '__main__':
    main()
