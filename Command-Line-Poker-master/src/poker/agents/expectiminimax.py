# from ..pokergamestate import PokerGameState

class Expectiminimax:
    def __init__(self):
        print('Construct')

    def expectiminimax(self, depth, game_state, cards_drawn):
        if game_state.game.check_game_over(): #start with d = 3
            print(f"eval: {game_state.game.check_game_over()}")
            return game_state.eval_game_state()

        if cards_drawn:
            print(f"eval drawn: {game_state.game.eval_game_state()}")
            return game_state.eval_game_state()
        else:
            #print(f"eval drawn: {self.get_max_action_value(game_state, depth)}")
            max_value =  self.get_max_action_value(game_state, depth)
            print(f"eval max: {max_value}")
            return max_value

        # else:
        #     return self.get_min_action_value(game_state, depth)

    def get_max_action_value(self, game_state, depth):
        depth -= 1

        if game_state.game.check_game_over():  # start with d = 3
            return game_state.eval_game_state()

        bestScore = -999

        for action in game_state.get_legal_actions():
            new_state = game_state.get_successor_state(0, action)
            if new_state is None:
                print(game_state)
                score = game_state.eval_game_state()
                print(f"best max score ... {score}:")
                return score
            bestScore = max(bestScore, self.get_min_action_value(new_state, depth))

        print(f"BEST max score ... {bestScore}:")
        return bestScore

    def get_min_action_value(self, game_state, depth):
        depth -= 1

        if game_state.game.check_game_over():  # start with d = 3
            return game_state.eval_game_state()

        bestScore = -999

        for action in game_state.get_legal_actions():
            new_state = game_state.get_successor_state(1, action)
            if new_state is None:
                score = game_state.eval_game_state()
                print(f"best min score ... {score}:")
                return score
            bestScore = min(bestScore, self.get_max_action_value(new_state, depth))

        print(f"BEST min score ... {bestScore}:")
        return bestScore

        #return self.evaluationFunction(game_state.game)


