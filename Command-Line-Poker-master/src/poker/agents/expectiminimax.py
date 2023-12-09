# from ..pokergamestate import PokerGameState

import copy

class Expectiminimax:
    def __init__(self):
        pass

    def expectiminimax(self, depth, game_state, cards_drawn, agent_index):
        current_state = copy.deepcopy(game_state)
        curr_active_players = current_state.players
        if depth == 0 or all(player.is_locked or player.is_all_in or player.is_folded for player in curr_active_players):
            return current_state.eval_game_state(agent_index)

        # if cards_drawn:
        #     print(f"eval drawn: {game_state.game.eval_game_state()}")
        #     return game_state.eval_game_state()
        #else:
        min_value = self.get_min_action_value(current_state, depth, agent_index)
        return min_value

        # else:
        #     return self.get_min_action_value(game_state, depth)

    def get_max_action_value(self, game_state, depth, agent_index):
        depth -= 1
        current_state = copy.deepcopy(game_state)
        curr_active_players = current_state.players

        #print(f"MAX OF: {curr_active_players[agent_index].name} AT {agent_index}")

        if depth == 0 or all(player.is_locked or player.is_all_in for player in curr_active_players):
            return current_state.eval_game_state(agent_index)

        bestScore = -999

        for action in current_state.get_legal_actions():
            new_state = current_state.get_successor_state(1 - agent_index, action)
            bestScore = max(bestScore, self.get_min_action_value(new_state, depth, 1 - agent_index))

        #print(f"MAX VALUE FOR {curr_active_players[agent_index].name}: {bestScore}")
        return bestScore

    def get_min_action_value(self, game_state, depth, agent_index):
        depth -= 1
        current_state = copy.deepcopy(game_state)
        curr_active_players = current_state.players

        #print(f"MIN OF: {curr_active_players[agent_index].name} AT {agent_index}")

        if depth == 0 or all(player.is_locked or player.is_all_in for player in curr_active_players):
            return current_state.eval_game_state(agent_index)

        bestScore = -999

        for action in current_state.get_legal_actions():
            new_state = current_state.get_successor_state(1 - agent_index, action)
            bestScore = min(bestScore, self.get_max_action_value(new_state, depth, 1 - agent_index))

        #print(f"MIN VALUE FOR {curr_active_players[agent_index].name}: {bestScore}")
        return bestScore

        #return self.evaluationFunction(game_state.game)


