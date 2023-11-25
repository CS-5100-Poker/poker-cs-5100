# from ..pokergamestate import PokerGameState

class Expectiminimax:
    def __init__(self, bob):
        print('Construct')

    def expectiminimax(self, depth, game_state, cards_drawn):
        if depth == 0 or game_state.game.check_game_over: #start with d = 3
            return game_state.eval_game_state()

        if cards_drawn:
            return game_state.eval_game_state()
        elif game_state.maxPlayerTurn:
            return self.get_max_action_value(game_state, depth)
        else:
            return self.get_min_action_value(game_state, depth)

    def get_max_action_value(self, game_state, depth):
        depth -= 1

        if game_state.check_game_over():
            return self.evaluationFunction(game_state.game)

        bestScore = -999

        for action in game_state.getLegalActions():
            new_state = game_state.getSuccessorState(0, action)
            bestScore = max(bestScore, expectiminimax(depth, new_state, game_state.is_card_draw()))

        return bestScore

    def get_min_action_value(self, game_state, depth):
        depth -= 1

        if game_state.check_game_over():
            return self.evaluationFunction(game_state.game)

        bestScore = -999

        for action in game_state.getLegalActions():
            new_state = game_state.getSuccessorState(0, action)
            bestScore = min(bestScore, expectiminimax(depth, new_state, game_state.is_card_draw()))

        return bestScore


